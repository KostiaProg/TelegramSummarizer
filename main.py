from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

import asyncio
from pyrogram import Client
from pyrogram.errors import ChatIdInvalid, PeerIdInvalid, ChannelInvalid, BadRequest

from dotenv import load_dotenv
from os import getenv

from model import summarize

# get .env data keys
load_dotenv()
api_id = getenv("API_ID")
api_hash = getenv("API_HASH")
bot_token = getenv("BOT_TOKEN")
phone_number=getenv("PHONE_NUMBER")

if not api_id or not api_hash or not bot_token:
    raise ValueError("Didn't found some api")

# create user client
user_client = Client(
    "current_session",
    api_id=api_id,
    api_hash=api_hash,
    phone_number=phone_number
)

# summarize button
keyboard = [
        [InlineKeyboardButton("Summarize", callback_data="summarize")]
    ]
reply_markup = InlineKeyboardMarkup(keyboard)

# to show a button
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Want to summarize smt?:', reply_markup=reply_markup)

# when clicked - summarize
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "summarize":
        await summarize_startup(update, context)


async def summarize_startup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ask for chat
    query = update.callback_query
    chat_id = query.message.chat_id if query.message else query.from_user.id

    await context.bot.send_message(
        chat_id=chat_id,
        text="Hello! Enter the user / chat link and then whitespace and a number of messages to summarize"
    )

    context.user_data["awaiting_summarize_input"] = True

async def summarize_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # work with current user's message
    if context.user_data.get("awaiting_summarize_input"):
        reply_text = update.message.text.strip().split(maxsplit=1)
    else:
        return

    # wrong foramtting check
    if len(reply_text) != 2:
        await update.message.reply_text("Wrong format!.\nTry again.", reply_markup=reply_markup)
        return

    try:
        # split
        target = reply_text[0]
        await user_client.get_chat(target) # try to find chat, if can't - exception
        limit = int(reply_text[1])

        messages = []
        async for msg in user_client.get_chat_history(target, limit=limit):
            # get each sender and it's message
            sender = msg.from_user.username if msg.from_user else "?"
            text = (msg.text or msg.caption or "").strip()

            # add to message from each user
            messages.append(sender + " - " + text)

        str_messages = ".\n".join(messages)
        await update.message.reply_text(f'Summarization: {summarize(str_messages)}\n\nWant to summirize something else?', reply_markup=reply_markup)

    except ValueError:
        await update.message.reply_text('Pass integer as the second argument.\nTry again.', reply_markup=reply_markup)

    except (ChatIdInvalid, PeerIdInvalid, ChannelInvalid, BadRequest) as e:
        await update.message.reply_text(f"Coulldn't access the group/user, context: {e}.\nTry again.", reply_markup=reply_markup)

async def main():
    # start user client
    await user_client.start()

    # create bot
    bot_app = ApplicationBuilder().token(bot_token).build()

    # commands
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CallbackQueryHandler(button_handler))
    bot_app.add_handler(CommandHandler("summarize", summarize_startup)) # can also call it like /summarize
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, summarize_logic))

    # start your Telegram bot (polling)
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling(drop_pending_updates=True, allowed_updates=["message", "callback_query"])

    # Keep everything alive
    print("Ctrl+C to stop")
    await asyncio.Event().wait()  # or use pyrogram.idle() if no bot

    # Graceful shutdow
    await bot_app.updater.stop()
    await bot_app.stop()
    await bot_app.shutdown()
    await user_client.stop()

if __name__ == "__main__":
    asyncio.run(main())