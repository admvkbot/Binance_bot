from binance import Client, ThreadedWebsocketManager, ThreadedDepthCacheManager
import sys
import os
import time
import xmltodict
import mysql.connector as conn
from datetime import datetime
import telegram_send
import re

path = "/var/www/html/"
orlov_path = "/home/run/orlovbot/"

leverage = 10


def log_time(string, file=""):
    if file:
        f = open(file, "a+")
        f.write(str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]) + ': ' + string + "\n")
        f.close()
    else:
        print(str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]) + ': ' + string)


def set_pipe():
    global path
    f = open(path + 'pipe7', 'w+')
    f.close()


def check_pipe():
    global path
    return os.path.isfile(path + 'pipe7')


def del_pipe():
    global path
    os.remove(path + 'pipe7')


if check_pipe():
    log_time("Terminated")
    sys.exit()


def base_init():
    global cursor
    cursor.execute("""USE orlovbot""")
    db.commit()


def get_orders(type):
    global db
    cursor2 = db.cursor()
    if type == "all":
        cursor2.execute("SELECT * FROM limit_orders WHERE status='new' OR status='renew' ORDER BY symbol")
    else:
        cursor2.execute("SELECT * FROM limit_orders WHERE status='" + type + "' ORDER BY symbol")
    r = cursor2.fetchall()
    db.commit()
    cursor2.close()
    return r


def del_orders_by_symbol(symbol):
    global db
    cursor2 = db.cursor()
    sql = "DELETE FROM limit_orders WHERE symbol='" + symbol + "'"
    cursor2.execute(sql)
    db.commit()
    cursor2.close()
    print(cursor2.rowcount, "record(s) ", symbol, " deleted")


def del_orders_by_id(id):
    global db
    cursor2 = db.cursor()
    sql = "DELETE FROM limit_orders WHERE orderId=" + str(id)
    cursor2.execute(sql)
    db.commit()
    cursor2.close()
    print(cursor2.rowcount, "record(s)", str(id), " deleted!")


def take_buy(symbol, price, amount, type):
    if float(amount):
        try:
            bclient_2.futures_cancel_all_open_orders(symbol=symbol)
        except:
            o = 0
        return bclient_2.futures_create_order(
            symbol=symbol,
            type='LIMIT',
            timeInForce='GTC',
            price=price,  # The price at which you wish to buy/sell, float
            side='BUY',  # Direction ('BUY' / 'SELL'), string
            quantity=amount,  # Number of coins you wish to buy / sell, float
            reduceOnly=type
        )


def set_order(order, type):
    global db
    cursor2 = db.cursor()
    print(order)
    sys.stdout.flush()
    sql = "INSERT INTO limit_orders (symbol, orderId, updateTime, price, origQty, side, status, number) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    val = (
    order['symbol'], order['orderId'], order['updateTime'], order['price'], order['origQty'], order['side'], type, 1)
    cursor2.execute(sql, val)
    db.commit()
    cursor2.close()
    print(cursor2.rowcount, "record inserted.")


def check_add(symbol):
    global db
    cursor2 = db.cursor()
    cursor2.execute("SELECT * FROM limit_orders WHERE status='add' AND symbol='" + symbol + "'")
    r = cursor2.fetchall()
    db.commit()
    cursor2.close()
    return r


def set_balance_file(balance_2):
    # f = open(orlov_path+'coins2/_balance', 'w+')
    # f.write(str(balance))
    # f.close()
    f = open(orlov_path + 'coins2/_balance_2', 'w+')
    f.write(str(balance_2))
    f.close()


def get_balance_from_file():
    f = open(orlov_path + 'coins2/_balance_2', 'r+')
    str_balance_2 = f.read()
    f.close()
    return float(str_balance_2)


def check_sell(bclient_2, symbol):
    return bclient_2.futures_get_open_orders(symbol=m_symbol, side='SELL')


##########################################################################################

set_pipe()

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

stdout = path + 'orlovbot7_out.log'
stderr = path + 'orlovbot7_err.log'

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

##if proxy:
##    bclient = Client(api_key, api_secret, {'proxies': proxies})
##else:
##    bclient = Client(api_key, api_secret)

if proxy_2:
    bclient_2 = Client(api_key_2, api_secret_2, {'proxies': proxies_2})
else:
    bclient_2 = Client(api_key_2, api_secret_2)
###bclient_2 = bclient###

sys.stderr.flush()
with open(stderr, 'a+') as stderr:
    os.dup2(stderr.fileno(), sys.stderr.fileno())

sys.stdout.flush()
##print(4)
with open(stdout, 'a+') as stdout:
    os.dup2(stdout.fileno(), sys.stdout.fileno())

# try:
if (1):
    db=conn.connect(host="localhost",user="root",password="connect", database="orlovbot")
    # cursor=db.cursor()
    # base_init(db)
    # print(bclient_2.futures_get_open_orders())
    print("---")
    f = open(orlov_path + 'coins2/_balance_old', 'w+')
    f.write("")
    f.close()

    # print(bclient_2.futures_position_information())
    # print("---")
    sys.stdout.flush()
    old_balance = get_balance_from_file()
    while check_pipe():
        limit_orders = None
        try:
            limit_orders = get_orders("new")
        except:
            telegram_send.send(messages=["Хьюстон, у нас проблемы в воркере! Возможно, нужен перезапуск."],
                               conf="/etc/telegram-send.conf")
            time.sleep(5)
            db = conn.connect(host="localhost", user="root", password="connect", database="orlovbot")
        old_symbol = ""
        open_orders = None
        #        if limit_orders:
        # print (limit_orders)
        for order in limit_orders:
            m_symbol = order[1]
            if old_symbol != m_symbol:
                open_orders = bclient_2.futures_get_open_orders(symbol=m_symbol)
            #            continue
            old_symbol = m_symbol
            flag_limit_order = 0
            for open_order in open_orders:
                if open_order['type'] == 'LIMIT':
                    flag_limit_order = 1
                    break
            # tmp = bclient_2.futures_position_information(symbol=m_symbol)
            # open_orders = bclient_2.futures_get_open_orders(symbol=m_symbol)
            # print (open_orders)
            if not flag_limit_order and 1:  ###
                del_orders_by_symbol(m_symbol)
                bclient_2.futures_cancel_all_open_orders(symbol=m_symbol)
                balance_raw_2 = bclient_2.futures_account_balance()
                for item in balance_raw_2:
                    if item['asset'] == 'USDT':
                        balance_str_2 = item['balance']
                log_time("Balance: " + balance_str_2)
                telegram_send.send(messages=[">> " + m_symbol + " deleted, balance: " + balance_str_2],
                                   conf="/etc/telegram-send.conf")
                balance_2 = float(balance_str_2)
                if balance_2 > old_balance:
                    f = open(orlov_path + 'coins2/_balance_old', 'w+')
                    f.write(m_symbol)
                    f.close()
                else:
                    f = open(orlov_path + 'coins2/_balance_old', 'w+')
                    f.write('')
                    f.close()
                old_balance = balance_2
                sys.stdout.flush()
                set_balance_file(balance_str_2)
                continue

            old_timestamp = order[3]
            timestamp = time.time()  # utcnow()
            tmp = timestamp - old_timestamp / 1000
            # print ("timestamps: "+str(old_timestamp)+" | "+str(timestamp) + " | " + str(tmp))

            if tmp > 120 and order[6] == 'BUY':  ###
                # нужно определенее ранее переустановленных ордеров
                m_orderId = order[2]
                # bclient_2.futures_cancel_order(symbol=m_symbol, orderId=m_orderId)
                tmp_p = float(order[4])
                tmp_price = tmp_p + tmp_p / 100 * 0.5
                # вычисление точности
                precision_price = 0
                if tmp_price < 0.1:
                    precision_price = 5
                elif tmp_price < 1:
                    precision_price = 4
                elif tmp_price < 10:
                    precision_price = 3
                elif tmp_price < 1000:
                    precision_price = 2
                take_price = "{:0.0{}f}".format(tmp_price, precision_price)
                # установка нового ордера
                info = bclient_2.futures_position_information(symbol=m_symbol)
                # log_time ("---")
                # print (info)
                # print ("---")
                position_amount = None
                for inf in info:
                    position_amount = inf['positionAmt']
                if position_amount[0] == '-':
                    position_amount = position_amount[1:]
                try:
                    t = 5 / 0
                    log_time("take_buy")
                    new_order = take_buy(m_symbol, take_price, order[5], 'true')
                    # order[4] = take_price
                    log_time("set_order renew")
                    set_order(new_order, "renew")
                    log_time("end of set_order renew")
                    telegram_send.send(messages=[m_symbol + " order changed to Breakeven: " + take_price],
                                       conf="/etc/telegram-send.conf")
                except:
                    # Buy by market
                    log_time("except take_buy")
                    try:
                        bclient_2.futures_cancel_all_open_orders(symbol=m_symbol)
                        bclient_2.futures_create_order(
                            symbol=m_symbol,
                            side='BUY',
                            type='MARKET',
                            quantity=position_amount,
                            reduceOnly='true'
                        )
                        del_orders_by_id(m_orderId)
                        balance_raw_2 = bclient_2.futures_account_balance()
                        for item in balance_raw_2:
                            if item['asset'] == 'USDT':
                                balance_str_2 = item['balance']
                        telegram_send.send(
                            messages=[">> " + m_symbol + " order market sell. Balance: " + balance_str_2],
                            conf="/etc/telegram-send.conf")
                        log_time('STOP_MARKET end')
                    except:
                        telegram_send.send(messages=["ERROR " + m_symbol + " order market sell"],
                                           conf="/etc/telegram-send.conf")
                        print(info)
                        log_time('STOP_MARKET end error')
                        sys.stdout.flush()
                        time.sleep(3)
            if tmp > 100 and order[6] == 'SELL':  ###
                # нужно определенее ранее переустановленных ордеров
                m_orderId = order[2]
                # bclient_2.futures_cancel_order(symbol=m_symbol, orderId=m_orderId)
                tmp_p = float(order[4])
                tmp_price = tmp_p + tmp_p / 100 * 0.5
                # вычисление точности
                precision_price = 0
                if tmp_price < 0.1:
                    precision_price = 5
                elif tmp_price < 1:
                    precision_price = 4
                elif tmp_price < 10:
                    precision_price = 3
                elif tmp_price < 1000:
                    precision_price = 2
                take_price = "{:0.0{}f}".format(tmp_price, precision_price)
                # установка нового ордера
                info = bclient_2.futures_position_information(symbol=m_symbol)
                # log_time ("---")
                # print (info)
                # print ("---")
                position_amount = None
                for inf in info:
                    position_amount = inf['positionAmt']
                if position_amount[0] == '-':
                    position_amount = position_amount[1:]
                try:
                    t = 5 / 0
                    log_time("take_buy")
                    new_order = take_buy(m_symbol, take_price, order[5], 'true')
                    # order[4] = take_price
                    log_time("set_order LONG renew")
                    set_order(new_order, "renew")
                    log_time("end of set_order LONG renew")
                    telegram_send.send(messages=[m_symbol + " order changed to Breakeven: " + take_price],
                                       conf="/etc/telegram-send.conf")
                except:
                    # Buy by market
                    log_time("except LONG take_buy")
                    try:
                        bclient_2.futures_cancel_all_open_orders(symbol=m_symbol)
                        bclient_2.futures_create_order(
                            symbol=m_symbol,
                            side='SELL',
                            type='MARKET',
                            quantity=position_amount,
                            reduceOnly='true'
                        )
                        del_orders_by_id(m_orderId)
                        balance_raw_2 = bclient_2.futures_account_balance()
                        for item in balance_raw_2:
                            if item['asset'] == 'USDT':
                                balance_str_2 = item['balance']
                        telegram_send.send(
                            messages=[">> " + m_symbol + " order market sell LONG. Balance: " + balance_str_2],
                            conf="/etc/telegram-send.conf")
                        log_time('STOP_MARKET end')
                    except:
                        telegram_send.send(messages=["ERROR " + m_symbol + " order market sell LONG"],
                                           conf="/etc/telegram-send.conf")
                        print(info)
                        log_time('STOP_MARKET LONG end error')
                        sys.stdout.flush()
                        time.sleep(3)
            time.sleep(0.5)
        renew_orders = get_orders("all")
        old_symbol = ""
        # for order in renew_orders:
        if 0:
            m_symbol = order[1]
            if old_symbol == m_symbol or check_add(m_symbol):
                log_time("Повтор symbol или уже есть защитный ордер (" + m_symbol + ")")
                continue
            old_symbol = m_symbol

            info = bclient_2.futures_position_information(symbol=m_symbol)
            # log_time ("+++")
            # print (info)
            # print ("+++")
            liq_price = None
            entry_price = None
            position_amount = None
            for inf in info:
                liq_price = float(inf['liquidationPrice'])
                entry_price = float(inf['entryPrice'])
                position_amount = inf['positionAmt']
            if not entry_price:
                log_time('Entry price is 0.000. Continue 1.')
                continue
            if position_amount[0] == '-':
                position_amount = position_amount[1:]

            add_coin = re.match(r'(\w+)USDT', m_symbol).group(1)
            f = open(orlov_path + 'coins2/' + add_coin, 'r+')
            str_price = f.read()
            f.close()
            add_price_now = float(str_price)
            base_plus_price = entry_price + entry_price / 100 * (100 / leverage / 100 * 70)
            if add_price_now >= base_plus_price:
                # вычисление точности
                precision_price = 0
                if base_plus_price < 0.1:
                    precision_price = 5
                elif base_plus_price < 1:
                    precision_price = 4
                elif base_plus_price < 10:
                    precision_price = 3
                elif base_plus_price < 1000:
                    precision_price = 2
                order_price = liq_price - (liq_price - entry_price) / 100 * 10
                take_price = "{:0.0{}f}".format(order_price, precision_price)
                telegram_send.send(messages=[m_symbol + " position alert. Safe order price: " + take_price],
                                   conf="/etc/telegram-send.conf")
                log_time("Short order price: " + take_price)
                add_order = bclient_2.futures_create_order(
                    symbol=m_symbol,
                    type='LIMIT',
                    timeInForce='GTC',
                    price=take_price,  # The price at which you wish to buy/sell, float
                    side='SELL',  # Direction ('BUY' / 'SELL'), string
                    quantity=position_amount  # Number of coins you wish to buy / sell, float
                )
                set_order(add_order, "add")
            sys.stdout.flush()
            time.sleep(1)

        add_orders = get_orders("add")
        old_symbol = ""
        if 0:
            # for order in add_orders:
            m_symbol = order[1]
            sell_order = check_sell(bclient_2, m_symbol)
            if old_symbol == m_symbol or sell_order:
                log_time("Повтор symbol или защитный ордер ещё не сработал (" + m_symbol + ")")
                continue
            old_symbol = m_symbol
            del_orders_by_symbol(m_symbol)

            info = bclient_2.futures_position_information(symbol=m_symbol)
            log_time("%%%")
            print(info)
            print("%%%")
            liq_price = None
            entry_price = None
            position_amount = None
            for inf in info:
                liq_price = float(inf['liquidationPrice'])
                entry_price = float(inf['entryPrice'])
                position_amount = inf['positionAmt']
            if not entry_price:
                log_time('Entry price is 0.000. Continue 2.')
                continue
            if position_amount[0] == '-':
                position_amount = position_amount[1:]

            tmp_p = float(order[4])
            tmp_price = entry_price - entry_price / 100 * 0.5
            # вычисление точности
            precision_price = 0
            if tmp_price < 0.1:
                precision_price = 5
            elif tmp_price < 1:
                precision_price = 4
            elif tmp_price < 10:
                precision_price = 3
            elif tmp_price < 1000:
                precision_price = 2
            take_price = "{:0.0{}f}".format(tmp_price, precision_price)

            log_time("Limit ADD order price: " + take_price)
            add_order = bclient_2.futures_create_order(
                type='LIMIT',
                timeInForce='GTC',
                price=take_price,  # The price at which you wish to buy/sell, float
                side='BUY',  # Direction ('BUY' / 'SELL'), string
                quantity=position_amount,  # Number of coins you wish to buy / sell, float
                reduceOnly=type
            )
            set_add_order(add_order, "readd")
            time.sleep(1)

        """    
        add_orders = get_orders("add")
        for add_order in add_orders:
            add_symbol = float(add_order[1])
            add_coin = re.match(r'(\w+)USDT', add_symbol).group(1)
            f = open(orlov_path+'coins2/'+add_coin, 'r+')
            str_price = f.read()
            f.close()
            add_price_now = float(str_price)
        """
        sys.stdout.flush()
        time.sleep(0.5)

"""    
except (e):
    print (e)
"""
# asyncio.get_event_loop().run_until_complete(socket_client())

print('THE END')