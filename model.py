import torch
from transformers import BartTokenizer, BartForConditionalGeneration, Trainer, TrainingArguments
from datasets import load_dataset
from torch.cuda import is_available

# get train and test data
TRAIN_PATH = "data/ukr_train.jsonl"
VAL_PATH = "data/ukr_test.jsonl"
TEST_PATH = "data/ukr_test.jsonl"
MODEL_PATH = "models/"

# process dataset
def preprocess(dataset):
    tokenizer = BartTokenizer.from_pretrained("facebook/bart-large-cnn")

    inputs = tokenizer(dataset['text'], padding='max_length', max_length=1024, truncation=True)
    labels = tokenizer(dataset['summary'], padding='max_length', max_length=128, truncation=True)
    inputs['labels'] = labels["input_ids"]
    return inputs

def train():
    # create BART model
    model = BartForConditionalGeneration.from_pretrained("facebook/bart-large-cnn")

    dataset = load_dataset("json", data_files={
        "train": TRAIN_PATH,
        "val": VAL_PATH,
        "test": TEST_PATH
    })

    tokenized_dataset = dataset.map(preprocess, batched=True)

    # training settings for ukrainian dataset
    training_args = TrainingArguments(
        output_dir=MODEL_PATH,
        num_train_epochs=10,
        per_device_train_batch_size=6,
        per_device_eval_batch_size=6,
        gradient_accumulation_steps=32,
        warmup_steps=400,
        weight_decay=0.05,
        logging_dir="./logs",
        logging_steps=10,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        fp16=True if is_available() else False,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset["train"],
        eval_dataset=tokenized_dataset["val"],
    )

    # train and save
    trainer.train()
    trainer.save_model(MODEL_PATH)
    model.save_pretrained('ukr_summarizer')

def summarize(text: str) -> str:
    # load the model
    model = BartForConditionalGeneration.from_pretrained("./models")
    tokenizer = BartTokenizer.from_pretrained("./models")

    # to gpu
    device = "cuda" if is_available() else "cpu"
    model.to(device)
    model.eval()  

    # tokenize input
    input_ids = tokenizer(text, max_length = 1024, padding='max_length', truncation = True, return_tesors = 'pt').input_ids
    if is_available():
        input_ids = input_ids.to('cuda')
    
    # process it
    with torch.inference_mode():
        output = model.generate(input_ids, max_length=128, num_beams = 5)

    # get summary
    summary_ids = output[0].tolist()
    return tokenizer.decode(summary_ids, skip_special_tokens = True)