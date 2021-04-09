########################################################################################################
# 종목 일 - 시각 시세 추출.
# thistime=20210408153000. 추출 일자와 장 종료시각
# max page = 50
########################################################################################################
import datetime
# 라이브러리 로드
# requests는 작은 웹브라우저로 웹사이트 내용을 가져온다.
import requests
# BeautifulSoup 을 통해 읽어 온 웹페이지를 파싱한다.
from bs4 import BeautifulSoup as bs
# 크롤링 후 결과를 데이터프레임 형태로 보기 위해 불러온다.
import pandas as pd
# 환경파일
import yaml

# CSV 파일명
csv_filename = "agreement.csv"
# 시작일자
start_dt = "20210406"
# 종료일자
end_dt = "20210408"
# 날짜형 시작일자
dtm_start = datetime.datetime.strptime(start_dt, "%Y%m%d")
# 최종 데이터 리스트
list_agree = []
# 날짜 증가를 위한 변수
icnt = 0

while True:
    dtm_dt = dtm_start + datetime.timedelta(days=icnt)
    dt = dtm_dt.strftime("%Y%m%d")
    if dt > end_dt: break
    last_tf = False
    for pages in range(50):
        # 0 페이지는 없어서 스킵
        if pages == 0: continue
            # 9시 데이터 읽었으면 종료
        if last_tf == True:
            break
        jongmok = "122630"
        main_url = f"https://finance.naver.com/item/sise_time.nhn?code={jongmok}&thistime={dt}153000&page={pages}"
        response = requests.get( main_url, headers={"User-agent": "Mozilla/5.0"} )
        soup = bs(response.text, 'html.parser')
        idx = 0
        num = 0
        for href in soup.find_all("td"):
            str_href = str(href)
            idx += 1
            # time
            if 'class="tah p10 gray03' in str_href:
                list_data = []
                agree_time = str_href.replace("</span></td>", "").replace('<td align="center"><span class="tah p10 gray03">', "").replace(":", "").zfill(4)
                num = idx + 1
                list_data.append(dt)
                list_data.append(agree_time)
                if agree_time == "0900":
                    last_tf = True
            # price
            elif idx == num:
                agree_price = str_href.replace("</span></td>", "").replace('<td class="num"><span class="tah p11">', "").replace(",", "")
                list_data.append(agree_price)
                list_agree.append(list_data)
                
    icnt += 1

df_agree = pd.DataFrame(list_agree, columns=["date", "time", "price"])
df_agree.to_csv(csv_filename, encoding="utf-8-sig", index=False)