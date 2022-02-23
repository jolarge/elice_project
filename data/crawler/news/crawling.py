import requests
import calendar
import platform
import time
from time import sleep

from multiprocessing import Process
import re
from bs4 import BeautifulSoup
from util import connectDB
from datetime import date, datetime
import json
# package 설정
from CustomExceptions import *
from ariticleparser import ArticleParser


class Crewler(object):
    def __init__(self):
        self.categories = {'정치': 100, '경제': 101, '사회': 102, '생활/문화': 103, '세계': 104, 'IT과학': 105, '오피니언': 110}
        self.selected_categories = []
        self.date = {'start_year': 0, 'start_month': 0, 'end_year': 0, 'end_month': 0}
        self.user_operating_system = str(platform.system())

    def set_category(self, *args):
        for key in args:
            if self.categories.get(key) is None:
                raise InvalidCategory(key)
        self.selected_categories = args

    def set_date_range(self, start_year, start_month, end_year, end_month):
        args = [start_year, start_month, end_year, end_month]
        if start_year > end_year:
            raise InvalidYear(start_year, end_year)
        if start_month < 1 or start_month > 12:
            raise InvalidMonth(start_month)
        if end_month < 1 or end_month > 12:
            raise InvalidMonth(end_month)
        if start_year == end_year and start_month == end_month:
            raise OverbalanceMonth(start_month, end_month)
        # if start_day < 1 or start_day > 31:

        for key, date in zip(self.date, args):
            self.date[key] = date
        print(self.date)

    @staticmethod
    def make_news_page_url(category_url, start_year, end_year, start_month, end_month, start_day, end_day):
        made_urls = []
        for year in range(start_year, end_year + 1):
            target_start_month = start_month
            target_end_month = end_month

            if start_year != end_year:
                if year == start_year:
                    target_start_month = start_month
                    target_end_month = 12
                elif year == end_year:
                    target_start_month = 1
                    target_end_month = end_month
                else:
                    target_start_month = 1
                    target_end_month = 12

            for month in range(target_start_month, target_end_month + 1):
                if month == target_start_month and year == start_year:
                    for month_day in range(start_day, end_day + 1):
                        if len(str(month)) == 1:
                            month = "0" + str(month)
                        if len(str(month_day)) == 1:
                            month_day = "0" + str(month_day)

                        url = category_url + str(year) + str(month) + str(month_day)

                        ## totalpage 계산 네이버 페이지는 page=10000이 최대이다.
                        ## 만약 10000 페이지가 없는경우 최대 페이지로 redirecting 된다.
                        totalpage = ArticleParser.find_news_totalpage(url + "&page=10000")

                        for page in range(1, totalpage + 1):
                            made_urls.append(url + "&page=" + str(page))
                else:
                    for month_day in range(1, calendar.monthrange(year, month)[1] + 1):
                        if len(str(month)) == 1:
                            month = "0" + str(month)
                        if len(str(month_day)) == 1:
                            month_day = "0" + str(month_day)

                        url = category_url + str(year) + str(month) + str(month_day)

                        ## totalpage 계산 네이버 페이지는 page=10000이 최대이다.
                        ## 만약 10000 페이지가 없는경우 최대 페이지로 redirecting 된다.
                        totalpage = ArticleParser.find_news_totalpage(url + "&page=10000")

                        for page in range(1, totalpage + 1):
                            made_urls.append(url + "&page=" + str(page))

        return made_urls

    @staticmethod
    def get_url_data(url, max_tries=5):
        remaining_tries = int(max_tries)

        while remaining_tries > 0:
            try:
                return requests.get(url, headers={'User-Agent':'Mozilla/5.0'})
            except requests.exceptions.ConnectTimeout:
                sleep(1)
            remaining_tries = remaining_tries - 1
        raise ResponseTimeout()

    def crawling(self, category_name, start_year, end_year, start_month, end_month, start_day, end_day):
        # MultiProcess PID
        print(category_name + "새로운 PID 구동: " + str(os.getpid()))
        print(start_year, end_year, start_month, end_month, start_day, end_day)

        total_count = 0


        pass_count = 0
        # 기사 url 형식
        url_format = f'http://news.naver.com/main/list.nhn?mode=LSD&mid=sec&sid1={self.categories.get(category_name)}&date='
        # start_year년 start_month월 ~ end_year의 end_month 날짜 까지 기사를 수집합니다.
        # target_urls = self.make_news_page_url(url_format, self.date['start_year'], self.date['end_year'], self.date['start_month'], self.date['end_month'])
        target_urls = self.make_news_page_url(url_format, start_year, end_year, start_month, end_month, start_day, end_day)
        # print(target_urls)
        print(category_name, "Url are generated")
        print("The crawler starts")

        newsDB = connectDB()
        nomal = newsDB['nomal']




        for url in target_urls:

            request = self.get_url_data(url)

            document = BeautifulSoup(request.content, 'html.parser')

            # html - newflash_body - type06_headline, type06
            # 각 페이지에 있는 기사들의 url 저장
            temp_post = document.select('.newsflash_body .type06_headline li dl')
            temp_post.extend(document.select('.newsflash_body .type06 li dl'))

            # 각 페이지에 있는 기사들의 url 저장
            post_urls = []

            for line in temp_post:
                # 해당 되는 page에서 모든 기사들의 URL을 post_urls 리스트에 넣음
                post_urls.append(line.a.get('href'))

            del temp_post

            for content_url in post_urls:

                # 크롤링 대기 시간
                sleep(0.01)
                total_count += 1
                # 크롤링 수 확인 10000개 마다
                if total_count % 10000 == 1:
                    print(category_name)
                    print(content_url)
                    print('크롤링 갯수 : ' + str(total_count))
                    # print('넘어간 갯수 : ' +  str(pass_count))

                # # Summary 데이터 수집 - 수집이 안되는 경우가 너무 많다.
                # oid = content_url.split('&')[-2].split('=')[-1]
                # aid = content_url.split('&')[-1].split('=')[-1]
                # summary_url = "https://tts.news.naver.com/article/{}/{}/summary"
                # summary_url = summary_url.format(oid, aid)
                # # print(summary_url)
                # try:
                #     request_summary = self.get_url_data(summary_url)
                #     request_summary = request_summary.json()
                # except:
                #     pass_count +=1
                #     # print(pass_count)
                #     continue

                # 기사 HTML 가져옴
                request_content = self.get_url_data(content_url)

                try:
                    document_content = BeautifulSoup(request_content.content, 'html.parser')
                except:
                    continue

                try:

                    # 기사 제목을 가져옴
                    tag_headline = document_content.find_all('h3', {'id': 'articleTitle'}, {'class': 'tts_head'})
                    # 뉴스 기사 제목 초기화
                    text_headline = ''
                    text_headline = text_headline + ArticleParser.clear_headline(
                        str(tag_headline[0].find_all(text=True)))
                    # 공백일 경우 기사 제외 처리
                    if not text_headline:
                        continue

                    # 기사 본문 가져옴
                    tag_content = document_content.find_all('div', {'id': 'articleBodyContents'})
                    # 뉴스 기사 본문 초기화
                    text_content = ''
                    text_content = text_content + ArticleParser.clear_content(str(tag_content[0].find_all(text=True)))
                    # 공백일 경우 기사 제외 처리
                    if not text_content:
                        continue

                    # 기사 언론사 가져옴
                    tag_company = document_content.find_all('meta', {'property': 'me2:category1'})

                    # 언론사 초기화
                    text_company = ''
                    text_company = text_company + str(tag_company[0].get('content'))

                    # 공백일 경우 기사 제외 처리
                    if not text_company:
                        continue

                    # 기사 시간대 가져옴
                    time = re.findall('<span class="t11">(.*)</span>', request_content.text)[0]

                    # text_summary = ''
                    # text_summary = text_summary + ArticleParser.clear_summary(str(request_summary['summary']))
                    # 공백일 경우 기사 제외 처리
                    # if not text_summary:
                    #     continue
                    # 해당 기사 요약문 제공 하지 않는 경우
                    # if text_summary == '해당 기사는 요청하신 자동 요약문을 제공할 수 없습니다.':
                    #     text_summary = text_headline

                    new = {'time': time, 'category': category_name, 'text_headline': text_headline,
                           'text_context': text_content, 'text_company': text_company, 'context_url': content_url}

                    nomal.insert_one(new)

                    del time
                    del text_company, text_content, text_headline
                    del tag_company
                    del tag_content, tag_headline
                    del request_content, document_content

                except Exception as ex:
                    del request_content, document_content
                    pass
        print(category_name + "PID 종료: " + str(os.getpid()))

    def start(self):
        # MultiProcess 크롤링
        # for category_name in self.selected_categories:
        #     proc = Process(target=self.crawling, args = (category_name,))
        #     proc.start()
        # for category_name in self.selected_categories:
        #     self.crawling(category_name)
        year = datetime.now().year;
        month = datetime.now().month;
        day = datetime.now().day;
        #day = datetime.now().day - 1;

        year, month, day = make_yesterday(year, month, day)


        #if today == 1:


        proc = Process(target=self.crawling, args=('사회', year, year, month, month, day, day))
        proc.start()

        proc = Process(target=self.crawling, args=('정치', year, year, month, month, day, day))
        proc.start()

        proc = Process(target=self.crawling, args=('경제', year, year, month, month, day, day))
        proc.start()

        proc = Process(target=self.crawling, args=('생활/문화', year, year, month, month, day, day))
        proc.start()

        # proc = Process(target=self.crawling, args=('사회', year, year, month, month, 26, 29))
        # proc.start()
        #
        # proc = Process(target=self.crawling, args=('정치', year, year, month, month, 26, 29))
        # proc.start()
        #
        # proc = Process(target=self.crawling, args=('경제', year, year, month, month, 26, 29))
        # proc.start()
        #
        # proc = Process(target=self.crawling, args=('생활/문화', year, year, month, month, 26, 29))
        # proc.start()

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

if __name__ == "__main__":
    crewler = Crewler()
    crewler.start()











