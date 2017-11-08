#coding:utf-8
import sys
import time
import random
import json
import requests

reload(sys)
sys.setdefaultencoding('utf-8')

FuncName = lambda n=0: sys._getframe(n + 1).f_code.co_name

def quit(signum, frame):
    print 'You choose to stop me.'
    sys.exit()



def readFile(file):
    #读文件
    tem=[]
    with open(file) as f:
        for ck in f:
            tem.append(ck.strip('\n'))
    return tem

def tag_val(tag, key=''):
    '''
    return html tag attribute @key
    if @key is empty, return tag content
    '''
    if tag is None:
        return ''
    elif key:
        txt = tag.get(key)
    else:
        txt = tag.text
    return txt.strip(' \t\r\n') if txt else ''

def tags_val(tag, key='', index=0):
    '''
    return html tag list attribute @key @index
    if @key is empty, return tag content
    '''
    if len(tag) == 0 or len(tag) <= index:
        return ''
    elif key:
        txt = tag[index].get(key)
    else:
        txt = tag[index].text
    return txt.strip(' \t\r\n') if txt else ''

def timestamp_datetime(value):
    format = '%Y-%m-%d'
    ## value为传入的值为时间戳(整形)，如：1332888820
    value = time.localtime(value)
    ## 经过localtime转换后变成
    # ## time.struct_time(tm_year=2012, tm_mon=3, tm_mday=28, tm_hour=6, tm_min=53, tm_sec=40, tm_wday=2, tm_yday=88, tm_isdst=0)
    ## 最后再经过strftime函数转换为正常日期格式。
    dt = time.strftime(format, value)
    return dt

def datetime_timestamp(dt):
    # dt为字符串
    # #中间过程，一般都需要将字符串转化为时间数组
    time.strptime(dt, '%Y-%m-%d %H:%M:%S')
    ## time.struct_time(tm_year=2012, tm_mon=3, tm_mday=28, tm_hour=6, tm_min=53, tm_sec=40, tm_wday=2, tm_yday=88, tm_isdst=-1)
    # 将"2012-03-28 06:53:40"转化为时间戳
    s = time.mktime(time.strptime(dt, '%Y-%m-%d %H:%M:%S'))
    return int(s)

def timeValidation(sess,cookies,headers,gettime):
    #验证是否到达秒杀时间
    try:
        # 获取系统时间（带headers）
        resp = sess.get(
            'https://a.jd.com/ajax/queryServerData.html',
            cookies=cookies,
            headers=headers,
            params={
                'r': '%u' % random.uniform(0, 1),
            }
        )
        if resp.status_code != requests.codes.OK:
            print (u'网络问题，请重试！状态码: %u' % resp.status_code)
            return False
        x = json.loads(resp.text.encode('utf8'))
        servertime = int(x['serverTime'])
        bftime = servertime
        #特殊处理24点
        if gettime == '24':
            coupontime = timestamp_datetime(float(servertime / 1000)) + ' ' + '23:59:59'
            coupontime = datetime_timestamp(coupontime) * 1000 + 1000
        else:
            coupontime = timestamp_datetime(float(servertime / 1000)) + ' ' + str(gettime) + ':00:00'
            coupontime = datetime_timestamp(coupontime) * 1000
        #留出1s以内，以便手动减少延迟
        while coupontime - servertime > 999:
            jsq1 = time.time()
            pd = True
            servertime = servertime + 1000
            strtime = time.strftime('%H:%M:%S', time.localtime((coupontime - servertime) / 1000))
            H = int(strtime[:2]) - 8
            print u'剩余时间为：%d:%s' % (H, time.strftime('%M:%S', time.localtime((coupontime - servertime) / 1000)))
            #每10秒重新获取京东系统时间
            if servertime - bftime == 10000:
                jsq1 = time.time() #计时器1
                resp = sess.get(
                    'https://a.jd.com/ajax/queryServerData.html',
                    cookies=cookies,
                    headers=headers,
                    params={
                        'r': '%u' % random.uniform(0, 1),
                    }
                )
                jsq3 = time.time()#计时器3，用（jsq3-jsq1）/2约为发送请求用的时间
                #print jsq3-jsq1 #0.5
                if resp.status_code != requests.codes.OK:
                    print (u'网络问题，请重试！状态码: %u' % resp.status_code)
                    return False
                pd = False
                x = json.loads(resp.text.encode('utf8'))
                servertime = int(x['serverTime'])
            #每次睡眠一秒，包含代码运行时间，所以需要去掉代码时间
            if pd:
                jsq2 = time.time()
                time.sleep(1 - jsq2 + jsq1)
            #长期睡眠会造成延迟，通过重新获取系统时间，去掉延迟
            else:
                jsq2 = time.time()
                servertime += int((jsq2 - (jsq1+jsq3)/2) * 1000)
                bftime = servertime
        #预留50ms误差
        if coupontime - servertime -50> 0:
            time.sleep((coupontime - servertime-50) / 1000.0)
        return True
    except Exception, e:
        print 'Exp {0} : {1}'.format(FuncName(), e)
        return False

def getBeiJingTime():
    # 获取gettime时间
    sess=requests.Session()
    resp = sess.get(
        'http://api.k780.com:88/?app=life.time&appkey=10003&sign=b59bc3ef6191eb9f747dd4e83c99f2a4&format=json')
    if resp.status_code != requests.codes.OK:
        print (u'网络问题，请重试！状态码: %u' % resp.status_code)
        return False
    x = json.loads(resp.text)
    if x['success'] == '1':
        print u'当前时间：{}'.format(x['result']['timestamp'])
    else:
        print u'获取时间出错'
        return False

def loginValidation(sess,cookies):
    #https://passport.jd.com/loginservice.aspx?callback=jQuery4549788&method=Login&_=1508417256151
    # 获取登录状态
    headers={
        'Host': 'home.jd.com',
        'Connection': 'keep-alive',
        'Accept': 'application/json,text/javascript,*/*;q=0.01',
        'X-Requested-With': 'XMLHttpRequest',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36',
        'DNT': '1',
        'Referer': 'https://a.jd.com/',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6'
    }
    resp = sess.get(
        'http://home.jd.com/',
        cookies=cookies,
        headers=headers
    )
    if resp.status_code != requests.codes.OK:
        print (u'网络问题，请重试！状态码: %u' % resp.status_code)
        return False
    if resp.text!='{"error":"NotLogin"}':
        return True
    else:
        return False

def updatethor(sess,cookies):
    #更新cookies以保持cookies活性
    url='https://passport.jd.com/new/helloService.ashx'
    headers={
        'Host': 'passport.jd.com',
        'Connection': 'keep-alive',
        'User - Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
        'Accept': '*/*',
        'DNT': '1',
        'Referer': 'https://i.jd.com/user/info',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh - CN, zh;q = 0.8, en;q = 0.6'
    }
    resp=sess.get(
        url,
        headers=headers,
        cookies=cookies,
        params={
            'callback': 'jQuery%u' % random.randint(100000, 999999),
            '_': (long)(time.time() * 1000)
        },
    )
    if resp.status_code != requests.codes.OK:
        print u'获取二维码失败: %u' % resp.status_code
        return False
    print resp.cookies
    cookies['thor']=resp.cookies['thor']




