def get_posi_nega_cnt(jongmok_name):
    posi_cnt = 0
    nega_cnt = 0
    f = open("./report.txt", 'r', encoding="utf-8-sig")
    lines = f.readlines()
    for line in lines:
        if jongmok_name in line:
            div = line.split(" ")[0]
            if div == "긍정":
                posi_cnt = line.split(" ")[3].replace("]","").replace("[","").replace("\n","")
                break
            else:
                nega_cnt = line.split(" ")[3].replace("]","").replace("[","").replace("\n","")
                break
    f.close()

    return posi_cnt, nega_cnt

print(get_posi_nega_cnt("한화솔루션"))    