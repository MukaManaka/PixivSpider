#! /usr/bin/python
# -*- coding: utf-8 -*-

import os
import re
import time

import requests
from bs4 import BeautifulSoup

from SpiderCookies import *

# 解决Python3 requests发送HTTPS请求，已经关闭认证（verify=False）情况下，控制台输出InsecureRequestWarning的问题
# from requests.packages.urllib3.exceptions import InsecureRequestWarning  
# requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# import sys
# non_bmp_map = dict.fromkeys(range(0x10000, sys.maxunicode + 1), 0xfffd)

# 需打开SS全局代理
# 不支持多图及动图
'''
异常会出现在日期换算
'''

# 显示函数执行report
def stateReport(func):
    def wrapper(*args, **kw):
        res = func(*args, **kw)
        if res[0]:
            print(res[1])
        else:
            raise Exception(res[1])
        return res
    return wrapper

class PixivSpider(object):
    def __init__(self, user, password):
        self.initSetting()
        self.initVar()

    # 配置设置
    def initSetting(self):
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36'}

        self.illust_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.80 Safari/537.36',
        'accept-language': 'zh-CN,zh;q=0.9',
        'cache-control': 'max-age=0',
        'referer': 'https://www.pixiv.net/ranking.php?mode=daily&content=illust',
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        'accept-encoding': 'gzip, deflate, br'}
        
        self.proxies = {'https': 'http://127.0.0.1:10809'}

    # 全局变量
    def initVar(self):
        self.session = requests.session()
        # self.rawcookies = open('cookies.txt',encoding = 'utf-8').read()
        self.lib = []
        self.user = user
        self.password = password

    # 目录检验：载入已存在的文件名，用于避免重复下载
    def search_lib(self):
        dir_ = os.getcwd() + r'\Pixiv Download'
        # print(dir_)
        for root, dirs, files in os.walk(dir_):
            for file in files:
                self.lib.append(file[:-4])

    # 登录账户
    @stateReport
    def login(self):
        print("正在登录...")
        url = 'https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index'
        log = self.session.get(url=url, headers=self.headers, proxies=self.proxies)
        if log.status_code != 200:
            return False, f"获取登录key的网页GET错误，状态码为：{log.status_code}"
        else:
            logbs = BeautifulSoup(log.content, 'lxml')
            key = logbs.select('#old-login')[0].find('input')['value']

            self.data = {
                'pixiv_id': self.user,
                'captcha': None,
                'g_recaptcha_response': None,
                'password': self.password,
                'post_key': key,
                'source': 'pc',
                'ref': 'wwwtop_accounts_index',
                'return_to': 'https://www.pixiv.net/'}

            log = self.session.post(url=url, headers=self.headers, data=self.data, proxies=self.proxies)
            if log.status_code != 200:
                return False, f"获取登录网页POST错误，状态码为：{log.status_code}"
            else:
                return True, f"登陆成功!"

    # 根据illust_id网页的上传日期信息，推断及换算得到下载链接中的日期信息
    def get_uploaddate(self, text):
        date_match = re.search(r'"uploadDate":".+?"', text, flags=re.M).group()
        year = date_match[14:18]
        month = date_match[19:21]
        day = date_match[22:24]
        if (int(date_match[25:27]) + 9) >= 24:
            hour = str(int(date_match[25:27]) + 9 - 24)
            day = str(int(day) + 1)
        else:
            hour = str(int(date_match[25:27]) + 9)
        if len(hour) == 1:
            hour = '0' + hour
        if len(month) == 1:
            month = '0' + month
        if len(day) == 1:
            day = '0' + day
        minute = date_match[28:30]
        second = date_match[31:33]
        if len(minute) == 1:
            minute = '0' + minute
        if len(second) == 1:
            second = '0' + second
        return year, month, day, hour, minute, second

    # 根据uid下载文件
    @stateReport
    def download_for_uid(self, uid):
        url_illust = f'https://www.pixiv.net/member_illust.php?mode=medium&illust_id={uid}'
        illust = self.get_with_retry(url=url_illust, headers=self.illust_headers)
        if illust.status_code != 200:
            return False, f'访问illust_id网页出错，状态码为：{illust.status_code}'

        year, month, day, hour, minute, second = self.get_uploaddate(illust.text)
        
        # 下载链接
        img = r'https://i.pximg.net/img-original/img/{}/{}/{}/{}/{}/{}/{}_p0.jpg'.format(year, month, day, hour, minute, second, uid)

        status = self.save(img, uid)
        return status

    # 重复GET多次
    def get_with_retry(self, url, headers, n=3):
        for i in range(n):
            try:
                illust = self.session.get(url=url, headers=headers, proxies=self.proxies)
            except:
                time.sleep(0.5)
                print('Retry {} times'.format(i + 1))
                continue
            return illust
        return illust

    # 保存文件
    def save(self, img, name):
        # print('正在保存文件...')
        png = img[:-3] + 'png'
        headers = self.illust_headers
        headers['Referer'] = 'https://www.pixiv.net/member_illust.php?mode=medium&illust_id={}'.format(name)
        html = self.get_with_retry(url=img, headers=headers)
        if not html:
            html = self.get_with_retry(url=png, headers=headers)
            if not html:
                return False, f'保存文件出错,Get方法失败,html:{png}', 
        if html.status_code == 200:
            pix = html.content
            suffix = img[-4:]
            path = r'Pixiv Download\{}'.format(name + suffix)
            with open(path, 'wb') as f:
                f.write(pix)
            return True, '保存成功.'
        else:
            return False, f'保存文件出错,无法访问图片地址, 状态码：{html.status_code}'
            
    # 读取排行插画, num=排行前num个
    def daily(self, num=20):
        print('正在抓取daily...')
        url = 'https://www.pixiv.net/ranking.php?mode=daily&content=illust'
        # 静态抓取
        self.index_html = self.session.get(url=url, headers=self.headers, proxies=self.proxies)
        index_content = self.index_html.text

        soup = BeautifulSoup(index_content, 'lxml')
        # source = i.find('span', {'class': 'comeFrom'}).find('a').get_text().strip()
        list_a = soup.select('#wrapper .layout-body ._unit .ranking-items-container')  # .ranking-items adjust
        list_b = list_a[0].find_all(name='section')

        # 遍历50个html id
        for i, b in enumerate(list_b):
            data_id = b['data-id']
            print('\n当前index = {}, id = {}'.format(i, data_id))

            status = self.download_for_uid(data_id)

            if status[0]:
                print(f'index:{i + 1}/{num}   id = {data_id}  已保存')
            else:
                print('跳过index:{}'.format(i + 1))
            if i >= num-1:
                break


if __name__ == '__main__':
    # 账号密码
    user = input('请输入账号(邮箱)：')
    password = input('请输入密码：')
    pix = PixivSpider(user, password)

    pix.search_lib()
    if user == password == '':
        load_cookies(pix.session)
        print('使用cookies登陆')
    else:
        pix.login()
        save_cookies(pix.session.cookies)
    

    pix.daily()



