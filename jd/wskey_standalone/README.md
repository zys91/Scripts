# WSKEY_STANDALONE

## 使用须知：

- 基于 wskey 原作者 Zy143L [脚本](https://github.com/Zy143L/wskey)修改
- 实现本地 Python 环境部署，无需青龙容器双开实现 CK 生成与分发，更加安全高效
- 基于青龙OpenAPI对容器的环境变量进行读取与写入，所以需要提前在容器内设置好权限
- 脚本不含任何加密或上传用户信息的内容，完全基于原版修改，没有任何夹藏私货
- 风险自行定夺，本人不承担任何责任
- 如有侵权，邮件通知必删

## 使用说明：

```sh
# Linux环境 安装好 python3 pip3 cron git
apt-get install python3 python3-pip cron git
git clone https://github.com/zys91/Scripts.git
cd Scripts/jd/wskey_standalone
pip install -r ./requirements.txt
# 单次执行看输出调试
python3 ./wskey.py
# 没问题后添加到 cron 定时执行
# 首先创建shell文件，并赋予可执行权限
vim wskey.sh
# 填写内容如下(路径自己修改)
#-------内容开始-------
#！/usr/bin/bash
cd /home/xxx/Scripts/jd/wskey_standalone
python3 wskey.py
#-------内容结束-------
chmod +x ./wskey.sh
crontab -e
# 添加定时任务如下: (路径和定时自己修改)
#-------内容开始-------
12 2,14 * * * /home/xxx/Scripts/jd/wskey_standalone/wskey.sh &> /home/xxx/Scripts/jd/wskey_standalone/log.txt
#-------内容结束-------
# 启动并开机自启动服务
systemctl enable cron
systemctl start cron
```
## 配置说明：
- 在 config.json 中配置参数，具体参数含义如下
- 自行抓取好wskey，并在目标青龙容器中创建有环境变量权限的应用
```python
WSKEY_DEBUG = 0                             # 程序调试日志输出开关：0-关 1-开
WSKEY_CHECK_METHOD = 1                      # WSKEY有效期检查方式：0-不检查，强制更新 1-根据生成时间检查 2-JD接口查询有效性
WSKEY_SLEEP = 10                            # 生成WSKEY中休眠时间，默认10s
WSKEY_TRY_COUNT = 1                         # WSKEY生成失败最大尝试次数，默认1次
wskey_list = []                             # WSKEY清单，填写抓到的WSKEY，格式参考["pin=xxxx;wskey=xxxx;","pin=xxxx;wskey=xxxx;"]
ql_new = 1                                  # QL版本指定：0-旧版本<2.11.0 1-新版本>2.11.0
cks_push_ql_client_id = ""                  # 目标容器应用ID (目前只支持单容器，应用须有环境变量权限)
cks_push_ql_client_secret = ""              # 目标容器应用Secret
cks_push_ql_url = "http://localhost:5700/"  # 目标容器地址
BARK = ''                   # bark服务,自行搜索
BARK_PUSH = ''              # bark自建服务器，要填完整链接，结尾的/不要
SCKEY = ''                  # Server酱的SCKEY
TG_BOT_TOKEN = ''           # tg机器人的TG_BOT_TOKEN
TG_USER_ID = ''             # tg机器人的TG_USER_ID
TG_API_HOST = ''            # tg 代理api
TG_PROXY_IP = ''            # tg机器人的TG_PROXY_IP
TG_PROXY_PORT = ''          # tg机器人的TG_PROXY_PORT
DD_BOT_ACCESS_TOKEN = ''    # 钉钉机器人的DD_BOT_ACCESS_TOKEN
DD_BOT_SECRET = ''          # 钉钉机器人的DD_BOT_SECRET
QQ_SKEY = ''                # qq机器人的QQ_SKEY
QQ_MODE = ''                # qq机器人的QQ_MODE
QYWX_AM = ''                # 企业微信
QYWX_KEY = ''               # 企业微信BOT
PUSH_PLUS_TOKEN = ''        # 微信推送Plus+
```
