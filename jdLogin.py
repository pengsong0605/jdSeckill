# -*- coding: utf-8 -*-

'''
author:songqiu
time:2017/10/06 22:15
email:826410901@qq.com
function:jingdong seckill
'''


import requests
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()
import time
import json
import random
import argparse
import subprocess
import signal
from function import FuncName,quit,readFile,tags_val
import bs4
import os

import sys
reload(sys)
sys.setdefaultencoding('utf-8')



class JDLogin(object):
    '''
    This class used to login JD and get thor cookie
    '''

    def __init__(self):
        # tips：cookies only need thor
        self.cookies = []

    def writeCookies(self):
        if self.cookies:
            cookies_file = 'cookiesDate.txt'
            with open(cookies_file, 'wb') as f:
                for ck in self.cookies:
                    f.write(ck+'\n')

    def login_by_Account(self,id,pwd):
        #账号密码登陆
        headers0={
            'Host': 'passport.jd.com',
            'Cache-Control': 'max-age=0',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'DNT': '1',
            'Accept-Encoding':'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6'
        }
        headers1 = {
            'Host': 'passport.jd.com',
            'Connection': 'keep-alive',
            'Accept': 'text/plain, */*; q=0.01',
            'Origin': 'https://passport.jd.com',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari / 537.36',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'DNT': '1',
            'Referer': 'https://passport.jd.com/new/login.aspx?ReturnUrl=https%3A%2F%2Fwww.jd.com%2F',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6'
        }
        headers2={
            'Host': 'authcode.jd.com',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari / 537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'DNT': '1',
            'Referer': 'https://passport.jd.com/new/login.aspx?ReturnUrl=https%3A%2F%2Fwww.jd.com%2F',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6'
        }
        data1 = {'uuid': '',
             'eid': '',
             'fp': '',
             '_t': '_t',
             'loginType': 'c',
             'loginname': id,
             'nloginpwd': pwd,
             'chkRememberMe': '',
             'authcode': '',
             'pubKey': '',
             'sa_token':''
                 }
        data2={
            'loginName':id,
        }
        cookies={
            '_t':'',
            'alc':''
        }
        try:
            print '+++++++++++++++++++++++++++++++++++++++++++++++++++++++'
            print u'{0} > 正在登陆，准备获取cookies:'.format(time.ctime())
            urls=(
                'https://passport.jd.com/new/login.aspx?ReturnUrl=https%3A%2F%2Fwww.jd.com%2F' ,
                'https://passport.jd.com/uc/showAuthCode',
                'https://passport.jd.com/uc/loginService'
            )
            #get alc and _t
            sess = requests.Session()
            resp=sess.get(urls[0],headers=headers0,verify=False)
            if resp.status_code != requests.codes.OK:
                print u'获取二维码失败: %u' % resp.status_code
                return False
            cookies['_t']=resp.cookies['_t']
            cookies['alc']=resp.cookies['alc']
            #print cookies
            sess = requests.Session()

            #whether need verification code
            resp1=sess.post(
                urls[1],
                data=data2,
                headers=headers1,
                cookies=cookies,
                params={
                    'r': random.random(),
                    'version': '2015'
                },
                verify=False
            )
            jsonV=json.loads(resp1.text[1:-1])
            y = bs4.BeautifulSoup(resp.text, "html.parser")
            x = y.select('#formlogin input')
            data1['uuid']=tags_val(x,key='value',index=1).encode('utf8')
            data1['sa_token'] = tags_val(x, key='value', index=0).encode('utf8')
            vUrl='https://authcode.jd.com/verify/image?a=1&acid={0}&uid={0}&yys='.format(data1['uuid'])
            if jsonV['verifycode']==True:
                #需要验证码
                while not data1['authcode']:
                    print u'该账号需要验证码，请等待！(如需重新加载验证码请按回车键)'
                    # get v image
                    #sess = requests.Session()
                    vUrlt=vUrl+str(int(time.time() * 1000))
                    print vUrlt
                    sess = requests.Session()
                    resp2 = sess.get(
                            vUrlt,
                            headers=headers2,
                            verify=False
                        )
                    if resp2.status_code != requests.codes.OK:
                        print u'获取二维码失败: %u' % resp2.status_code
                        return False
                    image_file = 'qr.png'
                    with open(image_file, 'wb') as f:
                        for chunk in resp2.iter_content(chunk_size=1024):
                            f.write(chunk)
                    imgprocess = subprocess.Popen("mspaint.exe qr.png")
                    data1['authcode']=raw_input("Input Verification Code:\n").encode('utf8')
                    imgprocess.kill()
            #print '----------------------------------------------------'
            #time.sleep(0.2)
            #登陆
            sess = requests.Session()
            resp3 = sess.post(
                urls[2],
                headers=headers1,
                params={
                    'uuid': data1['uuid'],
                    'r': random.random(),
                    'version': '2015'
                },
                data=data1,
                cookies=cookies,
                verify=False
            )
            if resp3.status_code != requests.codes.OK:
                print u'获取二维码失败: %u' % resp3.status_code
                return False
            result=json.loads(resp3.text[1:-1])
            #print result
            #print resp3.text
            resultTem=result.get('success', "")
            if resultTem=='':
                for i in result.keys():
                    if i!='_t':
                        print u'登陆结果：'+result[i]
            else:
                self.cookies.append(resp3.cookies['thor'])
                print u'cookies获取成功！'
                return True
        except Exception as e:
            print 'Exp {0} : {1}'.format(FuncName(), e)
            raise

        return False





    def login_by_QR(self):
        #二维码登录
        # session
        sess = requests.Session()
        #login_by_QR headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36',
            'ContentType': 'text/html; charset=utf-8',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': 'zh-CN,zh;q=0.8',
            'Connection': 'keep-alive',
        }
        # jd login by QR code
        try:
            print '+++++++++++++++++++++++++++++++++++++++++++++++++++++++'
            print u'{0} > 请打开京东手机客户端，准备扫码获取cookies:'.format(time.ctime())

            urls = (
                'https://qr.m.jd.com/show',
                'https://qr.m.jd.com/check',
                'https://passport.jd.com/uc/qrCodeTicketValidation'
            )

            # step 1: get QR image
            resp = sess.get(
                urls[0],
                headers=headers,
                params={
                    'appid': 133,
                    'size': 147,
                    't': (long)(time.time() * 1000)
                },
                verify=False
            )
            if resp.status_code != requests.codes.OK:
                print u'获取二维码失败: %u' % resp.status_code
                return False

            wlfstk_smdl = resp.cookies['wlfstk_smdl']

            ## save QR code
            image_file = 'qr.png'
            with open(image_file, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=1024):
                    f.write(chunk)

            ## scan QR code with phone
            #mspaint.exe open qr.png
            imgprocess=subprocess.Popen("mspaint.exe qr.png")

            # step 2： check scan result
            ## mush have
            headers['Host'] = 'qr.m.jd.com'
            headers['Referer'] = 'https://passport.jd.com/new/login.aspx'

            # check if QR code scanned
            qr_ticket = None
            retry_times = 100
            while retry_times:
                retry_times -= 1
                resp = sess.get(
                    urls[1],
                    headers=headers,
                    params={
                        'callback': 'jQuery%u' % random.randint(100000, 999999),
                        'appid': 133,
                        'token': wlfstk_smdl,
                        '_': (long)(time.time() * 1000)
                    },
                    verify=False
                )

                if resp.status_code != requests.codes.OK:
                    continue

                n1 = resp.text.find('(')
                n2 = resp.text.find(')')
                rs = json.loads(resp.text[n1 + 1:n2])

                if rs['code'] == 200:
                    print u'{} : {}'.format(rs['code'], rs['ticket'])
                    qr_ticket = rs['ticket']
                    imgprocess.kill()
                    break
                elif rs['code'] == 203:
                    print u'{} : {}'.format(rs['code'], rs['msg'])
                    imgprocess.kill()
                    return False
                else:
                    print u'{} : {}'.format(rs['code'], rs['msg'])
                    time.sleep(3)

            if not qr_ticket:
                print u'二维码登陆失败'
                return False

            # step 3: validate scan result
            ## must have
            headers['Host'] = 'passport.jd.com'
            headers['Referer'] = 'https://passport.jd.com/uc/login?ltype=logout'
            resp = sess.get(
                urls[2],
                headers=headers,
                params={'t': qr_ticket},
                verify=False
            )
            if resp.status_code != requests.codes.OK:
                print u'二维码登陆校验失败: %u' % resp.status_code
                return False

            self.cookies.append(resp.cookies['thor'])

            print u'登陆成功'
            return True

        except Exception as e:
            print 'Exp {0} : {1}'.format(FuncName(), e)
            raise

        return False

def main(options):
    # 入口
    jd = JDLogin()
    try:
        signal.signal(signal.SIGINT, quit)
        signal.signal(signal.SIGTERM, quit)
        mode=options.mode
        if mode=='1':
            options.num = int(options.num)
            for i in range(options.num):
                if not jd.login_by_QR():
                    print u'第{}个 登陆失败，请重试！'.format(i+1)
        elif mode=='2':
            accountTem=readFile('accountDate.txt')
            for i in accountTem:
                id=i.split(',')
                print u'正在登录账号{}'.format(id[0])
                while not jd.login_by_Account(id[0],id[1]):
                    pass
    except Exception as exc:
        print exc
    finally:
        jd.writeCookies()



if __name__ == '__main__':
    # help message
    parser = argparse.ArgumentParser(description='login Jing Dong, get JingDong cookies.')

    parser.add_argument('-n', '--num',help='Number of login using two-dimensional code', default=1)
    parser.add_argument('-m', '--mode', help='1 is login by QR,2 is login by account in file', default=2)
    options = parser.parse_args()

    print options

    main(options)