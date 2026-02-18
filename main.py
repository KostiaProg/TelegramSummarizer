from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes

from pyrogram import Client
from pyrogram.errors import ChatIdInvalid, PeerIdInvalid, ChannelInvalid, BadRequest

from model import summarize

api_id = 39406457
api_hash = "dae8359668e99e352a06128300e69e3f"

# to show a button
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Summarize", callback_data="summarize")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Want to summarize smt?:', reply_markup=reply_markup)

# when clicked - summarize
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "summarize":
        await summarize(update, context)

async def summarize(update: Update, context: ContextTypes.DEFAULT_TYPE):  
    await update.message.reply_text('Hello! Enter the user, chat link and then whitespace and a number of messages to summarize')

    async with Client("my_account", api_id, api_hash) as app:
        reply_text = await update.message.text.split(" ")
        if len(reply_text) == 2:
            try:
                # split
                target = reply_text[0]
                await app.get_chat(target) # try to find chat, if can't - exception
                limit = int(reply_text[1])

                messages = []
                async for msg in app.get_chat_history(target, limit=limit):
                    # get each sender and it's message
                    sender = msg.from_user.username if msg.from_user else "?"
                    text = (msg.text or msg.caption or "").strip()

                    # add to message from each user
                    messages.append(sender + " - " + text)

                str_messages = ".\n".join(messages)

                await update.message.reply_text(f'Summarization: {summarize(str_messages)}')

            except ValueError:
                await update.message.reply_text('Pass integer as the second argument')

            except (ChatIdInvalid, PeerIdInvalid, ChannelInvalid, BadRequest) as e:
                await update.message.reply_text(f"Coulldn't access the group/user, context: {e}")

if __name__ == '__main__':
    bot_app = ApplicationBuilder().token("YOUR_API_TOKEN").build()

    # Commands
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CallbackQueryHandler(button_handler))
    bot_app.add_handler(CommandHandler("summarize", summarize)) # can also call like /summarize

    # Start the bot
    bot_app.run_polling()
