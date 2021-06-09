import requests
from bs4 import BeautifulSoup
import urllib.parse
import mariadb
import sys

# who = '쁘갤서포트'

# https://api.telegram.org/bot1826437448:AAGdDTiTnn8RRM7lN9VVZBmVjfcMZo3ItYc/getUpdates
# 특정 사용자를 찾을때: url = 'https://gall.dcinside.com/mgallery/board/lists/?id=bravegirls0409&s_type=search_name&s_keyword={}'.format( urllib.parse.quote(who) )
# 후방탐색: #re.search( '(?<=no=)\d+', li.get('href') ).group()


## 바람드리 차트
# https://gall.dcinside.com/mgallery/board/lists?id=bravegirls0409&s_type=search_subject_memo&s_keyword=%EC%B0%A8%ED%8A%B8

# telegram
def sendMessage2Channel(msg):
    # 채널에 알림
    botReq = 'https://api.telegram.org/bot1826437448:AAGdDTiTnn8RRM7lN9VVZBmVjfcMZo3ItYc/sendMessage?chat_id=@fearless_siren&text={}'.format(
        msg)
    res = requests.get(botReq)
    success = res.status_code == 200
    if success:
        return True
    else:
        sendMessage2Bot('텔레그램 메시지 보내기 실패')
        return False


def sendMessage2Bot(msg):
    requests.get(
        'https://api.telegram.org/bot1826437448:AAGdDTiTnn8RRM7lN9VVZBmVjfcMZo3ItYc/sendMessage?chat_id=83721701&text={}').format(
        urllib.parse.quote(msg))




# BS4
headers = {'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.143 Safari/537.36'}
url = 'https://gall.dcinside.com/mgallery/board/lists/?id=bravegirls0409&sort_type=N&search_head=100&page=1'
res = requests.get( url, headers=headers)

if res.status_code != 200:
    sendMessage2Bot('갤러리 정보를 가져오지 못했습니다.')
    print('network fail:', res.status_code )
    sys.exit(1)

soup = BeautifulSoup(res.text, 'html.parser')
list = soup.select('.gall_list tbody tr.us-post')



# Connect DB
try:
    conn = mariadb.connect(
        user="hohoyaing",
        password="W6.vrdj-E.*qpcrE",
        host="siren-db.co4su5fv6yzj.ap-northeast-2.rds.amazonaws.com",
        port=3306,
        database="dc",
        autocommit=True
    )
except mariadb.Error as e:
    sendMessage2Bot('DB 연결 실패: {}'.format(e))
    sys.exit(1)

cur = conn.cursor()


# 없는 번호인지 확인하고 insert
for li in list:
    no = li.select_one('.gall_num').text
    title = li.select_one('.gall_tit a:first-child').text
    who = li.select_one('.gall_writer').text

    cur.execute( "SELECT * FROM bbg WHERE no={}".format(no) )
    row = cur.fetchone()

    if row == None:
        try:
            # 텔레그램 채널에 메시지 전송후 DB에 입력
            # msg = urllib.parse.quote('https://gall.dcinside.com/mgallery/board/view/?id=bravegirls0409&no={}'.format(no))
            # botReq = 'https://api.telegram.org/bot1826437448:AAGdDTiTnn8RRM7lN9VVZBmVjfcMZo3ItYc/sendMessage?chat_id=@fearless_siren&text={}'.format( msg );
            # res = requests.get( botReq )

            msg = urllib.parse.quote('https://gall.dcinside.com/mgallery/board/view/?id=bravegirls0409&no={}'.format(no))
            if sendMessage2Channel( msg ) :
                cur.execute(
                    "INSERT INTO bbg (no,name,title) "
                    "VALUES (?,?,?)",
                    (no, who, title)
                )

        except mariadb.Error as e:
            sendMessage2Bot('DB 쓰기에러')


conn.close()



# adding data
# https://mariadb.com/resources/blog/how-to-connect-python-programs-to-mariadb/