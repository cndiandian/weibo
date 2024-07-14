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
    def __init__(self):
        self.BASE_DIR = os.path.split(os.path.realpath(__file__))[0]
        os.makedirs(os.path.join(self.BASE_DIR, 'db'), exist_ok=True)
        db_file_path = os.path.join(self.BASE_DIR, 'db', 'weibo.db')
        if not os.path.exists(db_file_path):
            print("SQLite database file does not exist. Checking out from repository...")
            os.system("git clone https://github.com/7755919/Girls-Frontline-weibo.git /tmp/repository")
            os.makedirs(os.path.dirname(db_file_path), exist_ok=True)
            os.system(f"cp /tmp/repository/db/weibo.db {db_file_path}")

        config = configparser.ConfigParser()
        config.read(os.path.join(self.BASE_DIR, 'config.ini'), encoding='utf-8')
        
        self.proxy = config.get("CONFIG", "PROXY")
        self.PROXIES = {"http": self.proxy, "https": self.proxy}
        
        self.WEIBO_ID = os.environ.get("WEIBO_ID")
        self.TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
        self.TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

        self.SESSION = HTMLSession()
        self.SESSION.adapters.DEFAULT_RETRIES = 5
        self.SESSION.keep_alive = False

    def plog(self, content):
        print('{} {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())), content))

    def send_telegram_message(self, text, weibo_link):
        headers = {'Content-Type': 'application/json'}
        data = f'{{"chat_id":"{self.TELEGRAM_CHAT_ID}", "text":"{text}", "reply_markup": {{"inline_keyboard":[[{{"text":"🔗點擊查看原微博", "url":"{weibo_link}"}}]]}}}}'
        url = f'https://api.telegram.org/bot{self.TELEGRAM_BOT_TOKEN}/sendMessage'
        try:
            self.SESSION.post(url, headers=headers, data=data.encode('utf-8'), proxies=self.PROXIES)
        except:
            print('    |-網絡代理錯誤，請檢查確認後關閉本程序重試')
            time.sleep(99999)

    def send_telegram_photo(self, img_url):
        url = f'https://api.telegram.org/bot{self.TELEGRAM_BOT_TOKEN}/sendPhoto'
        data = {'chat_id': self.TELEGRAM_CHAT_ID, 'photo': img_url}
        self.SESSION.post(url, data=data, proxies=self.PROXIES)

    def send_telegram_photos(self, pics):
        url = f'https://api.telegram.org/bot{self.TELEGRAM_BOT_TOKEN}/sendMediaGroup'
        params = {'chat_id': self.TELEGRAM_CHAT_ID, 'media': []}
        for pic in pics:
            params['media'].append({'type': 'photo', 'media': pic})
        params['media'] = json.dumps(params['media'])
        result = self.SESSION.post(url, data=params, proxies=self.PROXIES)
        if result.status_code != 200:
            for pic in pics:
                self.send_telegram_photo(pic)

    def parse_weibo(self, weibo):
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
            pics = weibo['pics']
            if len(pics) > 0:
                if len(pics) <= 2:
                    for pic in pics:
                        self.send_telegram_photo(pic)
                elif len(pics) > 10:
                    self.send_telegram_photos(pics[0: int(len(pics) / 2)])
                    self.send_telegram_photos(pics[int(len(pics) / 2):])
                else:
                    self.send_telegram_photos(pics)
            for pic in weibo['pics']:
                filename = pic.split('/')[-1].split('?')[0]
                filename = os.path.join(self.BASE_DIR, 'images', filename)
                wget.download(pic, out=filename)
            sql = "INSERT INTO weibo(summary, link) VALUES(?, ?)"
            cursor.execute(sql, (weibo['title'], weibo['link']))
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
            status_code = self.SESSION.get('https://www.google.com', proxies=self.PROXIES, timeout=5).status_code
            if status_code == 200:
                print('【正確】代理配置正確，可正常訪問')
            else:
                print('【錯誤】代理無法訪問到TG服務器')
        except:
            print('【錯誤】代理無法訪問到TG服務器')

    def get_weibo_detail(self, bid):
        url = f'https://m.weibo.cn/statuses/show?id={bid}'
        detail = self.SESSION.get(url).json()
        weibo = {}
        weibo['title'] = BeautifulSoup(detail['data']['text'].replace('<br />', '\n'), 'html.parser').get_text()
        weibo['nickname'] = detail['data']['user']['screen_name']
        weibo_id = detail['data']['user']['id']
        weibo['pics'] = []
        if 'pics' in detail['data']:
            weibo['pics'] = [pic['large']['url'] for pic in detail['data']['pics']]
        weibo['link'] = self.get_pc_url(weibo_id, bid)
        self.parse_weibo(weibo)

    def get_pc_url(self, weibo_id, bid):
        return f'https://weibo.com/{weibo_id}/{bid}'

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
                    if item['mblog']['isLongText']:
                        self.get_weibo_detail(item['mblog']['bid'])
                        continue
                except:
                    continue
                weibo['title'] = BeautifulSoup(item['mblog']['text'].replace('<br />', '\n'), 'html.parser').get_text()
                weibo['nickname'] = item['mblog']['user']['screen_name']
                if item['mblog'].get('weibo_position') == 3:
                    retweet = item['mblog']['retweeted_status']
                    try:
                        weibo['title'] = f"{weibo['title']} //@{retweet['user']['screen_name']}:{retweet['raw_text']}"
                    except:
                        weibo['title'] = f"{weibo['title']} //轉發原文不可見，可能已被刪除"
                try:
                    weibo['pics'] = [pic['large']['url'] for pic in item['mblog']['pics']]
                except:
                    weibo['pics'] = []
                weibo['link'] = self.get_pc_url(weibo_id, item['mblog']['bid'])
                self.parse_weibo(weibo)
            self.plog(f'    |-獲取結束 {weibo_id} 的微博')
        self.plog('運行結束>>>')

        # 在這裡調用更新數據庫的函數
        self.update_database()

    def update_database(self):
        conn = sqlite3.connect(os.path.join(self.BASE_DIR, 'db', 'weibo.db'))
        cursor = conn.cursor()

        # 示例更新語句，可以根據需要修改
        sql = "UPDATE weibo SET summary = ? WHERE link = ?"
        cursor.execute(sql, ('Updated summary', 'http://example.com'))

        conn.commit()
        conn.close()

if __name__ == "__main__":
    weibo = Weibo()
    weibo.run()
