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
        self.SESSION.adapters.DEFAULT_RETRIES = 5  # 增加重连次数
        self.SESSION.keep_alive = False  # 关闭多余连接
        proxy = config.get("CONFIG", "PROXY")
        self.PROXIES = {"http": proxy, "https": proxy}

    def send_telegram_message(self, text, weibo_link):
        """
        给电报发送文字消息
        """
        headers = {
            'Content-Type': 'application/json',
        }
        data = f'{{"chat_id":"{self.TELEGRAM_CHAT_ID}", "text":"{text}", "reply_markup": {{"inline_keyboard":' \
               f' [[{{"text":"🔗点击查看原微博", "url":"{weibo_link}"}}]]}}}} '
        url = f'https://api.telegram.org/bot{self.TELEGRAM_BOT_TOKEN}/sendMessage'
        try:
            self.SESSION.post(url, headers=headers, data=data.encode('utf-8'), proxies=self.PROXIES)
        except:
            print('    |-网络代理错误，请检查确认后关闭本程序重试')
            time.sleep(99999)

    def send_telegram_photo(self, img_url):
        """
        给电报发送图片
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
        if result.status_code != 200: # 如果分组发送失败 则单独发送图片
            for pic in pics:
                self.send_telegram_photo(pic)

    def parse_weibo(self, weibo):
        """
        检查当前微博是否已处理过，如果没处理过则发送博文以及配图到Telegram
        """
        conn = sqlite3.connect(os.path.join(self.BASE_DIR, 'db', 'weibo.db'))
        cursor = conn.cursor()

        sql = "SELECT COUNT(id) AS counts FROM weibo WHERE link = ?"
        cursor.execute(sql, (weibo['link'],))
        result = cursor.fetchone()

        if result[0] <= 0:
            self.send_telegram_message(
                '{}@{}:{}'.format(
                    f"[{len(weibo['pics'])}图] " if weibo['pics'] else '',
                    weibo['nickname'],
                    weibo['title'],
                ),
                weibo['link']
            )

            # 把图片url发送到Telegram中，可以第一时间在Telegram中收到推送
            pics = weibo['pics']
            if len(pics) > 0:
                if len(pics) <= 2: # 如果配图小于2张 则一张一张独立发送
                    for pic in pics:
                        self.send_telegram_photo(pics)
                elif len(pics) > 10: # 如果配图大于10张 则分2组发送
                    self.send_telegram_photos(pics[0 : int(len(pics)/2)])
                    self.send_telegram_photos(pics[int(len(pics)/2):])
                else:
                    self.send_telegram_photos(pics)

            # 配图发送到Telegram毕后，将配图独立保存到本地一份
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
        print('* 正在检查微博ID是否配置正确')
        url = f'https://m.weibo.cn/api/container/getIndex?containerid=100505{self.WEIBO_ID}'
        try:
            weibo_name = self.SESSION.get(url).json()['data']['userInfo']['screen_name']
            print(f'【正确】当前设置的微博账户为：@{weibo_name}')
        except:
            print('【错误】请重新测试或检查微博数字ID是否正确')

        print('\n* 正在检查代理是否配置正确')
        try:
            status_code = self.SESSION.get('https://www.google.com',proxies=self.PROXIES, timeout=5).status_code
            if status_code == 200:
                print('【正确】代理配置正确，可正常访问')
            else:
                print('【错误】代理无法访问到电报服务器')
        except:
            print('【错误】代理无法访问到电报服务器')

    def get_weibo_detail(self, bid):
        url = f'https://m.weibo.cn/statuses/show?id={bid}'
        detail = self.SESSION.get(url).json()
        weibo = {}
        weibo['title'] = BeautifulSoup(detail['data']['text'].replace('<br />', '\n'), 'html.parser').get_text()
        weibo['nickname'] = detail['data']['user']['screen_name']
        weibo_id = detail['data']['user']['id']
        weibo['pics'] = []
        if 'pics' in detail['data']: # 判断博文中是否有配图，如果有配图则做解析
            weibo['pics'] = [pic['large']['url'] for pic in detail['data']['pics']]
        weibo['link'] = self.get_pc_url(weibo_id, bid)
        self.parse_weibo(weibo)

    def get_pc_url(self, weibo_id, bid):
        return 'https://weibo.com/{weibo_id}/{uri}'.format(
            weibo_id = weibo_id,
            uri = bid
        )

    def run(self):
        self.plog('开始运行>>>')

        weibo_ids = self.WEIBO_ID.split(',')
        for weibo_id in weibo_ids:
            self.plog(f'    |-开始获取 {weibo_id} 的微博')
            url = f'https://m.weibo.cn/api/container/getIndex?containerid=107603{weibo_id}'

            try:
                weibo_items = self.SESSION.get(url).json()['data']['cards'][::-1]
            except:
                self.plog('    |-访问url出错了')

            for item in weibo_items:
                weibo = {}
                try:
                    if item['mblog']['isLongText']: # 如果博文包含全文 则去解析完整微博
                        self.get_weibo_detail(item['mblog']['bid'])
                        continue
                except:
                    continue

                weibo['title'] = BeautifulSoup(item['mblog']['text'].replace('<br />', '\n'), 'html.parser').get_text()
                weibo['nickname'] = item['mblog']['user']['screen_name']

                if item['mblog'].get('weibo_position') == 3:  # 如果状态为3表示转发微博，附加上转发链，状态1为原创微博
                    retweet = item['mblog']['retweeted_status']
                    try:
                        weibo['title'] = f"{weibo['title']}//@{retweet['user']['screen_name']}:{retweet['raw_text']}"
                    except:
                        weibo['title'] = f"{weibo['title']}//转发原文不可见，可能已被删除"

                try:
                    weibo['pics'] = [pic['large']['url'] for pic in item['mblog']['pics']]
                except:
                    weibo['pics'] = []

                weibo['link'] = self.get_pc_url(weibo_id, item['mblog']['bid'])

                self.parse_weibo(weibo)
            self.plog(f'    |-获取结束 {weibo_id} 的微博')
        self.plog('<<<运行结束\n')


if __name__ == '__main__':
    weibo = Weibo()
    argv = sys.argv[1] if len(sys.argv) > 1 else ''
    if argv.lower() == 'test':
        weibo.test()
    else:
        weibo.run()
