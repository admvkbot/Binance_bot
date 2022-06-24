import atexit
import datetime
import os
import signal
import sys
import time
#import telebot
from telethon import TelegramClient, sync, events
import re
from binance import Client, ThreadedWebsocketManager, ThreadedDepthCacheManager

class Daemon(object):
    """ Linux Daemon boilerplate. """
    def __init__(self, pid_file,
                 stdout='/var/log/orlovbot_out.log',
                 stderr='/var/log/orlovbot_err.log'):
        self.stdout = stdout
        self.stderr = stderr
        self.pid_file = pid_file


    summ = 50 #trade summ in dollars
    leverage = 20
    stop_percent = 0.3 #закрытие при уменьшении цены на этот %
    take_percent = 2.1 #тейк при увеличении цены на этот %

    api_key = 'RlB5ioperdXflSIZxWSHsHryhRiEsjXIpucnJMa4A4hEjAntfIsM6vW9eeC4Ylfi'
    api_secret = 'SPCTsjWiSTwdjHzkdFhRQhubAQzoNIUsD5YQxC5QkY4qW7v71iWo46MCY2GLKLHt'

    proxies = {
        'http': 'http://10.10.1.10:3128',
        'https': 'http://193.142.42.167:32809'
    }

    def get_text_messages(message):
        if message.text == "Привет":
            bot.send_message(message.from_user.id, "Привет, чем я могу тебе помочь?")
        elif message.text == "/help":
            bot.send_message(message.from_user.id, "Напиши привет")
        else:
            bot.send_message(message.from_user.id, "Я тебя не понимаю. Напиши /help.")

    bclient = Client(api_key, api_secret, {'proxies': proxies})

    def binance(symbol, summ):
        #order = bclient.create_test_order(
        #    symbol,
        #    side=Client.SIDE_BUY,
        #    type=Client.ORDER_TYPE_MARKET,
        #    quantity=100)
        #prices = bclient.get_all_tickers()
        #for i in prices:
        #    if i['symbol'] == symbol:
        #        print(i['price'])
        
        
        bclient.futures_change_leverage(symbol=symbol, leverage=leverage)
        #bclient.futures_change_margin_type(symbol=symbol, marginType='ISOLATED')
        
        # получение начальной цены для работы
        orderbook = bclient.get_ticker(symbol=symbol)
        print("Price: "+ orderbook['lastPrice'])
        last_price = orderbook['lastPrice']
        
        if not last_price:
            print ("last_price error")
            sys.exit()
        
        last_price = float(last_price)

        # вычисление объёма монет
        amount = summ/last_price*leverage
        #amount = summ/last_price
     
        # определение необходимой точности
        precision = 0
        if amount < 1:
            precision = 4
        amount = "{:0.0{}f}".format(amount, precision)
        print ("Amount: "+ str(amount))
        
        # покупка по рынку
        bclient.futures_create_order ( 
            symbol=symbol,
            type='MARKET',
            side='BUY',
            quantity=amount,
            isIsolated='TRUE'
        )

        # получение цены монеты сразу после покупки
        orderbook = bclient.get_ticker(symbol=symbol)
        last_price = orderbook['lastPrice']
        last_price = float(last_price)
        
        #вычисление цены для стоп-лосса
        stop_price = last_price - last_price/100*stop_percent
        precision = 4
        #if stop_price < 1:
        #    precision = 4
        stop_price = "{:0.0{}f}".format(stop_price, precision)
        print('Stop price: ' + str(stop_price))
        sys.exit()
        # установка стоп-ордера
        bclient.futures_create_order (
            symbol=symbol, 
            side='SELL', 
            type='STOP_MARKET', 
            stopPrice=stop_price,
            closePosition='true'
        )


        amount = float(amount) + 1 # +1 для того, чтобы точно закрылся весь ордер
        precision = 0
        if amount < 1:
            precision = 4
        amount = "{:0.0{}f}".format(amount, precision)
        print ("Amount: "+ str(amount))
        
        #вычисление цены для тейка
        take_price = last_price + last_price/100*take_percent
        precision = 4
        #if take_price < 1:
        #    precision = 4
        take_price = "{:0.0{}f}".format(take_price, precision)
        print('Take price: ' + str(take_price)) 
        
        # установка тейк-профита
        bclient.futures_create_order (
            symbol=symbol, 
            type='LIMIT', 
            timeInForce='GTC',
            price=take_price,  # The price at which you wish to buy/sell, float
            side='SELL',  # Direction ('BUY' / 'SELL'), string
            quantity=amount,  # Number of coins you wish to buy / sell, float
            reduceOnly='true'
        )
  




    def del_pid(self):
        """ Delete the pid file. """
        os.remove(self.pid_file)

    def daemonize(self):
        """ There shined a shiny daemon, In the middle, Of the road... """
        # fork 1 to spin off the child that will spawn the deamon.
        if os.fork():
            sys.exit()

        # This is the child.
        # 1. cd to root for a guarenteed working dir.
        # 2. clear the session id to clear the controlling TTY.
        # 3. set the umask so we have access to all files created by the daemon.
        os.chdir("/home/run/orlovbot")
        os.setsid()
        os.umask(0)

        # fork 2 ensures we can't get a controlling ttd.
        if os.fork():
            sys.exit()

        # This is a child that can't ever have a controlling TTY.
        # Now we shut down stdin and point stdout/stderr at log files.

        # stdin
        with open('/dev/null', 'r') as dev_null:
            os.dup2(dev_null.fileno(), sys.stdin.fileno())

        #
        # Exceptions raised after this point will be written to the log file.
        sys.stderr.flush()
        with open(self.stderr, 'a+') as stderr:
            os.dup2(stderr.fileno(), sys.stderr.fileno())

        #print(3)
        #
        # Print statements after this step will not work. Use sys.stdout
        # instead.
        sys.stdout.flush()
        ##print(4)
        with open(self.stdout, 'a+') as stdout:
            os.dup2(stdout.fileno(), sys.stdout.fileno())

        #print(2)
        # Before file creation, make sure we'll delete the pid file on exit!
        atexit.register(self.del_pid)
        pid = str(os.getpid())
        with open(self.pid_file, 'w+') as pid_file:
            pid_file.write('{0}'.format(pid))

    def get_pid_by_file(self):
        """ Return the pid read from the pid file. """
        try:
            with open(self.pid_file, 'r') as pid_file:
                pid = int(pid_file.read().strip())
            return pid
        except IOError:
            return

    def start(self):
        """ Start the daemon. """
        print ("Starting...")
        if self.get_pid_by_file():
            print ('PID file {0} exists. Is the deamon already running?'.format(self.pid_file))
            sys.exit(1)
        
        self.daemonize()
        self.run()

    def stop(self):
        """ Stop the daemon. """
        print ("Stopping...")
        pid = self.get_pid_by_file()
        if not pid:
            print ("PID file {0} doesn't exist. Is the daemon not running?".format(self.pid_file))
            return

        # Time to kill.
        try:
            while 1:
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.1)
        except OSError as err:
            if 'No such process' in err.strerror and os.path.exists(self.pid_file):
                os.remove(self.pid_file)
            else:
                print (err)
                sys.exit(1)

    def restart(self):
        """ Restart the deamon. """
        self.stop()
        self.start()

    def run(self):
        """ The main loop of the daemon. """
        api_id = 7428364
        api_hash = '98020087a8d56f047f3c92de8bd8d5bc'
        client = TelegramClient('X100TradingBot', api_id, api_hash)
        print ('STARTING')
        @client.on(events.NewMessage(pattern=r'Покупаю\s\#'))
        async def normal_handler(event):
            message = event.message.to_dict()['message']
            #print(message)
            symbol = re.match(r'Покупаю\s\#(\w+)', message).group(1)+'USDT'
            print(symbol)
            binance(symbol, summ)  
        print ('DONE')
        client.start()
        client.run_until_disconnected()

 
if __name__ == '__main__':
    

    if len(sys.argv) < 2:
        print ("Usage: {0} start|stop|restart".format(sys.argv[0]))
        sys.exit(2)

    daemon = Daemon('/tmp/daemon_example.pid')
    if 'start' == sys.argv[1]:
        daemon.start()
        
    elif 'stop' == sys.argv[1]:
        daemon.stop()
    elif 'restart' == sys.argv[1]:
        daemon.restart()
    else:
        print ("Unknown command '{0}'".format(sys.argv[1]))
        sys.exit(2)

