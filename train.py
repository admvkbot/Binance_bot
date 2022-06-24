import os
import re
import sys
import time
from datetime import datetime

import mysql.connector as conn
import pandas as pd
import xmltodict
from binance import Client
from binance.enums import HistoricalKlinesType
import json
import random

orlov_path = "C:/work/crypto/python/orlovbot/"
path = "C:/work/crypto/python/orlovbot/log"
coins = ["ARPA", "ANKR", "NEAR", "ZEN", "SFP", "GTC", "LUNA", "GALA", "LIT", "RSR", "MASK", "DOT", "TOMO", "BLZ", "ZEC", "ONE", "FTM", "CTK", "UNFI"]

config_xml = ''
with open(orlov_path + 'main.xml', 'r') as f:
    config_xml = ''.join(list(map(str.strip, f.readlines())))
config = xmltodict.parse(config_xml)

api_key = config['config']['api-key']
api_secret = config['config']['api-secret']
proxy = config['config']['proxy']

def log_time(string, file=""):
    if file:
        f = open(file, "a+")
        f.write(str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]) + ': ' + string + "\n")
        f.close()
    else:
        print(str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]) + ': ' + string)

str0 = 'http://' + str(proxy)
proxies = {
    'http': 'http://10.10.1.10:3128',
    'https': str0
}

log_time('START BOT')

#if proxy:
#    bclient = Client(api_key, api_secret, {'proxies': proxies})
#else:
if 1:
    bclient = Client(api_key, api_secret)

old_status_flag = 1
old2_status_flag = 1
while 1:
    kline_data = {
        "symbol": 'BLZUSDT',
        "status": 0,
        "year": 2021,
        "month": 1,
        "day": 12,
        "hour": 5,
        "min": 0
    }
    kline_data["symbol"] = coins[random.randint(0, len(coins)-1)] + 'USDT'
    kline_data["month"] = random.randint(7, 12)
    if kline_data["month"] == 2:
        max_month_days = 28
    else:
        max_month_days = 30
    kline_data["day"] = random.randint(1, max_month_days)
    kline_data["hour"] = random.randint(0, 23)
    kline_data["min"] = random.randint(0, 59)

#    input_data_array = input(":").split()
#    if len(input_data_array) != 3:
#        break
#    [kline_data["day"], kline_data["hour"], kline_data["min"]] = input_data_array

#    for key in kline_data.items():
#        try:
#            kline_data[key[0]] = int(key[1])
#        except:
#            o=0

    timestamp_start = datetime(kline_data["year"], kline_data["month"], kline_data["day"], kline_data["hour"],
                               kline_data["min"]).timestamp()-150*60
    timestamp_start_day = datetime(kline_data["year"], kline_data["month"], kline_data["day"], kline_data["hour"],
                               kline_data["min"]).timestamp()-60*60*24
    #timestamp_end = datetime(kline_data["year"], kline_data["month"], kline_data["day"], kline_data["hour"],
    #                         kline_data["min"]).timestamp()
    date_str_start = datetime.fromtimestamp(timestamp_start).strftime("%d %b, %Y %H:%M")
    date_str_start_hours = datetime.fromtimestamp(timestamp_start_day).strftime("%d %b, %Y %H:%M")

    date_str_end = datetime(kline_data["year"], kline_data["month"], kline_data["day"], kline_data["hour"], kline_data["min"]).strftime("%d %b, %Y %H:%M")

    timestamp_end_status = datetime(kline_data["year"], kline_data["month"], kline_data["day"], kline_data["hour"],
                               kline_data["min"]).timestamp()+15*60
    date_str_end_status = datetime.fromtimestamp(timestamp_end_status).strftime("%d %b, %Y %H:%M")
#    print("start "+str(date_str_end)+"; end "+str(date_str_end_status))
    print("start "+str(date_str_end)+"; end "+str(date_str_end_status))
    try:
        klines_past = bclient.get_historical_klines(kline_data["symbol"], Client.KLINE_INTERVAL_15MINUTE, date_str_end,
                                               date_str_end_status, klines_type=HistoricalKlinesType.FUTURES)
    except:
        continue

    proc_max_price = 0.5
    proc_profit = 2

    min_past_price = float(klines_past[0][3])
    max_past_price = float(klines_past[0][2])
    tmp_proc_min = (max_past_price - min_past_price) / max_past_price * 100

    def get_max_price(sub_klines):
        max_price = 0
        for kline_item in sub_klines:
            float_price = float(kline_item[2])
            if float_price > max_price:
                max_price = float_price
        return max_price

    if float(klines_past[0][1]) <= float(klines_past[0][4]): # если зелёная свеча
        if old_status_flag == 1:
            old_status_flag = 0
        else:
            continue

    elif (tmp_proc_min < proc_profit) and (float(klines_past[0][1]) > float(klines_past[0][4])): # если недостаточный профит и красная свеча
        #print(tmp_proc_min)
        if old_status_flag == 0:
            old_status_flag = 0.3
        else:
            continue

    klines = bclient.get_historical_klines(kline_data["symbol"], Client.KLINE_INTERVAL_1MINUTE, date_str_start,
                                           date_str_end, klines_type=HistoricalKlinesType.FUTURES)


    max_1m_kline_price = get_max_price(klines)

    tmp_proc_high = abs(max_past_price - max_1m_kline_price) / max_past_price * 100

    print(old_status_flag)

#    if tmp_proc_high > 0 and tmp_proc_high < proc_max_price and (tmp_proc_min >= proc_profit): # если верх посл. мин свечи ниже верха 5-минутной
    if tmp_proc_high < proc_max_price and (tmp_proc_min >= proc_profit):  # если верх посл. мин свечи ниже верха 5-минутной
        # и если этот зазор меньше заданного (0.5) и если длина 5-минутной свечи больше профита
        if old_status_flag == 0.6:
            kline_data["status"] = 1
            old_status_flag = 1
            print("Status: 1")
        else:
            continue
    elif (tmp_proc_min >= proc_profit): # ... но, если длина 5-минутки меньше профита
        if old_status_flag == 0.3:
            kline_data["status"] = 0.6
            old_status_flag = 0.6
            print("Status: 0.6")
        else:
            continue
    elif old_status_flag != old2_status_flag and old_status_flag < 0.6:
        print("Next: " + str(old_status_flag))
        kline_data["status"] = old_status_flag
        old2_status_flag = old_status_flag
    else:
        continue


    klines_hours = bclient.get_historical_klines(kline_data["symbol"], Client.KLINE_INTERVAL_1HOUR, date_str_start_hours,
                                           date_str_end, klines_type=HistoricalKlinesType.FUTURES)

    vol_1d = 0
    vol_3h = 0
    vol_1h = 0
    i = 0
    for kline in klines_hours:
        float_kline = float(kline[5])
        if i > (23-3):
            vol_3h = vol_3h + float_kline
        if i > (23-1):
            vol_1h = vol_1h + float_kline
        vol_1d = vol_1d + float_kline
        i = i + 1
        if i > 23:
            break
#    print(i)
    vol_1h = vol_1h / 60
    vol_3h = vol_3h / (3 * 60)
    vol_1d = vol_1d / (24 * 60)

#    print (vol_1h, vol_3h, vol_1d)


    klines.append(vol_1h)
    klines.append(vol_3h)
    klines.append(vol_1d)
    klines.append(kline_data["status"])
    list_to_json_array = json.dumps(klines)

    f = open("data.dump", 'a+')
    f.write(list_to_json_array+"\n")
    f.close()
