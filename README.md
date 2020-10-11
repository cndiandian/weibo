# 订阅微博并同步至Telegram
![](https://img.shields.io/badge/python-3.x-blue) 
![](https://img.shields.io/badge/%E6%8F%90%E7%A4%BA-%E7%94%B5%E6%8A%A5%E5%8A%9F%E8%83%BD%E9%9C%80%E7%A7%91%E5%AD%A6%E4%B8%8A%E7%BD%91-informational)
![](https://visitor-badge.glitch.me/badge?page_id=cndiandian.weibo)

[![](https://img.shields.io/badge/%E5%BE%AE%E5%8D%9A-%40%E7%A7%81%E8%81%8A%E8%AF%9D%E9%A2%98%E5%BA%9F-red "@私聊话题废")](https://weibo.com/u/5698313653)
![](https://img.shields.io/badge/Gmail-shadiaoapp%40gmail.com-red)
![](https://img.shields.io/badge/%E5%BE%AE%E4%BF%A1%EF%BC%88bug%E5%8F%8D%E9%A6%88\)-xshwy000-brightgreen)

## 实现了什么功能？
订阅某个博主的微博，如果有发新微博、转发微博等动态，则及时将微博博文以及配图发送到指定的Telegram频道，并将配图保存到本地一份。

**⚠️请注意：**
1. 微博博文中的表情包会被过滤掉
2. `粉丝可见`、`好友可见`、`分组可见`、`仅自己可见`等`非公开微博`无法被获取到

## 与微博的`特别关注`有什么区别？
除了可以第一时间收到更新通知外，还`可以将博文以及配图保存下来`，这样即便对方删掉微博或者配图被和谐，也还是可以看到原来的样子。

**`请勿用于不正当用途，本脚本初衷是为了追星、保存爱豆的博文配图的。`**

## 效果预览
👇这里应有一个gif图，如果加载不出来请点 [这里查看](https://wx2.sinaimg.cn/large/006LklRdly1gjlh0b9f7ig30oh0fnhdx.gif)
![](https://source.xshwy.cn/github/weibo/preview.gif)

# <h1 id="quickstart">快速开始</h1>
**目录：**
* [0. 目录结构介绍](#menu)
* [1. 下载&安装](#f1)
* [2. 配置](#f2)
    * [2.1 检查配置结果](#f21)
* [3. 开始使用](#f3)
* [4. 设置定时执行](#f4)
* [**🚼无开发经验的小白请看这里**](#beginner)

## <h2 id="menu">目录介绍<h2>
```
├── README.md          使用说明，你当前看到的这个
├── config.ini         主要配置文件，需要修改这个
├── db                 数据库存放处，小白请勿改动
├── images             博文配图存放处
├── install.bat        Win系统安装依赖文件
├── requirements.txt   Python依赖
├── weibo.py           入口文件
├── win_run.bat        Win系统一键启动脚本（供小白用
├── win_test.bat       Win系统测试脚本（供小白用
├── lxml-4.5.2-cp39-cp39-win32.whl
└── lxml-4.5.2-cp39-cp39-win_amd64.whl
```
## <h2 id="f1">下载&安装</h2>
```bash
git clone https://github.com/cndiandian/weibo.git
cd weibo
pip install -r requirements.txt
```

## <h2 id="f2">配置</h2>
编辑修改`config.ini`，按需填写字段即可

[如何创建bot & 获取token](#b3) | [如何获取微博数字ID](#b5)
|必填| 配置项        | 代表含义 | 示例 |
|----| --------      | -----:   |-----:   | 
|✅| TELEGRAM_BOT_TOKEN     |在Telegram申请的bot token |886947303:AAFGhtD3s5KDJ…|
|✅| TELEGRAM_CHAT_ID    |在Telegram创建的频道ID |-1003769903788|
|✅| WEIBO_ID            |微博数字ID             |758673838|
|×| PROXY               |http代理               | - |

### <h3 id="f21">检查配置是否正确</h3>
配置完成后执行`python weibo.py test`测试是否配置正确，测试结果如下：
```
* 正在检查微博ID是否配置正确
【正确】当前设置的微博账户为：@私聊话题废

* 正在检查代理是否配置正确
【正确】代理配置正确，可正常访问
```

## <h2 id="f3">使用</h2>
执行`python weibo.py`即可完成一次查询

## <h2 id="f4">如何定时执行</h2>
1. Linux系统配置：
执行`crontab -e`命令，添加如下内容保存退出即可

    `* * * * * python3绝对路径 -u 项目文件绝对路径 >> 日志存放绝对路径 2>&1`
    
    如：

    `* * * * * /usr/bin/python3 -u /home/weibo/weibo.py >> /home/weibo/weibo.log 2>&1`

2. Windows系统配置：
Windows系统直接打开同目录下的`win_run.bat`就可以定时执行了，每隔1分钟执行一次，如果想要加入到后台，请查阅`windows 计划任务`相关的资料，自行设置。

# <h1 id="beginner">无经验小白从0开始配置</h1>
**目录：**
* [1. 下载Python](#b1)
* [2. 安装Python](#b2)
* [3. Telegram创建BOT & 获取token](#b3)
* [4. Telegram创建频道 / 群组 & 添加bot](#b4)
* [5. 获取微博数字ID](#b5)
* [6. 获取Telegram频道数字ID](#b6)
* [7. 下载 & 使用](#b7)

## <h2 id="b1">1. 下载Python</h2>
* [Python 3.9 Win版 官网下载地址](https://www.python.org/ftp/python/3.9.0/python-3.9.0-amd64.exe) 
* [Python 3.9 Win版 百度网盘分享](https://pan.baidu.com/s/1cz7M0IG_DB-e4VuOngdp6A) 提取码: `xet3`
> `这里仅提供Win的安装方法，linux或mac用户默认你为高玩，可自行搜索安装方法🤪`

## <h2 id="b2">2. 安装Python</h2>
打开上一步下载的安装包，按照如下图所示勾选好项目，点击安装等待安装完成即可

↓ 此处应有配图，若无法看到图片，[请点此访问国内仓库地址](https://gitee.com/cndiandian/weibo)
![](http://qiniu.xshwy.cn/md/pyinstall.jpg)

## <h2 id="b3">3. Telegram创建BOT & 获取token</h2>
1. 私聊`@BotFather` 发送`/newbot`创建一个Telegram Bot
2. 按照提示发送bot名字，名字中英文都可以
3. 输入bot的唯一id，只能是数字、字母、下划线为组合，必须以`bot`结尾，如`ZGlhbmRpYW4Kbot`、`ZGlhbmRpYW4K_bot`都可以
4. 然后就可以获得到bot的token
![](http://qiniu.xshwy.cn/md/newbot.jpg)

## <h2 id="b4">4. Telegram创建频道 / 群组 & 添加bot</h2>
区别：频道类似公众号，只有管理员才可以发言；群组类似QQ群，所有加群人都可以一起发言；
**选择自己喜欢的类型就可以，一般情况只是追星或者特意关注某个博主，建议选择创建频道；如果是一边关注博主动态，一边有和朋友们一起聊天，可以选择群组。**
1. 创建频道`new Channel`
2. 设置频道头像以及名字`Channel name`，可以为中文
3. 设置频道描述`Description(optional)`可以为空
4. 设置频道类型，是公开`Public Channel`还是私密`Private Channel`，公开频道可以自定义链接，任何人都可以加入；私密频道无法自定义链接，只能通过生成的连接邀请加入
5. 创建最后一步，会弹出邀请好友的提示`Add Members`，这里搜索刚刚创建的bot名字，选择后就可以添加到频道里，添加进来会问是否要设置成管理员，点击`MAKE ADMIN`，然后点`SAVE`即可完成
![](http://qiniu.xshwy.cn/md/newchannel.jpg)

## <h2 id="b5">5. 获取微博数字ID</h2>
用电脑浏览器随意打开一条自己的微博，在地址栏 `weibo.com`后面的就是自己微博的数字ID
![](http://qiniu.xshwy.cn/md/weiboid.jpg)

## <h2 id="b6">6. 获取Telegram频道数字ID</h2>
1. 在已添加刚才创建bot的频道里任意发送一条消息
2. 访问：https://api.telegram.org/bot+刚才创建bot时申请的token+/getupdates
3. 在访问结果里找到```"chat":{"id":-1001385856968, "title":……}```，其中的`-1001385856968`就是当前频道的数字ID

## <h2 id="b7">7. 下载 & 使用</h2>
1. 点击右上角绿色的`↓Code`按钮，选择`Download ZIP`
2. 点右键解压下载的压缩包`⚠️请勿直接双击打开`
3. 双击打开`install.bat`，会打开一个屏幕刷刷刷有一堆`绿色的内容滚动`，结束后关闭当前窗口，`install.bat`就可以删掉了
4. 打开`config.ini`文件在里面填写好相关的内容
5. 打开`win_test.bat`文件查看配置是否正确，如果不正确请重新调整配置
5. 打开`win_run.bat`就可以开始运行了，稍后Telegram群组中就可以收到博文推送了

# 打赏
**如果感觉对您有帮助，请作者喝杯咖啡吧，请注明您的名字或者昵称，方便作者咚咚咚🙇‍♂️**

`非强制打赏 非强制打赏（除咚咚咚外 打赏不会提供其他额外服务`

| 微信 | 支付宝 |
| :---: | :---: |
| ![](http://qiniu.xshwy.cn/donate/wechat.jpg) | ![](http://qiniu.xshwy.cn/donate/alipay.jpg) |