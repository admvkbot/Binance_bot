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
                j = re.match(r'(\w+)USDT', tmp).group(1)
                try:
                    klines = bclient.get_historical_klines(j+'USDT', Client.KLINE_INTERVAL_1MINUTE, "20 min ago UTC", klines_type=HistoricalKlinesType.FUTURES)
                    #print (klines)
                    i = 10
                    i0 = i
                    volume_sum = 0
                    while i < len(klines)-2:
                        volume_sum = volume_sum + float(klines[i][7])
                        i = i + 1
                    volume = volume_sum / (i-i0)
                    
                    #print (volume)
                    #sys.stdout.flush()
                    
                    f = open(orlov_path+'coins2/'+j+'-vol', 'w+')
                    f.write(str(volume))
                    f.close() 
                    
                    
                    
                    i = 0
                    red_max = 0
                    while i < len(klines)-11:
                        kline_in = float(klines[i][1])
                        kline_max = float(klines[i][2])
                        kline_min = float(klines[i][3])
                        kline_out = float(klines[i][4])
                        kline_height = kline_out - kline_in
                        kline_height_perc = kline_height/kline_in*100
                        if kline_height < 0:                            
                            if red_max < abs(kline_height_perc):
                                red_max = abs(kline_height_perc)
                        i = i+1
                    i = 13
                    i0 = i
                    count_green = 0
                    count_red = 0
                    kline_height_perc_max = 0
                    proc_0 = 0
                    proc_7 = 0
                    proc_8 = 0
                    proc_red = 0
                    #print (len(klines))
                    #sys.stdout.flush()
                    #sys.exit()
                    while i < len(klines)-1:
                        kline_in = float(klines[i][1])
                        kline_max = float(klines[i][2])
                        kline_min = float(klines[i][3])
                        kline_out = float(klines[i][4])
                        kline_height = kline_out - kline_in
                        kline_height_perc = kline_height/kline_in*100
                        if kline_height > 0:
                            count_green = count_green + 1
                        else:
                            count_red = count_red + 1
                            proc_red = abs(kline_height_perc)
                        if kline_height_perc > 0 and i == i0:
                            proc_0 = kline_height_perc
                        if kline_height_perc > 0.05 and i == 7:
                            proc_7 = kline_height_perc
                        if kline_height_perc > 0.1 and i == 8:
                            proc_8 = kline_height_perc
                        abs_kline_height_perc = abs(kline_height_perc)
                        if abs_kline_height_perc > kline_height_perc_max:
                            kline_height_perc_max = abs_kline_height_perc
                        i = i+1
                    if count_red < 2 and kline_height_perc_max < 0.5 and proc_0 and proc_7 and proc_8 and proc_8 > proc_7 and proc_red < 0.1 and red_max < 0.7:
                        log_time (j+ " 7 - " +str(proc_7))
                        log_time (j+ " 8 - " +str(proc_8))
                        sys.stdout.flush()
                        f = open(orlov_path+'coins2/'+j+'-long', 'w+')
                        f.write('1')
                        f.close() 
                    else:
                        f = open(orlov_path+'coins2/'+j+'-long', 'w+')
                        f.write('0')
                        f.close() 
                        
                except:                    
                    f = open(orlov_path+'coins2/'+j+'-vol', 'w+')
                    f.write('0')
                    f.close() 
                    f = open(orlov_path+'coins2/'+j+'-long', 'w+')
                    f.write('0')
                    f.close() 

                try:
                    klines = bclient.get_historical_klines(j+'USDT', Client.KLINE_INTERVAL_1HOUR, "3 day ago UTC", klines_type=HistoricalKlinesType.FUTURES)
                    #print (klines)
                    i = 0
                    volume_sum = 0
                    while i < len(klines)-1:
                        volume_sum = volume_sum + float(klines[i][7])
                        i = i + 1
                    volume = (volume_sum / i)/60
                    f = open(orlov_path+'coins2/'+j+'-vold', 'w+')
                    f.write(str(volume))
                    f.close() 
                    i = 44
                    i0 = i
                    volume_sum = 0
                    h3_min = 0
                    while i < len(klines)-1:
                        volume_sum = volume_sum + float(klines[i][7])
                        min_kline = float(klines[i][3])
                        if h3_min < min_kline or h3_min == 0:
                            h3_min = min_kline
                        i = i + 1
                    volume = (volume_sum / (i-i0))/60
                    f = open(orlov_path+'coins2/'+j+'-vol3h', 'w+')
                    f.write(str(volume))
                    f.close() 
                    f = open(orlov_path+'coins2/'+j+'-min3h', 'w+')
                    f.write(str(h3_min))
                    f.close() 
                    
                    i = 46
                    i0 = i
                    volume_sum = 0
                    while i < len(klines)-1:
                        volume_sum = volume_sum + float(klines[i][7])
                        i = i + 1
                    volume = (volume_sum / (i-i0))/60
                    f = open(orlov_path+'coins2/'+j+'-vol1h', 'w+')
                    f.write(str(volume))
                    f.close() 
                except:                    
                    f = open(orlov_path+'coins2/'+j+'-vold', 'w+')
                    f.write('0')
                    f.close() 
                    f = open(orlov_path+'coins2/'+j+'-vol3h', 'w+')
                    f.write('0')
                    f.close() 
                    f = open(orlov_path+'coins2/'+j+'-min3h', 'w+')
                    f.write('0')
                    f.close() 
                    f = open(orlov_path+'coins2/'+j+'-vol1h', 'w+')
                    f.write('0')
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
            time.sleep(0.5)
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




