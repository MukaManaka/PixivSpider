#! /usr/bin/python
# -*- coding: utf-8 -*-
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from bs4 import BeautifulSoup
import requests
import json
import time
import re
import os
#import sys
#non_bmp_map = dict.fromkeys(range(0x10000, sys.maxunicode + 1), 0xfffd)
#需打开SS全局代理

#不支持多图及动图
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
'''
异常会出现在日期换算
'''

class Pixiv(object):
    def __init__(self,user,password):
        self.headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.80 Safari/537.36'}
        self.illust_headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.80 Safari/537.36',
                        'accept-language': 'zh-CN,zh;q=0.9',
                        'cache-control':'max-age=0',
                        'referer': 'https://www.pixiv.net/ranking.php?mode=daily&content=illust',
                        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                        'accept-encoding': 'gzip, deflate, br'
                        }                  
        self.proxies = {'http': 'http://127.0.0.1:1080'}
        self.session = requests.session()
        #self.rawcookies = open('cookies.txt',encoding = 'utf-8').read()
        self.lib = []
        self.user = user
        self.password = password 


    def search_lib(self):
        print('正在查找目录文件...')
        dir_ = os.getcwd() + r'\Pixiv Download'
        #print(dir_)
        for root, dirs, files in os.walk(dir_):
            for file in files:
                self.lib.append(file[:-4])


    def login(self):
        print('正在登陆...')
        url = 'https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index'
        log = self.session.get(url = url ,headers=self.headers, proxies=self.proxies)
        logbs = BeautifulSoup(log.content,'lxml')
        key = logbs.select('#old-login')[0].find('input')['value']
        self.data = {
        'pixiv_id': self.user,
        'captcha': None,
        'g_recaptcha_response': None,
        'password': self.password,
        'post_key': key,
        'source': 'pc',
        'ref': 'wwwtop_accounts_index',
        'return_to': 'https://www.pixiv.net/'
        }
        log = self.session.post(url = url ,headers=self.headers, data = self.data,proxies=self.proxies)
        print('登陆状态:{}'.format(log))
    

    def get_with_retry(self, url, headers):
        for i in range(3):
            try:
                illust = self.session.get(url=url, headers=headers, proxies=self.proxies)
            except:
                time.sleep(0.5)
                print('Retry {} times'.format(i+1))
                continue
            return illust
        return False
        
    def daily(self):
        print('正在抓取daily...')
        url = 'https://www.pixiv.net/ranking.php?mode=daily&content=illust'
        #静态抓取
        self.index_html = self.session.get(url=url, headers=self.headers, proxies=self.proxies)
        index_content = self.index_html.text
        if DELAY:
            time.sleep(0.5)
        soup = BeautifulSoup(index_content, 'lxml')
        #source = i.find('span', {'class': 'comeFrom'}).find('a').get_text().strip()
        list_a = soup.select('#wrapper .layout-body ._unit .ranking-items-container')#.ranking-items adjust
        list_b = list_a[0].find_all(name = 'section')

        #遍历50个html id
        for i,b  in enumerate(list_b):
            data_id = b['data-id']
            if DEBUG:   print('\n当前index = {}, id = {}'.format(i,data_id))
            url_illust = ('https://www.pixiv.net/member_illust.php?mode=medium&illust_id={}'.format(data_id))
            if DELAY:   time.sleep(0.2)
            if data_id in self.lib:
                print('index：{}   id：{}已存在...Skip'.format(i+1,data_id))
                continue
            illust = self.get_with_retry(url = url_illust,headers = self.illust_headers)
            if not illust:
                print('访问illust_id出错,跳过index:{}'.format(i+1))
                continue
            illust_text = illust.text
            if DELAY:   time.sleep(0.2)
            if DEBUG:   print('id网页访问: ', illust)
            # 日期推断及换算
            date_match = re.search(r'"uploadDate":".+?"', illust_text ,flags=re.M).group()
            year = date_match[14:18]
            month = date_match[19:21]
            day = date_match[22:24] 
            if (int(date_match[25:27]) + 9 ) >= 24:
                hour = str(int(date_match[25:27]) + 9 - 24)
                day = str(int(day) + 1)
            else:
                hour = str(int(date_match[25:27]) + 9) 
            if len(hour) == 1 : hour = '0' + hour
            if len(month) == 1 : month = '0' + month
            if len(day) == 1 : day = '0' + day
            minute = date_match[28:30]
            second = date_match[31:33]
            if len(minute) == 1 : minute = '0' + minute
            if len(second) == 1 : second = '0' + second
            date_code = (year, month, day, hour, minute, second, data_id)
            img = r'https://i.pximg.net/img-original/img/{}/{}/{}/{}/{}/{}/{}_p0.jpg'.format(year, month, day, hour, minute, second, data_id)
            if DEBUG:   print('date_code解析: ',date_code)
            #保存文件
            statu = self.save(img, data_id)
            if DELAY:   time.sleep(0.5)
            if statu:
                print('index:{}/50   id = {}  已保存' .format(i+1,data_id) )
            else:
                print('跳过index:{}'.format(i+1))


        
    def save(self, img, name):
        #print('正在保存文件...')
        png = img[:-3] + 'png'
        headers = self.illust_headers
        headers['Referer'] = 'https://www.pixiv.net/member_illust.php?mode=medium&illust_id={}'.format(name)
        html = self.get_with_retry(url=img, headers=headers)
        if not html:
            html = self.get_with_retry(url=png, headers=headers)
            if not html:
                print('保存文件出错,Get方法失败,html:',png)
                return False 
        if html.status_code == 200:
            pix = html.content
            suffix = img[-4:]
            path = r'Pixiv Download\{}'.format(name + suffix)
            with open(path,'wb') as f:  
                f.write(pix)
            return True
        else:
            print('保存文件出错,无法访问,{}'.format(html.status_code))
            return False


def save_cookies(cookies):
    saved = json.dumps(cookies.get_dict()) # 保存
    with open('cookies.json','w') as f:  
            f.write(saved)
            
def load_cookies(session):
    with open('cookies.json','r') as f:
        session.cookies.update(json.loads(f.read())) # 读取
    return session


def save_html(index_content):
    with open('foo.html','w',encoding='utf-8') as f:
        f.write(index_content)  




def main():
    user = input('请输入账号(邮箱)：')
    password = input('请输入密码：')
    pix = Pixiv(user,password)
    pix.search_lib()
    if user == password == '':
        load_cookies(pix.session)
        print('使用cookies登陆')
    else:
        pix.login()
        save_cookies(pix.session.cookies)
    pix.daily()





if __name__ == '__main__' :
    DELAY = False
    DEBUG = False
    main()
    input('Finished.')


















