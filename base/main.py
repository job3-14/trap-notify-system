from machine import Pin, I2C, UART
import time
import utime
import config
import random
import _thread

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
    uart.write('AT+TEST=RFCFG,'+str(config.frequency)+',SF12,125,12,15,'+str(config.pwr)+',ON,OFF,OFF\n')
    recive(uart)

def get_imsi(uart):
    '''
    IMSIを取得しstr型で返す

    uart = 対応機器のuartインスタンスが必要
    '''
    uart.write('AT+CIMI\r')
    imsi = recive(uart)
    print('###############')
    print(imsi)
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


def check_header(data):
    '''
    受信したデータが発信機からのものか確認をする

    data = loraで受信した生データ(str)
    '''
    return


def pick_lora_data(data):
    '''
    受信したデータのデータ部のみを取り出す関数

    data = loraで受信した生データ(str)
    '''
    start_index = data.find('"')+1
    finish_index = data.rfind('"')
    rx_data = data[start_index:finish_index]
    return rx_data

def gpio_power(gpio_pin, switch):
    '''
    GPIOのオン・オフを切り替えする関数
    gpio_pin = machine.Pin(22, machine.Pin.OUT)
    switch = 0->オフ, 1->オン
    '''
    gpio_pin.value(switch)
    return


def tx_lora(uart, rx_data):
    '''
    loraでデータを送信する関数

    uart = 対応機器のuartインスタンスが必要
    data = 送信するデータ(16進数)
    '''
    while True:
        # caria cense
        recive(uart)
        uart.write('AT+ TEST= RXLRPKT\n')
        utime.sleep(0.005)
        recive(uart)
        rxData = recive(uart)
        if rxData is not None and rxData !=b'+TEST: RXLRPKT\r\n':
            print('キャリアセンス受信')
            utime.sleep(0.05)
            continue
        else:            
            uart.write('AT+TEST=TXLRPKT, "'+rx_data+'"\n')
            recive(uart)
            return
                
    

def tx_return_lora(uart, rx_data):
    '''
    loraで応答データを

    uart = 対応機器のuartインスタンスが必要
    data = 送信するデータ(16進数)
    '''
    for i in range(5):
        tx_lora(uart, rx_data)
        utime.sleep(round(random.uniform(5.0, 8.0), 1)) #5.0秒から8.0秒ランダム


def json_escape_string(s):
    escape_chars = {
        '\\': '\\\\',
        '"': '\\"',
        '\'': '\\\'',
        '\n': '\\n',
        '\r': '\\r',
        '\t': '\\t',
        '\b': '\\b',
        '\f': '\\f',
    }
    
    escaped_str = ''
    for char in s:
        if char in escape_chars:
            escaped_str += escape_chars[char]
        else:
            escaped_str += char
    
    return escaped_str

def extract_hour(cclk_response):
    # 応答文字列を改行で分割して配列に変換
    lines = cclk_response.split('\r\n')
    
    # +CCLKの行を見つける
    for line in lines:
        if line.startswith('+CCLK:'):
            # 時刻部分を抽出
            datetime_str = line.split('"')[1]
            # 時刻を分割して時間部分を取得
            hour = datetime_str.split(',')[1].split(':')[0]
            return int(hour)
    
    return None


def calculate_hours_until_4(current_hour):
    if current_hour < 4:
        return 4 - current_hour
    else:
        return 24 - current_hour + 4
    

def tx_wdu(uart,imsi):
    '''
    wduをsoracom FUNK に送信します。

    uart = 対応機器のuartインスタンスが必要
    json_dict['IMSI']= IMSI番号str
    json_dict['txt'] = 送信テキスト
    '''
    word_count = str(22 + len(imsi))
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
    uart.write('{"dt":"wdu","IMSI":"'+imsi+'"}\r')
    recive(uart)
    uart.write('AT+SHREQ="/post",3\r')
    recive(uart)
    result = recive(uart).decode()
    uart.write('AT+SHREAD=0,1024\r')
    recive(uart)
    uart.write('AT+SHDISC\r')
    recive(uart)
    return result


def tx_wdr(uart,imsi):
    '''
    wdrをsoracom FUNK に送信します。

    uart = 対応機器のuartインスタンスが必要
    json_dict['IMSI']= IMSI番号str
    json_dict['txt'] = 送信テキスト
    '''
    word_count = str(22 + len(imsi))
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
    uart.write('{"dt":"wdr","IMSI":"'+imsi+'"}\r')
    recive(uart)
    uart.write('AT+SHREQ="/post",3\r')
    recive(uart)
    uart.write('AT+SHREAD=0,1024\r')
    recive(uart)
    uart.write('AT+SHDISC\r')
    recive(uart)
    return

def get_sleep_time(uart):
    uart.write('AT+CCLK?\r')
    time_sim = recive(uart).decode()
    time_sim = extract_hour(time_sim)
    sleep_time = calculate_hours_until_4(time_sim)
    return sleep_time


def watch_dog_thread(uart_sim, gpio_sim):
    gpio_sim.value(1)
    utime.sleep(3)
    setup_sim(uart_sim)
    imsi = get_imsi(uart_sim)
    up_result = tx_wdu(uart_sim,imsi)
    if '"POST",200' not in up_result:
        while True:
            led_ok() #エラー時
    sleep_time = get_sleep_time(uart_sim) * 60 * 60
    if sleep_time == 86400:
        tx_wdr(uart_sim,imsi)
    gpio_sim.value(0)
    utime.sleep(sleep_time)
    
        
    while True:
        gpio_sim.value(1)
        utime.sleep(3)
        setup_sim(uart_sim)
        tx_wdr(uart_sim,imsi)
        sleep_time = get_sleep_time(uart_sim) * 60 * 60
        if sleep_time == 0:
            sleep_time = 86400
        gpio_sim.value(0)
        if sleep_time < 1800:
            break
        print(sleep_time)
        utime.sleep(sleep_time)




def main():
    try:
        pass
    except:
        while True:
            led_ok() #エラー時
    #led_ok() #起動完了
            
    # UART番号とボーレートを指定
    uart_sim = UART(0, 115200)
    uart_lora = UART(1, 9600)
    gpio_sim = machine.Pin(22, machine.Pin.OUT)
    
    _thread.start_new_thread(watch_dog_thread,(uart_sim, gpio_sim))
    setup_lora(uart_lora)


    ############# 受信時
    rx_row_data = rx_lora(uart_lora)
    rx_str_data = pick_lora_data(rx_row_data)
    print('#####')
    print(rx_row_data)
    header_data = f'j314t+{config.version}'.encode('utf-8').hex()
    if header_data.lower() in rx_str_data.lower():
        gpio_sim.value(1)        #SIM7080Gの電源を入れる
        utime.sleep(3)
        setup_sim(uart_sim)
        tx_json_data = {'dt': 'alt'}
        tx_json_data['IMSI'] = get_imsi(uart_sim)   #### honban okikae
        tx_json_data['txt'] = json_escape_string(rx_row_data)      #### honban okikae
        tx_json(uart_sim,tx_json_data)
        gpio_sim.value(0)       #SIM7080Gの電源を切る
        return_data = rx_str_data+'30'
        tx_return_lora(uart_lora, return_data)



    
    print('return 0 OK')
        





        



if __name__ == '__main__':
    main()


