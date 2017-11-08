# -*- coding: utf-8 -*-
import requests
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()
import time
import signal
from function import updatethor,loginValidation,readFile,quit
import threading

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
jdpool = []
class updateThor(object):
    '''
    Update cookies every 20 minutes
    '''
    def __init__(self):
        self.sess=requests.session()
        self.cookies={
        }
    def update(self):
        #更新cookies中的thor并保存
        global jdpool
        while loginValidation(sess=self.sess,cookies=self.cookies):
            print '++++++++++++++++++++++++++++++++++++++++++++++++++'
            time.sleep(600)
            if self.cookies['thor'] in jdpool:
                jdpool.remove(self.cookies['thor'])
            updatethor(sess=self.sess,cookies=self.cookies)
            jdpool.append(self.cookies['thor'])


def quitw(signum, frame):
    print 'You choose to stop me.'
    sys.exit()

def writeCookies(cookies):
    #保存cookies
    if cookies:
        cookies_file = 'cookiesDate.txt'
        with open(cookies_file, 'wb') as f:
            for ck in cookies:
                f.write(ck+'\n')

if __name__ == '__main__':
    def updatethread(thor):
        jd = updateThor()
        jd.cookies['thor'] = thor
        jd.update()

    try:
        signal.signal(signal.SIGINT, quitw)
        signal.signal(signal.SIGTERM, quitw)
        cookiesThor=readFile('cookiesDate.txt')
        for thor in cookiesThor:
            t = threading.Thread(target=updatethread,args=(thor,))
            t.setDaemon(True)
            t.start()
        print '--------------------------------------'
        while True:
            pass
    except Exception as exc:
        print exc
    finally:
        print u'该程序已经结束！'
        writeCookies(jdpool)
