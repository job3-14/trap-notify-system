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

def setup_sim(uart):
    '''
    SIM7080GをAPN接続まで行う

    uart = 対応機器のuartインスタンスが必要
    '''
    uart.write('AT+CGDCONT=1,"IP","soracom.io"\r')
    recive(uart)
    uart.write('AT+CGAUTH=1,3,"sora","sora@soracom.io" \r')
    recive(uart)
    uart.write('AT+CNCFG=1,1,"soracom.io","sora@soracom.io","sora",3\r')
    recive(uart)
    uart.write('AT+COPS=1,2,"44051"\r')
    recive(uart)
    uart.write('AT+CGNAPN\r')
    recive(uart)
    uart.write('AT+CNACT=0,1\r')
    recive(uart)
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
    uart.write('AT+TEST=RFCFG,921.5,SF12,125,12,15,14,ON,OFF,OFF\n')
    recive(uart)

def get_imsi(uart):
    '''
    IMSIを取得しstr型で返す

    uart = 対応機器のuartインスタンスが必要
    '''
    uart.write('AT+CIMI\r')
    imsi = recive(uart)
    imsi = imsi.decode()
    imsi_find = imsi.find('440')
    imsi = imsi[imsi_find:imsi_find+15]
    return imsi



def rx_lora(uart):
    '''
    Loraを受信し、受信内容を返す

    uart = 対応機器のuartインスタンスが必要
    '''
    recive(uart)
    uart.write('AT+ TEST= RXLRPKT\n')
    while True:
        rxData = uart.read(100)
        if rxData is not None and rxData !=b'+TEST: RXLRPKT\r\n':
            rxData_str = rxData.decode()
            print(rxData_str)
            return rxData_str
        

def tx_json(uart,json_dict):
    '''
    jsonをsoracom FUNK に送信します。

    uart = 対応機器のuartインスタンスが必要
    json_dict['IMSI']= IMSI番号str
    json_dict['txt'] = 送信テキスト
    '''
    word_count = str(31 + len(json_dict['IMSI']) + len(json_dict['txt']))
    uart.write('AT+SHCONF="URL","http://funk.soracom.io"\r')
    recive(uart)
    uart.write('AT+SHCONF="BODYLEN",1024\r')
    recive(uart)
    uart.write('AT+SHCONF="HEADERLEN",350\r')
    recive(uart)
    uart.write('AT+SHCONN\r')
    recive(uart)
    uart.write('AT+SHSTATE?\r')
    recive(uart)
    uart.write('AT+SHCHEAD\r')
    recive(uart)
    uart.write('AT+SHAHEAD="Content-Type","application/json"\r')
    recive(uart)
    uart.write('AT+SHBOD='+word_count+',10000\r')  # mozisuunositei
    recive(uart)
    uart.write('{"dt":"alt","IMSI":"'+json_dict['IMSI']+'","txt":"'+json_dict['txt']+'"}\r')
    recive(uart)
    uart.write('AT+SHREQ="/post",3\r')
    recive(uart)
    uart.write('AT+SHREAD=0,1024\r')
    recive(uart)
    uart.write('AT+SHDISC\r')
    recive(uart)
    return






def main():
    header = f'j314t+{config.version}+'
    
    try:
        pass
    except:
        while True:
            led_ok() #エラー時
    #led_ok() #起動完了
            
    # UART番号とボーレートを指定
    uart_sim = UART(0, 115200)
    uart_lora = UART(1, 9600)
    
    setup_lora(uart_lora)
    #setup_sim(uart_sim)
    
    
    tx_json_data = {'dt': 'alt'}
    tx_json_data['IMSI'] = get_imsi(uart_sim)   #### honban okikae
    tx_json_data['txt'] = 'xxxxxxxxxx01'        #### honban okikae
    
    #tx_json_data = {"dt":"alt","IMSI":"440525060025394","txt": "xxxxxxxxxx01"}
    #tx_json(uart_sim,tx_json_data)

    
    rx_lora(uart_lora)
    
    print('return 0 OK')
        





        



if __name__ == '__main__':
    main()
