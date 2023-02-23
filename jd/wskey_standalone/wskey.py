#!/usr/bin/env python3
# -*- coding: utf-8 -*

# Rights: Zy143L
# Modify: zys91

import socket   # 用于端口检测
import base64   # 用于编解码
import json     # 用于Json解析
import os       # 用于导入系统变量
import sys      # 实现 sys.exit
import logging  # 用于日志输出
import time     # 时间
import re       # 正则过滤

# 默认配置
WSKEY_DEBUG = 0                             # 程序调试日志输出开关：0-关 1-开
WSKEY_CHECK_METHOD = 1                      # WSKEY有效期检查方式：0-不检查，强制更新 1-根据生成时间检查 2-JD接口查询有效性
WSKEY_SLEEP = 10                            # 生成WSKEY中休眠时间，默认10s
WSKEY_TRY_COUNT = 1                         # WSKEY生成失败最大尝试次数，默认1次
wskey_list = []                             # WSKEY清单，填写抓到的WSKEY
ql_new = 1                                  # QL版本指定：0-旧版本<2.11.0 1-新版本>2.11.0
cks_push_ql_client_id = ""                  # 目标容器应用ID (目前只支持单容器，应用须有环境变量权限)
cks_push_ql_client_secret = ""              # 目标容器应用Secret
cks_push_ql_url = "http://localhost:5700/"  # 目标容器地址

if os.path.exists('config.json'):
    with open(r"config.json") as json_file:
        try:
            config = json.load(json_file)
            globals().update(config)
        except:    
            config = {}
            print("配置文件格式不正确，程序退出\n")  # 日志输出
            sys.exit(1)  # 退出脚本
else:
    print("缺少配置文件，程序退出\n")  # 日志输出
    sys.exit(1)  # 退出脚本

if WSKEY_DEBUG:  # 判断调试模式变量
    logging.basicConfig(level=logging.DEBUG, format='%(message)s')  # 设置日志为 Debug等级输出
    logger = logging.getLogger(__name__)  # 主模块
    logger.debug("\nDEBUG模式开启!\n")  # 消息输出
else:  # 判断分支
    logging.basicConfig(level=logging.INFO, format='%(message)s')  # Info级日志
    logger = logging.getLogger(__name__)  # 主模块

try:  # 异常捕捉
    import requests  # 导入HTTP模块
except Exception as e:  # 异常捕捉
    logger.info(str(e) + "\n缺少requests模块, 请执行命令：pip3 install requests\n")  # 日志输出
    sys.exit(1)  # 退出脚本
requests.packages.urllib3.disable_warnings()  # 抑制错误
try:  # 异常捕捉
    from sendNotify import send  # 导入青龙消息通知模块
except Exception as err:  # 异常捕捉
    logger.debug(str(err))  # 调试日志输出
    logger.info("无推送文件")  # 标准日志输出

ver = 21212  # 版本号


def ql_send(text):
    try:  # 异常捕捉
        send('WSKEY转换', text)  # 消息发送
    except Exception as err:  # 异常捕捉
        logger.debug(str(err))  # Debug日志输出
        logger.info("通知发送失败")  # 标准日志输出


# 返回值 Token
def ql_login():  # 方法 青龙登录(获取Token 功能同上)
    url_token = cks_push_ql_url + 'open/auth/token?client_id=' + cks_push_ql_client_id + '&client_secret=' + cks_push_ql_client_secret
    try:  # 异常捕捉
        res = requests.get(url_token)
        if res.status_code == 200 and res.json()["code"] == 200:
            token = json.loads(res.text)["data"]["token"]
            return token
        else:
            logger.info("青龙登录失败")
            ql_send("青龙登录失败, 请检查!")
            sys.exit(1)  # 脚本退出
    except Exception as err:
        logger.debug(str(err))  # Debug日志输出


# 返回值 list[wskey]
def get_wskey():  # 方法 获取 wskey值 [系统变量传递]
    if len(wskey_list) > 0:  # 判断 WSKEY 数量 大于 0 个
        return wskey_list  # 返回 WSKEY [LIST]
    else:  # 判断分支
        logger.info("JD_WSCK变量未启用")  # 标准日志输出
        sys.exit(1)  # 脚本退出


# 返回值 bool
def check_ck(ck):  # 方法 检查 Cookie有效性 使用变量传递 单次调用
    searchObj = re.search(r'pt_pin=([^;\s]+)', ck, re.M | re.I)  # 正则检索 pt_pin
    if searchObj:  # 真值判断
        pin = searchObj.group(1)  # 取值
    else:  # 判断分支
        pin = ck.split(";")[1]  # 取值 使用 ; 分割
    if WSKEY_CHECK_METHOD == 1:
        updateHour = 23  # 更新间隔23小时
        nowTime = time.time()  # 获取时间戳 赋值
        updatedAt = 0.0  # 赋值
        searchObj = re.search(r'__time=([^;\s]+)', ck, re.M | re.I)  # 正则检索 [__time=]
        if searchObj:  # 真值判断
            updatedAt = float(searchObj.group(1))  # 取值 [float]类型
        if nowTime - updatedAt >= (updateHour * 60 * 60) - (10 * 60):  # 判断时间操作
            logger.info(str(pin) + ";即将到期或已过期\n")  # 标准日志输出
            return False  # 返回 Bool类型 False
        else:  # 判断分支
            remainingTime = (updateHour * 60 * 60) - (nowTime - updatedAt)  # 时间运算操作
            hour = int(remainingTime / 60 / 60)  # 时间运算操作 [int]
            minute = int((remainingTime % 3600) / 60)  # 时间运算操作 [int]
            logger.info(str(pin) + ";未到期，{0}时{1}分后更新\n".format(hour, minute))  # 标准日志输出
            return True  # 返回 Bool类型 True
    elif WSKEY_CHECK_METHOD == 2:
        url = 'https://me-api.jd.com/user_new/info/GetJDUserInfoUnion'  # 设置JD_API接口地址
        headers = {
            'Cookie': ck,
            'Referer': 'https://home.m.jd.com/myJd/home.action',
            'user-agent': ua
        }  # 设置 HTTP头
        try:  # 异常捕捉
            res = requests.get(url=url, headers=headers, verify=False, timeout=10, allow_redirects=False)  # 进行 HTTP请求[GET] 超时 10秒
        except Exception as err:  # 异常捕捉
            logger.debug(str(err))  # 调试日志输出
            logger.info("JD接口错误 请重试或者更换IP")  # 标准日志输出
            return False  # 返回 Bool类型 False
        else:  # 判断分支
            if res.status_code == 200:  # 判断 JD_API 接口是否为 200 [HTTP_OK]
                code = int(json.loads(res.text)['retcode'])  # 使用 Json模块对返回数据取值 int([retcode])
                if code == 0:  # 判断 code值
                    logger.info(str(pin) + ";状态正常\n")  # 标准日志输出
                    return True  # 返回 Bool类型 True
                else:  # 判断分支
                    logger.info(str(pin) + ";状态失效\n")
                    return False  # 返回 Bool类型 False
            else:  # 判断分支
                logger.info("JD接口错误码: " + str(res.status_code))  # 标注日志输出
                return False  # 返回 Bool类型 False
    else:
        logger.info("不检查账号有效性\n--------------------\n")  # 标准日志输出
        return False  # 返回 Bool类型 False


# 返回值 bool jd_ck
def getToken(wskey):  # 方法 获取 Wskey转换使用的 Token 由 JD_API 返回 这里传递 wskey
    try:  # 异常捕捉
        url = str(base64.b64decode(url_t).decode()) + 'api/genToken'  # 设置云端服务器地址 路由为 genToken
        header = {"User-Agent": ua}  # 设置 HTTP头
        params = requests.get(url=url, headers=header, verify=False, timeout=20).json()  # 设置 HTTP请求参数 超时 20秒 Json解析
    except Exception as err:  # 异常捕捉
        logger.info("Params参数获取失败")  # 标准日志输出
        logger.debug(str(err))  # 调试日志输出
        return False, wskey  # 返回 -> False[Bool], Wskey
    headers = {
        'cookie': wskey,
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'charset': 'UTF-8',
        'accept-encoding': 'br,gzip,deflate',
        'user-agent': ua
    }  # 设置 HTTP头
    url = 'https://api.m.jd.com/client.action'  # 设置 URL地址
    data = 'body=%7B%22to%22%3A%22https%253a%252f%252fplogin.m.jd.com%252fjd-mlogin%252fstatic%252fhtml%252fappjmp_blank.html%22%7D&'  # 设置 POST 载荷
    try:  # 异常捕捉
        res = requests.post(url=url, params=params, headers=headers, data=data, verify=False,
                            timeout=10)  # HTTP请求 [POST] 超时 10秒
        res_json = json.loads(res.text)  # Json模块 取值
        tokenKey = res_json['tokenKey']  # 取出TokenKey
    except Exception as err:  # 异常捕捉
        logger.info("JD_WSKEY接口抛出错误 尝试重试 更换IP")  # 标准日志输出
        logger.info(str(err))  # 标注日志输出
        return False, wskey  # 返回 -> False[Bool], Wskey
    else:  # 判断分支
        return appjmp(wskey, tokenKey)  # 传递 wskey, Tokenkey 执行方法 [appjmp]


# 返回值 bool jd_ck
def appjmp(wskey, tokenKey):  # 方法 传递 wskey & tokenKey
    wskey = "pt_" + str(wskey.split(";")[0])  # 变量组合 使用 ; 分割变量 拼接 pt_
    if tokenKey == 'xxx':  # 判断 tokenKey返回值
        logger.info(str(wskey) + ";疑似IP风控等问题 默认为失效\n--------------------\n")  # 标准日志输出
        return False, wskey  # 返回 -> False[Bool], Wskey
    headers = {
        'User-Agent': ua,
        'accept': 'accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'x-requested-with': 'com.jingdong.app.mall'
    }  # 设置 HTTP头
    params = {
        'tokenKey': tokenKey,
        'to': 'https://plogin.m.jd.com/jd-mlogin/static/html/appjmp_blank.html'
    }  # 设置 HTTP_URL 参数
    url = 'https://un.m.jd.com/cgi-bin/app/appjmp'  # 设置 URL地址
    try:  # 异常捕捉
        res = requests.get(url=url, headers=headers, params=params, verify=False, allow_redirects=False,
                           timeout=20)  # HTTP请求 [GET] 阻止跳转 超时 20秒
    except Exception as err:  # 异常捕捉
        logger.info("JD_appjmp 接口错误 请重试或者更换IP\n")  # 标准日志输出
        logger.info(str(err))  # 标准日志输出
        return False, wskey  # 返回 -> False[Bool], Wskey
    else:  # 判断分支
        try:  # 异常捕捉
            res_set = res.cookies.get_dict()  # 从res cookie取出
            pt_key = 'pt_key=' + res_set['pt_key']  # 取值 [pt_key]
            pt_pin = 'pt_pin=' + res_set['pt_pin']  # 取值 [pt_pin]
            if WSKEY_CHECK_METHOD == 1:
                jd_ck = str(pt_key) + ';' + str(pt_pin) + ';__time=' + str(time.time()) + ';'  # 拼接变量
            else:  # 判断分支
                jd_ck = str(pt_key) + ';' + str(pt_pin) + ';'  # 拼接变量
        except Exception as err:  # 异常捕捉
            logger.info("JD_appjmp提取Cookie错误 请重试或者更换IP\n")  # 标准日志输出
            logger.info(str(err))  # 标准日志输出
            return False, wskey  # 返回 -> False[Bool], Wskey
        else:  # 判断分支
            if 'fake' in pt_key:  # 判断 pt_key中 是否存在fake
                logger.info(str(wskey) + ";WsKey状态失效\n")  # 标准日志输出
                return False, wskey  # 返回 -> False[Bool], Wskey
            else:  # 判断分支
                logger.info(str(wskey) + ";WsKey状态正常\n")  # 标准日志输出
                return True, jd_ck  # 返回 -> True[Bool], jd_ck


def update():  # 方法 脚本更新模块
    up_ver = int(cloud_arg['update'])  # 云端参数取值 [int]
    if ver >= up_ver:  # 判断版本号大小
        logger.info("当前脚本版本: " + str(ver))  # 标准日志输出
        logger.info("--------------------\n")  # 标准日志输出
    else:  # 判断分支
        logger.info("当前脚本版本: " + str(ver) + "新版本: " + str(up_ver))  # 标准日志输出
        logger.info("存在新版本, 请更新脚本后执行")  # 标准日志输出
        logger.info("--------------------\n")  # 标准日志输出
        text = '当前脚本版本: {0}新版本: {1}, 请更新脚本~!'.format(ver, up_ver)  # 设置发送内容
        ql_send(text)
        # sys.exit(0)  # 退出脚本 [未启用]


def serch_ck(pin):  # 方法 搜索 Pin
    for i in range(len(envlist)):  # For循环 变量[envlist]的数量
        if "name" not in envlist[i] or envlist[i]["name"] != "JD_COOKIE":  # 判断 envlist内容
            continue  # 继续循环
        if pin in envlist[i]['value']:  # 判断envlist取值['value']
            value = envlist[i]['value']  # 取值['value']
            id = envlist[i][ql_id]  # 取值 [ql_id](变量)
            logger.info(str(pin) + "检索成功\n")  # 标准日志输出
            return True, value, id  # 返回 -> True[Bool], value, id
        else:  # 判断分支
            continue  # 继续循环
    logger.info(str(pin) + "检索失败\n")  # 标准日志输出
    return False, 1  # 返回 -> False[Bool], 1


def get_env():  # 方法 读取变量
    url = cks_push_ql_url + 'open/envs'  # 设置 URL地址
    try:  # 异常捕捉
        res = s.get(url)  # HTTP请求 [GET] 使用 session
    except Exception as err:  # 异常捕捉
        logger.debug(str(err))  # 调试日志输出
        logger.info("\n青龙环境接口错误")  # 标准日志输出
        sys.exit(1)  # 脚本退出
    else:  # 判断分支
        data = json.loads(res.text)['data']  # 使用Json模块提取值[data]
        return data  # 返回 -> data


def check_id():  # 方法 兼容青龙老版本与新版本 id & _id的问题
        if ql_new:  # 判断 [_id]
            logger.info("使用 id 键值")  # 标准日志输出
            return 'id'  # 返回 -> 'id'
        else:  # 判断分支
            logger.info("使用 _id 键值")  # 标准日志输出
            return '_id'  # 返回 -> '_id' 


def ql_update(e_id, n_ck):  # 方法 青龙更新变量 传递 id cookie
    url = cks_push_ql_url + 'open/envs'  # 设置 URL地址
    data = {
        "name": "JD_COOKIE",
        "value": n_ck,
        ql_id: e_id
    }  # 设置 HTTP POST 载荷
    data = json.dumps(data)  # json模块格式化
    s.put(url=url, data=data)  # HTTP [PUT] 请求 使用 session
    ql_enable(eid)  # 调用方法 ql_enable 传递 eid


def ql_enable(e_id):  # 方法 青龙变量启用 传递值 eid
    url = cks_push_ql_url + 'open/envs/enable'  # 设置 URL地址
    data = '["{0}"]'.format(e_id)  # 格式化 POST 载荷
    res = json.loads(s.put(url=url, data=data).text)  # json模块读取 HTTP[PUT] 的返回值
    if res['code'] == 200:  # 判断返回值为 200
        logger.info("\n账号启用\n--------------------\n")  # 标准日志输出
        return True  # 返回 ->True
    else:  # 判断分支
        logger.info("\n账号启用失败\n--------------------\n")  # 标准日志输出
        return False  # 返回 -> Fasle


def ql_disable(e_id):  # 方法 青龙变量禁用 传递 eid
    url = cks_push_ql_url + 'open/envs/disable'  # 设置 URL地址
    data = '["{0}"]'.format(e_id)  # 格式化 POST 载荷
    res = json.loads(s.put(url=url, data=data).text)  # json模块读取 HTTP[PUT] 的返回值
    if res['code'] == 200:  # 判断返回值为 200
        logger.info("\n账号禁用成功\n--------------------\n")  # 标准日志输出
        return True  # 返回 ->True
    else:  # 判断分支
        logger.info("\n账号禁用失败\n--------------------\n")  # 标准日志输出
        return False  # 返回 -> Fasle


def ql_insert(i_ck):  # 方法 插入新变量
    data = [{"value": i_ck, "name": "JD_COOKIE"}]  # POST数据载荷组合
    data = json.dumps(data)  # Json格式化数据
    url = cks_push_ql_url + 'open/envs'  # 设置 URL地址
    s.post(url=url, data=data)  # HTTP[POST]请求 使用session
    logger.info("\n账号添加完成\n--------------------\n")  # 标准日志输出


def cloud_info():  # 方法 云端信息
    url = str(base64.b64decode(url_t).decode()) + 'api/check_api'  # 设置 URL地址 路由 [check_api]
    for i in range(3):  # For循环 3次
        try:  # 异常捕捉
            headers = {"authorization": "Bearer Shizuku"}  # 设置 HTTP头
            res = requests.get(url=url, verify=False, headers=headers, timeout=20).text  # HTTP[GET] 请求 超时 20秒
        except requests.exceptions.ConnectTimeout:  # 异常捕捉
            logger.info("\n获取云端参数超时, 正在重试!" + str(i))  # 标准日志输出
            time.sleep(1)  # 休眠 1秒
            continue  # 循环继续
        except requests.exceptions.ReadTimeout:  # 异常捕捉
            logger.info("\n获取云端参数超时, 正在重试!" + str(i))  # 标准日志输出
            time.sleep(1)  # 休眠 1秒
            continue  # 循环继续
        except Exception as err:  # 异常捕捉
            logger.info("\n未知错误云端, 退出脚本!")  # 标准日志输出
            logger.debug(str(err))  # 调试日志输出
            sys.exit(1)  # 脚本退出
        else:  # 分支判断
            try:  # 异常捕捉
                c_info = json.loads(res)  # json读取参数
            except Exception as err:  # 异常捕捉
                logger.info("云端参数解析失败")  # 标准日志输出
                logger.debug(str(err))  # 调试日志输出
                sys.exit(1)  # 脚本退出
            else:  # 分支判断
                return c_info  # 返回 -> c_info


def check_cloud():  # 方法 云端地址检查
    url_list = ['aHR0cHM6Ly9hcGkubW9tb2UubWwv', 'aHR0cHM6Ly9hcGkubGltb2UuZXUub3JnLw==', 'aHR0cHM6Ly9hcGkuaWxpeWEuY2Yv']  # URL list Encode
    for i in url_list:  # for循环 url_list
        url = str(base64.b64decode(i).decode())  # 设置 url地址 [str]
        try:  # 异常捕捉
            requests.get(url=url, verify=False, timeout=10)  # HTTP[GET]请求 超时 10秒
        except Exception as err:  # 异常捕捉
            logger.debug(str(err))  # 调试日志输出
            continue  # 循环继续
        else:  # 分支判断
            info = ['HTTPS', 'Eu_HTTPS', 'CloudFlare']  # 输出信息[List]
            logger.info(str(info[url_list.index(i)]) + " Server Check OK\n--------------------\n")  # 标准日志输出
            return i  # 返回 ->i
    logger.info("\n云端地址全部失效, 请检查网络!")  # 标准日志输出
    ql_send('云端地址失效. 请联系作者或者检查网络.')  # 推送消息
    sys.exit(1)  # 脚本退出


if __name__ == '__main__':  # Python主函数执行入口
    token = ql_login()  # 调用方法 [ql_login]  并赋值 [token]
    s = requests.session()  # 设置 request session方法
    s.headers.update({"authorization": "Bearer " + str(token)})  # 增加 HTTP头认证
    s.headers.update({"Content-Type": "application/json;charset=UTF-8"})  # 增加 HTTP头 json 类型
    ql_id = check_id()  # 调用方法 [check_id] 并赋值 [ql_id]
    url_t = check_cloud()  # 调用方法 [check_cloud] 并赋值 [url_t]
    cloud_arg = cloud_info()  # 调用方法 [cloud_info] 并赋值 [cloud_arg]
    update()  # 调用方法 [update]
    ua = cloud_arg['User-Agent']  # 设置全局变量 UA
    wslist = get_wskey()  # 调用方法 [get_wskey] 并赋值 [wslist]
    envlist = get_env()  # 调用方法 [get_env] 并赋值 [envlist]
    if WSKEY_SLEEP > 0:
        sleepTime = WSKEY_SLEEP  # 获取变量 [int]
    else:  # 判断分支
        sleepTime = 10  # 默认休眠时间 10秒
    for ws in wslist:  # wslist变量 for循环  [wslist -> ws]
        wspin = ws.split(";")[0]  # 变量分割 ;
        if "pin" in wspin:  # 判断 pin 是否存在于 [wspin]
            wspin = "pt_" + wspin + ";"  # 封闭变量
            return_serch = serch_ck(wspin)  # 变量 pt_pin 搜索获取 key eid
            if return_serch[0]:  # bool: True 搜索到账号
                jck = str(return_serch[1])  # 拿到 JD_COOKIE
                if not check_ck(jck):  # bool: False 判定 JD_COOKIE 有效性
                    tryCount = 1  # 重试次数 1次
                    if WSKEY_TRY_COUNT > 0:
                        tryCount = WSKEY_TRY_COUNT  # 设置 [tryCount] int
                    for count in range(tryCount):  # for循环 [tryCount]
                        count += 1  # 自增
                        return_ws = getToken(ws)  # 使用 WSKEY 请求获取 JD_COOKIE bool jd_ck
                        if return_ws[0]:  # 判断 [return_ws]返回值 Bool类型
                            break  # 中断循环
                        if count < tryCount:  # 判断循环次
                            logger.info("{0} 秒后重试，剩余次数：{1}\n".format(sleepTime, tryCount - count))  # 标准日志输出
                            time.sleep(sleepTime)  # 脚本休眠 使用变量 [sleepTime]
                    if return_ws[0]:  # 判断 [return_ws]返回值 Bool类型
                        nt_key = str(return_ws[1])  # 从 return_ws[1] 取出 -> nt_key
                        # logger.info("wskey转pt_key成功", nt_key)  # 标准日志输出 [未启用]
                        logger.info("wskey转换成功")  # 标准日志输出
                        eid = return_serch[2]  # 从 return_serch 拿到 eid
                        ql_update(eid, nt_key)  # 函数 ql_update 参数 eid JD_COOKIE
                    else:  # 判断分支
                        logger.info(str(wspin) + "账号禁用")  # 标准日志输出
                        text = "账号: {0} WsKey疑似失效, Cookie转换失败".format(wspin)  # 设置推送内容
                        ql_send(text)
                else:  # 判断分支
                    logger.info(str(wspin) + "账号有效")  # 标准日志输出
                    logger.info("--------------------\n")  # 标准日志输出
            else:  # 判断分支
                logger.info("\n新wskey\n")  # 标准日志分支
                return_ws = getToken(ws)  # 使用 WSKEY 请求获取 JD_COOKIE bool jd_ck
                if return_ws[0]:  # 判断 (return_ws[0]) 类型: [Bool]
                    nt_key = str(return_ws[1])  # return_ws[1] -> nt_key
                    logger.info("wskey转换成功\n")  # 标准日志输出
                    ql_insert(nt_key)  # 调用方法 [ql_insert]
            logger.info("暂停{0}秒\n".format(sleepTime))  # 标准日志输出
            time.sleep(sleepTime)  # 脚本休眠
        else:  # 判断分支
            logger.info("WSKEY格式错误\n--------------------\n")  # 标准日志输出
    logger.info("执行完成\n--------------------")  # 标准日志输出
    sys.exit(0)  # 脚本退出
    # Enjoy
