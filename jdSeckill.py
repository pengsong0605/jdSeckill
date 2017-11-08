# -*- coding: utf-8 -*-

'''
author:songqiu
time:2017/10/06 22:15
email:826410901@qq.com
function:jingdong seckill
'''

import bs4
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()
import threading
import argparse
from function import *
import sys
import signal
reload(sys)
sys.setdefaultencoding('utf-8')


class JDSecKill(object):
    '''
    This class used to JingDong seckill.
    '''

    def __init__(self):
        '''
                33:在售,
                34:售完，
                36:预售
                40:可配货
        '''
        self.statusCode=[33,40]
        self.dicts = {}  # venderId,ptype,targetId,promoID
        self.orderId=''
        # session
        self.sess = requests.Session()
        #self.sess.proxies={'https':'127.0.0.1:8888'}
        self.headers = {
            'Host': 'a.jd.com',
            'Connection': 'keep-alive',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
            'DNT': '1',
            'Referer': 'https://a.jd.com/',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6'
        }
        # tips：cookies only need thor
        self.cookies = {

        }

    @staticmethod
    def response_status(resp):
        if resp.status_code != requests.codes.OK:
            print 'Status: %u, Url: %s' % (resp.status_code, resp.url)
            return False
        return True


    def good_stock(self, stock_id, area_id=None):
        # 物品销售状态
        # http://c0.3.cn/stocks?type=getstocks&skuIds=3133811&area=1_72_2799_0
        # https://c0.3.cn/stocks?type=getstocks&skuIds=4901275&area=4_50951_52496_0
        #   jQuery2289454({"3133811":{"StockState":33,"freshEdi":null,"skuState":1,"PopType":0,"sidDely":"40","channel":1,"StockStateName":"现货","rid":null,"rfg":0,"ArrivalDate":"","IsPurchase":true,"rn":-1}})
        # jsonp or json both work
        stock_url = 'http://c0.3.cn/stocks'

        payload = {
            'type': 'getstocks',
            'skuIds': str(stock_id),
            'area': area_id or '4_50951_52496_0',  # area change as needed
        }

        try:
            # get stock state
            resp = self.sess.get(stock_url, params=payload)
            if not self.response_status(resp):
                print u'获取商品库存失败'
                return (0, '')

            # return json
            resp.encoding = 'gbk'
            stock_info = json.loads(resp.text)
            stock_stat = int(stock_info[stock_id]['StockState'])
            stock_stat_name = stock_info[stock_id]['StockStateName']
            return stock_stat, stock_stat_name

        except Exception as e:
            print 'Exp {0} : {1}'.format(FuncName(), e)
            time.sleep(0.5)
            return (0, '')

    def good_detail(self, stock_id, area_id=None):
        # 物品详情
        # return good detail
        good_data = {
            'id': stock_id,
            'name': '',
            'link': '',
            'price': '',
            'stock': '',
            'stockName': '',
        }

        try:
            # shop page
            stock_link = 'http://item.jd.com/{0}.html'.format(stock_id)
            resp = self.sess.get(stock_link)

            # good page
            soup = bs4.BeautifulSoup(resp.text, "html.parser")

            # good name
            tags = soup.select('div#name h1')
            if len(tags) == 0:
                tags = soup.select('div.sku-name')
            good_data['name'] = tags_val(tags).strip(' \t\r\n')
            # body > div:nth-child(7) > div > div.itemInfo-wrap > div.sku-name


            # cart link
            # 购物车连接
            tags = soup.select('a#InitCartUrl')
            link = tags_val(tags, key='href')

            if link[:2] == '//':
                link = 'http:' + link
            good_data['link'] = link

        except Exception, e:
            print 'Exp {0} : {1}'.format(FuncName(), e)

        # good price
        good_data['price'] = self.good_price(stock_id)

        # good stock
        good_data['stock'], good_data['stockName'] = self.good_stock(stock_id=stock_id, area_id=area_id)

        print '+++++++++++++++++++++++++++++++++++++++++++++++++++++++'
        print u'{0} > 商品详情'.format(time.ctime())
        print u'编号：{0}'.format(good_data['id'])
        print u'库存：{0}'.format(good_data['stockName'])
        print u'价格：{0}'.format(good_data['price'])
        print u'名称：{0}'.format(good_data['name'])
        print u'链接：{0}'.format(good_data['link'])

        return good_data

    def good_price(self, stock_id):
        # 物品价格
        # get good price
        url = 'http://p.3.cn/prices/mgets'
        # 完整：https://p.3.cn/prices/mgets?callback=jQuery6880904&type=1&area=4_50951_52496_0&pdtk=&pduid=&pdpin=&pin=null&pdbp=0&skuIds=J_4577217&ext=11000000&source=item-pc
        payload = {
            'type': 1,
            'pduid': int(time.time() * 1000),
            'skuIds': 'J_' + stock_id,
        }

        price = '?'
        try:
            resp = self.sess.get(url, params=payload)
            resp_txt = resp.text.strip()
            # print resp_txt

            js = json.loads(resp_txt[1:-1])
            price = js.get('p')

        except Exception, e:
            print 'Exp {0} : {1}'.format(FuncName(), e)

        return price

    def buy(self, options):
        '''
            购买流程：
            首先清空购物车，获取物品信息，添加购物车，改变商品数量，查看购物车中的商品，提交订单,输出订单价格
        '''
        if not self.remove_cart():
            print u'清理失败！'
        # stock detail
        good_data = self.good_detail(options.good)

        # retry until stock not empty
        if good_data['stock'] not in self.statusCode:
            # flush stock state
            while good_data['stock'] not in self.statusCode and options.flush:
                print u'<%s> <%s> <%s>' % (good_data['stock'],good_data['stockName'], good_data['name'])
                time.sleep(options.wait / 1000.0)
                good_data['stock'], good_data['stockName'] = self.good_stock(stock_id=options.good,
                                                                             area_id=options.area)
        # failed
        link = good_data['link']
        if good_data['stock'] not in self.statusCode or link == '':
            print u'stock {0}, link {1}'.format(good_data['stock'], link)
            return False
        try:
            # add to cart
            resp = self.sess.get(link, cookies=self.cookies)
            soup = bs4.BeautifulSoup(resp.text, "html.parser")

            # tag if add to cart succeed
            tag = soup.select('h3.ftx-02')
            #
            if tag is None:
                tag = soup.select('div.p-name a')

            if tag is None or len(tag) == 0:
                print u'添加到购物车失败'
                return False

            print '+++++++++++++++++++++++++++++++++++++++++++++++++++++++'
            print u'{0} > 购买详情'.format(time.ctime())
            print u'结果：{0}'.format(tags_val(tag))
            print '+++++++++++++++++++++++++++++++++++++++++++++++++++++++'
            print u'{0} > 购物车详情(未修改商品数量)'.format(time.ctime())
            self.cart_detail()
            # change count
            self.buy_good_count(options.good, options.count)

        except Exception, e:
            print 'Exp {0} : {1}'.format(FuncName(), e)
        else:
            print '+++++++++++++++++++++++++++++++++++++++++++++++++++++++'
            print u'{0} > 购物车详情(已修改商品数量)'.format(time.ctime())
            self.cart_detail()
            if self.order_info(options.submit, options.time):
                self.obligation()
                return True

        return False

    def buy_good_count(self, good_id, count):
        # 改变购物车中good_id的数量为count
        url = 'https://cart.jd.com/changeNum.action'

        payload = {
            't': '0',
            'venderId': self.dicts[good_id][0].encode('utf8'),
            'pid': good_id,
            'pcount': count,
            'ptype': self.dicts[good_id][1].encode('utf8'),
            'targetId': self.dicts[good_id][2].encode('utf8'),
            'promoID': self.dicts[good_id][2].encode('utf8'),
            'outSkus': '',
            'random': random.random(),
            'locationId': '4_50951_52496_0',  # need changed to your area location id#4_50951_52496_0 （chongqing）
        }

        try:
            rs = self.sess.post(url, params=payload, cookies=self.cookies)
            if rs.status_code == 200:
                js = json.loads(rs.text)
                if js.get('pcount'):
                    print u'数量：%s @ %s' % (js['pcount'], js['pid'])
                    return True
            else:
                print u'购买 %d 失败' % count

        except Exception, e:
            print 'Exp {0} : {1}'.format(FuncName(), e)

        return False

    def cart_detail(self):
        # 购物车列表
        # list all goods detail in cart
        cart_url = 'https://cart.jd.com/cart.action'  # 购物车连接
        cart_header = u'购买    数量    价格        总价        商品'
        cart_format = u'{0:8}{1:8}{2:12}{3:12}{4}'

        try:
            resp = self.sess.get(cart_url, cookies=self.cookies)
            resp.encoding = 'utf-8'
            soup = bs4.BeautifulSoup(resp.text, "html.parser")

            print '+++++++++++++++++++++++++++++++++++++++++++++++++++++++'
            print u'{0} > 购物车明细'.format(time.ctime())
            print cart_header
            ##product_4436773 > div.item-form
            for item in soup.select('div.item-form'):
                ##product_17394070173 > div.item-form > div.cell.p-quantity > div.quantity-form
                check = tags_val(item.select('div.cart-checkbox input'),
                                 key='checked')  ##product_4436773 > div.item-form > div.cell.p-checkbox
                check = ' + ' if check else ' - '
                count = tags_val(item.select('div.quantity-form input'),
                                 key='value')  ##product_4436773 > div.item-form > div.cell.p-quantity > div.quantity-form
                venderId = tags_val(item.select('div.quantity-form a'), key='id')
                x = venderId.split('_')
                if len(x) == 6:
                    self.dicts[x[2]] = (x[1], x[4], x[5])
                elif len(x) == 5:
                    self.dicts[x[2]] = (x[1], x[4], '0')
                else:
                    print u'京东已修改，请联系脚本作者。'
                price = tags_val(
                    item.select('div.p-price strong'))  ##product_4436773 > div.item-form > div.cell.p-price
                sums = tags_val(
                    item.select('div.p-sum strong'))  ##product_4436773 > div.item-form > div.cell.p-price > strong
                gname = tags_val(item.select(
                    'div.p-name a'))  ##product_5105837 > div.item-form > div.cell.p-goods > div > div.item-msg > div.p-name
                #: ￥字符解析出错, 输出忽略￥
                print cart_format.format(check, count, price[1:], sums[1:], gname)

            t_count = tags_val(soup.select(
                'div.amount-sum em'))  ##cart-floatbar > div > div > div > div.options-box > div.toolbar-right > div.normal > div > div.amount-sum
            t_value = tags_val(soup.select(
                'span.sumPrice em'))  ##cart-floatbar > div > div > div > div.options-box > div.toolbar-right > div.normal > div > div.price-sum > div > span.price.sumPrice
            print u'总数: {0}'.format(t_count)
            print u'总额: {0}'.format(t_value[1:])

        except Exception, e:
            print 'Exp {0} : {1}'.format(FuncName(), e)



    def order_info(self, submit=False, gettime=22):
        if not timeValidation(self.sess, self.cookies, self.headers, gettime):
            print u'时间获取失败！'
            return False

        # 提交订单完成
        # get order info detail, and submit order
        print '+++++++++++++++++++++++++++++++++++++++++++++++++++++++'
        print u'{0} > 订单详情'.format(time.ctime())

        try:
            # order or not
            if not submit:
                return False

            # order
            order_url = 'http://trade.jd.com/shopping/order/submitOrder.action'  # 提交订单信息
            rp = self.sess.post(order_url, cookies=self.cookies)

            if rp.status_code == 200:
                # print rp.text
                js = json.loads(rp.text)
                if js['success'] == True:
                    self.orderId=js['orderId']
                    print u'下单成功！订单号：{0}'.format(self.orderId)
                    print u'请前往东京官方商城付款'
                    return True
                else:
                    print u'下单失败！<{0}: {1}>'.format(js['resultCode'], js['message'])
                    if js['resultCode'] == '60017':
                        # 60017: 您多次提交过快，请稍后再试
                        time.sleep(0.1)
            else:
                print u'请求失败. StatusCode:', rp.status_code
        except Exception, e:
            print 'Exp {0} : {1}'.format(FuncName(), e)

        return False

    def remove_cart(self):
        # 清理购物车中勾选项，以免和秒杀一起提交
        try:
            rp = self.sess.get('https://cart.jd.com/batchRemoveSkusFromCart.action', cookies=self.cookies)
            if rp.status_code == 200:
                print u'已经清空购物车！'
                return True
            return False
        except Exception, e:
            print 'Exp {0} : {1}'.format(FuncName(), e)
            return False

    def obligation(self):
        try:
            rp = self.sess.get('https://order.jd.com/center/list.action?s=1', cookies=self.cookies)
            if rp.status_code == 200:
                if '没有待付款的订单哦' in rp.text:
                    print u'没有订单需要付款！'
                else:
                    soup = bs4.BeautifulSoup(rp.text, "html.parser")
                    tags = soup.select('#tb-{}'.format(self.orderId))
                    print '+++++++++++++++++++++++++++++++++++++++++++++++++++++++'
                    print u'{0} > 订单价格详情'.format(time.ctime())
                    print u'{}价格为：'.format(self.orderId)+tags_val(tags[0].select('div.amount strong'), index=1)[1:]

        except Exception, e:
            print 'Exp {0} : {1}'.format(FuncName(), e)
            return False


def main(options):
    # 入口

    def sk(thor):
        jd = JDSecKill()
        print u'thor : {}'.format(thor)
        jd.cookies['thor'] = thor
        if not loginValidation(sess=jd.sess,cookies=jd.cookies):
            print u'cookies已经失效！'
            print thor
            return False
        while not jd.buy(options) and options.flush:
            time.sleep(options.wait / 1000.0)

    try:
        signal.signal(signal.SIGINT, quit)
        signal.signal(signal.SIGTERM, quit)
        ck=readFile('cookiesDate.txt')
        if ck:
            for c in ck:
                t=threading.Thread(target=sk,args=(c,))
                t.setDaemon(True)
                t.start()
            while True:
                pass
        else:
            print u'cookies is null'
    except Exception as exc:
        print exc



if __name__ == '__main__':
    # help message
    parser = argparse.ArgumentParser(
        description='When the specified time is reached, the specified item is purchased(using cookies).')

    parser.add_argument('-a', '--area',
                        help='Area string, like:1_72_2819_0 for Beijing,4_50951_52496_0 for chongqing',
                        default='4_50951_52496_0')
    # 重庆     4_50951_52496_0
    parser.add_argument('-g', '--good',
                        help='Jing Dong good ID', default='')
    parser.add_argument('-c', '--count', type=int,
                        help='The count to buy', default=1)
    parser.add_argument('-w', '--wait',
                        type=int, default=500,
                        help='Flush time interval, unit MS')
    parser.add_argument('-f', '--flush',
                        action='store_true',
                        help='Continue flash if good out of stock')
    parser.add_argument('-s', '--submit',
                        action='store_true',
                        help='Submit the order to Jing Dong')
    parser.add_argument('-t', '--time',
                        help='seckill time', default=22)

    # example goods
    good_id = '5525866'

    options = parser.parse_args()

    # for test
    if options.good == '':
        options.good = good_id

    print options

    main(options)
