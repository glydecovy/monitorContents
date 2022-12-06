import requests
from bs4 import BeautifulSoup
import ssl
from konlpy.tag import Okt  
import re
from selenium import webdriver
import time
from gazpacho import Soup
import telegram 
from telegram import ParseMode
from tabulate import tabulate
import os,sys
from numpy import nan as NA

tabulate.WIDE_CHARS_MODE = True

def text_preprocessing(text):
    stopwords = ['을', '를', '이', '가', '은', '는', '와', '과', '들', 
                '에', '고','의','로','으로','하고','하는','하여','이고', '있다', '했다', 
                 '이다','null', 
                 '~','어서', '어요', '어하네요' , '었네요' , '었는데' , '었습니다' , '었어요' , '었지만'
                 #제외단어 추가
                 ,'라', '구', '수', '제', '큰'
                ]
    tokenizer = Okt() #형태소 분석기 
    # stopwords = []
    token_list = []
    # txt.lower() ?
    txt = re.sub('[^가-힣]', ' ', text) #한글과 영어 소문자만 남기고 다른 글자 모두 제거
    token = tokenizer.morphs(txt) #형태소 분석
    token = [t for t in token if t not in stopwords ] #형태소 분석 결과 중 stopwords에 해당하지 않는 것만 추출
    token_list.append(token)
        
    return token_list, tokenizer


def search_result(search_text, godNm):    
    search_ok_flag = False

    request_headers = { 
    'User-Agent' : ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36') } 

#     wd = webdriver.Chrome('C:\chromedriver_win32\chromedriver.exe')
    options = webdriver.ChromeOptions()
    options.add_argument("start-maximized")
    options.add_argument("lang=ko_KR")
    options.add_argument('headless')
    options.add_argument('window-size=1920x1080')
    options.add_argument("disable-gpu")
    options.add_argument("--no-sandbox")

    # chrome driver
    wd = webdriver.Chrome('chromedriver', options=options)
    wd.implicitly_wait(3)      

    wd.get(url_search+search_text)
    time.sleep(5)
    html = wd.page_source
    bs = BeautifulSoup(html, 'html.parser')

    arta = bs.find_all("dd", {"class": "prdt-name"})  
#     print(arta)
    print('[검색결과]')
    for art in arta:	
        print(art.text.strip())
	search_word = None 
# 검색 결과중, 최초 상품명과 일치 하는 검색결과가 있으면 True 
# 예) 최초 상품명 : 오렌지착즙주스1L
#     검색어(형태소 분리) :['오렌지', '착즙', '주스']
#    "검색어" 로 검색한 결과에 "오렌지착즙주스1L" 가 있는지 확인하는 로직
        search_word = art.find("em", {"class": "search-word"})
        print(search_word)
# 	search_word 가 존재하는 상품명은 검색어 등록이 된 경우, search_word 없으면 추천상품으로 검색된 경우
#       신규 상품명 = 검색상품명 & 검색어에 의한 조회 성공한 경우만 true
        if godNm.strip() == art.text.strip() and search_word != None : search_ok_flag = True
	return search_ok_flag 

def sendMsg(telegram_token, cat_id, msgText):
	bot 	= telegram.Bot(token = telegram_token)
	bot.sendMessage(chat_id = cat_id, text=msgText, parse_mode="HTML")
	
if __name__ == '__main__':	
	telegram_token = sys.argv[1]
	cat_id 	= sys.argv[2]

	tokenizer = Okt() 

	context = ssl._create_unverified_context()

	url = 'https://m.glyde.co.kr/api/display/getRecommandGodList?gtrndSn=1021'
	url_search = 'https://m.glyde.co.kr/ui/search/searchResultPage?keyword='

	headers = {'Content-Type': 'application/json; charset=utf-8'}
	response = requests.get(url, headers=headers)

	for x in response.json():      # json → dict
		xx = x['god']
		print('===================================================================================')
		print('상품명 :'+ xx['shrtenGodNm'])
		godNm = xx['shrtenGodNm']

		x2 = text_preprocessing(godNm)[:1][0]

		if godNm.find("라구") != -1 : x2[0] += ["라구"]
		elif godNm.find("수제") != -1 : x2[0] += ["수제"]
		elif godNm.find("얼큰") != -1 : x2[0] += ["얼큰"]
		elif godNm.find("순댓국") != -1 : x2[0] += ["순댓국"]

		print('검색어(형태소 분리) :'+ str(x2[0]))
		for value in x2[0] :
			print('[검색어] :'+ value)
			search_flag = search_result(value, godNm)
			print(value + ":"+str(search_flag))
			#     search_flag = True 인 경우, 정상 검색 상태
			if search_flag == False :    
				t = '[상품명] :'+ xx['shrtenGodNm'] +'\n'
				t += '[검색어] :'+ value +'\n'
				t += '[검색결과] 없음'
				print(t)
				try:
					sendMsg(telegram_token, cat_id, "<pre>"+t+"</pre>")
				except Exception as e:
					print("e:",e)   
