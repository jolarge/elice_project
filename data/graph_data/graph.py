import pandas as pd
from tqdm import tqdm
import pymongo
from pymongo import MongoClient
from datetime import datetime
import calendar
import os
def mongo_connect(host, port, db_name, db_col, username, password):
    client = MongoClient(host, port, username = username, password = password)
    db = client[db_name]
    col = db[db_col]
    return col

predict = mongo_connect('mongodb://localhost', 27017, 'newsDB', 'predict', username = "master", password = "mWERIzcBlF")
graph = mongo_connect('mongodb://localhost', 27017, 'newsDB', 'graph', username = "master", password = "mWERIzcBlF")

path = os.getcwd() + '/project-template/data/graph_data/'
# predict = mongo_connect('mongodb://34.64.216.132', 27017, 'newsDB', 'predict', username = "root", password = "0000")
# graph = mongo_connect('mongodb://34.64.216.132', 27017, 'newsDB', 'graph', username = "root", password = "0000")

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

# query = {"time":{"$lt":today}}
query = {"time":{"$gte":today}}


news = pd.DataFrame(predict.find(query,{'_id':False, 'context_url':False}))

time = news['time'].map(lambda x: x.split()[0][:-1])
# title = news['text_headline'].map(lambda x : re.sub('[-=+,#/\?:^$.@*\"※~&%ㆍ!』\\‘|\(\)\[\]\<\>`\'…\"\“》’·]', ' ', x))
labels = list(news['label'])
category = news['category']

u_time = list(time.unique())

u_category = list(category.unique())

item = [[0 for i in range(len(u_category))] for i in range(len(u_time))]
# item_n = [[0 for i in range(len(u_category))]  for i in range(len(u_time))]
# item_m = [[0 for i in range(len(u_category))]  for i in range(len(u_time))]
total = [[0 for i in range(len(u_category))] for i in range(len(u_time))]

# 긍정 +1 부정 -1
for i in tqdm(range(len(time))):
    try:
        t = u_time.index(time[i])
        c = u_category.index(category[i])
        item[t][c] += (labels[i][2] - labels[i][1])
        total[t][c] += max(labels[i])
    except:
        pass

# print(item)

item_1 = [[0 for i in range(len(u_category))] for i in range(len(u_time))]
for i in range(len(item)):
    for j in range(len(item[i])):
        try:
            item_1[i][j] = (item[i][j] / total[i][j])
        except:
            item_1[i][j] = item[i][j]

from sklearn.preprocessing import StandardScaler

df = pd.DataFrame(item_1)


# transformer = StandardScaler()
# item_4 = transformer.fit_transform(df)

df = pd.DataFrame(item_1, columns = u_category, index =u_time)

# print(df)

df = df.reset_index().rename(columns={'index':'날짜'})

js = df.to_json(path + today + '.json', orient='records', force_ascii=False)

import json

with open(path + today + '.json', 'r', encoding='utf-8') as f:
    json_data = json.load(f)

graph.insert_many(json_data)

#df.to_json('./data/graph_data5.json', orient='records', force_ascii=False)