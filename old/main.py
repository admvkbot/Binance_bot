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

config_xml = ''
with open('/home/run/orlovbot/main.xml', 'r') as f:
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
    f = open(path+'pipe', 'w+')
    f.close() 

def check_pipe():
    global path
    return os.path.isfile(path+'pipe')

def del_pipe():
    global path
    os.remove(path+'pipe')

if check_pipe():
    log_time("Terminated")
    sys.exit()
        
set_pipe()

coin = sys.argv[1]
base_price = sys.argv[2]

if not coin:
    print ("Forgot COIN")
    sys.exit()
    
#summ = 60 #trade summ in dollars
leverage = 20
stop_percent = 0.3 #закрытие при уменьшении цены на этот %
stop_percent_short = 1
short_timeout = 5*60 # задержка перед выставлением стоп-ордера шорт-позиции
trigger_percent = 4 # высота свечи в %. Выше этого значения лонг отменяется

# далее расписана сетка тейков
take_percent1 = 1.3
take_percent_summ1 = 30
take_percent2 = 1.8
take_percent_summ2 = 30
take_percent3 = 2.2
take_percent_summ3 = 20
take_percent4 = 2.7
take_percent_summ4 = 20

balance = 0 # размер позиции для лонга
short_balance = 900 # размер позиции для шорта

take_type = 'true' # установка reduceOnly для тейков
if short_balance:
    take_type = 'false'

# далее расписана сетка шортов
short_percent1 = 5.5
short_percent_summ1 = 20
short_percent2 = 5.6
short_percent_summ2 = 20
short_percent3 = 5.7
short_percent_summ3 = 20
short_percent4 = 5.8
short_percent_summ4 = 20
short_percent5 = 5.9
short_percent_summ5 = 10
short_percent6 = 6
short_percent_summ6 = 10


stdout=path+'orlovbot_out.log'
stderr=path+'orlovbot_err.log'
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

def binance(symbol, base_price):
    log_time('Start binance(): ' + symbol)
    base_price = float(base_price)
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
    bclient.futures_change_leverage(symbol=symbol, leverage=leverage)
    log_time('futures_change_leverage received')
    #bclient.futures_change_margin_type(symbol=symbol, marginType='ISOLATED')
    
    # получение начальной цены для работы
    orderbook = bclient.get_ticker(symbol=symbol)
    print("Price: "+ orderbook['lastPrice'])
    last_price = orderbook['lastPrice']
    
    if not last_price:
        print ("last_price error")
        sys.exit()
    print ('Base price: ' + str(base_price))
    print ('Trigger percent: ' + str(trigger_percent))
    
    last_price = float(last_price)
    # вычисление триггера для отмены лонга
    long_trigger = 0
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
        
    # вычисление объёма монет
    amount = balance/last_price*leverage
    #amount = balance/last_price
    
    # определение необходимой точности
    precision = 0
    if amount < 1:
        precision = 4
    amount = "{:0.0{}f}".format(amount, precision)
    print ("Amount: "+ str(amount))
    sys.stdout.flush()
    #sys.exit()
    
    if not long_trigger and balance:    
        # покупка по рынку
        print("base_price: "+str(base_price))
        log_time('Buy start')
        long = 1
        if (1):
        #try:
            order = bclient.futures_create_order ( 
                symbol=symbol,
                type='MARKET',
                side='BUY',
                quantity=amount,
                isIsolated='TRUE'
            )
        """
        except:
            log_time('Long except')
            
            long = 0
            sys.exit()
        """    
        log_time('Buy end')

        # получение цены монеты сразу после покупки
        orderbook = bclient.get_ticker(symbol=symbol)
        log_time('get_ticker end')
        last_price = orderbook['lastPrice']
        last_price = float(last_price)
 
    def short(price, amount):
        print ("Log amount: " + amount)
        print ("Log price: " + price)
        bclient.futures_create_order (
            symbol=symbol, 
            type='LIMIT', 
            timeInForce='GTC',
            price=price,  # The price at which you wish to buy/sell, float
            side='SELL',  # Direction ('BUY' / 'SELL'), string
            quantity=amount  # Number of coins you wish to buy / sell, float
        ) 
    def take(price, amount, type):
        bclient.futures_create_order (
            symbol=symbol, 
            type='LIMIT', 
            timeInForce='GTC',
            price=price,  # The price at which you wish to buy/sell, float
            side='SELL',  # Direction ('BUY' / 'SELL'), string
            quantity=amount,  # Number of coins you wish to buy / sell, float
            reduceOnly=type
        )  
            
    # блок шортовой работы
    if short_balance:
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
        
        precision = 0
        if short_amount < 1:
            precision = 4
        short_amount1 = "{:0.0{}f}".format(short_amount1, precision)
        short_amount2 = "{:0.0{}f}".format(short_amount2, precision)
        short_amount3 = "{:0.0{}f}".format(short_amount3, precision)
        short_amount4 = "{:0.0{}f}".format(short_amount4, precision)
        short_amount5 = "{:0.0{}f}".format(short_amount5, precision)
        short_amount6 = "{:0.0{}f}".format(short_amount6, precision)
          
        short(short_price1, short_amount1)
        short(short_price2, short_amount2)
        short(short_price3, short_amount3)
        short(short_price4, short_amount4)
        short(short_price5, short_amount5)
        short(short_price6, short_amount6)
 
    if not long_trigger and balance: 
        #вычисление цены для стоп-лосса
        stop_price = last_price - last_price/100*stop_percent
        #if stop_price > 1:
        #if stop_price < 1:
        #    precision = 4
        stop_price = "{:0.0{}f}".format(stop_price, precision_price)
        print('Stop price: ' + str(stop_price))
        sys.stdout.flush()
        
        # установка стоп-ордера
        stop_order = bclient.futures_create_order (
            symbol=symbol, 
            side='SELL', 
            type='STOP_MARKET', 
            stopPrice=stop_price,
            closePosition='true'
        )
        log_time('stop_order end')
        amount = float(amount)
        # установка сетки ордеров
        ### 1
        amount1 = amount/100*take_percent_summ1
        tmp_amount = amount1
        precision = 0
        if amount1 < 1:
            precision = 4
        amount1 = "{:0.0{}f}".format(amount1, precision)
        print ("Amount1: "+ str(amount1)) 
        #вычисление цены для тейка
        take_price1 = last_price + last_price/100*take_percent1
        take_price1 = "{:0.0{}f}".format(take_price1, precision_price)
        print('Take price1: ' + str(take_price1)) 
        sys.stdout.flush()    
        #установка тейк-профита
        take(take_price1, amount1, take_type)

        log_time('take1 end')
        ### 2
        amount2 = amount/100*take_percent_summ2
        tmp_amount = tmp_amount + amount2
        precision = 0
        if amount2 < 1:
            precision = 4
        amount2 = "{:0.0{}f}".format(amount2, precision)
        print ("Amount2: "+ str(amount2)) 
        #вычисление цены для тейка
        take_price2 = last_price + last_price/100*take_percent2
        take_price2 = "{:0.0{}f}".format(take_price2, precision_price)
        print('Take price2: ' + str(take_price2)) 
        sys.stdout.flush()    
        #установка тейк-профита
        take(take_price2, amount2, take_type)            
        
        log_time('take2 end')
        ### 3
        amount3 = amount/100*take_percent_summ3
        tmp_amount = tmp_amount + amount3
        precision = 0
        if amount3 < 1:
            precision = 4
        amount3 = "{:0.0{}f}".format(amount3, precision)
        print ("Amount3: "+ str(amount3)) 
        #вычисление цены для тейка
        take_price3 = last_price + last_price/100*take_percent3
        take_price3 = "{:0.0{}f}".format(take_price3, precision_price)
        print('Take price3: ' + str(take_price3)) 
        sys.stdout.flush()    
        #установка тейк-профита
        take(take_price3, amount3, take_type)

        log_time('take3 end')
        #полное закрытие
        if not short_balance:
            amount4 = float(amount1) + 1 # +1 для того, чтобы точно закрылся весь ордер
        else:
            amount4 = amount - tmp_amount
        precision = 0
        if amount4 < 1:
            precision = 4
        amount4 = "{:0.0{}f}".format(amount4, precision)
        print ("Amount4: "+ str(amount4))     
        #вычисление цены для тейка
        take_price4 = last_price + last_price/100*take_percent4
        take_price4 = "{:0.0{}f}".format(take_price4, precision_price)
        print('Take price4: ' + str(take_price4)) 
        sys.stdout.flush()      
        # установка тейк-профита
        take(take_price4, amount4, take_type)

        log_time('Last take end')
  
        
        time.sleep(20)
        # отмена стоп ордера
        bclient.futures_cancel_order(symbol=symbol, orderId=stop_order["orderId"])
        log_time('futures_cancel_order end')
        #вычисление цены для переноса стоп-лосса в безубыток
        stop_price = last_price + last_price/100*0.1
        #if stop_price < 1:
        #    precision = 4
        stop_price = "{:0.0{}f}".format(stop_price, precision_price)
        print('Stop price2: ' + str(stop_price))
        sys.stdout.flush()   
        # установка нового стоп-ордера
        bclient.futures_create_order (
            symbol=symbol, 
            side='SELL', 
            type='STOP_MARKET', 
            stopPrice=stop_price,
            closePosition='true'
        )    
        log_time('futures_create_order(2) end')

    # установка стопа на шорт-блок
    if short_balance:
        time.sleep(short_timeout)
        print('Stop price short: ' + stop_price_short)
        sys.stdout.flush()   
        # установка стоп-ордера
        bclient.futures_create_order (
            symbol=symbol, 
            side='BUY', 
            type='STOP_MARKET', 
            stopPrice=stop_price_short,
            closePosition='true'
        )    
        log_time('futures_create_order(short) end')


    print ("---------------------------------------------------")
    
    
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
        binance(coin, base_price)
        sys.stdout.flush()
        time.sleep(60*15)
        del_pipe()
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




