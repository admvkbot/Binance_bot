from datetime import datetime
import os
import sys
import xmltodict
from binance import Client
from binance.enums import HistoricalKlinesType
import json

import keras as k
import pandas as pd
from keras import layers
import numpy as np

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

input_params = []
for i in range(103-1):
    input_params.append(i)

model = k.Sequential()
#print(train_x)
#print(train_y)
#model.add(layers.Dense(units=len(raw_data_array[0]), activation="relu"))
#model.add(layers.Dense(units=10, activation="relu"))
model.add(layers.Dense(len(input_params), input_dim=len(input_params), activation="relu"))
model.add(layers.Dense(30, activation="relu"))
model.add(layers.Dense(units=1, activation="sigmoid"))
#model.compile(loss="mse", optimizer="sgd", metrics=["accuracy"])
model.compile(loss="mse", optimizer="adam", metrics=["accuracy"])


max_klines = 30 # логика по 30 свечам

def map_data(str):
    if str.find(".") != -1:
        return int(str)
    return float(str)


def read_data(filename):
    f = open(filename, "r+")
    out_array = []
    for line in f.readlines():
        out_array.append(json.loads(line))
    f.close()
    return out_array


def data_reformat(array):

    def get_kline_height(data):
        return (1 - (float(data[3]) / float(data[2]))) * 100

    def get_kline_direction(data):
        if float(data[1]) > float(data[4]):
            return 0
        return 1

    def get_max(tmp_array, num):
        tmp_max = 0
        for tmp_item in tmp_array:
            if isinstance(tmp_item, list):
                item_float = float(tmp_item[num])
                if item_float > tmp_max:
                    tmp_max = item_float
        return tmp_max

    def get_min(tmp_array, num):
        tmp_min = 10000000
        for tmp_item in tmp_array:
            if isinstance(tmp_item, list):
                item_float = float(tmp_item[num])
                if item_float < tmp_min:
                    tmp_min = item_float
        return tmp_min

    def get_max_volume(tmp_array):
        tmp_max = 0
        for tmp_item in tmp_array:
            if tmp_item > tmp_max:
                tmp_max = tmp_item
        return tmp_max

    def get_average_volume(tmp_array):
        tmp_volume = 0
        for tmp_item in tmp_array:
            tmp_volume = tmp_volume + float(tmp_item[5])
        return tmp_volume / len(tmp_array)

    def get_kline_volume(data, tmp_max_volume):
        return float(data[5]) / tmp_max_volume * 100

    def get_max_price_in(tmp_array):
        return get_max(tmp_array, 1)

    def get_min_price_in(tmp_array):
        return get_min(tmp_array, 1)

    def get_kline_price_in(data, tmp_max_price_in):
        return (1 - float(data[1]) / tmp_max_price_in) * 100 * 10  # инверсия и увеличение градиента цены в 10 раз для улучшения показателей анализа

    def summ_list(list_one, list_two):
        combined_list = [list_one, list_two]
        return [i for sublist in combined_list for i in sublist]

    out_array = []
    for item in array:
        item_array = []
        average_3kline_volume = get_average_volume(item[-7:-4])
        #max_volume = get_max_volume(summ_list(item[-4:-1], [average_3kline_volume]))
        max_volume = average_3kline_volume
        max_price_in = get_max_price_in(item)
        min_price_in = get_min_price_in(item)
        num_green_klines = 0
        part1 = max_klines / 3
        part2 = part1 * 2
        num_green_klines_part1 = 0
        num_green_klines_part2 = 0
        num_green_klines_part3 = 0
        i = 0
        for kline_data in item:
            if isinstance(kline_data, list):
                item_array.append(get_kline_height(kline_data))
                kline_direction = get_kline_direction(kline_data)
                if kline_direction:
                    num_green_klines = num_green_klines + 1
                    if i < part1:
                        num_green_klines_part1 = num_green_klines_part1 + 1
                    elif i < part2:
                        num_green_klines_part2 = num_green_klines_part2 + 1
                    else:
                        num_green_klines_part3 = num_green_klines_part3 + 1
                item_array.append(kline_direction)
                #item_array.append(get_kline_volume(kline_data, max_volume))
                item_array.append(get_kline_price_in(kline_data, max_price_in))
            elif kline_data > 1:
                item_array.append((max_volume - kline_data) / max_volume)
            elif kline_data == 1 or kline_data == 0 or kline_data == 0.3 or kline_data == 0.6:
                #print(len(item_array), kline_data)
                #sys.exit()
                item_array.insert(0, kline_data) # status
            i = i + 1
        item_array.append(1 - ((max_volume - average_3kline_volume) / max_volume))
        item_array.append(num_green_klines)
        item_array.append(num_green_klines_part1)
        item_array.append(num_green_klines_part2)
        item_array.append(num_green_klines_part3)
        item_array.append((1 - min_price_in / max_price_in) * 100 * 10) # с увеличением чувствительности в 10 раз

        out_array.append(item_array)
    return out_array

max_vol = 1000000
encoders = {"vol1": lambda vol1: [vol1 / max_vol],
            "vol2": lambda vol2: [vol2 / max_vol],
            "vol3": lambda vol3: [vol3 / max_vol],
            "vol1d": lambda vol1d: [vol1d / max_vol],
            "vol3h": lambda vol3h: [vol3h / max_vol],
            "direction1": lambda gen: {"down": [0], "up": [1]}.get(gen),
            "direction2": lambda gen: {"down": [0], "up": [1]}.get(gen),
            "direction3": lambda gen: {"down": [0], "up": [1]}.get(gen),
            "min1": lambda min1: [min1],
            "max1": lambda max1: [max1],
            "min2": lambda min2: [min2],
            "max2": lambda max2: [max2],
            "min3": lambda min3: [min3],
            "max3": lambda max3: [max3],
            "status": lambda status: [status]
            }
encoders0 = {"4": lambda vol1: [vol1 / max_vol],
            "8": lambda vol2: [vol2 / max_vol],
            "12": lambda vol3: [vol3 / max_vol],
            "13": lambda vol1d: [vol1d / max_vol],
            "14": lambda vol3h: [vol3h / max_vol],
            "1": lambda gen: {"down": [0], "up": [1]}.get(gen),
            "5": lambda gen: {"down": [0], "up": [1]}.get(gen),
            "9": lambda gen: {"down": [0], "up": [1]}.get(gen),
            "2": lambda min1: [min1],
            "3": lambda max1: [max1],
            "6": lambda min2: [min2],
            "7": lambda max2: [max2],
            "10": lambda min3: [min3],
            "11": lambda max3: [max3],
            "0": lambda status: [status]
            }


def dataframe_to_dict(df):
    result = dict()
    for column in df.columns:
        values = data_frame[column].values
        result[column] = values
    return result


def make_supervised(data_frame):
    raw_input_data = data_frame[input_params]
    #print(raw_input_data)
    #sys.exit()
    #raw_output_data = data_frame[output_params]
    #print(raw_output_data)
    #sys.exit()
    return {"inputs": dataframe_to_dict(raw_input_data)}


def encode_old(data):
    vectors = []
    for data_name, data_values in data.items():
        #print(data_values)
        encoded = list(map(encoders[data_name], data_values)) # !!!
        vectors.append(encoded) #!!!
#        vectors.append(data_values)
#    return vectors
    sys.exit()
#    print(vectors)
    formatted = []
    for vector_raw in list(zip(*vectors)):
        vector = []
        for element in vector_raw:
#            print(element)
            for e in element:
                vector.append(e)
        formatted.append(vector)
#    print(formatted)
    #sys.exit()
    return formatted

def encode(data):
    vectors = []
    for data_name, data_values in data.items():
        #print(data_values)
        #sys.exit()
        tmp_list = []
        for item_dv in data_values:
            tmp_list.append([item_dv])
        #encoded = list(map(encoders[data_name], data_values)) # !!!
        #vectors.append(encoded) #!!!
        vectors.append(tmp_list)
    #print(vectors)
    #sys.exit()
    #return vectors
    formatted = []
    for vector_raw in list(zip(*vectors)):
        vector = []
        for element in vector_raw:
#            print(element)
            for e in element:
                vector.append(e)
        formatted.append(vector)
    #print(formatted)
    #sys.exit()
    return formatted


while 1:
    for coin in coins:
        symbol = coin + "USDT"
        try:
            klines = bclient.get_historical_klines(symbol, Client.KLINE_INTERVAL_1MINUTE,
                                                    "31 min ago UTC",
                                                   klines_type=HistoricalKlinesType.FUTURES)
            klines_hours = bclient.get_historical_klines(symbol, Client.KLINE_INTERVAL_1HOUR,
                                                         "1 day ago UTC",
                                                         klines_type=HistoricalKlinesType.FUTURES)
        except:
            continue

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
        #list_to_json_array = json.dumps(klines)
        #print(klines)

        raw_data_array = data_reformat([klines])
        if len(raw_data_array[0]) != 102: #462
            continue
        #print(raw_data_array[0])
        #print(len(raw_data_array[0]))
        #sys.exit()
        data_frame = pd.DataFrame(raw_data_array)
        supervised = make_supervised(data_frame)
        test_x = np.array(encode(supervised["inputs"]))

        quality_dict = {}
        i = 0
        for filename in os.listdir("weights"):
            model.load_weights("weights/" + filename)
            predicted_test = model.predict(test_x)
            quality = predicted_test[0][0]
            i = i + 1

            #print(filename + " -----------------")

            quality_dict[filename] = quality

#        print(coin, ":")
        num_99 = 0
        for key, value in quality_dict.items():
            if value > 0.99:
                num_99 = num_99 + 1
            if num_99 > 5:
                print(coin, ":")
                today = datetime.today()
                print("Today's date:", today)
                print(quality_dict)
                break
