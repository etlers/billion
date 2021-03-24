#-*- coding: utf-8 -*-
"""
    증권사 리서치 보고서, KOSPI200 및 외국인 보유현황을 조합하여 추천할 종목을 추출 후 텔레그램 메세지로 전송
"""

# requests는 작은 웹브라우저로 웹사이트 내용을 가져온다.
import requests
# BeautifulSoup 을 통해 읽어 온 웹페이지를 파싱한다.
from bs4 import BeautifulSoup as bs
# 크롤링 후 결과를 데이터프레임 형태로 보기 위해 불러온다.
import pandas as pd
# 각 단어의 빈도수
from collections import Counter
# 텔레그램 메세지 전송
import telegram

import sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding = 'utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding = 'utf-8')

# 실제 메세지 전송하는 곳. chat_id를 위해 하루에 한 번 '/my_id' 명령어 입력 필요
def send_message(msg):
    chat_token = "1740739677:AAFjOUObIBcjKs3nKAuHn4m349jbZvl6N6o"
    chat = telegram.Bot(token = chat_token)
    updates = chat.getUpdates()

    for u in updates:
        chat_id = u.message['chat']['id']

    bot = telegram.Bot(token = chat_token)
    bot.sendMessage(chat_id = chat_id, text=msg)


###############################################################################################################
# 외국인 매매동향. KOSPI200에서 호출
###############################################################################################################
def forgn_poss_info(jongmok_code, jongmok_name):
    list_columns = [
        "JONGMOK_CODE","JONGMOK_NAME","END_DT","END_PRICE","COMP_PRICE","COMP_RATE","COMP_DEAL","AVG_PRICE","COMPANY_DEAL","FORGN_DEAL","FORGN_RATE"
    ]
    main_url = "https://finance.naver.com/item/frgn.nhn?code=" + jongmok_code
    response = requests.get( main_url, headers={"User-agent": "Mozilla/5.0"} )
    soup = bs(response.text, 'html.parser')

    def get_date(in_param):
        deal_date = in_param.split("</span>")[0]
        deal_date = deal_date[len(deal_date) - 10:].replace(".", "")
        #print(deal_date)
        return deal_date

    def end_price(in_param):
        end_price = in_param.split("</span>")[0].split("<span class=")[1].split(">")[1]
        return end_price

    def extract_others(in_param):
        result_value = in_param.split("<span class=")[1].split(">")[1].split("<")[0].strip()
        #print(result_value)    
        return result_value
    
    def calc_mean_poss(df):
        end_price = 0
        company_deal = 0
        forgn_deal = 0
        forgn_rate = 0
        for _, row in df.iterrows():
            # 20일 이동평균 계산
            end_price += int(row["END_PRICE"].replace(",", "").strip())
            # 기관 매매량
            company_deal += int(row["COMPANY_DEAL"].replace(",", "").strip())
            # 외국인 매매량
            forgn_deal += int(row["FORGN_DEAL"].replace(",", "").strip())
            # 외국인 보유비율
            forgn_rate += float(row["FORGN_RATE"].replace(",", "").strip())
        avg_price = int(end_price / 20)
        forgn_rate = forgn_rate / 20
        
        return avg_price, company_deal, forgn_deal, forgn_rate

    list_foreign_info = []
    list_daily = []
    start_tf = False
    idx = 0

    for href in soup.find("div", class_="content_wrap").find_all("td"):
        str_href = str(href)    
        if start_tf == False:
            if '<td class="tc"' in str_href:
                list_foreign_info.append(list_daily)
                list_daily.append(get_date(str_href))
                start_tf = True
                idx += 1
            continue
        # 종료
        if '<td class="on">' in str_href:
            break
        # 일자를 만나는 경우
        if '<td class="tc"' in str_href:
            idx = 0        

        if idx == 0:
            list_foreign_info.append(list_daily)
            list_daily = []            
            list_daily.append(get_date(str_href))        
        #print(idx, str_href)

        elif idx == 1:
            list_daily.append(end_price(str_href))
        else:
            try:
                extract_value = extract_others(str_href)
                extract_value = extract_value.replace("%", "").replace("+", "")
                list_daily.append(extract_value)
            except:
                pass
        idx += 1

    list_foreign_info.append(list_daily)        
    del list_foreign_info[0]

    df_foreign = pd.DataFrame(list_foreign_info, columns=[list_columns[2:]])
    df_foreign["JONGMOK_CODE"] = jongmok_code
    df_foreign["JONGMOK_NAME"] = jongmok_name
    df_foreign = df_foreign[list_columns]
    
    return calc_mean_poss(df_foreign)


########################################################################################################
# 코스피200 종목 가져오기
########################################################################################################
def get_kospi200():
    list_columns = [
        "JONGMOK_CODE","JONGMOK_NAME", "NOW_PRICE","COMP_PRICE","COMP_RATE","DEAL_AMOUNT","AVG_PRICE","COMPANY_DEAL","FORGN_DEAL","FORGN_RATE"
    ]
    # 크롤링 할 사이트
    base_url = "https://finance.naver.com/sise/entryJongmok.nhn"
    # 종목, 사이트 저장할 리스트
    list_jongmok_link = []
    # 제거할 tag
    list_replace_char= [
        "<p>", "<strong>", "</p>", "</strong>", "<br/>", "\n", "\t", "<tr>", "</tr>", "<td>", "</td>", "</span>"
    ]

    def remove_special_char(in_href):
        result_text = in_href
        for char in list_replace_char:
            result_text = result_text.replace(char, "")
        return result_text

    def extract_jongmok_info(in_param):
        jongmok_code = in_param.split(' target="_parent">')[0].split("code=")[1].replace('"', '')
        jongmok_name = in_param.split(' target="_parent">')[1].split("</a")[0].replace("amp;", "")
        return jongmok_code, jongmok_name

    def extract_price_info(in_param):
        price_now = in_param.split("<td class=")[0]
        price_comp = in_param.split("<span class=")[1].split(">")[1].split("<td class=")[0]
        rate_comp = in_param.split('%<td class="number">')[0].split('><span class="tah')[2].split(">")[1]
        deal_amount = in_param.split('%<td class="number">')[1].split("<")[0]
        return price_now, price_comp, rate_comp, deal_amount

    def get_posi_nega_cnt(jongmok_name):
        result_posi_cnt = 0
        result_nega_cnt = 0
        f = open("./report.txt", 'r', encoding="utf-8-sig")
        lines = f.readlines()
        for line in lines:
            if jongmok_name in line:
                div = line.split(" ")[0]
                if div == "긍정":
                    result_posi_cnt = line.split(" ")[3].replace("]","").replace("[","").replace("\n","")
                    break
                else:
                    result_nega_cnt = line.split(" ")[3].replace("]","").replace("[","").replace("\n","")
                    break
        f.close()

        return result_posi_cnt, result_nega_cnt

    # 페이지 단위로 추출 저장    
    for page in range(21):
        
        if page > 0:
            main_url = base_url + "?&page=" + str(page + 1)
        else:
            main_url = base_url
        
        response = requests.get( main_url, headers={"User-agent": "Mozilla/5.0"} )
        soup = bs(response.text, 'html.parser')

        for href in soup.find("div", class_="box_type_m").find_all("tr"):
            list_temp = []
            str_href = str(href)
            if '<td class="ctg">' in str_href:        
                removed_str = remove_special_char(str_href)        
                jongmok_code, jongmok_name = extract_jongmok_info(removed_str)
                price_now, price_comp, rate_comp, deal_amount = extract_price_info(removed_str.split('</a><td class="number_2">')[1])
                if len(jongmok_code) > 0:
                    list_temp.append(jongmok_code)
                    list_temp.append(jongmok_name)
                    list_temp.append(price_now)
                    list_temp.append(price_comp)
                    list_temp.append(rate_comp)
                    list_temp.append(deal_amount)
                    # 외국인, 기관 정보
                    avg_price, company_deal, forgn_deal, forgn_rate = forgn_poss_info(jongmok_code, jongmok_name)
                    list_temp.append(avg_price)
                    list_temp.append(company_deal)
                    list_temp.append(forgn_deal)
                    list_temp.append(forgn_rate)
                    # 리스트에 저장
                    list_jongmok_link.append(list_temp)

    df_kospi200 = pd.DataFrame(list_jongmok_link, columns=list_columns)
    list_kospi200 = []
    # 20일 이동평균과 비교
    for _, row in df_kospi200.iterrows():
        list_temp = []
        deal_amount = int(row["DEAL_AMOUNT"].replace(",", ""))
        now_price = int(row["NOW_PRICE"].replace(",", ""))
        avg_price = int(row["AVG_PRICE"])
        up_rate = round((now_price - avg_price) / now_price, 4) * 100
        # 금액이 10만원 미만
        if (now_price < 100000):
            # 이동평균선에서 -5% ~ 1% 미만으로 내려와 있는 경우
            if (up_rate < 1.0 and up_rate > -3.0):
                # 전날대비 살짝(3% 미만) 상승하고 있는 종목
                if (float(row["COMP_RATE"]) >= -1.0 and float(row["COMP_RATE"]) <= 3.0):
                    list_temp.append(row["JONGMOK_NAME"])
                    list_temp.append(avg_price)
                    list_temp.append(now_price)
                    if float(row["COMP_RATE"]) < 0.0:
                        list_temp.append(int(row["COMP_PRICE"]) * -1)
                    else:
                        list_temp.append(int(row["COMP_PRICE"]))
                    list_temp.append(row["COMP_RATE"])
                    list_temp.append(row["DEAL_AMOUNT"])
                    list_temp.append(round(row["FORGN_RATE"], 2))
                    list_temp.append(up_rate)
                    # 긍정, 부정
                    get_posi_cnt, get_nega_cnt = get_posi_nega_cnt(row["JONGMOK_NAME"])
                    list_temp.append(get_posi_cnt)
                    list_temp.append(get_nega_cnt)
                    # 데이터 프레임을 위한 최종 리스트                    
                    list_kospi200.append(list_temp)
    #print(msg_string)
    df_kospi200 = pd.DataFrame(list_kospi200, columns=["종목","20일평균","현재가","전일비","등락률","거래량","외국인","평균대비","긍정","부정"])
    df_kospi200.to_csv("kospi200.csv", encoding="utf-8-sig", index=False)

    # 추출한 정보 메세지 푸쉬
    msg_string = "종목" + " | " + "차이" + " | " + "평균대비" + " | " + "등락률" + " | " + "거래량" + " | " + "긍부정" + "\n\n"
    for _, row in df_kospi200.iterrows():
        msg_string += row["종목"] + "| " + str(int(row["현재가"]) - int(row["20일평균"])) + "| " + str(round(row["평균대비"], 2)) + " | " + str(row["등락률"]) + " | " + str(row["거래량"]) + " | " + str(int(row["긍정"]) + int(row["부정"])) + "\n"
    
    send_message(msg_string)                    

###############################################################################################################
# 리서치 보고서
###############################################################################################################
list_replace_char = [
    "<p>", "<strong>", "</p>", "</strong>", "<br/>", "\n", "\t"
]

def count_word_freq(in_param):
    list_word_freq = []
    wordDict = Counter()

    in_param = in_param.replace(":","").replace("및","").replace("으로","").replace("하며","").replace("했다","")
    for word in in_param.split(): #한 문장에 들어있는 한 단어씩
        wordDict[word] += 1 #Counter에 count를 1씩 증가시킨다.

    for word, freq in wordDict.most_common(1000):
        list_word_freq.append(word + ":" + str(freq))
    
    return list_word_freq

def calc_posi_nega_word(df_jongmok):
    # 구분 키워드
    posi_word = ["상향","추천","안정","투자","매수","상승","개선","최대 실적","성장+","가파르게 상승","가파르게상승","개선","혁신","1위","1 위","선도","긍정적","실적 회복","최고치",
                 "실적호조","호실적"]
    nega_word = ["하향","매도","하락","악재","하락","부진","하회","실적 악화","하회","성장-","가파르게 하락","가파르게하락","진부","부정적","최저치","급락","매출 감소","매출감소",
                 "이익 감소","이익감소","성장 둔화","성장둔화","매출부진","부진","수수료증가","비용증가","수수료 증가","비용 증가"]
    
    def get_word_count(list_word_freq, check_word):
        for word in list_word_freq:
            if check_word in word:
                return int(word.split(":")[1])
            
        return 0

    list_columns = [
        "JONGMOK_CODE", "JONGMOK_NAME", "POSITIVE_CNT", "NEGATIVE_CNT", "RESULT_CNT"
    ]

    list_report = []
    for _, row in df_jongmok.iterrows():
        list_word_freq = count_word_freq(row["REPORT"])
                
        posi_cnt = 0
        nega_cnt = 0
        list_temp = []
        
        for word in posi_word:
            posi_cnt += get_word_count(list_word_freq, word)

        for word in nega_word:
            nega_cnt += get_word_count(list_word_freq, word)
                
        if (posi_cnt > 0 or nega_cnt > 0):
            list_temp.append(row["JONGMOK_CODE"])
            list_temp.append(row["JONGMOK_NAME"])
            list_temp.append(posi_cnt)
            list_temp.append(nega_cnt)
            list_temp.append(posi_cnt - nega_cnt)
            list_report.append(list_temp)

    df_result = pd.DataFrame(list_report, columns=list_columns)
    df_result = df_result.sort_values(by=["JONGMOK_CODE"], axis=0)
    return df_result

def get_text_detail(link_url):
    response = requests.get( link_url )
    link_soup = bs(response.text, 'html.parser')
    result_text = ""
    for link_text in link_soup.find("div", class_="box_type_m").find_all('p'):
        get_text = str(link_text)
        if '<b class="bar">|</b>조회' not in get_text:
            result_text += get_text
    
    for char in list_replace_char:
        result_text = result_text.replace(char, "")
        
    return result_text.strip()

def execute():
    # 앞에 붙이는 고정 주소
    prefix_addr = "https://finance.naver.com/research/"
    # 크롤링 할 사이트
    base_url = "https://finance.naver.com/research/company_list.nhn"
    # 종목, 사이트 저장할 리스트
    list_jongmok_link = []
    list_temp = []
    # 페이지 단위로 추출 저장    
    for page in range(20):
        
        if page > 0:
            main_url = base_url + "?&page=" + str(page)
        else:
            main_url = base_url
            
        response = requests.get( main_url )
        soup = bs(response.text, 'html.parser')

        for href in soup.find("div", class_="box_type_m").find_all("a"):
            if "code" in href.get("href"):
                list_temp.append(href.get("href").split("code=")[1])
            if href.get("title") is not None:
                list_temp.append(href.get("title"))
            if "company_read" in href.get("href"): 
                list_temp.append(prefix_addr + href.get("href"))
                list_jongmok_link.append(list_temp)
                list_temp = []
        
    df_jongmok = pd.DataFrame(list_jongmok_link, columns=["JONGMOK_CODE", "JONGMOK_NAME", "LINK"])

    list_df_value = []
    for link in list_jongmok_link:
        report_text = get_text_detail(link[2])
        list_df_value.append(report_text)

    df_jongmok["REPORT"] = list_df_value
    df_jongmok = df_jongmok.drop_duplicates()
    df_jongmok.to_csv("report.csv", index=False, encoding="utf-8-sig")
    # 긍정 부정 계산
    df_result = calc_posi_nega_word(df_jongmok)

    df_grouped = df_result.groupby(['JONGMOK_NAME'])['RESULT_CNT'].sum().reset_index()
    #df_grouped.loc[df_grouped.RESULT_CNT > 0].to_csv("report.csv", index=False, encoding="utf-8-sig")
    df_msg_posi = df_grouped.loc[df_grouped.RESULT_CNT >= 0]
    df_msg_posi = df_msg_posi.sort_values(by=["RESULT_CNT"], axis=0, ascending=False)
    df_msg_nega = df_grouped.loc[df_grouped.RESULT_CNT < 0]
    df_msg_nega = df_msg_nega.sort_values(by=["RESULT_CNT"], axis=0)

    f = open("report.txt", 'w', encoding="utf-8-sig")

    def call_send_msg(df_msg, div):
        msg_string = "# " + div + "\n"
        for _, row in df_msg.iterrows():
            msg_string += div + " - " + row["JONGMOK_NAME"] + " [" + str(row["RESULT_CNT"]) + "]\n" 
        #send_message(msg_string)
        #print(msg_string)
        f.write(msg_string)
        
    call_send_msg(df_msg_posi, "긍정")    
    call_send_msg(df_msg_nega, "부정")   

    f.close()


if __name__ == "__main__":
    # 보고서
    execute()
    # KOSPI200 종목 중에서 이동편균보다 높은 종목 메세지 보냄
    get_kospi200()

    