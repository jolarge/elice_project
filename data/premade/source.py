from pymongo import MongoClient
import pandas as pd
import time
from datetime import datetime
import re
import calendar
from tqdm import tqdm
import os

def mongo_connect(host, port, db_name, db_col, username, password):
    client = MongoClient(host, port, username = username, password = password)
    db = client[db_name]
    col = db[db_col]
    return db, col

db, resource = mongo_connect('mongodb://localhost', 27017, 'newsDB', 'resource', username = "master", password = "mWERIzcBlF")
db, predict = mongo_connect('mongodb://localhost', 27017, 'newsDB', 'predict', username = "master", password = "mWERIzcBlF")

path = os.getcwd() + '/project-template/data/premade/'
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
# query = {}



news = pd.DataFrame(predict.find(query))

source = news[['text_company', 'label']]

time = news['time'].map(lambda x: x.split()[0])
title = news['text_headline'].map(lambda x: re.sub('[-=+,#/\?:^$.@*\"※~&%ㆍ!』\\‘|\(\)\[\]\<\>`\'…\"\“》’·]', ' ', x))
keyword = ['코로나', '여행', '대선', '주식', '부동산', '백신', '자영업', 'IT', '친환경', '교육', '수도권']
labels = list(news['label'])
company = news['text_company']

print(title)
u_time = list(time.unique())
print(u_time)
u_company = list(company.unique())
print(len(u_time), len(u_company), len(keyword))

# time / keyword / company 순
# 전체count / 긍정 count/ 부정 count/ noaml count / 긍정 비율 / 부정 비율 / 노말 비율
# item = [[[[0, 0, 0, 0, .0, .0, .0]] * len(u_company)]*len(keyword)]*len(u_time)

item = [[[[0, 0, 0, 0, .0, .0, .0] for _ in range(len(u_company) + 1)] for _ in range(len(keyword))] for _ in
        range(len(u_time) + 1)]

key = [[] for i in range(len(time))]

print(item[0][10][0][5])

time = list(time)
title = list(title)

# for time in u_time:
# for company in u_company:
# for word in keyword:
# print(time, company, word)

for i in tqdm(range(len(time))):
    t = u_time.index(time[i])
    c = u_company.index(company[i])
    for idx in range(len(keyword)):
        if keyword[idx] in title[i]:
            key[i].append(keyword[idx])

source['time'] = time
source['key'] = key
source = source[['time', 'text_company', 'key', 'label']]

# source.to_csv('./data/source.csv', index = False, encoding='utf-8')
# source = pd.read_csv('./data/source.csv', encoding = 'utf-8')
source.to_json(path + today + '(resource).json', orient='records', force_ascii=False)

import json

with open(path + today + '(resource).json', 'r', encoding='utf-8') as f:
    json_data = json.load(f)

resource.insert_many(json_data)