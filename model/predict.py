from pymongo import MongoClient
import pandas as pd
import time
from datetime import datetime
import re
import calendar
import os
# my_client = MongoClient('mongodb://ec2-54-180-86-123.ap-northeast-2.compute.amazonaws.com:27017/', username="root", password="0000")
my_client = MongoClient('mongodb://localhost:27017/', username="master", password="mWERIzcBlF")
#my_client = MongoClient('mongodb://localhost:27017/', username="root", password="0000")
# my_client = MongoClient('localhost:27017/')


newsDB = my_client['newsDB']
nomal = newsDB['nomal']
predict = newsDB['predict']

path = os.getcwd() + '/project-template/data/model/'
# now = datetime.now()
def make_yesterday(year, month, day):
    if day == 1:
        if month == 1:
            month = 12;
            year -= 1;
            day = calendar.monthrange(year, month)[1]
        else:
            month -= 1
            day = calendar.monthrange(year, month)[1]
    else:
        day -= 1
    return year, month, day

year = datetime.now().year
month = datetime.now().month
day = datetime.now().day

year, month, day = make_yesterday(year, month, day)

year = str(year)
month = str(month)
day = str(day)

if len(str(month)) == 1:
    month = "0" + str(month)
if len(str(day)) == 1:
    day = "0" + str(day)

today = year+"."+month+"."+day

query = {"time":{"$gte":today}}
#query = {"time":{"$lt":today}}

news = pd.DataFrame(nomal.find(query,{'_id':False, 'text_context': False}))



data_list = []
for q in zip(news['text_headline']):
    data = []
    clean_title = re.sub('[-=+,#/\?:^$.@*\"※~&%ㆍ!』\\‘|\(\)\[\]\<\>`\'…\"\“》]', ' ', str(q))
    data.append(clean_title)
    data.append('0')

    data_list.append(data)


import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader
import gluonnlp as nlp
from tqdm import tqdm, tqdm_notebook, notebook
import numpy as np
import torch.nn.functional as F

from transformers import DistilBertModel
distilbert_model = DistilBertModel.from_pretrained('monologg/distilkobert')

from tokenization_kobert import KoBertTokenizer
tokenizer = KoBertTokenizer.from_pretrained('monologg/distilkobert')

device = torch.device('cpu')

max_len = 64
batch_size = 64
warmup_ratio = 0.1
num_epochs = 1
max_grad_norm = 1
log_interval = 1000
learning_rate =  4e-5


class BERTDataset(Dataset):
    def __init__(self, dataset, sent_idx, label_idx, bert_tokenizer, max_len,
                 pad, pair):
        tokens, masks, segments, targets = [], [], [], []

        start = time.time()
        # 문장을 토큰화

        # tokens = [bert_tokenizer.encode(d[sent_idx], max_length = max_len, pad_to_max_length=pad) for d in dataset]
        sentenses = [sentense[0] for sentense in dataset]

        tokens = bert_tokenizer.batch_encode_plus(sentenses, max_length=max_len, padding=pad)

        # 마스크 토큰화 한 부분 - 1 아닌 부분 0
        # num_zeros = [t.count(1) for t in tokens]

        # masks = [[1] * (max_len-num_zero) + [0] * num_zero for num_zero in num_zeros]

        # 문장의 전후 관계를 구분해주는 세그먼트는 문장이 1개 밖에 없으므로 모두 0

        # segments = [np.int32(max_len) for i in range(len(tokens))]

        targets = [np.int32(d[label_idx]) for d in dataset]

        masks = tokens['attention_mask']

        valid_length = [mask.count(1) for mask in masks]

        # segments = tokens['token_type_ids']
        tokens = tokens['input_ids']

        self.valid_length = np.array(valid_length)
        self.tokens = np.array(tokens)
        self.masks = np.array(masks)
        # self.segments = np.array(segments)
        self.targets = np.array(targets)

        end = time.time()
        print("Using time : ", round(end - start, 2), end='\n')

    def __getitem__(self, i):
        return (self.tokens[i], self.valid_length[i], self.masks[i], self.targets[i])

    def __len__(self):
        return (len(self.targets))


data_predict = BERTDataset(data_list, 0, 1,tokenizer, max_len, True, False)



predict_dataloader = torch.utils.data.DataLoader(data_predict, batch_size=64, num_workers=0)


class BERTClassifier(nn.Module):
    def __init__(self,
                 bert,
                 hidden_size=768,
                 num_classes=3,  ##클래스 수 조정##
                 dr_rate=None,
                 params=None):
        super(BERTClassifier, self).__init__()
        self.bert = bert
        self.dr_rate = dr_rate

        self.classifier = nn.Linear(hidden_size, num_classes)
        if dr_rate:
            self.dropout = nn.Dropout(p=dr_rate)

    def gen_attention_mask(self, token_ids, valid_length):
        attention_mask = torch.zeros_like(token_ids)
        for i, v in enumerate(valid_length):
            attention_mask[i][:v] = 1
        return attention_mask.float()

    def forward(self, token_ids, valid_length):
        attention_mask = self.gen_attention_mask(token_ids, valid_length)

        # _, pooler = self.bert(input_ids = token_ids, attention_mask = attention_mask.float().to(token_ids.device))
        output = self.bert(input_ids=token_ids, attention_mask=attention_mask.float().to(token_ids.device))
        # print(output[0][:,0])
        # print(output)
        if self.dr_rate:
            out = self.dropout(output[0][:, 0])
        return self.classifier(out)

model = torch.load(path + 'distilmodel_1_2.pt', map_location='cpu')

predict_value = []

test_acc = 0.0
count = 0
model.eval()
for batch_id, (token_ids, valid_length, segment_ids, labels) in enumerate(notebook.tqdm(predict_dataloader)):
    if batch_id % 20 == 0:
        print(str(batch_id) + " / " + str(len(predict_dataloader)) + " " + str((batch_id/len(predict_dataloader)) * 100) + "%")
    token_ids = token_ids.long().to(device)
    segment_ids = segment_ids.long().to(device)
    valid_length= valid_length
    out = model(token_ids, valid_length)
    out = F.softmax(out, dim=1)
    predict_value += out.tolist()
    # print(out.tolist())
    # print(predict_value)
    # count += 1
    # if count == 2:
        # break
    # predect_value.append(out)
    # print(out)
#torch.save(model, './model/model_{}.pt'.format(e+1))
len(predict_value)

news['label'] = predict_value

news = news[['time','category','text_headline','text_company','context_url', 'label']]

js = news.to_json(path  + today + '.json', orient='records', force_ascii=False)

import json

with open(path  + today + '.json', 'r', encoding='utf-8') as f:
    json_data = json.load(f)

predict.insert_many(json_data)

print("Finish Predict")