from transformers import BartTokenizer, BartForConditionalGeneration, Trainer, TrainingArguments
from datasets import load_dataset
from torch.cuda import is_available

# create BART model 
tokenizer = BartTokenizer.from_pretrained("facebook/bart-large-cnn")
model = BartForConditionalGeneration.from_pretrained("facebook/bart-large-cnn")

# get train and test data
TRAIN_PATH = "data/ukr_train.jsonl"
VAL_PATH = "data/ukr_test.jsonl"
TEST_PATH = "data/ukr_test.jsonl"
MODEL_PATH = "models/"

dataset = load_dataset("json", data_files={
    "train": TRAIN_PATH,
    "val": VAL_PATH,
    "test": TEST_PATH
})

# process dataset
def preprocess(dataset):
    inputs = tokenizer(dataset['text'], max_length=1024, truncation=True)
    labels = tokenizer(dataset['summary'], max_length=192, truncation=True)
    inputs['labels'] = labels["input_ids"]
    return inputs

tokenized_dataset = dataset.map(preprocess, batched=True)

# training settings for ukrainian dataset
training_args = TrainingArguments(
    output_dir=MODEL_PATH,
    num_train_epochs=6,
    per_device_train_batch_size=6,
    per_device_eval_batch_size=6,
    warmup_steps=500,
    weight_decay=0.1,
    logging_dir="./logs",
    logging_steps=10,
    evaluation_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
    fp16=True if is_available() else False,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset["train"],
    eval_dataset=tokenized_dataset["validation"],
)

# train and save
trainer.train()
trainer.save_model(MODEL_PATH)