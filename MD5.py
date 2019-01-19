# -*- coding: utf-8 -*-
from hashlib import md5
import json


#mode = '1'  #加密
mode = '2'  #解密

user = '*********'

pwd = ''

salt = 'openkey'


# 获取原始密码+salt的md5值  
def create_md5(pwd,salt):  
    md5_obj = md5()  
    md5_obj.update((pwd + salt).encode('utf-8'))  
    return md5_obj.hexdigest()   



if mode == '1':

    # 加密后的密码  
    md5_user = create_md5(user, salt)
    md5_pwd = create_md5(pwd, salt)
      
    #print '[pwd]\n',pwd  
    #print '[salt]\n', salt  
    #print '[md5]\n', md5  

    data = [md5_user,md5_pwd,salt]
    jsdata = json.dumps(data)

    with open('???.json','w')as f:
        f.write(jsdata)


if mode == '2':    
    with open('key.json','r')as f:
       jsdata = f.read()

    data = json.loads(jsdata)
    







        
