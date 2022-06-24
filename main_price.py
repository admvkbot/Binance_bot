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

api_key = config['config']['api-key']
api_secret = config['config']['api-secret']
proxy = config['config']['proxy']

path = "/var/www/html/"

def log_time(string):
    print(str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]) + ': ' + string)
    
def set_pipe():
    global path
    f = open(path+'pipe3', 'w+')
    f.close() 

def check_pipe():
    global path
    return os.path.isfile(path+'pipe3')

def del_pipe():
    global path
    os.remove(path+'pipe3')

if check_pipe():
    log_time("Terminated")
    sys.exit()
        
set_pipe()


stdout=path+'orlovbot3_out.log'
stderr=path+'orlovbot3_err.log'
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
    
 
    coins = ["CELO", "SNX", "TOMO", "TRB", "XEM", "XTZ", "ZRX",
        "HOT", "KNC", "LPT", "LTC", "MANA", "MKR", "OGN", "ONT", "RAY", "REEF", "REN", "RLC", "RVN", "SC",
        "CELR", "CHR", "CHZ", "COTI", "CRV", "CTSI", "CVC", "DASH", "DENT", "DODO", "DYDX", "ETC", "FLM", "HNT", 
        "BAT", "BAND", "ALGO", "ALICE", "BZRX", "SFP", "LIT", "BEL", "BLZ", "SKL", "BTS", "UNFI", "KEEP", 
        "CTK", "LINA", "NKN", "ATA", "AKRO", "GTC", "BTC", "ANKR", "NEAR", "ZEN", "LUNA", "MASK", "GALA", "RSR", 
        "FTM",  "GRT", "STMX", "RUNE", "OCEAN", "1000SHIB", "AUDIO", "IOST", "ZIL", "SUSHI", "TLM", "SAND", "NU", "ALPHA", "STORJ"]
    
    # получение начальной цен
    #prices = bclient.get_all_tickers()
    if 1:
    #for i in prices:
        #if 1:
        for j in coins:
            #print (j)
            #sys.stdout.flush()
            #tmp = i.get('symbol')
            #tmp2 = j + 'USDT'
            #if tmp == tmp2:
            #if re.search(r'USDT$', tmp):
             #   pr = i.get('price')
            #    j = re.match(r'(\w+)USDT', tmp).group(1)
            if 1:

                # вход, макс, мин, выход  
                klines = None
                #klines = bclient.get_historical_klines(j+'USDT', Client.KLINE_INTERVAL_1MINUTE, "5 min ago UTC", klines_type=HistoricalKlinesType.FUTURES)
                #print (klines)
                #sys.stdout.flush()
                try:
                    klines = bclient.get_historical_klines(j+'USDT', Client.KLINE_INTERVAL_1MINUTE, "10 min ago UTC", klines_type=HistoricalKlinesType.FUTURES)
                except:
                    log_time('klines error1')
                    sys.stdout.flush()
                    while not klines:
                        print ('NOT')
                        sys.stdout.flush()
                        try:
                            klines = bclient.get_historical_klines(j+'USDT', Client.KLINE_INTERVAL_1MINUTE, "10 min ago UTC", klines_type=HistoricalKlinesType.FUTURES)
                        except:
                            log_time('klines error2 '+j)
                            sys.stdout.flush()
                        time.sleep(0.1)
                n = 0
                kline_percent = 0
                for kline in klines:
                    kline_in = float(kline[1])
                    kline_max = float(kline[2])
                    kline_min = float(kline[3])
                    kline_out = float(kline[4])
                    #kline_percent = 0
                    #kline_height = kline_in - kline_min
                    """
                    if n >= 6 and n < 9:
###                        perc_kline = abs(kline_out-kline_in)/kline_in*100
                        perc_kline = (kline_out-kline_in)/kline_in*100
###                        if perc_kline >= 0.7:
                        if perc_kline <= 0.5:
                            f = open(orlov_path+'coins/'+j+'-old', 'w+')
                            f.write('0')
                            f.close()
                            kline_percent = 100
                            break
                    """
                    if kline_in > kline_out and n < 9:
                        kline_percent = (1 - kline_out / kline_in) * 100
                        #print ('kline_percent' + str(kline_percent))
                        if kline_percent >= 1.5:
                            f = open(orlov_path+'coins/'+j+'-old', 'w+')
                            f.write('0')
                            f.close()
                            break
                      
                    elif kline_in < kline_out and n < 9 and j == "BTC":
                        kline_percent = (1 - kline_in / kline_out) * 100
                        if kline_percent > 0.5:
                            f = open(orlov_path+'coins/'+j+'-old', 'w+')
                            f.write('0')
                            f.close()
                            kline_percent = 100
                            break
                    
                    n = n + 1
                if kline_percent >= 1.5:
                    continue
                """
                i = 7
                m = 0
                while i < 9:
#                    m = m + ( (float(klines[i][1]) + float(klines[i][4])) / 2 )
                    m = m + float(klines[i][4])
                    i = i+1
                m = m / 2
                #print (m)
                """
                m = float(klines[8][4])
                f = open(orlov_path+'coins/'+j+'-old', 'w+')
                f.write(str(m))
                f.close() 
#                f = open(orlov_path+'coins/'+j, 'w+')
#                f.write(pr)
#                f.close() 
            time.sleep(0.1)
    
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
            #time.sleep(10)
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




