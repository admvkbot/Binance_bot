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

coins = ["BZRX", "STMX", "SFP", "LIT", "BEL", "BLZ", "SKL", "BTS", "UNFI", "KEEP", "CTK", "LINA", "NKN", "ATA", "AKRO"]
percent = 0.8

orlov_path = "/home/run/orlovbot/"
config_xml = ''
with open(orlov_path+'main.xml', 'r') as f:
    config_xml = ''.join(list(map(str.strip, f.readlines())))
config = xmltodict.parse(config_xml)

api_key = config['config']['api-key']
api_secret = config['config']['api-secret']
proxy = config['config']['proxy']

api_key_2 = config['config']['api-key2']
api_secret_2 = config['config']['api-secret2']
proxy_2 = config['config']['proxy2']

path = "/var/www/html/"

def log_time(string):
    print(str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]) + ': ' + string)
    
def set_pipe():
    global path
    f = open(path+'pipe4', 'w+')
    f.close() 

def check_pipe():
    global path
    return os.path.isfile(path+'pipe4')

def del_pipe():
    global path
    os.remove(path+'pipe4')

if check_pipe():
    log_time("Terminated")
    sys.exit()
        
set_pipe()

balance = 0 # размер позиции для лонга
balance_2 = 0 # размер позиции для лонга
min_balance = 50 # минимальный размер баланса, ниже которого повторная сделка не происходит (работает по линии balance_2)
short_balance = 0 # размер позиции для шорта
short_balance_2 = 0 # размер позиции для шорта

#summ = 60 #trade summ in dollars
leverage = 20
stop_percent = 0.2 #закрытие при цена после покупки + этот %
stop_percent_short = 1
short_timeout = 5*60 # задержка перед выставлением стоп-ордера шорт-позиции
trigger_percent = 1.7 # высота свечи в %. Выше этого значения лонг отменяется

# далее расписана сетка тейков

take_percent1 = 1.5
take_percent_summ1 = 30
take_percent2 = 1.53
take_percent_summ2 = 30
take_percent3 = 1.55
take_percent_summ3 = 20
take_percent4 = 1.6
take_percent_summ4 = 20


take_type = 'true' # установка reduceOnly для тейков
if short_balance:
    take_type = 'false'

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



stdout=path+'orlovbot4_out.log'
stderr=path+'orlovbot4_err.log'
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

if proxy_2:
    bclient_2 = Client(api_key_2, api_secret_2, {'proxies': proxies_2})
else:
    bclient_2 = Client(api_key_2, api_secret_2)

def binance_work(symbol, base_price, last_price):
    global short_balance
    log_time('Start binance(): ' + symbol)
    ##sys.stdout.flush()
    #base_price = float(base_price)
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
    try:
        bclient_2.futures_change_leverage(symbol=symbol, leverage=leverage)
    except:
        o=0
        #coins.append(j)
        #return 0
    """
    try:
        bclient_2.futures_change_margin_type(symbol=symbol, marginType='ISOLATED')
    except:
        o=0
    """
    ##bclient.futures_change_leverage(symbol=symbol, leverage=leverage)
    ##log_time('futures_change_leverage received')
    #bclient.futures_change_margin_type(symbol=symbol, marginType='ISOLATED')
    
    # получение начальной цены для работы
    #orderbook = bclient.get_ticker(symbol=symbol)
    ##orderbook = bclient.futures_orderbook_ticker(symbol=symbol)
   # print (orderbook)
   #sys.stdout.flush()
   # sys.exit()
    ##print("Price: "+ orderbook['askPrice'])
    ##last_price = orderbook['askPrice']
    
    if not last_price:
        print ("last_price error")
        sys.exit()
    print ('Base price: ' + str(base_price))
    #print ('Trigger percent: ' + str(trigger_percent))
    
    #last_price = float(last_price)
    #last_price = last_price + last_price/100*0.03
    print("Price: "+ str(last_price))
    # вычисление триггера для отмены лонга
    long_trigger = 0
    if base_price:
        tmp = base_price + base_price/100*trigger_percent
        if last_price > tmp:
            long_trigger = 1
    print ("Long trigger: " + str(long_trigger))
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
    balance = 1    
    # вычисление объёма монет
    amount = balance/last_price*leverage
    amount_first = amount/100*65
    amount_second = (amount - amount_first)/100*75
    amount_2 = balance_2/last_price*leverage
    amount_2_first = amount_2/100*65
    amount_2_second = (amount_2 - amount_2_first)/100*75
    
    # определение необходимой точности
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
    #sys.stdout.flush()
    #sys.exit()
    
    if not long_trigger and balance:    
        # покупка по рынку
        #print("base_price: "+str(base_price))
        log_time('Buy start')
        #sys.stdout.flush()
        #sys.exit()
        long = 1
        my = 0
        nomy = 0
        if (1):
            try:            
                order_2 = bclient_2.futures_create_order ( 
                    symbol=symbol,
                    type='MARKET',
                    side='BUY',
                    quantity=amount_2_first,
                    isIsolated='TRUE'
                )
                print(order_2)
                #sys.exit()
                my = my + 1
            except:
                g=0
            try:
                order = bclient.futures_create_order ( 
                    symbol=symbol,
                    type='MARKET',
                    side='BUY',
                    quantity=amount_first,
                    isIsolated='TRUE'
                )
                print(order)
                nomy = nomy + 1
            except:
                g=0

            try:
                order_2 = bclient_2.futures_create_order ( 
                    symbol=symbol,
                    type='MARKET',
                    side='BUY',
                    quantity=amount_2_second,
                    isIsolated='TRUE'
                )
                my = my + 2
            except:
                g=0

            try:
                order = bclient.futures_create_order ( 
                    symbol=symbol,
                    type='MARKET',
                    side='BUY',
                    quantity=amount_second,
                    isIsolated='TRUE'
                )
                nomy = nomy + 2
            except:
                g=0

        """
        except:
            log_time('Long except')
            
            long = 0
            sys.exit()
        """    
        log_time('Buy end')

        # получение цены монеты сразу после покупки
        orderbook = bclient_2.futures_orderbook_ticker(symbol=symbol)
        log_time('futures_orderbook_ticker end')
        last_price = orderbook['askPrice']
        log_time('Last price (after buy): ' + last_price)
        last_price = float(last_price)
 
    def short(price, amount, amount_2):
        #print ("Long amount: " + amount)
        print ("Short order price: " + price)
        bclient_2.futures_create_order (
            symbol=symbol, 
            type='LIMIT', 
            timeInForce='GTC',
            price=price,  # The price at which you wish to buy/sell, float
            side='SELL',  # Direction ('BUY' / 'SELL'), string
            quantity=amount_2  # Number of coins you wish to buy / sell, float
        ) 
        bclient.futures_create_order (
            symbol=symbol, 
            type='LIMIT', 
            timeInForce='GTC',
            price=price,  # The price at which you wish to buy/sell, float
            side='SELL',  # Direction ('BUY' / 'SELL'), string
            quantity=amount  # Number of coins you wish to buy / sell, float
        ) 
    def take(price, amount, amount_2, type):
        if float(amount_2):
            bclient_2.futures_create_order (
                symbol=symbol, 
                type='LIMIT', 
                timeInForce='GTC',
                price=price,  # The price at which you wish to buy/sell, float
                side='SELL',  # Direction ('BUY' / 'SELL'), string
                quantity=amount_2,  # Number of coins you wish to buy / sell, float
                reduceOnly=type
            )  
        if float(amount):
            bclient.futures_create_order (
                symbol=symbol, 
                type='LIMIT', 
                timeInForce='GTC',
                price=price,  # The price at which you wish to buy/sell, float
                side='SELL',  # Direction ('BUY' / 'SELL'), string
                quantity=amount,  # Number of coins you wish to buy / sell, float
                reduceOnly=type
            )  
            
 
 
    if not long_trigger and balance:         
        amount = 0
        if nomy == 1:
            amount = float(amount_first)
        elif nomy == 2:
            amount = float(amount_second)
        elif nomy == 3:
            amount = float(amount_first) + float(amount_second)
        amount_2 = 0
        if my == 1:
            amount_2 = float(amount_2_first)
        elif my == 2:
            amount_2 = float(amount_2_second)
        elif my == 3:
            amount_2 = float(amount_2_first) + float(amount_2_second)
        # установка сетки ордеров
        ### 1
        amount1 = amount/100*take_percent_summ1
        amount1_2 = amount_2/100*take_percent_summ1
        tmp_amount = amount1
        precision = 0
        if amount1 < 1:
            precision = 4
        amount1 = "{:0.0{}f}".format(amount1, precision)
        print ("Amount1: "+ str(amount1)) 
        tmp_amount_2 = amount1_2
        precision = 0
        if amount1_2 < 1:
            precision = 4
        amount1_2 = "{:0.0{}f}".format(amount1_2, precision)
        print ("Amount1_2: "+ str(amount1_2)) 
        #вычисление цены для тейка
        take_price1 = last_price + last_price/100*take_percent1
        take_price1 = "{:0.0{}f}".format(take_price1, precision_price)
        print('Take price1: ' + str(take_price1)) 
        sys.stdout.flush()    
        #установка тейк-профита
        take(take_price1, amount1, amount1_2, take_type)

        log_time('take1 end')
        ### 2
        amount2 = amount/100*take_percent_summ2
        tmp_amount = tmp_amount + amount2
        precision = 0
        if amount2 < 1:
            precision = 4
        amount2 = "{:0.0{}f}".format(amount2, precision)
        print ("Amount2: "+ str(amount2)) 
        amount2_2 = amount_2/100*take_percent_summ2
        tmp_amount_2 = tmp_amount_2 + amount2_2
        precision = 0
        if amount2_2 < 1:
            precision = 4
        amount2_2 = "{:0.0{}f}".format(amount2_2, precision)
        print ("Amount2_2: "+ str(amount2_2)) 
        #вычисление цены для тейка
        take_price2 = last_price + last_price/100*take_percent2
        take_price2 = "{:0.0{}f}".format(take_price2, precision_price)
        print('Take price2: ' + str(take_price2)) 
        sys.stdout.flush()    
        #установка тейк-профита
        take(take_price2, amount2, amount2_2, take_type)            
        
        log_time('take2 end')
        ### 3
        amount3 = amount/100*take_percent_summ3
        tmp_amount = tmp_amount + amount3
        precision = 0
        if amount3 < 1:
            precision = 4
        amount3 = "{:0.0{}f}".format(amount3, precision)
        print ("Amount3: "+ str(amount3)) 
        amount3_2 = amount_2/100*take_percent_summ3
        tmp_amount_2 = tmp_amount_2 + amount3_2
        precision = 0
        if amount3_2 < 1:
            precision = 4
        amount3_2 = "{:0.0{}f}".format(amount3_2, precision)
        print ("Amount3_2: "+ str(amount3_2)) 
        #вычисление цены для тейка
        take_price3 = last_price + last_price/100*take_percent3
        take_price3 = "{:0.0{}f}".format(take_price3, precision_price)
        print('Take price3: ' + str(take_price3)) 
        sys.stdout.flush()    
        #установка тейк-профита
        take(take_price3, amount3, amount3_2, take_type)

        log_time('take3 end')
        #полное закрытие
        if not short_balance:
            amount4 = float(amount1) + 1 # +1 для того, чтобы точно закрылся весь ордер
            amount4_2 = float(amount1_2) + 1 # +1 для того, чтобы точно закрылся весь ордер
        else:
            amount4 = amount - tmp_amount
            amount4_2 = amount_2 - tmp_amount_2
        precision = 0
        if amount4 < 1:
            precision = 4
        amount4 = "{:0.0{}f}".format(amount4, precision)
        print ("Amount4: "+ str(amount4))     
        if amount4_2 < 1:
            precision = 4
        amount4_2 = "{:0.0{}f}".format(amount4_2, precision)
        print ("Amount4_2: "+ str(amount4_2))     
        #вычисление цены для тейка
        take_price4 = last_price + last_price/100*take_percent4
        take_price4 = "{:0.0{}f}".format(take_price4, precision_price)
        print('Take price4: ' + str(take_price4)) 
        sys.stdout.flush()      
        # установка тейк-профита
        take(take_price4, amount4, amount4_2, take_type)

        log_time('Last take end')
 
        #вычисление цены для стоп-лосса
        stop_price = last_price + last_price/100*stop_percent
        stop_price_0 = stop_price
        #if stop_price > 1:
        #if stop_price < 1:
        #    precision = 4
        
        # установка стоп-ордера
        time_start = time.time()
        time_end = time_start + 5
        tmp_price = last_price
        old_price = last_price
        while time_start < time_end or old_price <= tmp_price:
            # получение цены монеты сразу после покупки
            orderbook = bclient_2.futures_orderbook_ticker(symbol=symbol)
            old_price = tmp_price
            tmp_price = orderbook['askPrice']
            log_time('TMP price (sleep 2): ' + tmp_price)
            tmp_price = float(tmp_price)
            tmp_stop_price = tmp_price - tmp_price/100*0.2
            if tmp_stop_price > stop_price_0:
                stop_price = tmp_stop_price
                #stop_price_0 = tmp_stop_price
                log_time('STOP price (sleep 2): ' + str(stop_price))
            
            time_start = time.time()

        stop_price_0 = "{:0.0{}f}".format(stop_price_0, precision_price)
        print('Stop price0: ' + stop_price_0)
        stop_price = "{:0.0{}f}".format(stop_price, precision_price)
        print('Stop price: ' + stop_price)
       
        flag_stop = 0
        try:
            g = 1/0
            stop_order_2 = bclient_2.futures_create_order (
                symbol=symbol, 
                side='SELL', 
                type='STOP_MARKET', 
                stopPrice=stop_price,
                closePosition='true'
            )
        except:
            flag_stop = 1
            try:
                stop_order_2 = bclient_2.futures_create_order (
                    symbol=symbol, 
                    side='SELL', 
                    type='STOP_MARKET', 
                    stopPrice=stop_price_0,
                    closePosition='true'
                )
            except:
                flag_stop = 2
                stop_order_2 = bclient_2.futures_create_order (
                    symbol=symbol, 
                    side='SELL', 
                    type='MARKET',
                    quantity=amount_2,                    
                    reduceOnly='true'
                )
            
        try:
            if flag_stop:
                g = 1/0
            stop_order = bclient.futures_create_order (
                symbol=symbol, 
                side='SELL', 
                type='STOP_MARKET', 
                stopPrice=stop_price,
                closePosition='true'
            )
        except:
            try:
                if flag_stop == 2:
                    g = 1/0                
                stop_order = bclient.futures_create_order (
                    symbol=symbol, 
                    side='SELL', 
                    type='STOP_MARKET', 
                    stopPrice=stop_price_0,
                    closePosition='true'
                )
            except:
                stop_order = bclient.futures_create_order (
                    symbol=symbol, 
                    side='SELL', 
                    type='MARKET',
                    quantity=amount,                    
                    reduceOnly='true'
                )                
            
        log_time('stop_order end')
        sys.stdout.flush()

   # блок шортовой работы
    if (short_balance and base_price) or (not my and not nomy):
        if not my and not nomy:
            short_balance = amount
            short_balance_2 = amount_2
        # Рассчёт ордеров для шортов
        short_price1 = base_price+base_price/100*short_percent1
        short_price1 = "{:0.0{}f}".format(short_price1, precision_price)
        short_price2 = base_price+base_price/100*short_percent2
        short_price2 = "{:0.0{}f}".format(short_price2, precision_price)
        short_price3 = base_price+base_price/100*short_percent3
        stop_price_short = short_price3 + short_price3/100*stop_percent_short  # вычисление уровня стоп ордера для шорта  
        short_price3 = "{:0.0{}f}".format(short_price3, precision_price)
        stop_price_short = "{:0.0{}f}".format(stop_price_short, precision_price)
        short_price4 = base_price+base_price/100*short_percent4
        short_amount = short_balance/short_price4*leverage # вычисление объёма монет для шорта
        short_amount_2 = short_balance_2/short_price4*leverage # вычисление объёма монет для шорта
        short_price4 = "{:0.0{}f}".format(short_price4, precision_price)
        short_price5 = base_price+base_price/100*short_percent5
        short_price5 = "{:0.0{}f}".format(short_price5, precision_price)
        short_price6 = base_price+base_price/100*short_percent6
        short_price6 = "{:0.0{}f}".format(short_price6, precision_price)
        
        short_amount1 = short_amount/100*short_percent_summ1
        short_amount2 = short_amount/100*short_percent_summ2
        short_amount3 = short_amount/100*short_percent_summ3
        short_amount4 = short_amount/100*short_percent_summ4
        short_amount5 = short_amount/100*short_percent_summ5
        tmp_amount = short_amount1 + short_amount2 + short_amount3 + short_amount4 + short_amount5
        short_amount6 = short_amount - tmp_amount
        short_amount1_2 = short_amount_2/100*short_percent_summ1
        short_amount2_2 = short_amount_2/100*short_percent_summ2
        short_amount3_2 = short_amount_2/100*short_percent_summ3
        short_amount4_2 = short_amount_2/100*short_percent_summ4
        short_amount5_2 = short_amount_2/100*short_percent_summ5
        tmp_amount_2 = short_amount1_2 + short_amount2_2 + short_amount3_2 + short_amount4_2 + short_amount5_2
        short_amount6_2 = short_amount_2 - tmp_amount_2
        
        precision = 0
        if short_amount < 1:
            precision = 4
        short_amount1 = "{:0.0{}f}".format(short_amount1, precision)
        short_amount2 = "{:0.0{}f}".format(short_amount2, precision)
        short_amount3 = "{:0.0{}f}".format(short_amount3, precision)
        short_amount4 = "{:0.0{}f}".format(short_amount4, precision)
        short_amount5 = "{:0.0{}f}".format(short_amount5, precision)
        short_amount6 = "{:0.0{}f}".format(short_amount6, precision)
        precision = 0
        if short_amount_2 < 1:
            precision = 4
        short_amount1_2 = "{:0.0{}f}".format(short_amount1_2, precision)
        short_amount2_2 = "{:0.0{}f}".format(short_amount2_2, precision)
        short_amount3_2 = "{:0.0{}f}".format(short_amount3_2, precision)
        short_amount4_2 = "{:0.0{}f}".format(short_amount4_2, precision)
        short_amount5_2 = "{:0.0{}f}".format(short_amount5_2, precision)
        short_amount6_2 = "{:0.0{}f}".format(short_amount6_2, precision)
          
        short(short_price1, short_amount1, short_amount1_2)
        short(short_price2, short_amount2, short_amount2_2)
        short(short_price3, short_amount3, short_amount3_2)
        short(short_price4, short_amount4, short_amount4_2)
        short(short_price5, short_amount5, short_amount5_2)
        short(short_price6, short_amount6, short_amount6_2)

    if not long_trigger and balance and 0: 
        time.sleep(10)
        # отмена стоп ордера
        ##bclient.futures_cancel_order(symbol=symbol, orderId=stop_order["orderId"])
        ##log_time('futures_cancel_order end')
        #вычисление цены для переноса стоп-лосса в безубыток
        stop_price = last_price + last_price/100*0.1
        stop_price2 = stop_price
        #if stop_price < 1:
        #    precision = 4
        stop_price = "{:0.0{}f}".format(stop_price, precision_price)
        print('Stop price2: ' + stop_price)
        
        # получение цены монеты 
        orderbook = bclient_2.futures_orderbook_ticker(symbol=symbol)
        new_price = orderbook['askPrice']
        new_price = float(new_price)
        if new_price > stop_price2:        
            # установка нового стоп-ордера
            bclient.futures_create_order (
                symbol=symbol, 
                side='SELL', 
                type='STOP_MARKET', 
                stopPrice=stop_price,
                closePosition='true'
            )    
        sys.stdout.flush()   
        log_time('futures_create_order(2) end')

    # установка стопа на шорт-блок
    """
    if short_balance and base_price:
        ta = short_timeout/60
        print('Stop price SHORT: ' + stop_price_short+ '. Wait for ' + str(ta) + ' min...')
        sys.stdout.flush()   
        time.sleep(short_timeout)
        # установка стоп-ордера
        bclient.futures_create_order (
            symbol=symbol, 
            side='BUY', 
            type='STOP_MARKET', 
            stopPrice=stop_price_short,
            closePosition='true'
        )    
        log_time('futures_create_order(short) end')
    """
    #time.sleep(60)
    print ("---------------------------------------------------")
    

for h in coins:
    if os.path.isfile(orlov_path+"bot/"+h):
        coins.remove(h)
        continue
for h in coins:
    if os.path.isfile(orlov_path+"bot/"+h):
        coins.remove(h)
        continue


def binance():
    global coins
    #log_time('Start binance(): ' + symbol)
    #base_price = float(base_price)
 
#    coins = ["BZRX", "STMX", "SFP", "LIT", "BEL", "SKL", "BTS", "UNFI", "KEEP", "CTK", "LINA", "ATA", "GTC", "AKRO"]
    
    # получение начальной цен
    #prices = bclient.get_all_tickers()
    prices = bclient_2.futures_orderbook_ticker()
    for i in prices:
        tmp = i.get('symbol')
        for j in coins:
            #if os.path.isfile(orlov_path+"bot/"+j):
            #    coins.remove(j)
            #    continue
            tmp2 = j + 'USDT'
            if tmp == tmp2:
                str0 = ''
                try:
                    f = open(orlov_path+'coins/'+j+'-old', 'r+')
                    str0 = f.read()
                    f.close()
                except:
                    f = open(orlov_path+'coins2/'+j+'-old', 'r+')
                    str0 = f.read()
                    f.close()
                old_price = float(str0)
                price = float(i.get('askPrice'))
                tmp = old_price + old_price/100*percent
                tmp_error = old_price + old_price/100*(percent + 0.925)
                if price >= tmp and price < tmp_error:
                    f = open(orlov_path+"bot/"+j, 'w+')
                    f.write(str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]) + ': ' + str(old_price)+' - '+str(price)+"\n")
                    f.close()
                    
                    binance_work(tmp2, old_price, price)
                    coins.remove(j)
                    b = 0
                    while balance_2 < min_balance and b < 60:
                        get_balance()
                        time.sleep(1)
                        b = b + 1
                    if b >= 60:
                        print ("Bot stopped normal")
                        del_pipe()
                        sys.exit()
                    break
#                    del_pipe()
#                    sys.exit()
                """
                if price >= tmp_error and 0: # если цена выше допустимого проскальзывания, то только шорт
                    #balance = 0
                    f = open(orlov_path+"bot/"+j, 'w+')
                    f.write(str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]) + ': ' + str(old_price)+' - '+str(price)+"\n")
                    f.close()
                    log_time('price '+str(price)+' >= tmp_error ' + str(tmp_error) + '. Short only.')
                    binance_work(tmp2, old_price, price)
                    coins.remove(j)
                    b = 0
                    while balance_2 < min_balance and b < 60:
                        get_balance()
                        time.sleep(1)
                        b = b + 1
                    if b >= 60:
                        print ("Bot stopped normal")
                        del_pipe()
                        sys.exit()
                """
                tmp2 = old_price + old_price/100*0.7
                if price >= tmp2 and price < tmp:
                    f = open(orlov_path+"bot/"+j+'-07', 'w+')
                    f.write(str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]) + ': ' + str(old_price)+' - '+str(price)+"\n")
                    f.close()                   
                    coins.remove(j)
                    break
                tmp3 = old_price + old_price/100*0.6
                if price >= tmp3 and price < tmp2:
                    f = open(orlov_path+"bot/"+j+'-06', 'w+')
                    f.write(str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]) + ': ' + str(old_price)+' - '+str(price)+"\n")
                    f.close() 
                    coins.remove(j)
                    break
                tmp4 = old_price + old_price/100*0.5
                if price >= tmp4 and price < tmp3:
                    f = open(orlov_path+"bot/"+j+'-05', 'w+')
                    f.write(str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]) + ': ' + str(old_price)+' - '+str(price)+"\n")
                    f.close()   
                    coins.remove(j)
                    break

def get_balance():
    global balance
    global balance_2
    balance_raw = ''
    balance_raw_2 = ''
    try:
        balance_raw = bclient.futures_account_balance()
        balance_raw_2 = bclient_2.futures_account_balance()
    except:
        log_time('Balance getting error 1')
        flag = 0
        while not flag:
            try:
                balance_raw = bclient.futures_account_balance()
                balance_raw_2 = bclient_2.futures_account_balance()
                flag = 1
            except:
                log_time('Balance getting error 2')
                time.sleep(1)
    if not balance_raw or not balance_raw_2:
        print ("balance_raw error. Exit.")
        sys.exit()
    balance_str = ''
    for item in balance_raw:
        if item['asset'] == 'USDT':
            balance_str = item['balance']  
    if not balance_str:
        print ('Error getting balance')
        sys.exit()
    if not balance:
        balance = float(balance_str)
    log_time('>> Balance: ' + balance_str)
    for item in balance_raw_2:
        if item['asset'] == 'USDT':
            balance_str_2 = item['balance']  
    if not balance_str_2:
        print ('Error getting balance 2')
        sys.exit()
    log_time('>> Balance 2: ' + balance_str_2)
    if not balance_2:
        balance_2 = float(balance_str_2)
    sys.stdout.flush()     
    
# =======================================================================
        

sys.stderr.flush()
with open(stderr, 'a+') as stderr:
    os.dup2(stderr.fileno(), sys.stderr.fileno())

sys.stdout.flush()
    ##print(4)
with open(stdout, 'a+') as stdout:
    os.dup2(stdout.fileno(), sys.stdout.fileno())

#bot.polling(none_stop=True, interval=0)

#client = TelegramClient('X100TradingBot', api_id, api_hash)
get_balance()
#@client.on(events.NewMessage(pattern=r'Покупаю\s\#|orlovbot'))
if 1:
#async def normal_handler(event):

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
            #sys.stdout.flush()
            time.sleep(0.2)            
#        del_pipe()
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




