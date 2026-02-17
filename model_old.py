import torch
import torch.nn as nn
from torch import optim
import torch.nn.functional as F

import json
import pandas as pd

device = "cuda" if torch.cuda.is_available() else "cpu"

# get train and test data
TEST_PATH = "data/ukr_test.jsonl"
TRAIN_PATH = "data/ukr_train.jsonl"

x_train, y_train = pd.DataFrame(), pd.DataFrame()
with open(TRAIN_PATH, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            json_line = json.loads(line)
            x_train.loc[len(x_train)] = json_line['text']
            y_train.loc[len(x_train)] = json_line['summary']
        except json.JSONDecodeError as e:
            print(f"Problem with: {line}")

x_test, y_test = pd.DataFrame(), pd.DataFrame()
with open(TEST_PATH, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            json_line = json.loads(line)
            x_test.loc[len(x_train)] = json_line['text']
            y_test.loc[len(x_train)] = json_line['summary']
        except json.JSONDecodeError as e:
            print(f"Problem with: {line}")


# actual model
class EncoderRNN(nn.Module):
    def __init__(self, input_size, hidden_size, dropout_p=0.1):
        super().__init__()
        self.hidden_size = hidden_size

        self.embedding = nn.Embedding(input_size, hidden_size)
        self.gru = nn.GRU(hidden_size, hidden_size, batch_first=True) # Gate (simpler version of Long Short Term Memory)
        self.dropout = nn.Dropout(dropout_p)

    def forward(self, input):
        embedded = self.dropout(self.embedding(input))
        output, hidden = self.gru(embedded)
        return output, hidden
    
class DecoderRNN(nn.Module):
    def __init__(self, hidden_size, output_size):
        super().__init__()
        self.embedding = nn.Embedding(output_size, hidden_size)
        self.gru = nn.GRU(hidden_size, hidden_size, batch_first=True) # Gate (simpler version of Long Short Term Memory)
        self.out = nn.Linear(hidden_size, output_size)

    def forward(self, encoder_outputs, encoder_hidden, target_tensor=None):
        batch_size = encoder_outputs.size(0)
        decoder_input = torch.empty(batch_size, 1, dtype=torch.long, device=device).fill(SOS_token)