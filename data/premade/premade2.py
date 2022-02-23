import pandas as pd
from tqdm import tqdm, notebook
import calendar

import pymongo
from pymongo import MongoClient

from datetime import datetime
import os
def mongo_connect(host, port, db_name, db_col, username, password):
    client = MongoClient(host, port, username = username, password = password)
    db = client[db_name]
    col = db[db_col]
    return col

resource = mongo_connect('mongodb://localhost', 27017, 'newsDB', 'resource', username = "master", password = "mWERIzcBlF")
premade = mongo_connect('mongodb://localhost', 27017, 'newsDB', 'premade', username = "master", password = "mWERIzcBlF")

# predict = mongo_connect('mongodb://34.64.216.132', 27017, 'newsDB', 'predict', username = "root", password = "0000")
# premade = mongo_connect('mongodb://34.64.216.132', 27017, 'newsDB', 'premade', username = "root", password = "0000")
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


#query = {"time":{"$gte":today}}
#query = {"time":{"$lt":today}}
# query = {"time":{'$regex':'2021.11.29'}}

query = {}

news = pd.DataFrame(resource.find(query,{'_id':False}))
# df_premade = pd.DataFrame(premade.find({"날짜":"전체"},{'_id':False}))

news = news[news['time'] > '2021.01.01']

import re
import ast


time = news['time']
# title = news['text_headline'].map(lambda x: re.sub('[-=+,#/\?:^$.@*\"※~&%ㆍ!』\\‘|\(\)\[\]\<\>`\'…\"\“》’·]', ' ', x))
keyword = ['코로나', '여행', '대선', '주식', '부동산', '백신', '자영업', 'IT', '친환경', '교육', '수도권']
key = list(news['key'])
labels = list(news['label'])
company = news['text_company']



del news


u_time = list(time.unique())
print(u_time)
u_company = list(company.unique())


# time / keyword / company 순
# 전체count / 긍정 count/ 부정 count/ noaml count / 긍정 비율 / 부정 비율 / 노말 비율
# item = [[[[0, 0, 0, 0, .0, .0, .0]] * len(u_company)]*len(keyword)]*len(u_time)

item = [[[[0, 0, 0, 0, .0, .0, .0] for _ in range(len(u_company) + 1)] for _ in range(len(keyword))] for _ in
        range(len(u_time) + 1)]



time = list(time)


# for time in u_time:
# for company in u_company:
# for word in keyword:
# print(time, company, word)
print("Start_premade")
for i in tqdm(range(len(time))):

    if i % 100000 == 0:
        print(str(i) + " / " + str(len(time)) + ' (' + str((i / len(time))*100) + ' %)')
    try:
        t = u_time.index(time[i])
        c = u_company.index(company[i])
        # key_temp = ast.literal_eval(key[i])
        # label_temp = ast.literal_eval(labels[i])
        key_temp = key[i]
        label_temp = labels[i]
        # print(key[i])
        for k in key_temp:

            item[t][keyword.index(k)][c][0] += 1
            # 긍정,부정,노말 비율
            item[t][keyword.index(k)][c][4] += round(label_temp[0], 2)
            item[t][keyword.index(k)][c][5] += round(label_temp[1], 2)
            item[t][keyword.index(k)][c][6] += round(label_temp[2], 2)

            # 긍정, 부정, 노말 count
            item[t][keyword.index(k)][c][1 + label_temp.index(max(label_temp))] += 1
    except:
        pass

    # item[len(u_time)-1][len(keyword)-1][c][0] += 1
    # item[len(u_time)-1][len(keyword)-1][c][1+labels[i].index(max(labels[i]))] += 1
    # item[len(u_time)-1][len(keyword)-1][c][4] += 1
    # item[len(u_time)-1][len(keyword)-1][c][5] += 1
    # item[len(u_time)-1][len(keyword)-1][c][6] += 1

item_2 = [[[0, 0, 0, 0, .0, .0, .0] for _ in range(len(u_company) + 1)] for _ in range(len(u_time) + 1)]

for i in tqdm(range(len(time))):
    if i % 100000 == 0:
        print(str(i) + " / " + str(len(time)) + ' (' + str((i / len(time))*100) + ' %)')

    try:
        t = u_time.index(time[i])
        c = u_company.index(company[i])
        # label_temp = ast.literal_eval(labels[i])
        label_temp = labels[i]
        item_2[t][c][0] += 1

        # 긍정,부정,노말 비율
        item_2[t][c][4] += round(label_temp[0], 2)
        item_2[t][c][5] += round(label_temp[1], 2)
        item_2[t][c][6] += round(label_temp[2], 2)

        # 긍정, 부정, 노말 count
        item_2[t][c][1 + label_temp.index(max(label_temp))] += 1
    except:
        pass


def sum_module(a, b):
    a[0] += b[0]
    a[1] += b[1]
    a[2] += b[2]
    a[3] += b[3]
    a[4] += b[4]
    a[5] += b[5]
    a[6] += b[6]
    return a

# def sum_module2(a, b):
#     if len(b) <= 6: return a
#     a[0] += b[0]
#     a[1] += b[1]
#     a[2] += b[2]
#     a[3] += b[3]
#     a[4] += (b[4] * b[0])
#     a[5] += (b[5] * b[0])
#     a[6] += (b[6] * b[0])
#     return a

for t in notebook.tqdm(range(len(u_time))):
    for k in range(len(keyword)):
        for c in range(len(u_company)):
            item[len(u_time)][k][c] = sum_module(item[len(u_time)][k][c], item[t][k][c])
            item[t][k][len(u_company)] = sum_module(item[t][k][len(u_company)], item[t][k][c])
            item[len(u_time)][k][len(u_company)] = sum_module(item[len(u_time)][k][len(u_company)], item[t][k][c])

for t in notebook.tqdm(range(len(u_time))):
    for c in range(len(u_company)):
        try:
            item_2[len(u_time)][c] = sum_module(item_2[len(u_time)][c], item_2[t][c])
            item_2[t][len(u_company)] = sum_module(item_2[t][len(u_company)], item_2[t][c])
            item_2[len(u_time)][len(u_company)] = sum_module(item_2[len(u_time)][len(u_company)], item_2[t][c])
        except:
            pass

# for k in range(len(keyword)):
#     for c in range(len(u_company)):
#         item[len(u_time)][k][c] = sum_module2(item[len(u_time)][k][c], df_premade[
#             (df_premade['날짜'] == '전체') & (df_premade['키워드'] == keyword[k]) & (df_premade['언론사'] == company[c])][
#             ['전체', '노말', '부정', '긍정', '노말비율', '부정비율', '긍정비율']].values.tolist()[-1])
#
# for k in range(len(keyword)):
#     item[len(u_time)][k][len(u_company)] = sum_module2(item[len(u_time)][k][len(u_company)], df_premade[
#         (df_premade['날짜'] == '전체') & (df_premade['키워드'] == keyword[k]) & (df_premade['언론사'] == '전체')][
#         ['전체', '노말', '부정', '긍정', '노말비율', '부정비율', '긍정비율']].values.tolist()[-1])


# for c in range(len(u_company)):
#      item_2[len(u_time)][c] = sum_module2(item_2[len(u_time)][c], df_premade[(df_premade['날짜'] == '전체') & (df_premade['키워드'] == '전체') & (df_premade['언론사']==company[c])][['전체', '노말', '부정', '긍정','노말비율', '부정비율', '긍정비율']].values.tolist()[-1])
# item_2[len(u_time)][len(u_company)] = sum_module2(item_2[len(u_time)][len(u_company)], df_premade[(df_premade['날짜'] == '전체') & (df_premade['키워드'] == '전체') & (df_premade['언론사']=='전체')][['전체', '노말', '부정', '긍정','노말비율', '부정비율', '긍정비율']].values.tolist()[-1])

result = []
print(len(u_time), len(keyword), len(u_company))

l_company = len(u_company)
l_time = len(u_time)

for t in range(len(u_time)):
    for k in range(len(keyword)):
        for c in range(len(u_company)):
            positive = .0
            negative = .0
            nomal = .0

            if item[t][k][c][0] > 0:
                nomal = item[t][k][c][4] / item[t][k][c][0]
                negative = item[t][k][c][5] / item[t][k][c][0]
                positive = item[t][k][c][6] / item[t][k][c][0]
            result.append({
                '날짜': u_time[t], '키워드': keyword[k], '언론사': u_company[c],
                '전체': item[t][k][c][0], '노말': item[t][k][c][1],
                '부정': item[t][k][c][2], '긍정': item[t][k][c][3],
                '노말비율': nomal, '부정비율': negative,
                '긍정비율': positive})

for t in range(len(u_time)):
    for k in range(len(keyword)):
        positive = .0
        negative = .0
        nomal = .0
        if item[t][k][l_company][0] > 0:
            nomal = item[t][k][l_company][4] / item[t][k][l_company][0]
            negative = item[t][k][l_company][5] / item[t][k][l_company][0]
            positive = item[t][k][l_company][6] / item[t][k][l_company][0]
        result.append({
            '날짜': u_time[t], '키워드': keyword[k], '언론사': '전체',
            '전체': item[t][k][l_company][0], '노말': item[t][k][l_company][1],
            '부정': item[t][k][l_company][2], '긍정': item[t][k][l_company][3],
            '노말비율': nomal, '부정비율': negative,
            '긍정비율': positive})

for c in range(len(u_company)):
    for k in range(len(keyword)):
        positive = .0
        negative = .0
        nomal = .0
        if item[l_time][k][c][0] > 0:
            nomal = item[l_time][k][c][4] / item[l_time][k][c][0]
            negative = item[l_time][k][c][5] / item[l_time][k][c][0]
            positive = item[l_time][k][c][6] / item[l_time][k][c][0]
        result.append({
            '날짜': '전체', '키워드': keyword[k], '언론사': u_company[c],
            '전체': item[l_time][k][c][0], '노말': item[l_time][k][c][1],
            '부정': item[l_time][k][c][2], '긍정': item[l_time][k][c][3],
            '노말비율': nomal, '부정비율': negative,
            '긍정비율': positive})

for k in range(len(keyword)):
    positive = .0
    negative = .0
    nomal = .0
    if item[l_time][k][l_company][0] > 0:
        nomal = item[l_time][k][l_company][4] / item[l_time][k][l_company][0]
        negative = item[l_time][k][l_company][5] / item[l_time][k][l_company][0]
        positive = item[l_time][k][l_company][6] / item[l_time][k][l_company][0]
    result.append({
        '날짜': '전체', '키워드': keyword[k], '언론사': '전체',
        '전체': item[l_time][k][l_company][0], '노말': item[l_time][k][l_company][1],
        '부정': item[l_time][k][l_company][2], '긍정': item[l_time][k][l_company][3],
        '노말비율': nomal, '부정비율': negative,
        '긍정비율': positive})

for t in range(len(u_time)):
    for c in range(len(u_company)):
        positive = .0
        negative = .0
        nomal = .0

        if item_2[t][c][0] > 0:
            nomal = item_2[t][c][4] / item_2[t][c][0]
            negative = item_2[t][c][5] / item_2[t][c][0]
            positive = item_2[t][c][6] / item_2[t][c][0]
        result.append({
            '날짜': u_time[t], '키워드': '전체', '언론사': u_company[c],
            '전체': item_2[t][c][0], '노말': item_2[t][c][1],
            '부정': item_2[t][c][2], '긍정': item_2[t][c][3],
            '노말비율': nomal, '부정비율': negative,
            '긍정비율': positive})

for t in range(len(u_time)):
    positive = .0
    negative = .0
    nomal = .0

    if item_2[t][len(u_company)][0] > 0:
        nomal = item_2[t][len(u_company)][4] / item_2[t][len(u_company)][0]
        negative = item_2[t][len(u_company)][5] / item_2[t][len(u_company)][0]
        positive = item_2[t][len(u_company)][6] / item_2[t][len(u_company)][0]
    result.append({
        '날짜': u_time[t], '키워드': '전체', '언론사': '전체',
        '전체': item_2[t][len(u_company)][0], '노말': item_2[t][len(u_company)][1],
        '부정': item_2[t][len(u_company)][2], '긍정': item_2[t][len(u_company)][3],
        '노말비율': nomal, '부정비율': negative,
        '긍정비율': positive})

for c in range(len(u_company)):
    positive = .0
    negative = .0
    nomal = .0

    if item_2[len(u_time)][c][0] > 0:
        nomal = item_2[len(u_time)][c][4] / item_2[len(u_time)][c][0]
        negative = item_2[len(u_time)][c][5] / item_2[len(u_time)][c][0]
        positive = item_2[len(u_time)][c][6] / item_2[len(u_time)][c][0]
    result.append({
        '날짜': '전체', '키워드': '전체', '언론사': u_company[c],
        '전체': item_2[len(u_time)][c][0], '노말': item_2[len(u_time)][c][1],
        '부정': item_2[len(u_time)][c][2], '긍정': item_2[len(u_time)][c][3],
        '노말비율': nomal, '부정비율': negative,
        '긍정비율': positive})
positive = .0
negative = .0
nomal = .0

if item_2[len(u_time)][len(u_company)][0] > 0:
    nomal = item_2[len(u_time)][len(u_company)][4] / item_2[len(u_time)][len(u_company)][0]
    negative = item_2[len(u_time)][len(u_company)][5] / item_2[len(u_time)][len(u_company)][0]
    positive = item_2[len(u_time)][len(u_company)][6] / item_2[len(u_time)][len(u_company)][0]

result.append({
    '날짜': '전체', '키워드': '전체', '언론사': '전체',
    '전체': item_2[len(u_time)][len(u_company)][0], '노말': item_2[len(u_time)][len(u_company)][1],
    '부정': item_2[len(u_time)][len(u_company)][2], '긍정': item_2[len(u_time)][len(u_company)][3],
    '노말비율': nomal, '부정비율': negative,
    '긍정비율': positive})

df = pd.DataFrame(result)
df

js = df.to_json(path + today + '.json', orient='records', force_ascii=False)

import json

with open(path + today + '.json', 'r', encoding='utf-8') as f:
    json_data = json.load(f)

delete = premade.delete_many({})

# print(delete.deleted_count)

premade.insert_many(json_data)
print("finish_premade")

