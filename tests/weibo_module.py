import os
import sys
import time
import wget
import json
import sqlite3
import configparser
from bs4 import BeautifulSoup
from requests_html import HTMLSession


class Weibo:

    def plog(self,content):
        print('{} {}'.format(time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.time())), content))

    def __init__(self):
        self.BASE_DIR = os.path.split(os.path.realpath(__file__))[0]
        config = configparser.ConfigParser()
        config.read(os.path.join(self.BASE_DIR, 'config.ini'), encoding='utf-8')
        self.WEIBO_ID = config.get("CONFIG", "WEIBO_ID")
        self.TELEGRAM_BOT_TOKEN = config.get("CONFIG", "TELEGRAM_BOT_TOKEN")
        self.TELEGRAM_CHAT_ID = config.get("CONFIG", "TELEGRAM_CHAT_ID")
        self.SESSION = HTMLSession()
        self.SESSION.adapters.DEFAULT_RETRIES = 5  # 增加重連次數
        self.SESSION.keep_alive = False  # 關閉多余連接
        proxy = config.get("CONFIG", "PROXY")
        self.PROXIES = {"http": proxy, "https": proxy}

    def send_telegram_message(self, text, weibo_link):
        """
        給電報發送文字消息
        """
        headers = {
            'Content-Type': 'application/json',
        }
        data = f'{{"chat_id":"{self.TELEGRAM_CHAT_ID}", "text":"{text}", "reply_markup": {{"inline_keyboard":' \
               f' [[{{"text":"🔗點擊查看原微博", "url":"{weibo_link}"}}]]}}}} '
        url = f'https://api.telegram.org/bot{self.TELEGRAM_BOT_TOKEN}/sendMessage'
        try:
            self.SESSION.post(url, headers=headers, data=data.encode('utf-8'), proxies=self.PROXIES)
        except:
            print('    |-網絡代理錯誤，請檢查確認後關閉本程序重試')
            time.sleep(99999)

    def send_telegram_photo(self, img_url):
        """
        給電報發送圖片
        """
        url = f'https://api.telegram.org/bot{self.TELEGRAM_BOT_TOKEN}/sendPhoto'
        data = dict(chat_id=f"{self.TELEGRAM_CHAT_ID}&", photo=img_url)

        self.SESSION.post(url, data=data, proxies=self.PROXIES)

    def send_telegram_photos(self, pics):
        url = f'https://api.telegram.org/bot{self.TELEGRAM_BOT_TOKEN}/sendMediaGroup'
        params = {
            'chat_id': self.TELEGRAM_CHAT_ID,
            'media': [],
        }
        for pic in pics:
            params['media'].append({'type': 'photo', 'media': pic})
        params['media'] = json.dumps(params['media'])
        result = self.SESSION.post(url, data=params, proxies=self.PROXIES)
        if result.status_code != 200: # 如果分組發送失敗 則單獨發送圖片
            for pic in pics:
                self.send_telegram_photo(pic)

    def parse_weibo(self, weibo):
        """
        檢查當前微博是否已處理過，如果沒處理過則發送博文以及配圖到Telegram
        """
        conn = sqlite3.connect(os.path.join(self.BASE_DIR, 'db', 'weibo.db'))
        cursor = conn.cursor()

        sql = "SELECT COUNT(id) AS counts FROM weibo WHERE link = ?"
        cursor.execute(sql, (weibo['link'],))
        result = cursor.fetchone()

        if result[0] <= 0:
            self.send_telegram_message(
                '{}@{}:{}'.format(
                    f"[{len(weibo['pics'])}圖] " if weibo['pics'] else '',
                    weibo['nickname'],
                    weibo['title'],
                ),
                weibo['link']
            )

            # 把圖片url發送到Telegram中，可以第一時間在Telegram中收到推送
            pics = weibo['pics']
            if len(pics) > 0:
                if len(pics) <= 2: # 如果配圖小於2張 則一張一張獨立發送
                    for pic in pics:
                        self.send_telegram_photo(pics)
                elif len(pics) > 10: # 如果配圖大於10張 則分2組發送
                    self.send_telegram_photos(pics[0 : int(len(pics)/2)])
                    self.send_telegram_photos(pics[int(len(pics)/2):])
                else:
                    self.send_telegram_photos(pics)

            # 配圖發送到Telegram畢後，將配圖獨立保存到本地一份
            for pic in weibo['pics']:
                filename = pic.split('/')[-1].split('?')[0]
                filename = os.path.join(self.BASE_DIR, 'images', filename)
                wget.download(pic, out=filename)

            sql = "INSERT INTO weibo(summary, link) VALUES(?, ?)"
            cursor.execute(sql, (
                weibo['title'],
                weibo['link'],
            ))
            conn.commit()
            conn.close()

            return True
        else:
            return False

    def test(self):
        print('* 正在檢查微博ID是否配置正確')
        url = f'https://m.weibo.cn/api/container/getIndex?containerid=100505{self.WEIBO_ID}'
        try:
            weibo_name = self.SESSION.get(url).json()['data']['userInfo']['screen_name']
            print(f'【正確】當前設置的微博賬戶為：@{weibo_name}')
        except:
            print('【錯誤】請重新測試或檢查微博數字ID是否正確')

        print('\n* 正在檢查代理是否配置正確')
        try:
            status_code = self.SESSION.get('https://www.google.com',proxies=self.PROXIES, timeout=5).status_code
            if status_code == 200:
                print('【正確】代理配置正確，可正常訪問')
            else:
                print('【錯誤】代理無法訪問到電報服務器')
        except:
            print('【錯誤】代理無法訪問到電報服務器')

    def get_weibo_detail(self, bid):
        url = f'https://m.weibo.cn/statuses/show?id={bid}'
        detail = self.SESSION.get(url).json()
        weibo = {}
        weibo['title'] = BeautifulSoup(detail['data']['text'].replace('<br />', '\n'), 'html.parser').get_text()
        weibo['nickname'] = detail['data']['user']['screen_name']
        weibo_id = detail['data']['user']['id']
        weibo['pics'] = []
        if 'pics' in detail['data']: # 判斷博文中是否有配圖，如果有配圖則做解析
            weibo['pics'] = [pic['large']['url'] for pic in detail['data']['pics']]
        weibo['link'] = self.get_pc_url(weibo_id, bid)
        self.parse_weibo(weibo)

    def get_pc_url(self, weibo_id, bid):
        return 'https://weibo.com/{weibo_id}/{uri}'.format(
            weibo_id = weibo_id,
            uri = bid
        )

    def run(self):
        self.plog('開始運行>>>')

        weibo_ids = self.WEIBO_ID.split(',')
        for weibo_id in weibo_ids:
            self.plog(f'    |-開始獲取 {weibo_id} 的微博')
            url = f'https://m.weibo.cn/api/container/getIndex?containerid=107603{weibo_id}'

            try:
                weibo_items = self.SESSION.get(url).json()['data']['cards'][::-1]
            except:
                self.plog('    |-訪問url出錯了')

            for item in weibo_items:
                weibo = {}
                try:
                    if item['mblog']['isLongText']: # 如果博文包含全文 則去解析完整微博
                        self.get_weibo_detail(item['mblog']['bid'])
                        continue
                except:
                    continue

                weibo['title'] = BeautifulSoup(item['mblog']['text'].replace('<br />', '\n'), 'html.parser').get_text()
                weibo['nickname'] = item['mblog']['user']['screen_name']

                if item['mblog'].get('weibo_position') == 3:  # 如果狀態為3表示轉發微博，附加上轉發鏈，狀態1為原創微博
                    retweet = item['mblog']['retweeted_status']
                    try:
                        weibo['title'] = f"{weibo['title']}//@{retweet['user']['screen_name']}:{retweet['raw_text']}"
                    except:
                        weibo['title'] = f"{weibo['title']}//轉發原文不可見，可能已被刪除"

                try:
                    weibo['pics'] = [pic['large']['url'] for pic in item['mblog']['pics']]
                except:
                    weibo['pics'] = []

                weibo['link'] = self.get_pc_url(weibo_id, item['mblog']['bid'])

                self.parse_weibo(weibo)
            self.plog(f'    |-獲取結束 {weibo_id} 的微博')
        self.plog('<<<運行結束\n')


if __name__ == '__main__':
    weibo = Weibo()
    argv = sys.argv[1] if len(sys.argv) > 1 else ''
    if argv.lower() == 'test':
        weibo.test()
    else:
        weibo.run()
