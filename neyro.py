import keras as k
import pandas as pd
from keras import layers
from keras import backend as K
#from keras.utils import normalize, to_categorical
import numpy as np
import sys
import tensorflow as tf
import matplotlib.pyplot as plt
import json
import os

max_klines = 150 # логика по 150 свечам

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
        return (1 - float(data[1]) / tmp_max_price_in) * 100 * 1  # инверсия и увеличение градиента цены в 33 раз для улучшения показателей анализа

    def summ_list(list_one, list_two):
        combined_list = [list_one, list_two]
        return [i for sublist in combined_list for i in sublist]

    k = 0
    k2 = 0
    out_array = []
    for item in array:
        item_array = []
        average_3kline_volume = get_average_volume(item[-7:-4])
        max_volume = get_max_volume(summ_list(item[-4:-1], [average_3kline_volume]))
        #max_volume_3kline = average_3kline_volume
        max_price_in = get_max_price_in(item)
        min_price_in = get_min_price_in(item)
        num_green_klines = 0
        part1 = max_klines / 3
        part2 = part1 * 2
        num_green_klines_part1 = 0
        num_green_klines_part2 = 0
        num_green_klines_part3 = 0
        i = 0
        #print(":",len(item))
        for kline_data in item:
            #if i < 200:
            #    i = i + 1
            #    continue
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
                #k2 = k2 + 1
            elif kline_data > 1:
                item_array.append((max_volume - kline_data) / max_volume)
            elif kline_data == 1 or kline_data == 0 or kline_data == 0.3 or kline_data == 0.6:
                #print(len(item_array), kline_data)
                #sys.exit()
                item_array.insert(0, kline_data) # status
                k2 = k2 + 1
            i = i + 1
        item_array.append(1 - ((max_volume - average_3kline_volume) / max_volume))
        #print(max_volume, average_3kline_volume)
        item_array.append(num_green_klines)
        item_array.append(num_green_klines_part1)
        item_array.append(num_green_klines_part2)
        item_array.append(num_green_klines_part3)
        item_array.append((1 - min_price_in / max_price_in) * 100 * 1) # с увеличением чувствительности в 3 раз
        #print(len(item_array))

        flag_more_then_100 = 0
        l = 0
        for tt in item_array:
            if tt > 100:
                print(tt, k, l)
                flag_more_then_100 = 1
#                sys.exit()
            l = l + 1
        if flag_more_then_100:
            continue
        out_array.append(item_array)
        k = k + 1
    #print(len(out_array))
    #print(k2)
    #sys.exit()
    return out_array


raw_data_array = data_reformat(read_data("data.dump"))

data_frame = pd.DataFrame(raw_data_array)

#data_frame = pd.read_csv("neyro.csv")
#print(raw_data_array[0])
#print(len(raw_data_array[0]))
#sys.exit()

input_params = []
#print(len(raw_data_array[0]))
for i in range(len(raw_data_array[0])):
    if i != 0:
        input_params.append(i)
#input_params = ['status','direction1','min1','max1','vol1','direction2','min2','max2','vol2','direction3','min3','max3','vol3','vol1d','vol3h']
#print(input_params)
#sys.exit()
output_params = [0]
#output_params = ["status"]

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
    raw_output_data = data_frame[output_params]
    #print(raw_output_data)
    #sys.exit()
    return {"inputs": dataframe_to_dict(raw_input_data),
            "outputs": dataframe_to_dict(raw_output_data)}


def encode_old(data):
    vectors = []
    for data_name, data_values in data.items():
        #print(data_values)
        encoded = list(map(encoders[data_name], data_values)) # !!!
        vectors.append(encoded) #!!!
#        vectors.append(data_values)
#    return vectors
#    sys.exit()
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



supervised = make_supervised(data_frame)
#print(len(encode(supervised["inputs"])))
#sys.exit()
encode_inputs = np.array(encode(supervised["inputs"]))
encode_outputs = np.array(encode(supervised["outputs"]))

#print(encode(supervised["inputs"]))
#print(len(input_params))
#sys.exit()
NUM = len(encode_inputs)-20
#NUM = 90
#print(encode_outputs)
#sys.exit()

train_x = encode_inputs[:NUM]
train_y = encode_outputs[:NUM]
#print(train_x)
print(train_y)
sys.exit()

test_x = encode_inputs[NUM:]
test_y = encode_outputs[NUM:]

#train_x = train_x.astype('float32')
#test_x = test_x.astype('float32')
#train_x /= 255
#test_x /= 255

#print(train_x)
#sys.exit()

max_quality = {
    "y_all": 0,
    "n": 0}
n = 100
while n:
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
    K.set_value(model.optimizer.learning_rate, 0.0001)
    #model.compile(loss="categorical_crossentropy", optimizer="adam", metrics=["accuracy"])
    fit_results = model.fit(x=train_x, y=train_y, epochs=200, validation_split=0.2, verbose=0)

    if 0:
        plt.title("Losses train/validation")
        plt.plot(fit_results.history["loss"], label="Train")
        plt.plot(fit_results.history["val_loss"], label="Validation")
        plt.legend()
        plt.show()

        plt.title("Accuracies train/validation")
        plt.plot(fit_results.history["accuracy"], label="Train")
        plt.plot(fit_results.history["val_accuracy"], label="Validation")
        plt.legend()
        plt.show()

    predicted_test = model.predict(test_x)
    real_data = data_frame.iloc[NUM:][output_params]
    real_data["PSurvived"] = predicted_test
    #print(real_data)
    real_data_list = real_data.values.tolist()

    print("n: " + str(n) + " -----------------")

    y_all = 0
    flag_bad = 0
    j = 0
    for real_data_list_item in real_data_list:
        [y, y2] = real_data_list_item
        print(real_data_list_item)
        if y == 1 and y2 > 0.9:
            print(real_data_list_item)
            y_all = y_all + y2
            j = j + 1
        elif y < 0.6 and y2 > 0.8:
            print(real_data_list_item)
            flag_bad = 1
            print("Found high 0.0 - 0.3")
            break
        elif y2 > 0.94:
            print(real_data_list_item)
            flag_bad = 1
            print("Found high 0.6")
            break
    if j < 2 or flag_bad:
        n = n - 1
        continue
    y_all = y_all / j
    print(y_all)
    if y_all > max_quality["y_all"]:
        max_quality["y_all"] = y_all
        max_quality["n"] = n
    model.save_weights("weights_" + str(n) + "__" + str(j) + ".h5")
    #sys.exit()
    n = n - 1

print("Max quality: " + str(max_quality["n"]) + " (" + str(max_quality["y_all"]) + ")")
print("")
print("========================================")
print("")

max_quality = {
    "y_all": 0,
    "n": 0}
i = 0
for filename in os.listdir("weights"):
    model.load_weights("weights/" + filename)
    predicted_test = model.predict(test_x)
    real_data["PSurvived"] = predicted_test
    #print(real_data)
    i = i + 1
    #real_data_list = predicted_test.values.tolist()
    #print("-----")
    real_data_list = real_data.values.tolist()

    print(filename + " -----------------")

    y_all = 0
    flag_bad = 0
    j = 0
    for real_data_list_item in real_data_list:
        [y, y2] = real_data_list_item
        if y == 1 and y2 > 0.9:
            #print(real_data_list_item)
            y_all = y_all + y2
            j = j + 1
        elif y < 0.6 and y2 > 0.8:
            #print(real_data_list_item)
            flag_bad = 1
            print("Found high 0.0 - 0.3")
            break
        elif y2 > 0.94:
            #print(real_data_list_item)
            flag_bad = 1
            print("Found high 0.6")
            break
    if j < 2 or flag_bad:
        continue
    y_all = y_all / j
    print(j)
    print(y_all)
    if y_all > max_quality["y_all"]:
        max_quality["y_all"] = y_all
        max_quality["n"] = n
    #model.save_weights("weights_" + str(n) + "__" + str(j) + ".h5")
    #sys.exit()




