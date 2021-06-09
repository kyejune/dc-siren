# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import urllib.parse
import mariadb
import sys
import re
import base64

# url encode + base64
def encode64(str):
    ue = urllib.parse.quote(str)
    message_bytes = ue.encode('ascii')
    base64_bytes = base64.b64encode(message_bytes)
    base64_message = base64_bytes.decode('ascii')
    return base64_message

# 알림
def notifiy( id, title ):
    # 채널에 알림
    req = 'http://13.209.32.248:19876/api/v1/oneSignal/message'
    obj = {
        "subject": encode64(title),
        "link": encode64('https://gall.dcinside.com/mgallery/board/view/?id=bravegirls0409&no={}'.format(id)),
        "notiType": "dc"
    }

    res = requests.post(req, data=obj)
    success = res.status_code == 200
    if success:
        return True
    else:
        errorLog('push fail {}'.format(res.status_code))
        return False

# 에러
def errorLog(msg):
    print('[stalker]', msg)


# 목록 크롤링
def getList( url ):
    headers = {'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.143 Safari/537.36'}
    res = requests.get( url, headers=headers)

    if res.status_code != 200:
        errorLog('network error:{}'.format(res.status_code))
        sys.exit(1)

    soup = BeautifulSoup(res.text, 'html.parser')
    return soup.select('.gall_list tbody tr.us-post')


# DB
try:
    conn = mariadb.connect(
        user="",
        password="",
        host="",
        port=3306,
        database="",
        autocommit=True
    )
except mariadb.Error as e:
    errorLog('DB 연결 실패: {}'.format(e))
    sys.exit(1)

cur = conn.cursor()

# 없는 번호인지 확인하고 insert
def writeData(list, titleRegexp ):
    for li in list:
        no = li.select_one('.gall_num').text
        title = li.select_one('.gall_tit a:first-child').text
        who = li.select_one('.gall_writer').text

        # 제목용 정규식이 있다면 검사
        if titleRegexp != None :
            exp = re.compile(titleRegexp)
            if exp.search( title ) == None:
                continue

        cur.execute( "SELECT * FROM bbg WHERE no={}".format(no) )
        row = cur.fetchone()

        if row == None:
            try:
                if notifiy( no, title ) :
                    cur.execute(
                        "INSERT INTO bbg (no,name,title) "
                        "VALUES (?,?,?)",
                        (no, who, title)
                    )

            except mariadb.Error as e:
                errorLog('DB 쓰기에러')


# 공지
notis = getList('https://gall.dcinside.com/mgallery/board/lists/?id=bravegirls0409&sort_type=N&search_head=100&page=1')

# 차트게이
charts = getList('https://gall.dcinside.com/mgallery/board/lists/?id=bravegirls0409&s_type=search_name&s_keyword=%EB%B0%94%EB%9E%8C%EB%93%9C%EB%A6%AC')

writeData(notis, None)
writeData(charts, '\d{2}:\d{2}\s?차트\s현황')
conn.close()