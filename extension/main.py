# v2.2
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

def check_return(uart):
    '''
    通信モジュールからのメッセージを受信(シリアル通信)

    uart = 対応機器のuartインスタンスが必要
    '''
    uart.write('AT+ MODE= TEST\n')
    recive(uart)
    uart.write('AT+ TEST= RXLRPKT\n')
    time.sleep(1)
    recive(uart)
    for i in range(90):
        buf = uart.read(100)
        time.sleep(0.3)
        if buf != None:
            #print(buf)  #デバッグ時に使用!!!!!!!!!
            buf = buf.decode()
            #print(buf)
            return buf
        time.sleep(1)
    return None


#LEDを点滅させる
def led_ok():
    for i in range(5):
        led.value(1)
        time.sleep(0.3)
        led.value(0)
        time.sleep(0.3)
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

def downsystem(uart):
    '''
    Loraをsleep状態にし、picoもdeepsleepにする
    '''
    uart.write('AT+WDT=OFF\n')
    recive(uart)
    uart.write('AT+LOWPOWER\n')
    recive(uart)
    time.sleep(1)
    machine.deepsleep()



# UART番号とボーレートを指定
uart = UART(1, 9600)

setup_lora(uart)
lora_id = get_lora_id(uart)
rx_data = f'j314t+{config.version}/{lora_id}/'.encode('utf-8').hex()
confirmation_data = f'j314t+{config.version}/{lora_id}/0'.encode('utf-8').hex()

count = 0
while True:
    # caria cense
    recive(uart)
    uart.write('AT+ TEST= RXLRPKT\n')
    recive(uart)
    rxData = recive(uart)
    if rxData is not None and rxData != b'+TEST: RXLRPKT\r\n':
        #print(rxData)
        #print('キャリアセンス受信')
        time.sleep(1)
        continue
    # TX
    #print('tx-------------')
    uart.write('AT+TEST=TXLRPKT, "'+rx_data+'"\n')
    recive(uart)
    time.sleep(5)
    
    #Check Return
    return_data = check_return(uart)
    if return_data is not None:
        if confirmation_data.lower() in return_data.lower():
            #print('OK!')
            led_ok()
            break
        else:
            count += 1
    else:
        count += 1
    if count == 2:
        break

downsystem(uart)
            
    
        




