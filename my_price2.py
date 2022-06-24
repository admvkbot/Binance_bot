# import telebot
# from telethon import TelegramClient, sync, events
import os
import re
import sys
import time
from datetime import datetime

import mysql.connector as conn
import pandas as pd
import telegram_send
# import math # math.floor()
import xmltodict
from binance import Client

coins = [""]
# coins_true = ["BZRX", "ARPA", "ANKR", "NEAR", "ZEN", "SFP", "GTC", "KEEP", "LUNA", "GALA", "LIT", "RSR", "MASK", "DOT", "TOMO", "BLZ", "ZEC", "ONE", "FTM", "CTK", "UNFI"]
# coins_true = ["BZRX", "ARPA", "ANKR", "ZEN", "SFP", "GTC", "KEEP", "LUNA", "GALA", "LIT", "RSR", "MASK", "TOMO", "BLZ", "ZEC", "ONE", "FTM", "CTK", "UNFI"]
coins_true = []
coins_black = ["RLC", "REN", "MTL", "KLAY", "CVC", "STMX", "PEOPLE"]

orlov_path = "/home/run/orlovbot/"
config_xml = ''
with open(orlov_path + 'main.xml', 'r') as f:
    config_xml = ''.join(list(map(str.strip, f.readlines())))
config = xmltodict.parse(config_xml)

api_key = config['config']['api-key']
api_secret = config['config']['api-secret']
proxy = config['config']['proxy']

api_key_2 = config['config']['api-key2']
api_secret_2 = config['config']['api-secret2']
proxy_2 = config['config']['proxy2']

path = "/var/www/html/"


def log_time(string, file=""):
    if file:
        f = open(file, "a+")
        f.write(str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]) + ': ' + string + "\n")
        f.close()
    else:
        print(str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]) + ': ' + string)


def set_pipe():
    global path
    f = open(path + 'pipe6', 'w+')
    f.close()


def check_pipe():
    global path
    return os.path.isfile(path + 'pipe6')


def del_pipe():
    global path
    os.remove(path + 'pipe6')


if check_pipe():
    log_time("Terminated")
    sys.exit()

set_pipe()

# balance = 0 # размер позиции для лонга
balance_2 = 0  # размер позиции для лонга
# min_balance = 50 # минимальный размер баланса, ниже которого повторная сделка не происходит (работает по линии balance_2)
# short_balance = 0 # размер позиции для шорта
short_balance_2 = 0  # размер позиции для шорта

# summ = 60 #trade summ in dollars

leverage = 10
delitel = 1.2  # делитель баланса
percent_3h = 7  # процент предельного роста за последние 3 часа
### short
time_kline = 25  # время сбора свечи
percent = 1.6
time_wait_buy = 15  # время ожидания перед покупкой
min_perc = 0.1  # при ожидкнии перед покупкой
max_perc = 0.03  # при ожидкнии перед покупкой (to the moon)
zazor = 0.05  # зазор цены между окончанием ожидания и минимальным срабатыванием (0.05 ok)
stop_percent = 0.8  # закрытие при цена после покупки + этот %
moon_overload = 4
take_percent0_main = 0.5
take_percent0_small = 0.45  # при возврате цены в течение отрезка времени
take_percent0_max = 0.5
take_percent0 = take_percent0_main

### long
time_kline_long = 15  # время сбора свечи
percent_long = 1
time_wait_buy_long = 10  # время ожидания перед покупкой
min_perc_long = 0.1  # при ожидкнии перед покупкой
max_perc_long = 0.02  # при ожидкнии перед покупкой (to the moon)
zazor_long = 0.05  # зазор цены между окончанием ожидания и минимальным срабатыванием (0.05 ok)
stop_percent_long = 0.3  # закрытие при цена после покупки + этот %
moon_overload_long = 4
take_percent0_main_long = 0.3
# take_percent0_small = 0.45 # при возврате цены в течение отрезка времени
# take_percent0_max = 0.6
take_percent0_long = take_percent0_main_long

stop_percent_short = 1
short_timeout = 5 * 60  # задержка перед выставлением стоп-ордера шорт-позиции
trigger_percent = 1.6  # высота свечи в %. Выше этого значения лонг отменяется

# далее расписана сетка тейков

take_percent1 = 1.5
take_percent_summ1 = 30
take_percent2 = 1.53
take_percent_summ2 = 30
take_percent3 = 1.55
take_percent_summ3 = 20
take_percent4 = 1.6
take_percent_summ4 = 20

buy_data = {
    'symbol': "",
    'price': 0,
    'stopPrice': 0,
    'count': 0,
    'timestamp': 0
}

buy_data_long = {
    'symbol': "",
    'price': 0,
    'stopPrice': 0,
    'count': 0,
    'timestamp': 0
}
bad_buy = {
    'symbol': "",
    'price': 0,
    'timestamp': 0
}

bad_buy_long = {
    'symbol': "",
    'price': 0,
    'timestamp': 0
}

to_the_moon = {
    'status': 0,
    'symbol': "",
    'price': 0,
    'lowPrice': 0,
    'timestamp': 0
}

to_the_moon_long = {
    'status': 0,
    'symbol': "",
    'price': 0,
    'lowPrice': 0,
    'timestamp': 0
}

take_type = 'true'  # установка reduceOnly для тейков
# if short_balance:
#    take_type = 'false'

# далее расписана сетка шортов
short_percent1 = 5.3
short_percent_summ1 = 20
short_percent2 = 5.5
short_percent_summ2 = 20
short_percent3 = 5.7
short_percent_summ3 = 20
short_percent4 = 5.8
short_percent_summ4 = 20
short_percent5 = 5.9
short_percent_summ5 = 10
short_percent6 = 6
short_percent_summ6 = 10

stdout = path + 'orlovbot6_out.log'
stderr = path + 'orlovbot6_err.log'
str0 = 'http://' + str(proxy)
proxies = {
    'http': 'http://10.10.1.10:3128',
    'https': str0
}
str0 = 'http://' + str(proxy_2)
proxies_2 = {
    'http': 'http://10.10.1.10:3128',
    'https': str0
}

# bot = telebot.TeleBot('1990712394:AAFK_R3HrJYGM76wV_1UltpQzKY1lig2_bA')
# @bot.message_handler(content_types=['text'])


log_time('START BOT')
"""
def get_text_messages(message):
    if message.text == "Привет":
        bot.send_message(message.from_user.id, "Привет, чем я могу тебе помочь?")
    elif message.text == "/help":
        bot.send_message(message.from_user.id, "Напиши привет")
    else:
        bot.send_message(message.from_user.id, "Я тебя не понимаю. Напиши /help.")
"""
# if proxy:
#    bclient = Client(api_key, api_secret, {'proxies': proxies})
# else:
#    bclient = Client(api_key, api_secret)

if proxy_2:
    bclient_2 = Client(api_key_2, api_secret_2, {'proxies': proxies_2})
else:
    bclient_2 = Client(api_key_2, api_secret_2)


###bclient_2 = bclient ###

def telega(messages, conf):
    try:
        telegram_send.send(messages=messages, conf=conf)
    except:
        o = 0


def set_limit_order(order, num):
    db = conn.connect(host="localhost", user="root", password="connect", database="orlovbot")
    cursor = db.cursor()

    # print (order)
    # sys.stdout.flush()
    """
    cursor.execute("SELECT * FROM limit_orders WHERE symbol='"+order['symbol']+"'")
    r = cursor.fetchall()
    db.commit()
    for order in r:
        num = num + order[8]
    """
    sql = "DELETE FROM limit_orders WHERE symbol='" + order['symbol'] + "'"
    cursor.execute(sql)
    db.commit()
    sql = "INSERT INTO limit_orders (symbol, orderId, updateTime, price, origQty, side, status, number) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    val = (
        order['symbol'], order['orderId'], order['updateTime'], order['price'], order['origQty'], order['side'], "new",
        num)
    cursor.execute(sql, val)
    db.commit()
    print(cursor.rowcount, "record inserted.")
    db.close()


def get_order_num(symbol):
    db = conn.connect(host="localhost", user="root", password="connect", database="orlovbot")
    cursor = db.cursor()
    cursor.execute("SELECT * FROM limit_orders WHERE symbol='" + symbol + "'")
    r = cursor.fetchall()
    db.commit()
    db.close()
    num = 0
    for order in r:
        num = order[8]
    return num


def buy(symbol, amount_2):
    try:
        order_2 = bclient_2.futures_create_order(
            symbol=symbol,
            type='MARKET',
            side='SELL',
            quantity=amount_2,
            isIsolated='TRUE'
        )
        print(order_2)
        return order_2
    except:
        return 0


def buy_long(symbol, amount_2):
    try:
        order_2 = bclient_2.futures_create_order(
            symbol=symbol,
            type='MARKET',
            side='BUY',
            quantity=amount_2,
            isIsolated='TRUE'
        )
        print(order_2)
        return order_2
    except:
        return 0


def buy2(symbol, amount_2):
    order_2 = bclient_2.futures_create_order(
        symbol=symbol,
        type='MARKET',
        side='SELL',
        quantity=amount_2,
        isIsolated='TRUE'
    )
    print(order_2)
    return order_2


to_the_moon['status'] = 0
to_the_moon_long['status'] = 0


def binance_work(symbol, base_price, last_price,
                 j):  ###############################################################   binance_work
    # global short_balance
    global coins
    global balance_2
    # global balance
    global cursor
    global take_percent0
    global next_kline_status
    global to_the_moon
    global buy_data

    print("------------------------------------------------------------------------------------------------")
    log_time('Start binance(): ' + symbol)
    log_time('Start binance(): ' + str(base_price) + ", last_price: " + str(last_price), orlov_path + "log/" + symbol)
    sys.stdout.flush()
    # base_price = float(base_price)
    """
    balance_raw = bclient.futures_account_balance()
    log_time('balance_raw received')
    balance = ''
    for item in balance_raw:
        if item['asset'] == 'USDT':
            balance = item['balance']
            print ('Balance: ' + balance)
    sys.stdout.flush()        
    if not balance:
        print ('Error getting balance')
        sys.exit()
    balance = float(balance)
    """
    """
    orders = bclient.get_all_orders(symbol=symbol, limit=1)
    print (orders)
    sys.exit()
    """
    # провевка на наличие открытых ордеров
    try:
        if bclient_2.futures_get_open_orders(symbol=symbol):
            log_time(symbol + " has open orders. Rejected.")
            telega(messages=[symbol + " has open orders (" + str(last_price) + "). Rejected."],
                   conf="/etc/telegram-send.conf")
            time.sleep(3)
            return 0
        else:
            o = 1
    except:
        time.sleep(3)
        return 0

    try:
        bclient_2.futures_change_leverage(symbol=symbol, leverage=leverage)
    except:
        time.sleep(1)
        try:
            bclient_2.futures_change_leverage(symbol=symbol, leverage=leverage)

        except:
            print("futures_change_leverage error")
            sys.stdout.flush()
            time.sleep(60)
            #        coins.append(j)
            return 0
    """
    try:
        bclient_2.futures_change_margin_type(symbol=symbol, marginType='ISOLATED')
    except:
        o=0
    try:
        bclient.futures_change_margin_type(symbol=symbol, marginType='ISOLATED')
    except:
        o=0
    """

    ##log_time('futures_change_leverage received')
    # bclient_2.futures_change_margin_type(symbol=symbol, marginType='ISOLATED')

    # получение начальной цены для работы
    # orderbook = bclient.get_ticker(symbol=symbol)
    # time.sleep(1)
    old_min = datetime.now().minute
    """
    ##определение была ли цена близка к текущей за последние 15 минут
    klines = bclient_2.get_historical_klines(symbol, Client.KLINE_INTERVAL_1MINUTE, "40 min ago UTC", klines_type=HistoricalKlinesType.FUTURES)
    if not klines:
        log_time ("Kline 39 error")
        sys.stdout.flush()
        return 0
    ###orderbook = bclient_2.futures_orderbook_ticker(symbol=symbol)
   # print (orderbook)
   #sys.stdout.flush()
   # sys.exit()
    ##print("Price: "+ orderbook['askPrice'])
    ###last_price = float(orderbook['askPrice'])
    try:
        klines[39][4]
    except IndexError:
        print ("klines[39][4] error")
        sys.stdout.flush()
        return 2        
    last_price = float(klines[39][4])

    orderbook = bclient_2.futures_orderbook_ticker(symbol=symbol)
    last_price = float(orderbook['askPrice'])
    if not last_price:
        print ("last_price error")
        sys.stdout.flush()
        return 0
    """
    log_time('Base price: ' + str(base_price))
    # print ('Trigger percent: ' + str(trigger_percent))

    # last_price = float(last_price)
    # last_price = last_price + last_price/100*0.03
    print("Price: " + str(last_price))
    sys.stdout.flush()
    # вычисление триггера для отмены лонга
    long_trigger = 0
    """
    if base_price:
        tmp = base_price + base_price/100*trigger_percent
        if last_price > tmp:
            long_trigger = 1
    print ("Long trigger: " + str(long_trigger))
    """
    # вычисление точности
    precision_price = 0
    if last_price < 0.1:
        precision_price = 5
    elif last_price < 1:
        precision_price = 4
    elif last_price < 10:
        precision_price = 3
    elif last_price < 1000:
        precision_price = 2

        ##balance = 42
    ##balance_2 = 21
    # balance_n = balance / 9
    balance_2_n = balance_2 / delitel
    # вычисление объёма монет
    # amount = balance_n/last_price*leverage
    # amount_first = amount/100*65
    # amount_second = (amount - amount_first)/100*75

    amount_2 = balance_2_n / last_price * leverage
    # amount_2_first = amount_2/100*65
    # amount_2_second = (amount_2 - amount_2_first)/100*75
    # amount = balance_n
    # amount_2 = balance_2_n

    # определение необходимой точности
    """
    precision = 0
    if amount < 1:
        precision = 4
    amount = "{:0.0{}f}".format(amount, precision)
    print ("Amount: "+ str(amount))
    """
    """
    precision = 0
    if amount_first < 1:
        precision = 4
    amount_first = "{:0.0{}f}".format(amount_first, precision)
    print ("Amount_first: "+ str(amount_first))
    precision = 0
    if amount_second < 1:
        precision = 4
    amount_second = "{:0.0{}f}".format(amount_second, precision)
    print ("Amount_second: "+ str(amount_second))
    """
    precision = 0
    if amount_2 < 1:
        precision = 4
    amount_2 = "{:0.0{}f}".format(amount_2, precision)
    print("Amount_2: " + str(amount_2))
    """
    precision = 0
    if amount_2_first < 1:
        precision = 4
    amount_2_first = "{:0.0{}f}".format(amount_2_first, precision)
    print ("Amount_2_first: "+ str(amount_2_first))
    precision = 0
    if amount_2_second < 1:
        precision = 4
    amount_2_second = "{:0.0{}f}".format(amount_2_second, precision)
    print ("Amount_2_second: "+ str(amount_2_second))
    """
    # sys.stdout.flush()
    # sys.exit()
    num = 0
    if balance_2:
        stop_price = last_price + last_price / 100 * stop_percent
        stop_price_0 = stop_price
        # if stop_price > 1:
        # if stop_price < 1:
        #    precision = 4
        max_time = 5
        # установка стоп-ордера
        time_start = time.time()
        time_end = time_start + max_time / 2
        tmp_price = last_price
        old_price = last_price
        flag_return = 0
        f_price = last_price - last_price / 100 * 0.4
        for coin_true in coins_true:
            if coin_true == j and 1:
                flag_return = 1
        # if not flag_return:
        # f_price = last_price-last_price/100*0.4
        # l_price = last_price+last_price/100*(100/leverage*(100-leverage)*1.1)
        # telega(messages=["Trigger: "+j+" ("+str(last_price)+"), limit: "+str(f_price)], conf="/etc/telegram-send.conf")
        """
        while not flag_return and time_start < time_end and 0:# or old_price <= tmp_price:
            # получение цены монеты сразу после покупки
            orderbook = bclient_2.futures_orderbook_ticker(symbol=symbol)
            old_price = tmp_price
            tmp_price = orderbook['askPrice']
            log_time('TMP price ('+symbol+'): ' + str(tmp_price), orlov_path+"log/"+symbol)

            tmp_price = float(tmp_price)
            tmp_stop_price = tmp_price - tmp_price/100*0.2
            if tmp_stop_price > stop_price_0:
                stop_price = tmp_stop_price
                #stop_price_0 = tmp_stop_price
                log_time('STOP price (sleep 2): ' + str(stop_price), orlov_path+"log/"+symbol)

            time.sleep(0.2)
            time_start = time.time()
        """
        log_time(j + '===========================================================', orlov_path + "log/" + symbol)
        # print('===========================================================')
        # sys.stdout.flush()
        """
        num = get_order_num(db, symbol)     
        if num > 4:
            telega(messages=["Num > 4. Rejected 1.("+symbol+")"], conf="/etc/telegram-send.conf")
            sys.stdout.flush()
            time.sleep(1)
            return 1
        """
        # покупка по рынку
        # print("base_price: "+str(base_price))
        log_time('Buy start')

        # sys.exit()
        long = 1
        my = 0  ###
        nomy = 0
        tmp_15 = 0
        tmp_30 = 0
        if (1):  ####
            """
            now_min = datetime.now().minute
            jm = 39
            im = 34
            if old_min != now_min:
                jm = 38
                im = 33
            kline_in = float(klines[jm][1])
            check_kline_perc = (float(klines[jm][4])-kline_in)/kline_in*100
            """
            """
            check_kline_perc = (last_price-base_price)/base_price*100
            min_check_perc = percent - 0.25
            if check_kline_perc < min_check_perc and not next_kline_status:
                log_time ("Rejected: short kline " + str(check_kline_perc))
                sys.stdout.flush()
                telega(messages=["Rejected: "+symbol+" short kline " + str(check_kline_perc)], conf="/etc/telegram-send.conf")
                time.sleep(10)
                return 0
            """
            # telega(messages=["Trigger: "+j+" ("+str(last_price)+"), limit: "+str(f_price)], conf="/etc/telegram-send.conf")
            # log_time('Buy start - telegram sent')
            """
            max_15_price = 0 #25 первых свечей
            max_30_price = 0 #все свечи возле последней
            z = 0
            for kline in klines:
                kline_max = float(kline[2])
                if z < im:
                    if kline_max > max_15_price:
                        max_15_price = kline_max
                if z < jm and z > im:
                    if kline_max > max_30_price:
                        max_30_price = kline_max
                z = z + 1
            print ('15: '+str(max_15_price)+'/'+str(last_price))
            tmp_15 = (1-max_15_price/last_price)*100
            log_time("Tmp 15 percent : "+str(tmp_15))
            tmp_30 = (1-max_30_price/last_price)*100
            log_time("Tmp 30 percent : "+str(tmp_30))
            if tmp_30 < 0.2:
                print (symbol+ " tmp_30 reject (40 sec)")
                sys.stdout.flush()
                time.sleep(60)
                return 0                
            """

            """
            try:
                orderbook = bclient_2.futures_orderbook_ticker(symbol=symbol)
            except:
                print ("Error futures_orderbook_ticker after 'tmp_30 reject (40 sec)'")
                sys.stdout.flush()
                return 0
            """
            # tmp_price_start = float(orderbook['askPrice'])
            tmp_price_start = last_price
            # time.sleep(10)
            # orderbook = bclient_2.futures_orderbook_ticker(symbol=symbol)
            # tmp_price_now = float(orderbook['askPrice'])
            # perc_price = tmp_price_start - tmp_price_start/100*0.2

            ###            if tmp_price_now >= perc_price:
            ####            if 1:
            try:
                ###order_2 = buy(symbol, amount_2)  ###################################################### BUYING
                order_2 = 1
                if order_2:
                    my = my + 1
                    num = num + 1
                else:
                    g = 0
                    print(symbol + " buying error")
                    sys.stdout.flush()
                    time.sleep(60)
                    return 0
            except:
                ####            else:
                log_time("Order rejected by 10 sec")
                telega(messages=["Order rejected by 10 sec"], conf="/etc/telegram-send.conf")
                sys.stdout.flush()
                # time.sleep(60)
                return 1

        # log_time('Buy end')
        # попытка докупить по более высокой цене

        time_start = int(time.time() * 1000.0)
        time_start0 = time_start

        time_end = time_start + time_wait_buy * 1000
        buy_flag = 0
        """
        time.sleep(0.5)
        info = bclient_2.futures_position_information(symbol=symbol)          
        last_price = None
        for inf in info:
            last_price = inf['entryPrice'] 
        float_last_price = float(last_price)
        """
        float_last_price = last_price  ###
        tmp_price_plus1 = float_last_price + float_last_price / 100 * min_perc  # Процент дополнительного роста для срабатывания второй покупки
        tmp_price_plus2 = float_last_price + float_last_price / 100 * max_perc  # Процент дополнительного роста для срабатывания второй увеличенной покупки
        tmp_price_minus1 = tmp_price_start - tmp_price_start / 100 * min_perc
        tmp_price_minus_minus = tmp_price_start - tmp_price_start / 100 * (min_perc + zazor + 0.15)
        additional_flag = 0
        plus = min_perc
        tmp_price_plus = tmp_price_plus1
        tmp_price_now = None

        flag_buy = 0
        log_time("Start waiting...")
        while time_start < time_end and 1:
            orderbook = bclient_2.futures_orderbook_ticker(symbol=symbol)
            tmp_price_now = float(orderbook['askPrice'])
            # log_time (">>tmp_price_now: " + orderbook['askPrice'])
            time_test = int(time.time() * 1000.0)

            tmp_time_5 = time_test - time_start0
            """
            if tmp_price_now >= tmp_price_plus1 and tmp_time_5 < 3 and plus == min_perc:
                ###time_end = time_end + 3
                tmp_price_plus = tmp_price_plus2
                plus = max_perc
                log_time("PLUS: "+str(plus))
                sys.stdout.flush()
                continue  
            elif tmp_price_now >= tmp_price_plus:
            """
            plus_time = 0
            if to_the_moon['status']:
                plus_time = to_the_moon['status'] * 1000
            if tmp_price_now > tmp_price_plus2:
                if to_the_moon['status'] >= moon_overload:
                    print(symbol + " to the moon overload")
                    telega(messages=[symbol + " to the moon overload"], conf="/etc/telegram-send.conf")
                    next_kline_status = 0
                    sys.stdout.flush()
                    time.sleep(30)
                    return 0
                ##take_percent0 = take_percent0 + take_percent0_main*max_perc
                print(symbol + " to the moon")
                telega(messages=[symbol + " to the moon"], conf="/etc/telegram-send.conf")
                next_kline_status = time_test
                to_the_moon['status'] = to_the_moon['status'] + 1
                to_the_moon['symbol'] = symbol
                to_the_moon['price'] = tmp_price_now + tmp_price_now / 100 * 0.1
                to_the_moon['lowPrice'] = tmp_price_start
                log_time(symbol + " to the moon. Return 2.")
                sys.stdout.flush()
                # time.sleep(0.1)
                return 2
            elif tmp_price_now <= tmp_price_minus1 and tmp_price_now > tmp_price_minus_minus and tmp_time_5 > 3500 + plus_time:
                ##zazor_price = (tmp_price_minus1 - tmp_price_now)/tmp_price_minus1*100
                ##if zazor_price < zazor:
                flag_buy = 1
                break
            # time.sleep(0.1)
            time_start = int(time.time() * 1000.0)
        if not to_the_moon['status']:
            log_time(symbol + " no tothemoon. Rejected.")
            telega(messages=[symbol + " no tothemoon. Rejected."], conf="/etc/telegram-send.conf")
            sys.stdout.flush()
            time.sleep(30)
            return 0
        if not flag_buy:
            log_time(symbol + " waiting more then max. Rejected.")
            telega(messages=[symbol + " waiting was END. Rejected."], conf="/etc/telegram-send.conf")
            next_kline_status = 0
            sys.stdout.flush()
            time.sleep(30)
            return 0
        log_time(symbol + " waiting was END")
        """
            if tmp_price_now > tmp_price_plus1 and tmp_time_5 < 2000 and 0:
                print (symbol+ " to the moon 2")
                telega(messages=["To the moon 2"], conf="/etc/telegram-send.conf")
                #next_kline_status = time_test
                sys.stdout.flush()
                time.sleep(20)
                return 0

            elif tmp_price_now >= tmp_price_plus:                
                if num > 4:
                    telega(messages=["Num > 4. Rejected 2."], conf="/etc/telegram-send.conf")
                    sys.stdout.flush()
                    time.sleep(1)
                    return 1
                order_2 = buy(symbol, amount_2)  ###################################################### BUYING+
                if not order_2:
                    print (symbol+ " buying PLUS error !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                    sys.stdout.flush()
                    time.sleep(60)
                    return 0
                num = num + 1
                buy_flag = 1
                print (">>> Additional buy: OK")
                additional_flag = 1
                telega(messages=["Additional buy: "+str(plus)+"%"], conf="/etc/telegram-send.conf")
                break
        """
        tmp_price_now = float(orderbook['askPrice'])
        tmp_zazor = zazor
        if to_the_moon['status']:
            tmp_zazor = zazor + 0.1
        perc_price = tmp_price_start - tmp_price_start / 100 * (min_perc + tmp_zazor)
        bp_flag = 0
        if tmp_price_now >= perc_price and tmp_price_now < tmp_price_plus2:

            if not to_the_moon['status'] and 0:
                print(symbol + " no to the moon. Rejected : Start: " + str(tmp_price_start) + ", Now: " + str(
                    tmp_price_now) + ", MAX: " + str(tmp_price_plus2))
                sys.stdout.flush()
                telega(messages=[symbol + " no to the moon. Rejected : " + str(tmp_price_now)],
                       conf="/etc/telegram-send.conf")
                bad_buy['symbol'] = symbol
                bad_buy['price'] = tmp_price_start
                bad_buy['timestamp'] = time.time()
                time.sleep(3)
                return 4

            order_2 = buy(symbol, amount_2)  ###################################################### BUYING
            if not order_2:
                print(symbol + " buying error !!!")
                telega(messages=[symbol + " buying error"], conf="/etc/telegram-send.conf")
                sys.stdout.flush()
                time.sleep(60)
                return 0

            ff0 = (last_price - base_price) / base_price * 100
            ff0 = "{:0.0{}f}".format(ff0, 2)
            ff = (tmp_price_now - base_price) / base_price * 100
            ff = "{:0.0{}f}".format(ff, 2)
            l_t = tmp_price_now - tmp_price_now / 100 * take_percent0
            telega(messages=["Buy price " + symbol + ": " + str(tmp_price_now) + ", limit: " + str(
                l_t) + ", percent trigger: " + ff0 + "%" + ", percent buy: " + ff + "%"],
                   conf="/etc/telegram-send.conf")
        elif tmp_price_now < tmp_price_plus2:
            print(symbol + " bad buy price: Start: " + str(tmp_price_start) + ", Now: " + str(
                tmp_price_now) + ", MAX: " + str(tmp_price_plus2))
            sys.stdout.flush()
            bp_flag = 1

            order_2 = buy(symbol, amount_2)  ###################################################### BUYING
            if not order_2:
                print(symbol + " buying bad error !!!")
                telega(messages=[symbol + " buying bad error"], conf="/etc/telegram-send.conf")
                sys.stdout.flush()
                time.sleep(60)
                return 0

            ff0 = (last_price - base_price) / base_price * 100
            ff0 = "{:0.0{}f}".format(ff0, 2)
            ff = (tmp_price_now - base_price) / base_price * 100
            ff = "{:0.0{}f}".format(ff, 2)
            l_t = tmp_price_now - tmp_price_now / 100 * take_percent0
            telega(messages=["Buy (bad) price " + symbol + ": " + str(tmp_price_now) + ", limit: " + str(
                l_t) + ", percent trigger: " + ff0 + "%" + ", percent buy: " + ff + "%"],
                   conf="/etc/telegram-send.conf")

        else:
            print(symbol + " bad OVERLOAD buy price: Start: " + str(tmp_price_start) + ", Now: " + str(
                tmp_price_now) + ", MAX: " + str(tmp_price_plus2))
            sys.stdout.flush()
            telega(messages=[symbol + " bad OVERLOAD buy price: Start: " + str(tmp_price_start) + ", Now: " + str(
                tmp_price_now) + ", MAX: " + str(tmp_price_plus2)], conf="/etc/telegram-send.conf")
            bad_buy['symbol'] = symbol
            bad_buy['price'] = tmp_price_start
            bad_buy['timestamp'] = time.time()
            time.sleep(3)
            return 4
        """
        if not additional_flag and tmp_price_now >= tmp_price_plus1:
            if num > 4:
                telega(messages=["Num > 4. Rejected 3."], conf="/etc/telegram-send.conf")
                sys.stdout.flush()
                time.sleep(1)
                return 1
            order_2 = buy(symbol, amount_2)  ###################################################### BUYING+
            if not order_2:
                print (symbol+ " buying PLUS error 2 !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                sys.stdout.flush()
                time.sleep(60)
                return 0
            num = num + 1
            buy_flag = 1
            print (">>> Additional buy (last): OK")
            additional_flag = 1
            telega(messages=["Additional buy (last): "], conf="/etc/telegram-send.conf")
        """

        # получение цены монеты сразу после покупки
        # orderbook = bclient_2.futures_orderbook_ticker(symbol=symbol)
        # if not buy_flag:
        info = bclient_2.futures_position_information(symbol=symbol)
        # print ("+++")
        # print (info)
        # print ("+++")
        sys.stdout.flush()
        last_amount = None
        last_price = None
        for inf in info:
            last_price_str = inf['entryPrice']
            last_amount = inf['positionAmt']
        if last_amount[0] == '-':
            amount_2 = last_amount[1:]
        else:
            amount_2 = last_amount
        log_time('Real price (after buy): ' + last_price_str + '; real amount: ' + amount_2)
        last_price = float(last_price_str)
        buy_data['price'] = last_price

        if last_price < tmp_price_now:
            perc_last_price = (last_price - tmp_price_now) / last_price * 100
            tmp_take_percent = take_percent0 - perc_last_price
            if tmp_take_percent < take_percent0_small:
                take_percent0 = take_percent0_small
            ###else:
            ###    take_percent0 = tmp_take_percent
        if bp_flag or not to_the_moon['status']:
            take_percent0 = take_percent0_small
        if bp_flag and buy_data['stopPrice']:
            take_percent0 = take_percent0_max

    def short(price, amount_2):
        # print ("Long amount: " + amount)
        print("Short order price: " + price)
        bclient_2.futures_create_order(
            symbol=symbol,
            type='LIMIT',
            timeInForce='GTC',
            price=price,  # The price at which you wish to buy/sell, float
            side='SELL',  # Direction ('BUY' / 'SELL'), string
            quantity=amount_2  # Number of coins you wish to buy / sell, float
        )
        """
        bclient.futures_create_order (
            symbol=symbol, 
            type='LIMIT', 
            timeInForce='GTC',
            price=price,  # The price at which you wish to buy/sell, float
            side='SELL',  # Direction ('BUY' / 'SELL'), string
            quantity=amount  # Number of coins you wish to buy / sell, float
        ) 
        """

    def stop_loss(stopPrice, amount):
        print("Stop order: " + stopPrice)
        try:
            return bclient_2.futures_create_order(
                symbol=symbol,
                side='BUY',
                type='STOP_MARKET',
                timeInForce='GTC',
                stopPrice=stopPrice,
                quantity=amount,
                closePosition=True
            )
        except:
            return 0

    def take_buy(price, amount_2, type):
        if float(amount_2):
            # try:
            #    bclient_2.futures_cancel_all_open_orders(symbol=symbol)
            # except:
            #    o=0
            try:
                return bclient_2.futures_create_order(
                    symbol=symbol,
                    type='LIMIT',
                    timeInForce='GTC',
                    price=price,  # The price at which you wish to buy/sell, float
                    side='BUY',  # Direction ('BUY' / 'SELL'), string
                    quantity=amount_2,  # Number of coins you wish to buy / sell, float
                    reduceOnly=type
                )
            except:
                return 0
        """
        if float(amount):
            bclient.futures_create_order (
                symbol=symbol, 
                type='LIMIT', 
                timeInForce='GTC',
                price=price,  # The price at which you wish to buy/sell, float
                side='BUY',  # Direction ('BUY' / 'SELL'), string
                quantity=amount,  # Number of coins you wish to buy / sell, float
                reduceOnly=type
            )  
        """
        return 0

    stop_percent_n = stop_percent
    if to_the_moon['status'] > 2:
        stop_percent_n = stop_percent + 0.033
    stopPrice = last_price + last_price / 100 * stop_percent_n  ############### STOP ORDER
    precision_price_real = len(last_price_str.split(".")[1])
    tmp_precision_price = precision_price_real
    if precision_price_real > precision_price:
        tmp_precision_price = precision_price
    stopPrice_str = "{:0.0{}f}".format(stopPrice, tmp_precision_price)
    if buy_data['symbol'] == symbol or buy_data['symbol'] == '':
        buy_data['count'] = buy_data['count'] + 1

    buy_data['stopPrice'] = stopPrice + stopPrice / 100 * 0.5
    buy_data['timestamp'] = time.time()
    buy_data['symbol'] = symbol
    if not stop_loss(stopPrice_str, amount_2):
        bclient_2.futures_create_order(
            symbol=symbol,
            side='BUY',
            type='MARKET',
            quantity=amount_2,
            reduceOnly='true'
        )
        log_time("stop_loss error")
        telega(messages=["stop_loss error"], conf="/etc/telegram-send.conf")
        sys.stdout.flush()
        # time.sleep(60)
        time.sleep(0.2)
        return 3
    # else:
    #    buy_data['stopPrice'] = stopPrice + stopPrice/100*0.05

    if not long_trigger and balance_2 and my:
        # amount = float(amount)
        amount1_2 = float(amount_2)
        # установка сетки ордеров
        ### 1
        # amount1 = amount#/100*take_percent_summ1
        # amount1_2 = amount_2#/100*take_percent_summ1
        # tmp_amount = amount1
        """
        precision = 0
        if amount1 < 1:
            precision = 4
        amount1 = "{:0.0{}f}".format(amount1, precision)
        print ("Amount1: "+ str(amount1)) 
        tmp_amount_2 = amount1_2
        """
        precision = 0
        if amount1_2 < 1:
            precision = 4
        amount1_2 = "{:0.0{}f}".format(amount1_2, precision)
        print("Amount1_2: " + str(amount1_2))
        # вычисление цены для тейка
        take_percent_tmp = take_percent0
        if to_the_moon['status'] > 2:
            take_percent_tmp = take_percent0_max
        """
        if not additional_flag:
            take_percent_tmp = take_percent0_max
        """
        take_price1 = last_price - last_price / 100 * take_percent_tmp
        take_price1 = "{:0.0{}f}".format(take_price1, tmp_precision_price)
        binance_percent = (last_price - base_price) / base_price * 100
        ffb = "{:0.0{}f}".format(binance_percent, 2)
        log_time('Take price1: ' + take_price1)
        ffp = "{:0.0{}f}".format(take_percent_tmp, 2)
        telega(messages=[ffp + '%, kline: ' + ffb + '%'], conf="/etc/telegram-send.conf")

        # sys.stdout.flush()
        # time.sleep(1)
        # return 1

        sys.stdout.flush()
        # установка тейк-профита
        ord = take_buy(take_price1, amount1_2, take_type)
        if not ord:
            log_time("Take_buy error. Return 2.")
            sys.stdout.flush()
            time.sleep(35)
            return 2
        try:
            set_limit_order(ord, num)
        except:
            bclient_2.futures_create_order(
                symbol=symbol,
                side='BUY',
                type='MARKET',
                quantity=amount_2,
                reduceOnly='true'
            )
            log_time("Mysql error. Exit.")
            telega(messages=["Mysql error. Exit."], conf="/etc/telegram-send.conf")
            sys.exit()

        log_time('take1 end')
    # time.sleep(60)
    info = bclient_2.futures_position_information(symbol=symbol)
    # liq_price = None
    # for inf in info:
    #    liq_price = inf['liquidationPrice']
    telega(messages=["New position: " + j + " (Pos: " + str(last_price) + ", Limit: " + str(
        take_price1) + ", Stop:" + stopPrice_str + ")"], conf="/etc/telegram-send.conf")
    print("---------------------------------------------------OK")
    # time.sleep(0.5)
    return 3


def binance_work_long(symbol, base_price, last_price,
                      j):  ###############################################################   binance_work_LONG
    # global short_balance
    global coins
    global balance_2
    # global balance
    global cursor
    global take_percent0_long
    # global next_kline_status
    global to_the_moon_long
    global buy_data_long
    global bad_buy_long

    print("--LONG----------------------------------------------------------------------------------------------")
    log_time('Start binance() LONG: ' + symbol)
    log_time('Start binance() LONG: ' + str(base_price) + ", last_price: " + str(last_price),
             orlov_path + "log/" + symbol)
    sys.stdout.flush()
    # base_price = float(base_price)
    """
    balance_raw = bclient.futures_account_balance()
    log_time('balance_raw received')
    balance = ''
    for item in balance_raw:
        if item['asset'] == 'USDT':
            balance = item['balance']
            print ('Balance: ' + balance)
    sys.stdout.flush()        
    if not balance:
        print ('Error getting balance')
        sys.exit()
    balance = float(balance)
    """
    """
    orders = bclient.get_all_orders(symbol=symbol, limit=1)
    print (orders)
    sys.exit()
    """
    # провевка на наличие открытых ордеров
    try:
        if bclient_2.futures_get_open_orders(symbol=symbol):
            log_time(symbol + " has open orders. Long rejected.")
            telega(messages=[symbol + " has open orders (" + str(last_price) + "). Long rejected."],
                   conf="/etc/telegram-send.conf")
            time.sleep(3)
            return 0
        else:
            o = 1
    except:
        time.sleep(3)
        return 0

    try:
        bclient_2.futures_change_leverage(symbol=symbol, leverage=leverage)
    except:
        time.sleep(1)
        try:
            bclient_2.futures_change_leverage(symbol=symbol, leverage=leverage)

        except:
            print("futures_change_leverage error")
            sys.stdout.flush()
            time.sleep(60)
            #        coins.append(j)
            return 0
    """
    try:
        bclient_2.futures_change_margin_type(symbol=symbol, marginType='ISOLATED')
    except:
        o=0
    try:
        bclient.futures_change_margin_type(symbol=symbol, marginType='ISOLATED')
    except:
        o=0
    """

    ##log_time('futures_change_leverage received')
    # bclient_2.futures_change_margin_type(symbol=symbol, marginType='ISOLATED')

    # получение начальной цены для работы
    # orderbook = bclient.get_ticker(symbol=symbol)
    # time.sleep(1)
    # old_min = datetime.now().minute
    """
    ##определение была ли цена близка к текущей за последние 15 минут
    klines = bclient_2.get_historical_klines(symbol, Client.KLINE_INTERVAL_1MINUTE, "40 min ago UTC", klines_type=HistoricalKlinesType.FUTURES)
    if not klines:
        log_time ("Kline 39 error")
        sys.stdout.flush()
        return 0
    ###orderbook = bclient_2.futures_orderbook_ticker(symbol=symbol)
   # print (orderbook)
   #sys.stdout.flush()
   # sys.exit()
    ##print("Price: "+ orderbook['askPrice'])
    ###last_price = float(orderbook['askPrice'])
    try:
        klines[39][4]
    except IndexError:
        print ("klines[39][4] error")
        sys.stdout.flush()
        return 2        
    last_price = float(klines[39][4])

    orderbook = bclient_2.futures_orderbook_ticker(symbol=symbol)
    last_price = float(orderbook['askPrice'])
    if not last_price:
        print ("last_price error")
        sys.stdout.flush()
        return 0
    """
    log_time('Base price LONG: ' + str(base_price))
    # print ('Trigger percent: ' + str(trigger_percent))

    # last_price = float(last_price)
    # last_price = last_price + last_price/100*0.03
    print("Price LONG: " + str(last_price))
    sys.stdout.flush()
    # вычисление триггера для отмены лонга
    long_trigger = 0
    """
    if base_price:
        tmp = base_price + base_price/100*trigger_percent
        if last_price > tmp:
            long_trigger = 1
    print ("Long trigger: " + str(long_trigger))
    """
    # вычисление точности
    precision_price = 0
    if last_price < 0.1:
        precision_price = 5
    elif last_price < 1:
        precision_price = 4
    elif last_price < 10:
        precision_price = 3
    elif last_price < 1000:
        precision_price = 2

    balance_2_n = balance_2 / 15.2
    ##balance_2_n = balance_2 / delitel

    # вычисление объёма монет
    amount_2 = balance_2_n / last_price * leverage

    # определение необходимой точности
    precision = 0
    if amount_2 < 1:
        precision = 4
    amount_2 = "{:0.0{}f}".format(amount_2, precision)
    print("Amount_2: " + str(amount_2))

    # sys.stdout.flush()
    # sys.exit()
    num = 0
    if balance_2:
        ##stop_price = last_price + last_price/100*stop_percent
        ##stop_price_0 = stop_price
        # if stop_price > 1:
        # if stop_price < 1:
        #    precision = 4
        ##max_time = 5
        # установка стоп-ордера
        """
        time_start = time.time()
        time_end = time_start + max_time/2
        tmp_price = last_price
        old_price = last_price
        flag_return = 0
        f_price = last_price-last_price/100*0.4
        for coin_true in coins_true:
            if coin_true == j and 1:
                flag_return = 1
        #if not flag_return:
            #f_price = last_price-last_price/100*0.4
            #l_price = last_price+last_price/100*(100/leverage*(100-leverage)*1.1)
            #telega(messages=["Trigger: "+j+" ("+str(last_price)+"), limit: "+str(f_price)], conf="/etc/telegram-send.conf")
        """
        """
        while not flag_return and time_start < time_end and 0:# or old_price <= tmp_price:
            # получение цены монеты сразу после покупки
            orderbook = bclient_2.futures_orderbook_ticker(symbol=symbol)
            old_price = tmp_price
            tmp_price = orderbook['askPrice']
            log_time('TMP price ('+symbol+'): ' + str(tmp_price), orlov_path+"log/"+symbol)

            tmp_price = float(tmp_price)
            tmp_stop_price = tmp_price - tmp_price/100*0.2
            if tmp_stop_price > stop_price_0:
                stop_price = tmp_stop_price
                #stop_price_0 = tmp_stop_price
                log_time('STOP price (sleep 2): ' + str(stop_price), orlov_path+"log/"+symbol)

            time.sleep(0.2)
            time_start = time.time()
        """
        log_time(j + '==LONG=========================================================', orlov_path + "log/" + symbol)
        # print('===========================================================')
        # sys.stdout.flush()
        """
        num = get_order_num(db, symbol)     
        if num > 4:
            telega(messages=["Num > 4. Rejected 1.("+symbol+")"], conf="/etc/telegram-send.conf")
            sys.stdout.flush()
            time.sleep(1)
            return 1
        """
        # покупка по рынку
        # print("base_price: "+str(base_price))
        log_time('Buy start LONG')

        # sys.exit()
        # long = 1
        # my = 0 ###
        # nomy = 0
        # tmp_15 = 0
        # tmp_30 = 0
        if (1):  ####
            """
            now_min = datetime.now().minute
            jm = 39
            im = 34
            if old_min != now_min:
                jm = 38
                im = 33
            kline_in = float(klines[jm][1])
            check_kline_perc = (float(klines[jm][4])-kline_in)/kline_in*100
            """
            """
            check_kline_perc = (last_price-base_price)/base_price*100
            min_check_perc = percent - 0.25
            if check_kline_perc < min_check_perc and not next_kline_status:
                log_time ("Rejected: short kline " + str(check_kline_perc))
                sys.stdout.flush()
                telega(messages=["Rejected: "+symbol+" short kline " + str(check_kline_perc)], conf="/etc/telegram-send.conf")
                time.sleep(10)
                return 0
            """
            # telega(messages=["Trigger: "+j+" ("+str(last_price)+"), limit: "+str(f_price)], conf="/etc/telegram-send.conf")
            # log_time('Buy start - telegram sent')
            """
            max_15_price = 0 #25 первых свечей
            max_30_price = 0 #все свечи возле последней
            z = 0
            for kline in klines:
                kline_max = float(kline[2])
                if z < im:
                    if kline_max > max_15_price:
                        max_15_price = kline_max
                if z < jm and z > im:
                    if kline_max > max_30_price:
                        max_30_price = kline_max
                z = z + 1
            print ('15: '+str(max_15_price)+'/'+str(last_price))
            tmp_15 = (1-max_15_price/last_price)*100
            log_time("Tmp 15 percent : "+str(tmp_15))
            tmp_30 = (1-max_30_price/last_price)*100
            log_time("Tmp 30 percent : "+str(tmp_30))
            if tmp_30 < 0.2:
                print (symbol+ " tmp_30 reject (40 sec)")
                sys.stdout.flush()
                time.sleep(60)
                return 0                
            """

            """
            try:
                orderbook = bclient_2.futures_orderbook_ticker(symbol=symbol)
            except:
                print ("Error futures_orderbook_ticker after 'tmp_30 reject (40 sec)'")
                sys.stdout.flush()
                return 0
            """
            # tmp_price_start = float(orderbook['askPrice'])

            tmp_price_start = last_price

            # time.sleep(10)
            # orderbook = bclient_2.futures_orderbook_ticker(symbol=symbol)
            # tmp_price_now = float(orderbook['askPrice'])
            # perc_price = tmp_price_start - tmp_price_start/100*0.2

            ###            if tmp_price_now >= perc_price:
            ####            if 1:
            try:
                g = 0
                # order_2 = buy_long(symbol, amount_2)  ###################################################### BUYING
                order_2 = ""
                if not order_2 and g:
                    print(symbol + " LONG buying error")
                    sys.stdout.flush()
                    time.sleep(60)
                    return 0
            except:
                ####            else:
                log_time("LONG order rejected by 10 sec")
                telega(messages=["LONG order rejected by 10 sec"], conf="/etc/telegram-send.conf")
                sys.stdout.flush()
                # time.sleep(60)
                return 0

        # log_time('Buy end')
        # попытка докупить по более высокой цене

        time_start = int(time.time() * 1000.0)
        time_start0 = time_start

        time_end = time_start + time_wait_buy * 1000
        buy_flag = 0
        float_last_price = last_price  ###
        tmp_price_plus1 = float_last_price - float_last_price / 100 * min_perc_long  # Процент дополнительного роста для срабатывания второй покупки
        tmp_price_plus2 = float_last_price - float_last_price / 100 * max_perc_long  # Процент дополнительного роста для срабатывания второй увеличенной покупки
        tmp_price_minus1 = tmp_price_start + tmp_price_start / 100 * min_perc_long
        tmp_price_minus_minus = tmp_price_start + tmp_price_start / 100 * (min_perc_long + zazor_long)
        additional_flag = 0
        plus = min_perc_long
        tmp_price_plus = tmp_price_plus1
        tmp_price_now = None

        flag_buy = 0
        log_time("Start waiting LONG...")
        while time_start < time_end and 1:
            orderbook = bclient_2.futures_orderbook_ticker(symbol=symbol)
            tmp_price_now = float(orderbook['askPrice'])
            # log_time (">>tmp_price_now: " + orderbook['askPrice'])
            time_test = int(time.time() * 1000.0)

            tmp_time_5 = time_test - time_start0
            plus_time = 0
            if to_the_moon_long['status']:
                plus_time = to_the_moon_long['status'] * 1000
            if tmp_price_now < tmp_price_plus2:
                if to_the_moon_long['status'] >= moon_overload_long:
                    print(symbol + " to the moon LONG overload")
                    telega(messages=[symbol + " to the moon LONG overload"], conf="/etc/telegram-send.conf")
                    next_kline_status = 0
                    sys.stdout.flush()
                    time.sleep(30)
                    return 0
                ##take_percent0 = take_percent0 + take_percent0_main*max_perc
                print(symbol + " to the moon LONG")
                telega(messages=[symbol + " to the moon LONG"], conf="/etc/telegram-send.conf")
                next_kline_status = time_test
                to_the_moon_long['status'] = to_the_moon_long['status'] + 1
                to_the_moon_long['symbol'] = symbol
                to_the_moon_long['price'] = tmp_price_now  # + tmp_price_now/100*0.2
                to_the_moon_long['lowPrice'] = tmp_price_start
                log_time(symbol + " to the moon LONG. Return 2.")
                sys.stdout.flush()
                # time.sleep(0.1)
                return 2
            elif tmp_price_now >= tmp_price_minus1 and tmp_price_now < tmp_price_minus_minus and tmp_time_5 > 3500 + plus_time:
                ##zazor_price = (tmp_price_minus1 - tmp_price_now)/tmp_price_minus1*100
                ##if zazor_price < zazor:
                flag_buy = 1
                break
            # time.sleep(0.1)
            time_start = int(time.time() * 1000.0)

        if not flag_buy:
            log_time(symbol + " waiting LONG more then max. Rejected.")
            telega(messages=[symbol + " waiting LONG was END"], conf="/etc/telegram-send.conf")
            next_kline_status = 0
            sys.stdout.flush()
            time.sleep(30)
            return 0
        log_time(symbol + " waiting LONG was END")
        """
            if tmp_price_now > tmp_price_plus1 and tmp_time_5 < 2000 and 0:
                print (symbol+ " to the moon 2")
                telega(messages=["To the moon 2"], conf="/etc/telegram-send.conf")
                #next_kline_status = time_test
                sys.stdout.flush()
                time.sleep(20)
                return 0

            elif tmp_price_now >= tmp_price_plus:                
                if num > 4:
                    telega(messages=["Num > 4. Rejected 2."], conf="/etc/telegram-send.conf")
                    sys.stdout.flush()
                    time.sleep(1)
                    return 1
                order_2 = buy(symbol, amount_2)  ###################################################### BUYING+
                if not order_2:
                    print (symbol+ " buying PLUS error !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                    sys.stdout.flush()
                    time.sleep(60)
                    return 0
                num = num + 1
                buy_flag = 1
                print (">>> Additional buy: OK")
                additional_flag = 1
                telega(messages=["Additional buy: "+str(plus)+"%"], conf="/etc/telegram-send.conf")
                break

        """
        # orderbook = bclient_2.futures_orderbook_ticker(symbol=symbol)
        tmp_price_now = float(orderbook['askPrice'])
        tmp_zazor = zazor_long
        if to_the_moon_long['status']:
            tmp_zazor = zazor_long + 0.1
        perc_price = tmp_price_start + tmp_price_start / 100 * (min_perc + tmp_zazor)
        bp_flag = 0
        if tmp_price_now <= perc_price and tmp_price_now < tmp_price_plus2:

            if not to_the_moon_long['status'] and 0:
                print(symbol + " no to the moon. Rejected : Start: " + str(tmp_price_start) + ", Now: " + str(
                    tmp_price_now) + ", MAX: " + str(tmp_price_plus2))
                sys.stdout.flush()
                telega(messages=[symbol + " no to the moon. Rejected : " + str(tmp_price_now)],
                       conf="/etc/telegram-send.conf")
                bad_buy['symbol'] = symbol
                bad_buy['price'] = tmp_price_start
                bad_buy['timestamp'] = time.time()
                time.sleep(3)
                return 4

            order_2 = buy_long(symbol, amount_2)  ###################################################### BUYING
            if not order_2:
                print(symbol + " buying LONG error !!!")
                telega(messages=[symbol + " buying LONG error"], conf="/etc/telegram-send.conf")
                sys.stdout.flush()
                time.sleep(60)
                return 0

            ff0 = (last_price - base_price) / base_price * 100
            ff0 = "{:0.0{}f}".format(ff0, 2)
            ff = (tmp_price_now - base_price) / base_price * 100
            ff = "{:0.0{}f}".format(ff, 2)
            l_t = tmp_price_now + tmp_price_now / 100 * take_percent0_long
            telega(messages=["Buy price LONG " + symbol + ": " + str(tmp_price_now) + ", limit: " + str(
                l_t) + ", percent trigger: " + ff0 + "%" + ", percent buy: " + ff + "%"],
                   conf="/etc/telegram-send.conf")
        elif tmp_price_now > tmp_price_plus2:
            print(symbol + " bad buy price LONG: Start: " + str(tmp_price_start) + ", Now: " + str(
                tmp_price_now) + ", MAX: " + str(tmp_price_plus2))
            sys.stdout.flush()
            bp_flag = 1

            order_2 = buy_long(symbol, amount_2)  ###################################################### BUYING
            if not order_2:
                print(symbol + " buying bad LONG error !!!")
                telega(messages=[symbol + " buying bad LONG error"], conf="/etc/telegram-send.conf")
                sys.stdout.flush()
                time.sleep(60)
                return 0

            ff0 = (last_price - base_price) / base_price * 100
            ff0 = "{:0.0{}f}".format(ff0, 2)
            ff = (tmp_price_now - base_price) / base_price * 100
            ff = "{:0.0{}f}".format(ff, 2)
            l_t = tmp_price_now + tmp_price_now / 100 * take_percent0_long
            telega(messages=["Buy (bad) LONG price " + symbol + ": " + str(tmp_price_now) + ", limit: " + str(
                l_t) + ", percent trigger: " + ff0 + "%" + ", percent buy: " + ff + "%"],
                   conf="/etc/telegram-send.conf")

        else:
            print(symbol + " bad OVERLOAD LONG buy price: Start: " + str(tmp_price_start) + ", Now: " + str(
                tmp_price_now) + ", MAX: " + str(tmp_price_plus2))
            sys.stdout.flush()
            telega(messages=[symbol + " bad OVERLOAD LONG buy price: Start: " + str(tmp_price_start) + ", Now: " + str(
                tmp_price_now) + ", MAX: " + str(tmp_price_plus2)], conf="/etc/telegram-send.conf")
            bad_buy_long['symbol'] = symbol
            bad_buy_long['price'] = tmp_price_start
            bad_buy_long['timestamp'] = time.time()
            time.sleep(3)
            return 4

        # получение цены монеты сразу после покупки
        # orderbook = bclient_2.futures_orderbook_ticker(symbol=symbol)
        # if not buy_flag:
        info = bclient_2.futures_position_information(symbol=symbol)
        # print ("+++")
        # print (info)
        # print ("+++")
        # sys.stdout.flush()
        last_amount = None
        last_price = None
        for inf in info:
            last_price = inf['entryPrice']
            last_amount = inf['positionAmt']
        if last_amount[0] == '-':
            amount_2 = last_amount[1:]
        else:
            amount_2 = last_amount
        log_time('Real price (after LONG buy): ' + last_price + '; real amount: ' + amount_2)
        try:
            new_precision = len(last_amount.rsplit('.')[1])
        except:
            new_precision = 0
        last_price = float(last_price)
        buy_data_long['price'] = last_price
        """
        if last_price < tmp_price_now:
            perc_last_price = (last_price - tmp_price_now)/last_price*100
            tmp_take_percent = take_percent0 - perc_last_price
            if tmp_take_percent < take_percent0_small:
                take_percent0 = take_percent0_small
            ###else:
            ###    take_percent0 = tmp_take_percent
        if bp_flag or not to_the_moon['status']:
            take_percent0 = take_percent0_small
        if bp_flag and buy_data['stopPrice']:
            take_percent0 = take_percent0_max
        """

    def short(price, amount_2):
        # print ("Long amount: " + amount)
        print("Short order price: " + price)
        bclient_2.futures_create_order(
            symbol=symbol,
            type='LIMIT',
            timeInForce='GTC',
            price=price,  # The price at which you wish to buy/sell, float
            side='SELL',  # Direction ('BUY' / 'SELL'), string
            quantity=amount_2  # Number of coins you wish to buy / sell, float
        )
        """
        bclient.futures_create_order (
            symbol=symbol, 
            type='LIMIT', 
            timeInForce='GTC',
            price=price,  # The price at which you wish to buy/sell, float
            side='SELL',  # Direction ('BUY' / 'SELL'), string
            quantity=amount  # Number of coins you wish to buy / sell, float
        ) 
        """

    def stop_loss_long(stopPrice, amount):
        print("Stop order LONG: " + stopPrice)
        try:
            return bclient_2.futures_create_order(
                symbol=symbol,
                side='SELL',
                type='STOP_MARKET',
                timeInForce='GTC',
                stopPrice=stopPrice,
                quantity=amount,
                closePosition=False
            )
        except:
            return 0

    def take_buy_long(price, amount_2, type):
        if float(amount_2):
            # try:
            #    bclient_2.futures_cancel_all_open_orders(symbol=symbol)
            # except:
            #    o=0
            try:
                return bclient_2.futures_create_order(
                    symbol=symbol,
                    type='LIMIT',
                    timeInForce='GTC',
                    price=price,  # The price at which you wish to buy/sell, float
                    side='SELL',  # Direction ('BUY' / 'SELL'), string
                    quantity=amount_2,  # Number of coins you wish to buy / sell, float
                    reduceOnly=type
                )
            except:
                return 0
        """
        if float(amount):
            bclient.futures_create_order (
                symbol=symbol, 
                type='LIMIT', 
                timeInForce='GTC',
                price=price,  # The price at which you wish to buy/sell, float
                side='BUY',  # Direction ('BUY' / 'SELL'), string
                quantity=amount,  # Number of coins you wish to buy / sell, float
                reduceOnly=type
            )  
        """
        return 0

    """    
    stop_percent_n = stop_percent
    if to_the_moon['status'] > 2:
        stop_percent_n = stop_percent+0.1
    """
    stopPrice = last_price - last_price / 100 * stop_percent_long  ############### STOP ORDER
    stopPrice_str = "{:0.0{}f}".format(stopPrice, new_precision)
    if buy_data_long['symbol'] == symbol or buy_data_long['symbol'] == '':
        buy_data_long['count'] = buy_data_long['count'] + 1

    buy_data_long['stopPrice'] = stopPrice + stopPrice / 100 * 0.5
    buy_data_long['timestamp'] = time.time()
    buy_data_long['symbol'] = symbol
    if not stop_loss_long(stopPrice_str, amount_2):
        bclient_2.futures_create_order(
            symbol=symbol,
            side='SELL',
            type='MARKET',
            quantity=amount_2,
            reduceOnly='true'
        )
        log_time("stop_loss LONG error")
        telega(messages=["stop_loss LONG error"], conf="/etc/telegram-send.conf")
        sys.stdout.flush()
        # time.sleep(60)
        time.sleep(0.2)
        return 3
    # else:
    #    buy_data['stopPrice'] = stopPrice + stopPrice/100*0.05

    if not long_trigger and balance_2:
        # amount = float(amount)
        amount1_2 = float(amount_2)
        # установка сетки ордеров
        ### 1
        # amount1 = amount#/100*take_percent_summ1
        # amount1_2 = amount_2#/100*take_percent_summ1
        # tmp_amount = amount1

        precision = 0
        if amount1_2 < 1:
            precision = 4
        amount1_2 = "{:0.0{}f}".format(amount1_2, precision)
        print("Amount1_2: " + str(amount1_2))
        # вычисление цены для тейка
        take_percent_tmp = take_percent0_long
        # if to_the_moon['status'] > 2:
        #    take_percent_tmp = take_percent0_max

        take_price1 = last_price + last_price / 100 * take_percent_tmp
        take_price1 = "{:0.0{}f}".format(take_price1, new_precision)
        binance_percent = (last_price - base_price) / base_price * 100
        ffb = "{:0.0{}f}".format(binance_percent, 2)
        log_time('Take price1: ' + take_price1)
        ffp = "{:0.0{}f}".format(take_percent_tmp, 2)
        telega(messages=[ffp + '%, kline: ' + ffb + '%'], conf="/etc/telegram-send.conf")

        # sys.stdout.flush()
        # time.sleep(1)
        # return 1

        sys.stdout.flush()
        # установка тейк-профита
        ord = take_buy_long(take_price1, amount1_2, take_type)
        if not ord:
            log_time("Take_buy LONG error. Return 0.")
            sys.stdout.flush()
            time.sleep(35)
            return 2
        try:
            set_limit_order(ord, num)
        except:
            bclient_2.futures_create_order(
                symbol=symbol,
                side='SELL',
                type='MARKET',
                quantity=amount_2,
                reduceOnly='true'
            )
            log_time("Mysql error (LONG). Exit.")
            telega(messages=["Mysql error (LONG). Exit."], conf="/etc/telegram-send.conf")
            sys.exit()

        log_time('take1 end')
    # time.sleep(60)
    info = bclient_2.futures_position_information(symbol=symbol)
    # liq_price = None
    # for inf in info:
    #    liq_price = inf['liquidationPrice']
    telega(messages=["New LONG position: " + j + " (Pos: " + str(last_price) + ", Limit: " + str(
        take_price1) + ", Stop:" + stopPrice_str + ")"], conf="/etc/telegram-send.conf")
    print("---------------------------------------------------OK")
    # time.sleep(0.5)
    return 3


def get_balance_from_file():
    # global balance
    global balance_2
    """
    f = open(orlov_path+'coins2/_balance', 'r+')
    str_balance = f.read()
    f.close()
    balance = float(str_balance)
    """
    f = open(orlov_path + 'coins2/_balance_2', 'r+')
    str_balance_2 = f.read()
    f.close()
    balance_2 = float(str_balance_2)


def set_balance_file():
    """
    f = open(orlov_path+'coins2/_balance', 'w+')
    f.write(str(balance))
    f.close()
    """
    f = open(orlov_path + 'coins2/_balance_2', 'w+')
    f.write(str(balance_2))
    f.close()


symbols = pd.DataFrame({'symbol': [], 'timestamp': [], 'price': []})

flag_symbol = ""
send_flag = 0


def binance():
    global coins
    # global balance
    global balance_2
    global coins_black
    global next_kline_status
    global symbols
    global take_percent0
    global take_percent0_long
    global to_the_moon
    global to_the_moon_long
    global buy_data
    global buy_data_long
    global flag_symbol
    global send_flag
    # log_time('S binance(): ' + symbol)
    # base_price = float(base_price)

    # получение начальной цен
    prices = None
    try:
        prices = bclient_2.futures_orderbook_ticker()
    except:
        log_time("Getting prices error")
        sys.stdout.flush()
        time.sleep(5)
        return 0
    # print (prices)
    # sys.stdout.flush()
    #    sys.exit()
    """
    BTC_price = 0
    for b in prices:
        tmp = b.get('symbol')
        ""
        time_coin = b.get('time')
        timestamp = time.time()
        t = timestamp - time_coin/1000
        print (t)
        sys.exit()
        ""
        if tmp == "BTCUSDT":
            BTC_price = float(b.get('askPrice'))
            break
    if not BTC_price:
        log_time("Error getting BTC price")
        sys.stdout.flush()
        time.sleep(1)
        return 1
    """
    # flag_symbol = ""
    for i in prices:
        tmp = i.get('symbol')
        if flag_symbol:
            if tmp != flag_symbol:
                continue
        if re.search(r'USDT$', tmp):
            #            if not any(symbols.symbol == tmp):
            #               symbols[tmp] = {}

            j = re.match(r'(\w+)USDT', tmp).group(1)
            jj_flag = 0
            for jj in coins_black:
                if j == jj:
                    jj_flag = 1
                    break
            if jj_flag:
                continue

            timestamp_coin = time.time()
            symbols.loc[len(symbols.index)] = {'symbol': tmp, 'timestamp': timestamp_coin,
                                               'price': float(i.get('askPrice'))}
            # for j in coins:
            # if os.path.isfile(orlov_path+"bot2/"+j):
            #    coins.remove(j)
            #    continue

            tmp2 = j + 'USDT'
            if tmp == tmp2:
                # log_time(j)
                # sys.stdout.flush()
                time_now = time.time()
                time_kline_begin = time_now - time_kline
                symbols_coin_begin = symbols.loc[
                    (symbols['timestamp'] <= time_kline_begin) & (symbols['symbol'] == tmp2)].sort_values(
                    by=['timestamp'], ascending=False)
                if len(symbols_coin_begin.index) < 3:
                    continue
                symbols_coin_begin.reset_index(drop=True, inplace=True)
                # print (symbols_coin_begin)
                old_price = (symbols_coin_begin.loc[0].price + symbols_coin_begin.loc[1].price + symbols_coin_begin.loc[
                    2].price) / 3

                time_kline_begin_long = time_now - time_kline_long
                symbols_coin_begin_long = symbols.loc[
                    (symbols['timestamp'] <= time_kline_begin_long) & (symbols['symbol'] == tmp2)].sort_values(
                    by=['timestamp'], ascending=False)
                if len(symbols_coin_begin_long.index) < 3:
                    continue
                symbols_coin_begin_long.reset_index(drop=True, inplace=True)
                # print (symbols_coin_begin)
                old_price_long = (symbols_coin_begin_long.loc[0].price + symbols_coin_begin_long.loc[1].price +
                                  symbols_coin_begin_long.loc[2].price) / 3

                #                print ('Pandas price: ' + str(price.price))
                #                sys.exit()
                #                sys.stdout.flush()

                price = float(i.get('askPrice'))

                try:
                    f = open(orlov_path + 'coins2/' + j + '-long', 'r+')
                    long = int(f.read())
                    f.close()
                    """
                    p = pathlib.Path(orlov_path+'coins/'+j+'-old')
                    st = p.stat()
                    coin_file_date = st.st_mtime
                    tmp_time = time.time()-50
                    if coin_file_date < tmp_time:
                        #log_time (j + " устарел")
                        #sys.stdout.flush()
                        continue
                    """
                    tn = time.time()
                    if float(long) and not send_flag:
                        telega(messages=[j + " long trigger (" + str(price) + ")"], conf="/etc/telegram-send.conf")
                        send_flag = tn
                    elif send_flag <= tn - 60:
                        send_flag = 0
                # else:
                except:
                    log_time(j + " long file error")
                    o = 0

                tmp = old_price + old_price / 100 * percent
                tmp_long30 = old_price + old_price / 100 * percent_long
                tmp_long15 = old_price_long + old_price_long / 100 * percent_long

                tmp_short = old_price - old_price / 100 * percent
                tmp_BTC = old_price + old_price / 100 * 0.8

                if price >= tmp_BTC and j == 'BTC':
                    telega(messages=["BTC overload. Sleep 60 min."], conf="/etc/telegram-send.conf")
                    time.sleep(60 * 60)
                    break
                ################## LONG ######################
                if 0:
                    time_buy_data_long = buy_data_long['timestamp'] + 60
                    tmp_time2 = time.time()
                    if (price >= tmp_long30 and price < tmp_long15) or (
                            to_the_moon_long['status'] and price < to_the_moon_long['price'] and to_the_moon_long[
                        'symbol'] == tmp2) or (buy_data_long['stopPrice'] and price < buy_data_long[
                        'stopPrice'] and time_buy_data_long >= tmp_time2 and buy_data_long['symbol'] == tmp2):
                        if buy_data_long['stopPrice'] and buy_data_long['stopPrice'] < price and buy_data_long[
                            'symbol'] == tmp2:
                            # telega(messages=["buy_data['stopPrice'] >= price"], conf="/etc/telegram-send.conf")
                            continue
                        if bad_buy_long['symbol'] and price >= bad_buy_long['price'] and bad_buy_long['symbol'] == tmp2:
                            continue
                        elif bad_buy_long['symbol'] and bad_buy_long['symbol'] == tmp2:
                            telega(messages=["Bad buy LONG trigger " + j + ": " + str(price)],
                                   conf="/etc/telegram-send.conf")

                        if to_the_moon_long['status'] and price < to_the_moon_long['price'] and to_the_moon_long[
                            'symbol'] == tmp2:
                            log_time('!! ' + str(to_the_moon_long['status']) + ' - ' + str(to_the_moon_long['price']))
                            sys.stdout.flush()
                        elif to_the_moon_long['status'] and price >= to_the_moon_long['price'] and to_the_moon_long[
                            'symbol'] == tmp2:
                            log_time('?? ' + str(to_the_moon_long['status']) + ' - ' + str(to_the_moon_long['price']))
                            sys.stdout.flush()
                        # if not buy_data_long['symbol']:
                        if 1:
                            if buy_data_long['count'] >= 2 and buy_data_long['symbol'] == tmp2:
                                log_time('Buy count LONG ' + j + ' > 2. Rejected.')
                                telega(messages=["Buy count LONG " + j + " > 2. Rejected."],
                                       conf="/etc/telegram-send.conf")
                                continue
                            elif buy_data_long['count'] and buy_data_long['symbol'] != tmp2:
                                buy_data_long['count'] = 0

                            get_balance_from_file()
                            bin_long = binance_work_long(tmp2, old_price, price, j)
                            if bin_long == 2:
                                flag_symbol = tmp2
                                buy_data_long['symbol'] = tmp2
                                bad_buy_long['symbol'] = ""
                                buy_data_long['stopPrice'] = 0
                                buy_data_long['price'] = 0
                            elif bin_long == 3:
                                flag_symbol = ""
                                take_percent0_long = take_percent0_main_long
                                to_the_moon_long['status'] = 0
                                bad_buy_long['symbol'] = ""
                            elif bin_long == 4:
                                flag_symbol = ""
                                take_percent0_long = take_percent0_main_long
                                to_the_moon_long['status'] = 0
                                # next_kline_status = 0
                                buy_data_long['stopPrice'] = 0
                                buy_data_long['price'] = 0
                                log_time("Return 4")
                            elif bin_long:
                                flag_symbol = tmp2
                                take_percent0_long = take_percent0_main_long
                                to_the_moon_long['status'] = 0
                                bad_buy_long['symbol'] = ""
                                buy_data_long['stopPrice'] = 0
                                buy_data_long['price'] = 0
                            else:
                                flag_symbol = ""
                                take_percent0_long = take_percent0_main_long
                                to_the_moon_long['status'] = 0
                                # next_kline_status = 0
                                bad_buy_long['symbol'] = ""
                                buy_data_long['stopPrice'] = 0
                                buy_data_long['price'] = 0
                                time.sleep(60)  ####
                                log_time("Return 0")
                            break
                    elif price >= tmp_long30:
                        buy_data_long['symbol'] = tmp2
                        buy_data_long['timestamp'] = tmp_time2
                    tt = time.time()
                    if buy_data_long['symbol'] and time_buy_data_long < tt:
                        buy_data_long['symbol'] = ""
                    if time_buy_data_long < tt:
                        to_the_moon_long['status'] = 0
                        buy_data_long['stopPrice'] = 0
                        buy_data_long['price'] = 0
                        flag_symbol = ""

                    ################## MAIN ######################
                time_buy_data = buy_data['timestamp'] + 60 * 2
                tmp_time2 = time.time()
                if price >= tmp or (
                        to_the_moon['status'] and price >= to_the_moon['price'] and buy_data['symbol'] == tmp2) or (
                        bad_buy['symbol'] and bad_buy['symbol'] == tmp2) or (
                        buy_data['stopPrice'] and price > buy_data['stopPrice'] and time_buy_data >= tmp_time2 and
                        buy_data['symbol'] == tmp2):  # and modul_BTC < tmp_modul:

                    if buy_data['stopPrice'] >= price and buy_data['symbol'] == tmp2:
                        # telega(messages=["buy_data['stopPrice'] >= price"], conf="/etc/telegram-send.conf")
                        continue
                    if bad_buy['symbol'] and price < bad_buy['price'] and bad_buy['symbol'] == tmp2:
                        continue
                    elif bad_buy['symbol'] and bad_buy['symbol'] == tmp2:
                        telega(messages=["Bad buy trigger " + j + ": " + str(price)], conf="/etc/telegram-send.conf")
                    """
                    if time_buy_data >= tmp_time2 and buy_data['symbol'] == tmp2:
                        if price <= buy_data['price']:
                            continue
                    """
                    # проверка положительной сделки по symbol
                    f = open(orlov_path + 'coins2/_balance_old', 'r+')
                    balance_symbol = f.read()
                    f.close()
                    if balance_symbol == tmp2:
                        log_time(j + ' already plused. Rejected.')
                        continue

                    f = open(orlov_path + 'coins2/' + j + '-vol', 'r+')
                    vol_str1m = f.read()
                    f.close()
                    log_time("--- " + tmp2 + " volume 10 min is " + vol_str1m)

                    f = open(orlov_path + 'coins2/' + j + '-min3h', 'r+')
                    min3h_str = f.read()
                    f.close()
                    log_time("--- " + tmp2 + " min price 3 hour is $" + min3h_str)

                    # Защита по принципу предельного роста за последний 3 часа
                    if float(min3h_str):
                        tmp_min3h = float(min3h_str)
                        tmp_min3h_percent = tmp_min3h + tmp_min3h / 100 * percent_3h
                        if tmp_min3h_percent < price:
                            # log_time("Volume "+j+" overload. Rejected.")
                            tmp_perc = tmp_min3h / price * 100
                            telega(messages=["Price " + j + " The price has gone up too much in 3 hours (" + str(
                                tmp_perc) + "%). Rejected."], conf="/etc/telegram-send.conf")
                            time.sleep(60)
                            break

                    f = open(orlov_path + 'coins2/' + j + '-vol1h', 'r+')
                    vol_str1h = f.read()
                    f.close()
                    log_time("--- " + tmp2 + " volume 1 hour is " + vol_str1h)

                    f = open(orlov_path + 'coins2/' + j + '-vol3h', 'r+')
                    vol_str3h = f.read()
                    f.close()
                    log_time("--- " + tmp2 + " volume 3 hour is " + vol_str3h)
                    # Защита по принципу резкого увеличеня объёма за последние 3 часа
                    if float(vol_str3h):
                        tmp_str1m = float(vol_str1m)
                        tmp_str3h = float(vol_str3h)
                        vol_fuse = tmp_str1m / tmp_str3h
                        if (vol_fuse >= 1.25 and tmp_str3h > 100000) or tmp_str3h > 1000000:
                            # log_time("Volume "+j+" overload. Rejected.")
                            # telega(messages=["Volume "+j+" overload. Rejected."], conf="/etc/telegram-send.conf")
                            time.sleep(10)
                            break
                        elif tmp_str1m < 40000:
                            break
                        elif tmp_str3h < 30000:
                            break

                    f = open(orlov_path + 'coins2/' + j + '-vold', 'r+')
                    vol_str1d = f.read()
                    f.close()
                    log_time("--- " + tmp2 + " volume 1 day is " + vol_str1d)

                    if not float(vol_str1d):
                        break

                    # Защита по принципу резкого увеличеня объёма за последний день
                    if float(vol_str1d):
                        tmp_str1m = float(vol_str1m)
                        vol_fuse = tmp_str1m / float(vol_str1d)
                        if vol_fuse >= 3 or (vol_fuse >= 2 and tmp_str1m > 100000):
                            # log_time("Volume "+j+" overload. Rejected.")
                            # telega(messages=["Volume "+j+" overload. Rejected."], conf="/etc/telegram-send.conf")
                            time.sleep(10)
                            break
                        elif tmp_str1m < 20000:
                            break

                    if buy_data['count'] >= 2 and buy_data['symbol'] == tmp2:
                        log_time('Buy count ' + j + ' > 2. Rejected.')
                        telega(messages=["Buy count " + j + " > 2. Rejected."], conf="/etc/telegram-send.conf")
                        continue
                    elif buy_data['count'] and buy_data['symbol'] != tmp2:
                        buy_data['count'] = 0

                    # if (price >= tmp and price < buy_data['price'] and time_buy_data >= tmp_time2 and buy_data['symbol'] == tmp2)
                    #    log_time("Свеча высокая, но время ожидания поещё не прошло")
                    #    break
                    # f = open(orlov_path+"coins/"+j+"2", 'w+')
                    # f.write("")
                    # f.close()
                    get_balance_from_file()
                    ##symbols_coin_kline = symbols.loc[(symbols['timestamp'] > time_kline_begin) & (symbols['symbol'] == tmp2)]
                    ##symbols_coin_kline = symbols_coin_kline.sort_values(by=['timestamp'], ascending=False)
                    ##symbols_coin_kline.reset_index(drop=True, inplace=True)
                    ##print (symbols_coin_kline)
                    bin = binance_work(tmp2, old_price, price, j)
                    # telega(messages=["----------------------------"], conf="/etc/telegram-send.conf")
                    if bin == 2:
                        flag_symbol = tmp2
                        buy_data['symbol'] = tmp2
                        bad_buy['symbol'] = ""
                        buy_data['stopPrice'] = 0
                        buy_data['price'] = 0
                    elif bin == 3:
                        flag_symbol = ""
                        take_percent0 = take_percent0_main
                        to_the_moon['status'] = 0
                        bad_buy['symbol'] = ""
                    elif bin == 4:
                        flag_symbol = ""
                        take_percent0 = take_percent0_main
                        to_the_moon['status'] = 0
                        next_kline_status = 0
                        buy_data['stopPrice'] = 0
                        buy_data['price'] = 0
                        log_time("Return 4")
                    elif bin:
                        flag_symbol = tmp2
                        take_percent0 = take_percent0_main
                        to_the_moon['status'] = 0
                        bad_buy['symbol'] = ""
                        buy_data['stopPrice'] = 0
                        buy_data['price'] = 0
                    else:
                        flag_symbol = ""
                        take_percent0 = take_percent0_main
                        to_the_moon['status'] = 0
                        next_kline_status = 0
                        bad_buy['symbol'] = ""
                        buy_data['stopPrice'] = 0
                        buy_data['price'] = 0
                        time.sleep(60)  ####
                        log_time("Return 0")
                    break
                elif to_the_moon['status'] and price < to_the_moon['lowPrice']:
                    # to_the_moon['status'] = 0
                    flag_symbol = ""
                    telega(messages=[tmp2 + " to the moon price too low"], conf="/etc/telegram-send.conf")
                    time.sleep(60)
                    break

                tt = time.time()

                if time_buy_data < tt:
                    to_the_moon['status'] = 0
                    buy_data['stopPrice'] = 0
                    buy_data['price'] = 0
                    flag_symbol = ""

                if bad_buy['symbol']:
                    tmp_bad_buy_time = bad_buy['timestamp'] + 60 * 2
                    if tmp_bad_buy_time < tt:
                        bad_buy['symbol'] = ""

                if price < tmp_short and 0:  # and modul_BTC < tmp_modul:
                    telega(messages=["Short trigger " + tmp2 + ": " + str(price)], conf="/etc/telegram-send.conf")
                    time.sleep(3)
                    """
                    symbols_coin_kline = symbols.loc[(symbols['timestamp'] > time_kline_begin) & (symbols['symbol'] == tmp2)]
                    symbols_coin_kline = symbols_coin_kline.sort_values(by=['timestamp'], ascending=False)
                    symbols_coin_kline.reset_index(drop=True, inplace=True)
                    log_time('1% ('+j+'): ' + str(len(symbols_coin_begin.index))+ ", price: " +str(price), orlov_path+"log/"+j)
                    log_time('-----------------------------------------', orlov_path+"log/"+j)
                    """

    tmp_time = time.time() - time_kline - 5
    symbols = symbols.loc[symbols['timestamp'] >= tmp_time]
    symbols.reset_index(drop=True, inplace=True)
    # print (symbols)
    sys.stdout.flush()


def get_balance():
    # global balance
    global balance_2
    # balance_raw = ''
    balance_raw_2 = ''
    try:
        # balance_raw = bclient.futures_account_balance()
        balance_raw_2 = bclient_2.futures_account_balance()
    except:
        log_time('Balance getting error 1')
        flag = 0
        while not flag:
            try:
                # balance_raw = bclient.futures_account_balance()
                balance_raw_2 = bclient_2.futures_account_balance()
                flag = 1
            except:
                log_time('Balance getting error 2')
                time.sleep(1)
    if not balance_raw_2:
        print("balance_raw error. Exit.")
        sys.exit()
    # balance_str = ''
    """
    for item in balance_raw:
        if item['asset'] == 'USDT':
            balance_str = item['balance']  
    if not balance_str:
        print ('Error getting balance')
        sys.exit()
    if not balance:
        balance = float(balance_str)
    print ("==============================================================================================")
    log_time('>> Balance: ' + balance_str)
    """
    for item in balance_raw_2:
        if item['asset'] == 'USDT':
            balance_str_2 = item['balance']
    if not balance_str_2:
        print('Error getting balance 2')
        sys.exit()
    log_time('>> Balance 2: ' + balance_str_2)
    if not balance_2:
        balance_2 = float(balance_str_2)
    sys.stdout.flush()
    set_balance_file()


def base_init():
    db = conn.connect(host="localhost", user="root", password="connect", database="orlovbot")
    cursor = db.cursor()

    cursor.execute("""CREATE DATABASE IF NOT EXISTS orlovbot""")
    db.commit()
    cursor.execute("""USE orlovbot""")
    db.commit()
    cursor.execute("""CREATE TABLE IF NOT EXISTS limit_orders(
        id INT NOT NULL AUTO_INCREMENT,
        symbol CHAR(15) NOT NULL,
        orderId BIGINT UNSIGNED NOT NULL,
        updateTime BIGINT UNSIGNED NOT NULL,
        price TINYTEXT NOT NULL,
        origQty TINYTEXT NOT NULL,
        side TINYTEXT NOT NULL,
        status ENUM('new', 'renew', 'add', 'readd'),
        number INT UNSIGNED DEFAULT 0,
        PRIMARY KEY (id))""")
    db.commit()
    db.close()


# =======================================================================


# base_init(db)


# set_limit_order(db, "Test")


sys.stderr.flush()
with open(stderr, 'a+') as stderr:
    os.dup2(stderr.fileno(), sys.stderr.fileno())

sys.stdout.flush()
##print(4)
with open(stdout, 'a+') as stdout:
    os.dup2(stdout.fileno(), sys.stdout.fileno())

# bot.polling(none_stop=True, interval=0)

# client = TelegramClient('X100TradingBot', api_id, api_hash)
get_balance()
next_kline_status = 0
# @client.on(events.NewMessage(pattern=r'Покупаю\s\#|orlovbot'))
if 1:
    # async def normal_handler(event):

    # out = subprocess.run(["ps", "aux"], stdout=subprocess.PIPE, text=True)
    # print (out.stdout)
    # sys.exit()
    # tmp = re.findall(r'python3 /home/run/orlovbot/main.py', out.stdout)
    # print (len(tmp))
    # for item in out.stdout:
    # print (out.stdout)

    #    message = event.message.to_dict()['message']
    #    log_time('MESSAGE RECEIVED')
    if 1:
        # if re.match(r'Покупаю\s\#(\w+)', message):
        # print(message)
        # symbol = re.match(r'Покупаю\s\#(\w+)', message).group(1)+'USDT'
        # print(symbol)
        stop = 0
        # telega(messages=["Orlovbot started"], conf="/etc/telegram-send.conf")
        while check_pipe():
            """
            klines = bclient_2.get_historical_klines("BZRXUSDT", Client.KLINE_INTERVAL_1MINUTE, "40 min ago UTC", klines_type=HistoricalKlinesType.FUTURES)
            print (klines[38][2])
            sys.stdout.flush()
            sys.exit()

            i = 0
            for kline in klines:
                kline_max = kline[2]
                log_time (str(i)+ " - "+kline_max)
                i = i + 1
            """
            if next_kline_status:
                kline_timestamp_now = time.time()
                tmp_t = next_kline_status + 10
                if kline_timestamp_now > tmp_t:
                    next_kline_status = 0
            binance()
            sys.stdout.flush()
            time.sleep(0.3)
        #        del_pipe()
        # await client.send_message('@Adm_S_R', symbol+" buy")
        """
    elif re.match(r'orlovbot', message):
        tmp = re.match(r'orlovbot\s(\w+)\s([\d\.]+)\s(\w+)', message)
        command = tmp.group(1)
        price = tmp.group(2) = 0
        market_type = tmp.group(3)
        if not command or not price or not market_type:
            print ('Orlovbot command error')
            sys.exit()
        print (command)
        print (price)
        print (market_type)
        sys.stdout.flush()

client.start()
client.run_until_disconnected()
"""
# 193.142.42.167:32809
