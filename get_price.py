########################################################################################################
# 네이버 현재가 추출
########################################################################################################
import time, datetime, random
import requests
from bs4 import BeautifulSoup as bs

list_jongmok = [
    "005930", "005830", "001040", "105560"
]

while True:
    for code in list_jongmok:
        base_url = "https://finance.naver.com/item/main.nhn?code=" + code
        response = requests.get( base_url, headers={"User-agent": "Mozilla/5.0"} )
        soup = bs(response.text, 'html.parser')
        idx = 0
        for href in soup.find("div", class_="rate_info").find_all("dd"):
            if idx == 0:
                str_href = str(href).split(" ")[1]
                now_dtm = datetime.datetime.now()
                run_hms = str(now_dtm.hour).zfill(2) + str(now_dtm.minute).zfill(2) + str(now_dtm.second).zfill(2)
                print(run_hms, str_href)                
            idx += 1
    print("#" * 50)
    time.sleep(round(random.uniform(0.7, 1.2), 1))