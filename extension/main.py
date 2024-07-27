from machine import Pin, I2C, UART
import time
import utime
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
    utime.sleep(1)
    for i in range(10):
        buf = uart.read(100)
        utime.sleep(0.3)
        if buf != None:
            print(buf)  #デバッグ時に使用!!!!!!!!!
            return buf
    return


#LEDを点滅させる
def led_ok():
    for i in range(5):
        led.value(1)
        utime.sleep(0.3)
        led.value(0)
        utime.sleep(0.3)
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
lora_id = get_lora_id(uart)
rx_data = f'j314t+{config.version}/{lora_id}/'.encode('utf-8').hex()
confirmation_data = f'j314t+{config.version}/{lora_id}/0'.encode('utf-8').hex()

while True:
    # caria cense
    recive(uart)
    uart.write('AT+ TEST= RXLRPKT\n')
    utime.sleep(0.005)
    rxData = recive(uart)
    if rxData is not None and rxData !=b'+TEST: RXLRPKT\r\n':
        print('キャリアセンス受信')
        utime.sleep(0.05)
        continue
    else:
        # TX
        uart.write('AT+TEST=TXLRPKT, "'+rx_data+'"\n')
        recive(uart)
        #break
        led_ok()
        utime.sleep(15) #30秒に１回送信
        

