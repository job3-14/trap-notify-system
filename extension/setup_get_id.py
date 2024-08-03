# wio e5のlora番号を出力するプログラム
# 初回のデータベースへの登録で使用する

from machine import Pin, I2C, UART
import time
import config
import random

#LED制御
led = machine.Pin(25, machine.Pin.OUT)
led.value(1)



def recive(uart):
    '''
    通信モジュールからのメッセージを受信(シリアル通信)

    uart = 対応機器のuartインスタンスが必要
    '''
    time.sleep(1)
    for i in range(10):
        buf = uart.read(100)
        time.sleep(0.3)
        if buf != None:
            #print(buf)  #デバッグ時に使用!!!!!!!!!
            return buf
    return

def setup_lora(uart):
    '''
    Wio E5のセットアップを実行
    周波数などをセット

    uart = 対応機器のuartインスタンスが必要
    '''
    uart.write('AT+UART=TIMEOUT,0\n')
    recive(uart)
    uart.write('AT+ MODE= TEST\n')
    recive(uart)
    uart.write('AT+TEST=?\n')
    recive(uart)
    uart.write('AT+TEST=RFCFG,'+str(config.frequency)+',SF12,125,12,15,'+str(config.pwr)+',ON,OFF,OFF\n')
    recive(uart)


def get_lora_id(uart):
    '''
    loraのIDを取得する

    uart = 対応機器のuartインスタンスが必要
    '''
    uart.write('AT+ ID\n')
    result = recive(uart)
    result = result.decode()
    adress_index = result.find('DevAddr')
    result = result[adress_index+9:adress_index+20]
    return result


# UART番号とボーレートを指定
uart = UART(0, 9600)
setup_lora(uart)
print('------------------\n')
print(get_lora_id(uart))
print('------------------\n')