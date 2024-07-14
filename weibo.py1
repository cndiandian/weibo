import os
import sys
import time
import wget
import json
import sqlite3
import configparser
from bs4 import BeautifulSoup
from requests_html import HTMLSession

WEIBO_ID = os.environ.get("WEIBO_ID")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

class Weibo:
    def plog(self,content):
        print('{} {}'.format(time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.time())), content))

    def __init__(self):
        self.BASE_DIR = os.path.split(os.path.realpath(__file__))[0]
        config = configparser.ConfigParser()
        config.read(os.path.join(self.BASE_DIR, 'config.ini'), encoding='utf-8')

        # 存储环境变量到类属性中
        self.WEIBO_ID = os.environ.get("WEIBO_ID")
        self.TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
        self.TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

        self.SESSION = HTMLSession()
        self.SESSION.adapters.DEFAULT_RETRIES = 5  # 增加重连次数
        self.SESSION.keep_alive = False  # 关闭多余连接
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

    def parse_weibo(self, weibos):
        """
        检查当前微博是否已处理过，如果没处理过则发送博文以及配图到 Telegram
        """
        weibo_data_file = os.path.join(self.BASE_DIR, 'json_data', 'weibo_data.json')

        # 检查是否已处理过的微博链接列表
    
        if not os.path.exists(weibo_data_file):
            processed_weibos = []
        else:
            with open(weibo_data_file, 'r') as f:
                processed_weibos = json.load(f)
                if not isinstance(processed_weibos, list):  # 确保processed_weibos是一个列表
                        processed_weibos = []

        for weibo in weibos:
            if weibo['link'] not in processed_weibos:
                self.send_telegram_message(
                    '{}@{}:{}'.format(
                        f"[{len(weibo['pics'])}图] " if weibo['pics'] else '',
                        weibo['nickname'],
                        weibo['title'],
                    ),
                    weibo['link']
                )

                # 发送图片到Telegram
                pics = weibo['pics']
                if len(pics) > 0:
                    if len(pics) <= 2:
                        for pic in pics:
                            self.send_telegram_photo(pic)
                    elif len(pics) > 10:
                        self.send_telegram_photos(pics[0 : int(len(pics)/2)])
                        self.send_telegram_photos(pics[int(len(pics)/2):])
                    else:
                        self.send_telegram_photos(pics)

                # 保存图片到本地
                for pic in weibo['pics']:
                    filename = pic.split('/')[-1].split('?')[0]
                    filename = os.path.join(self.BASE_DIR, 'images', filename)
                    wget.download(pic, out=filename)

                # 将已处理的微博链接保存到JSON文件中
                processed_weibos.append(weibo['link'])

        # 将已处理的微博链接列表保存回JSON文件中
        with open(weibo_data_file, 'w') as f:
            json.dump(processed_weibos, f)

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
        self.plog('开始运行>>>')

        weibo_ids = self.WEIBO_ID.split(',')
        for weibo_id in weibo_ids:
            self.plog(f'    |-开始获取 {weibo_id} 的微博')
            url = f'https://m.weibo.cn/api/container/getIndex?containerid=107603{weibo_id}'

            try:
                weibo_items = self.SESSION.get(url).json()['data']['cards'][::-1]
            except:
                self.plog('    |-访问URL出错了')
                continue

            weibos = []  # 存储获取到的所有微博信息
            for item in weibo_items:
                weibo = {}
                try:
                    if item['mblog']['isLongText']:
                        # 如果博文包含全文则获取完整微博信息
                        weibo = self.get_weibo_detail(item['mblog']['bid'])
                    else:
                        weibo['title'] = BeautifulSoup(item['mblog']['text'].replace('<br />', '\n'), 'html.parser').get_text()
                        weibo['nickname'] = item['mblog']['user']['screen_name']
                        weibo['pics'] = [pic['large']['url'] for pic in item['mblog'].get('pics', [])]
                        weibo['link'] = self.get_pc_url(weibo_id, item['mblog']['bid'])
                except Exception as e:
                    self.plog(f"    |-处理微博出错: {str(e)}")
                    continue

                weibos.append(weibo)

            self.parse_weibo(weibos)  # 将获取到的微博信息列表传递给parse_weibo方法
            self.plog(f'    |-获取结束 {weibo_id} 的微博')

        self.plog('<<<运行结束\n')

if __name__ == '__main__':
    weibo = Weibo()
    argv = sys.argv[1] if len(sys.argv) > 1 else ''
    if argv.lower() == 'test':
        weibo.test()
    else:
        weibo.run()
