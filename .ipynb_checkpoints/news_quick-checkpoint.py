########################################################################################################
# 네이버 증권 속보
########################################################################################################
# requests는 작은 웹브라우저로 웹사이트 내용을 가져온다.
import requests
# BeautifulSoup 을 통해 읽어 온 웹페이지를 파싱한다.
from bs4 import BeautifulSoup as bs
# 크롤링 후 결과를 데이터프레임 형태로 보기 위해 불러온다.
import pandas as pd
import datetime

base_url = "https://finance.naver.com/news/news_list.nhn?mode=LSS3D&section_id=101&section_id2=258&section_id3=402"


def extract_value(in_param, idx):
    nam = idx % 7
    # date
    try:
        if nam == 1:
            result_value = in_param.split('<span class="tah p10 gray03">')[1].replace("</span></td>","").replace(".","")
        elif nam == 3:
            if "상승" in in_param:
                result_value = in_param.split('<span class="tah p11 red02">')[1].replace("</span>","").replace("</td>","").replace(",","")
            elif "하락" in in_param:
                result_value = in_param.split('<span class="tah p11 nv01">')[1].replace("</span>","").replace("</td>","").replace(",","")
            else:
                result_value = "0"
        else:
            result_value = in_param.split('<span class="tah p11">')[1].replace("</span></td>","").replace(",","")
    except:
        result_value = ""

    return result_value.strip()


# 이동평균 및 현재가
def get_mean_now_price(jongmok_code):
    # 현재가
    base_url = "https://finance.naver.com/item/main.nhn?code=" + jongmok_code
    response = requests.get( base_url, headers={"User-agent": "Mozilla/5.0"} )
    soup = bs(response.text, 'html.parser')
    idx = 0
    for href in soup.find("div", class_="rate_info").find_all("dd"):
        if idx == 0:
            try:
                now_price = int(str(href).split(" ")[1].replace(",",""))
            except:
                now_price = 0
        idx += 1
    # 20일 평균
    idx = 0
    cnt = 0
    mean_price = 0
    for page in range(2):
        base_url = "https://finance.naver.com/item/sise_day.nhn?code=" + jongmok_code + "&page=" + str(page+1)
        response = requests.get( base_url, headers={"User-agent": "Mozilla/5.0"} )
        soup = bs(response.text, 'html.parser')
        
        for href in soup.find_all("td"):
            str_href = str(href)
            # 종료
            if '<td class="on">' in str_href: break
            # 제외
            if ("<td colspan=" in str_href or "<td bgcolor" in str_href): continue 
            # 실제 처리
            idx += 1
            nam = idx % 7
            # 첫번째 날짜 키
            if nam == 2:
                try:
                    mean_price += int(extract_value(str_href, idx))
                    cnt += 1
                except:
                    mean_price += 0
            else:
                continue
    
    return int((mean_price - now_price) / (cnt - 1)), now_price

def extract_link(in_param):
    pre_fix = "https://finance.naver.com"
    if "title=" in in_param:
        result_link = pre_fix + in_param.split("title=")[0].split("href=")[1].replace('amp;','').replace('"',"")
        result_link = result_link.replace("§ion_id", "&section_id").replace("§ion_id2", "&section_id2").replace("§ion_id3", "&section_id3")
        result_head = in_param.split("title=")[1].replace("</a>","").replace('"',"")        
    else:
        result_link = "" 
        result_head = ""
        
    return result_link, result_head

# 크롤링 할 사이트
list_news = []
for page in range(11):
    main_url = base_url + "&page=" + str(page + 1)
    response = requests.get( main_url, headers={"User-agent": "Mozilla/5.0"} )
    soup = bs(response.text, 'html.parser')
    for href in soup.find("ul", class_="realtimeNewsList").find_all("a"):
        str_href = str(href)
        result_link, result_head = extract_link(str_href)
        if result_link != "":
            list_temp = []
            list_temp.append(result_link)
            list_temp.append(result_head)
            list_news.append(list_temp)

df_result = pd.DataFrame(list_news, columns=["LINK","TITLE"])
df_result.to_csv("news.csv", encoding="utf-8-sig", index=False)

df_jongmok = pd.read_csv("data_3346_20210324.csv", encoding="CP949")

now_dt = datetime.date.today()
DT = str(now_dt.year) + str(now_dt.month) + str(now_dt.day)
file_name = "news_" + DT + ".txt"

f = open(file_name, 'w', encoding="utf-8-sig")

idx = 0
for head in list_news:
    headline = " -  " + head[1]
    for _, row in df_jongmok.iterrows():
        if row["한글 종목약명"] in headline:
            mean_price, now_price = get_mean_now_price(row["단축코드"])
            #print("# [" + row["한글 종목약명"] + "] -  * 평균대비 증감: " + format(now_price - mean_price, ',') + "  * 증감율: " + format(round(((now_price - mean_price) / now_price) * 100, 2), ',') + "%  * 19일평균: " + format(mean_price, ',') + "  * 현재가: " + format(now_price, ',') + "\n" + headline)
            f.write("# [ " + row["한글 종목약명"] + " ]\n")
            msg_string = " -  * 평균대비 증감: " + format(now_price - mean_price, ',') + "  * 증감율: " + format(round(((now_price - mean_price) / now_price) * 100, 2), ',') + "%  * 19일평균: " + format(mean_price, ',') + "  * 현재가: " + format(now_price, ',') + "\n" + headline + "\n"
            f.write(msg_string)
            f.write("\n")
            idx += 1
f.close()
