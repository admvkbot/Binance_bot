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
from binance.enums import HistoricalKlinesType

orlov_path = "/home/run/orlovbot/"
config_xml = ''
with open(orlov_path+'main.xml', 'r') as f:
    config_xml = ''.join(list(map(str.strip, f.readlines())))
config = xmltodict.parse(config_xml)

api_key = config['config']['api-key2']
api_secret = config['config']['api-secret2']
proxy = config['config']['proxy2']

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

def binance():
    #log_time('Start binance(): ' + symbol)
    #base_price = float(base_price)
    
 
    coins = ["BZRX", "STMX", "SFP", "LIT", "BEL", "BLZ", "SKL", "BTS", "UNFI", "KEEP", "CTK", "LINA", "LUNA", "NKN", "GALA"]
    
    # получение начальной цен
    prices = bclient.futures_orderbook_ticker()
    #print(prices)
    #sys.stdout.flush()
    #sys.exit()
    #prices = bclient.get_all_tickers()
    for i in prices:
        if 1:
        #for j in coins:
            tmp = i.get('symbol')
            #tmp2 = j + 'USDT'
            #if tmp == tmp2:
            if re.search(r'USDT$', tmp):
                pr = i.get('askPrice')
                j = re.match(r'(\w+)USDT', tmp).group(1)
            #if 1:
                try:
                    f = open(orlov_path+'coins2/'+j+'-old2', 'r+')
                    str000 = f.read()
                    f.close() 
                    f = open(orlov_path+'coins2/'+j+'-old', 'r+')
                    str00 = f.read()
                    f.close() 
                    f = open(orlov_path+'coins2/'+j+'', 'r+')
                    str0 = f.read()
                    f.close() 		    
                    fstr0 = float(str0)
                    fstr00 = float(str00)
                    fstr000 = float(str000)
                    fpr = float(pr)
                    m = (fstr0+fstr00)/2
                    if fstr0 > fstr00 and fstr00 > fstr000 and fpr > fstr0:
                        m = (fstr0+fstr00+fstr000)/3
                    f = open(orlov_path+'coins2/'+j+'-old', 'w+')
                    f.write(str(m))
#                    f.write(str0)
                    f.close() 
                    f = open(orlov_path+'coins2/'+j+'-old2', 'w+')
                    f.write(str00)
                    f.close() 
                except:                    
                    f = open(orlov_path+'coins2/'+j+'-old2', 'w+')
                    f.write(pr)
                    f.close() 
                    f = open(orlov_path+'coins2/'+j+'-old', 'w+')
                    f.write(pr)
                    f.close() 
                f = open(orlov_path+'coins2/'+j, 'w+')
                f.write(pr)
                f.close() 
    
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
            time.sleep(60)
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




