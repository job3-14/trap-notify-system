from machine import Pin, I2C, UART
import time
import utime
#import config
import random

#LED制御
led = machine.Pin(25, machine.Pin.OUT)
led.value(1)

# UART番号とボーレートを指定
uart = UART(0, 115200)

#通信モジュールからのメッセージを受信(シリアル通信)
def recive():
    utime.sleep(1)
    for i in range(10):
        buf = uart.read(100)
        utime.sleep(0.3)
        if buf != None:
            print(buf)  #デバッグ時に使用!!!!!!!!!
            #return buf
    return

#LEDを点滅させる
def led_ok():
    for i in range(5):
        led.value(1)
        utime.sleep(0.3)
        led.value(0)
        utime.sleep(0.3)
    return



def main():
    try:
        uart.write('AT+CGDCONT=1,"IP","soracom.io"\r')
        recive()
        uart.write('AT+CGAUTH=1,3,"sora","sora@soracom.io" \r')
        recive()
        uart.write('AT+CNCFG=1,1,"soracom.io","sora@soracom.io","sora",3\r')
        recive()
        uart.write('AT+COPS=1,2,"44051"\r')
        recive()
        uart.write('AT+CGNAPN\r')
        recive()
        uart.write('AT+CNACT=0,1\r')
        recive()
        # ping
        uart.write('AT+SNPING4="google.com",3,16,5000\r')
        recive()


        
    except:
        while True:
            led_ok() #エラー時
    led_ok() #起動完了


if __name__ == '__main__':
    main()
