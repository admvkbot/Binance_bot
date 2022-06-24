#import telebot
#from telethon import TelegramClient, sync, events
import re
from binance import Client, ThreadedWebsocketManager, ThreadedDepthCacheManager
import sys
import os
import subprocess
import time
from datetime import datetime
#import math # math.floor() 
import xmltodict

percent = 1.5
trade_balance = 10 # размер позиции

orlov_path = "/home/run/orlovbot/"
config_xml = ''
with open(orlov_path+'main.xml', 'r') as f:
    config_xml = ''.join(list(map(str.strip, f.readlines())))
config = xmltodict.parse(config_xml)

api_key = config['config']['api-key']
api_secret = config['config']['api-secret']
proxy = config['config']['proxy']

path = "/var/www/html/"

def log_time(string):
    print(str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]) + ': ' + string)
    
def set_pipe():
    global path
    f = open(path+'pipe5', 'w+')
    f.close() 

def check_pipe():
    global path
    return os.path.isfile(path+'pipe5')

def del_pipe():
    global path
    os.remove(path+'pipe5')

if check_pipe():
    log_time("Terminated")
    sys.exit()
        
set_pipe()
bad_coins = []

#summ = 60 #trade summ in dollars
leverage = 20
stop_percent = 0 #закрытие при уменьшении цены на этот %


# далее расписана сетка тейков

take_percent1 = 0.3
take_percent_summ1 = 50
take_percent2 = 0.4
take_percent_summ2 = 40
take_percent3 = 0.5
take_percent_summ3 = 10

"""
take_percent1 = 0.1
take_percent_summ1 = 30
take_percent2 = 0.2
take_percent_summ2 = 30
take_percent3 = 0.3
take_percent_summ3 = 20
take_percent4 = 0.4
take_percent_summ4 = 20
"""

trade_lifetime = 60 # время для установки стоп-лосса

take_type = 'true' # установка reduceOnly для тейков



stdout=path+'orlovbot5_out.log'
stderr=path+'orlovbot5_err.log'
str0 = 'http://' + str(proxy)
proxies = {
    'http': 'http://10.10.1.10:3128',
    'https': str0
}

#bot = telebot.TeleBot('1990712394:AAFK_R3HrJYGM76wV_1UltpQzKY1lig2_bA')
#@bot.message_handler(content_types=['text'])


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
if proxy:
    bclient = Client(api_key, api_secret, {'proxies': proxies})
else:
    bclient = Client(api_key, api_secret)

coins = {}

def take(symbol, price, amount, side):
    order = bclient.futures_create_order (
        symbol=symbol, 
        type='LIMIT', 
        timeInForce='GTC',
        price=price,  # The price at which you wish to buy/sell, float
        side=side,  # Direction ('BUY' / 'SELL'), string
        quantity=amount,  # Number of coins you wish to buy / sell, float
        reduceOnly='true'
    )
    return int(order['orderId'])


def binance_work(symbol, work_coin, order_type):

    log_time('Start binance(): ' + symbol)
    sys.stdout.flush()
    balance_raw = bclient.futures_account_balance()
    #log_time('balance_raw received')
    balance_str = ''
    for item in balance_raw:
        if item['asset'] == 'USDT':
            balance_str = item['balance']
            print ('Balance: ' + balance_str)
    sys.stdout.flush()        
    if not balance_str:
        print ('Error getting balance')
        sys.exit()
    balance = float(balance_str)
    log_time('Balance: ' + balance_str)
    """
    orders = bclient.get_all_orders(symbol=symbol, limit=1)
    print (orders)
    sys.exit()
    """   
    try:
        bclient.futures_change_leverage(symbol=symbol, leverage=leverage)
    except:
        log_time('Error coin '+ symbol)
        os.remove(orlov_path+"bot/"+work_coin)
        bad_coins.append(symbol)
        return 0
        
    try:
        bclient.futures_change_margin_type(symbol=symbol, marginType='ISOLATED')
    except:
        log_time('Error changing margin type of '+ symbol)
    
    # получение начальной цены для работы
    orderbook = bclient.get_ticker(symbol=symbol)
    last_price = orderbook['lastPrice']
    print("Start price: "+ last_price)
    
    if not last_price:
        print ("last_price error")
        return 0
    
    last_price = float(last_price)

    #вычисление точности
    precision_price = 0
    if last_price < 0.1:
        precision_price = 5
    elif last_price < 1:
        precision_price = 4
    elif last_price < 10:
        precision_price = 3      
    elif last_price < 1000:
        precision_price = 2  
        
    # вычисление объёма монет
    amount = trade_balance/last_price*leverage
    #amount = balance/last_price
    
    # определение необходимой точности
    precision = 0
    if amount < 0.1:
        precision = 3
    elif amount < 1:
        precision = 2
    elif amount < 10:
        precision = 1

    amount_str = "{:0.0{}f}".format(amount, precision)
    log_time ("Amount (coin): "+ amount_str)
    sys.stdout.flush()
    #sys.exit()
    
    if 1:    
        # открытие позиции по рынку
        order = None
        #if 1:
        try:
            order = bclient.futures_create_order ( 
                symbol=symbol,
                type='MARKET',
                side=order_type,
                quantity=amount_str,
                isIsolated='TRUE'
            )

        except:
            log_time ("Open position error: "+ symbol)
            print (order)
            os.remove(orlov_path+"bot/"+work_coin)
            return 0

        coins[symbol] = 1 # подсветка сущности монеты
                
        # получение цены монеты сразу после покупки
        orderbook = bclient.get_ticker(symbol=symbol)  
        last_price_old = last_price
        last_price_str = orderbook['lastPrice']
        last_price = float(last_price_str)
        tmp = (last_price_old - last_price) / last_price * 100
        tmp = "{:0.0{}f}".format(tmp, 2)
        log_time('Price after buing: ' + last_price_str +'. Проскальзывание: '+ tmp +'%')
                 
            
        order_ids = []
 
        take_type = 'SELL'
        if order_type == 'SELL':
            take_type = 'BUY'
        
        # установка сетки ордеров
        ### 1
        amount1 = amount/100*take_percent_summ1
        amount1_str = "{:0.0{}f}".format(amount1, precision)
        print ("Amount1: "+ amount1_str) 
        #вычисление цены для тейка
        take_price1 = None
        p = last_price/100*take_percent1
        if order_type == 'BUY':
            take_price1 = last_price + p
        else:
            take_price1 = last_price - p
        take_price1_str = "{:0.0{}f}".format(take_price1, precision_price)
        print('Take price1: ' + take_price1_str) 
        sys.stdout.flush()    
        #установка тейк-профита
        order_id = take(symbol, take_price1_str, amount1_str, take_type)
        order_ids.append(order_id)
        log_time('take1 end')
        
        ### 2
        amount2 = amount/100*take_percent_summ2
        amount2_str = "{:0.0{}f}".format(amount2, precision)
        print ("Amount2: "+ amount2_str) 
        #вычисление цены для тейка
        take_price2 = None
        p = last_price/100*take_percent2
        if order_type == 'BUY':
            take_price2 = last_price + p
        else:
            take_price2 = last_price - p
        take_price2_str = "{:0.0{}f}".format(take_price2, precision_price)
        print('Take price2: ' + take_price2_str) 
        sys.stdout.flush()    
        #установка тейк-профита
        order_id = take(symbol, take_price2_str, amount2_str, take_type)
        order_ids.append(order_id)
        log_time('take2 end')

        #полное закрытие

        
        if amount1<1.1:
            amount3 = amount1 + 0.1
        else:
            amount3 = amount1 + 1 # +1 для того, чтобы точно закрылся весь ордер
        amount3_str = "{:0.0{}f}".format(amount3, precision)
        print ("Amount3: "+ amount3_str) 
        #вычисление цены для тейка
        take_price3 = None
        p = last_price/100*take_percent3
        if order_type == 'BUY':
            take_price3 = last_price + p
        else:
            take_price3 = last_price - p
        take_price3_str = "{:0.0{}f}".format(take_price3, precision_price)
        print('Take price3: ' + take_price3_str) 
        sys.stdout.flush()    
        #установка тейк-профита
        order_id = take(symbol, take_price3_str, amount3_str, take_type)
        order_ids.append(order_id)
        log_time('Last take end')
 

        # блок ожидания установки стоп-ордера
        i = 0        
        flag = 0
        while i < trade_lifetime*2   and not flag:
            # получение цены монеты сразу после покупки
            orderbook = bclient.get_ticker(symbol=symbol)  
            tmp_price_str = orderbook['lastPrice']
            tmp_price = float(tmp_price_str)
            p = last_price / 100 * 0.2
            if order_type == 'BUY':
                best_price = last_price + p
                if tmp_price >= best_price:
                    flag = 1
                    log_time('TMP price: ' + str(tmp_price))
                    break
            else:
                best_price = last_price - p
                if tmp_price <= best_price:
                    flag = 1
                    log_time('TMP price: ' + str(tmp_price))
                    break                    
            i = i + 1
            time.sleep(0.3)
        if flag:
            if 1:
            #try:
                if order_type == 'BUY':
                    #вычисление цены для стоп-лосса
                    stop_price = last_price + last_price/100*stop_percent
                    stop_price_str = "{:0.0{}f}".format(stop_price, precision_price)
                    print('Stop price long: ' + stop_price_str)
                    sys.stdout.flush()
                    # установка стоп-ордера
                    try:
                        stop_order = bclient.futures_create_order (
                            symbol=symbol, 
                            side='SELL', 
                            type='STOP_MARKET', 
                            stopPrice=stop_price_str,
                            closePosition='true'
                        )
                    except:
                        stop_price = stop_price - stop_price/100*0.1
                        stop_price_str = "{:0.0{}f}".format(stop_price, precision_price)                    
                        stop_order = bclient.futures_create_order (
                            symbol=symbol, 
                            side='SELL', 
                            type='STOP_MARKET', 
                            stopPrice=stop_price_str,
                            closePosition='true'
                        )
                else:
                    #вычисление цены для стоп-лосса
                    stop_price = last_price - last_price/100*stop_percent
                    stop_price_str = "{:0.0{}f}".format(stop_price, precision_price)
                    log_time('Stop price short: ' + stop_price_str)
                    sys.stdout.flush()
                    # установка стоп-ордера
                    try:
                        stop_order = bclient.futures_create_order (
                            symbol=symbol, 
                            side='BUY', 
                            type='STOP_MARKET', 
                            stopPrice=stop_price_str,
                            closePosition='true'
                        )                
                    except:
                        stop_price = stop_price + stop_price/100*0.1
                        stop_price_str = "{:0.0{}f}".format(stop_price, precision_price)                    
                        stop_order = bclient.futures_create_order (
                            symbol=symbol, 
                            side='SELL', 
                            type='STOP_MARKET', 
                            stopPrice=stop_price_str,
                            closePosition='true'
                        )
                
        else:
            # закрытие позиции и ордеров
            print ('Clear order '+symbol+'...')
            tmp_close_amount = amount+1
            tmp_close_amount_str = "{:0.0{}f}".format(tmp_close_amount, precision)
            #if 1:
            try:
                order = bclient.futures_create_order ( 
                    symbol=symbol,
                    type='MARKET',
                    side=take_type,
                    quantity=tmp_close_amount_str,
                    reduceOnly='true'
                )
                bclient.futures_cancel_orders(symbol=symbol, orderIdList=order_ids)
            except:
                log_time ("Force close position error: "+ symbol)
                return 0
            
    
    print ("---------------------------------------------------")
    


def binance():
    #log_time('Start binance(): ' + symbol)
    #base_price = float(base_price)
 
    #coins = ["BZRX", "STMX", "SFP", "LIT", "BEL", "BLZ", "SKL", "BTS", "UNFI", "KEEP", "CTK", "LINA", "NKN", "ZZZZ"]
    #coins = None
    
    # получение начальной цен
    prices = bclient.get_all_tickers()
    for i in prices:
        work_symbol = i.get('symbol')
        fl = 0
        for j in bad_coins:
            if work_symbol == j:
                fl = 1
                break
        if fl:
            continue
        tmp = work_symbol[-4:]
        if tmp == 'USDT':
            work_coin = work_symbol[:-4]
            # создание сущности монеты
            if not work_symbol in coins:
                coins[work_symbol] = 0
#            print ('work_coin: ' + work_coin)
            if coins[work_symbol]:
                coins[work_symbol] = coins[work_symbol] + 1
                if coins[work_symbol] > 200 :
                    try:
                        print ('work_symbol: ' + work_symbol)
                        o = bclient.futures_coin_get_open_orders(pair=work_symbol)
                        if o:
                            coins[work_symbol] = 1
                        else:
                            coins[work_symbol] = 0
                        print (o)
                    except:
                        coins[work_symbol] = 0                
                if coins[work_symbol]:
                    continue
            f = open(orlov_path+'coins/'+work_coin+'-old', 'r+')
            str0 = f.read()
            f.close()
            if not str0:
                continue
            old_price = float(str0)            
            price = float(i.get('price'))
            tmp = old_price + old_price/100*percent
            tmp2 = old_price - old_price/100*percent
            if price >= tmp:
                f = open(orlov_path+"bot/"+work_coin, 'a+')
                f.write(str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]) + ': ' + str(old_price)+' - '+str(price) + "(BUY)\n")
                f.close()
                    
                binance_work(work_symbol, work_coin, 'BUY')
            elif price < tmp2:
                f = open(orlov_path+"bot/"+work_coin, 'a+')
                f.write(str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]) + ': ' + str(old_price)+' - '+str(price) + "(SELL)\n")
                f.close()
                    
                binance_work(work_symbol, work_coin, 'SELL')
                    
                #del_pipe()
                #sys.exit()

    
# =======================================================================
        
if(1):    
    if (1):
        sys.stderr.flush()
        with open(stderr, 'a+') as stderr:
            os.dup2(stderr.fileno(), sys.stderr.fileno())

        sys.stdout.flush()
        ##print(4)
        with open(stdout, 'a+') as stdout:
            os.dup2(stdout.fileno(), sys.stdout.fileno())

#bot.polling(none_stop=True, interval=0)

# Вставляем api_id и api_hash
#api_id = 7428364
#api_hash = '98020087a8d56f047f3c92de8bd8d5bc'

#client = TelegramClient('X100TradingBot', api_id, api_hash)

#@client.on(events.NewMessage(pattern=r'Покупаю\s\#|orlovbot'))
if 1:
#async def normal_handler(event):
    log_time('SIGNAL')
    #out = subprocess.run(["ps", "aux"], stdout=subprocess.PIPE, text=True)
    #print (out.stdout)
    #sys.exit()
    #tmp = re.findall(r'python3 /home/run/orlovbot/main.py', out.stdout)
    #print (len(tmp))
    #for item in out.stdout:
    #print (out.stdout)

#    message = event.message.to_dict()['message']
#    log_time('MESSAGE RECEIVED')
    if 1:
    #if re.match(r'Покупаю\s\#(\w+)', message):
        #print(message)
        #symbol = re.match(r'Покупаю\s\#(\w+)', message).group(1)+'USDT'
        #print(symbol)
        stop = 0
        while check_pipe():
            binance()
            sys.stdout.flush()
            time.sleep(0.3)
#        del_pipe()
        print ("STOPED")
        #await client.send_message('@Adm_S_R', symbol+" buy")
        """
    elif re.match(r'orlovbot', message):
        tmp = re.match(r'orlovbot\s(\w+)\s([\d\.]+)\s(\w+)', message)
        command = tmp.group(1)
        price = tmp.group(2)
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
#193.142.42.167:32809




