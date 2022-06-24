#import telebot
from telethon import TelegramClient, sync, events
import re
import sys
import os
import time
from datetime import datetime
import requests
import xmltodict

stdout='telbot_out.log'
stderr='telbot_err.log'

config_xml = ''
with open('config.xml', 'r') as f:
    config_xml = ''.join(list(map(str.strip, f.readlines())))
config = xmltodict.parse(config_xml)

api_id = config['config']['api-id']
api_hash = config['config']['api-hash']
api_name = config['config']['api-name']

def log_time(string):
    print(str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]) + ': ' + string)

log_time('START TELBOT')

def get_text_messages(message):
    if message.text == "Привет":
        bot.send_message(message.from_user.id, "Привет, чем я могу тебе помочь?")
    elif message.text == "/help":
        bot.send_message(message.from_user.id, "Напиши привет")
    else:
        bot.send_message(message.from_user.id, "Я тебя не понимаю. Напиши /help.")


# =======================================================================
        
if(0):    
    sys.stderr.flush()
    with open(stderr, 'a+') as stderr:
        os.dup2(stderr.fileno(), sys.stderr.fileno())

    sys.stdout.flush()
    ##print(4)
    with open(stdout, 'a+') as stdout:
        os.dup2(stdout.fileno(), sys.stdout.fileno())



# Вставляем api_id и api_hash
#api_id = 7428364
#api_id = 1990712394
#api_hash = '98020087a8d56f047f3c92de8bd8d5bc'
#api_hash = 'AAFK_R3HrJYGM76wV_1UltpQzKY1lig2_bA'


client = TelegramClient(api_name, api_id, api_hash)

#@client.on(events.NewMessage(pattern=r'Покупаю\s\#|orlovbot'))
@client.on(events.NewMessage(pattern=r'.*\#'))
async def normal_handler(event):
    log_time('SIGNAL')
    message = event.message.to_dict()['message']
    #log_time('MESSAGE RECEIVED')
    if re.match(r'Покупаю\s\#(\w+)', message):
        #print(message)
        symbol = re.match(r'Покупаю\s\#(\w+)', message).group(1)+'USDT'
        print(symbol)
        base_price = re.search(r'Buy price\):\s([\d\.]+)', message).group(1)
        print("Base price: " + base_price)
        
        requests.get('http://178.170.42.19/index.php?c=' + symbol + '&p=' + base_price)
        
        
        await client.send_message('@Adm_S_R', symbol+" buy")
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





