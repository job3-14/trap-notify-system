# python3.9
# v2.3

import json
import boto3
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo
import binascii

def post_line_notify(line_api_token, contents):
    '''
    LineにPOSTを送信する関数
    line_api_token = line notifyのAPI
    contents = 送信するテキスト
    '''
    api_url = 'https://notify-api.line.me/api/notify'
    
    request_headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': 'Bearer' + ' ' + line_api_token
        }
    params = {'message': contents}
    data = urllib.parse.urlencode(params).encode('ascii')
    req = urllib.request.Request(api_url, headers=request_headers, data=data, method='POST')
    conn = urllib.request.urlopen(req)
    return


def get_all_records(dynamodb, table, **kwargs):
    '''
    DynamoDB上の全てのデータをScanする
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    '''
    while True:
        response = table.scan(**kwargs)
        if 'result_data' in locals():
            result_data.append(response['Items'])
        else:
            result_data = response['Items']
        if 'LastEvaluatedKey' not in response:
            break
        kwargs.update(ExclusiveStartKey=response['LastEvaluatedKey'])
    return result_data

def push_records(dynamodb, table, item,**kwargs):
    '''
    DynamoDB上に書き込みを行います
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    item = 書き込みたいテーブル(辞書)
    '''
    table.put_item(Item=item)
    return
    

def watchdog_check(dynamodb, table):
    '''
    DynamoDBから時間を確認し確認が取れなければ通知を送信する関数
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    '''
    # db取得
    base_data_list = get_all_records(dynamodb, table)
    
    # 確認と通知送信
    for base in base_data_list:
        print(base['name'])
        if base['watchdog']:
            base['watchdog'] = False
            push_records(dynamodb, table, base)
        else:
            contents = f'\n[通信不能] '+ base['name'] + f'が通信確認取れません。\n\n' + '最終確認時刻：' + base['timeStamp'] + f'\nIMSI：' + base['id']
            post_line_notify(base['LineNotifyApi'],contents)
    return

def get_query_record(dynamodb, table, key):
    '''
    dynamodbから特定のクエリを検索します
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    key = 出力するメインキー
    '''
    response = table.get_item(Key={'id': key})
    print('############')
    print(response)
    result_data = response['Item']
    return result_data



def watchdog_write(dynamodb, table, imsi, watchdog):
    '''
    watchdogを受信し時刻を書き換える
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    imsi = id
    watchdog = True->watchdog False->起動時  通知の有無です.
    '''
    result_data = get_query_record(dynamodb, table, imsi)
    result_data['watchdog'] = watchdog
    # 現在の時間を取得
    tokyo_tz = ZoneInfo('Asia/Tokyo')
    current_time = str(datetime.now(tokyo_tz))
    result_data['timeStamp'] = current_time
    push_records(dynamodb, table, result_data)
    return

def alert(dynamodb, table_base, table_sub, imsi, txt):
    '''
    アラートを発信する
    dynamodb = boto3.resource('dynamodb')
    table_base = dynamodb.Table(table_name親機)
    table_sub = dynamodb.Table(table_name子機)
    IMSI = 発信機親機IMSI
    txt = 受信内容
    '''
    # imsiからAPIを取得
    base_result = get_query_record(dynamodb, table_base, imsi)
    api = base_result['LineNotifyApi']
    
    # 受信内容を解析
    rx_data = rx_decode(txt)  # 16進数から文字列に変換
    sn = take_sn(rx_data)  #シリアルナンバー
    info = rx_info(txt) #電波強度など
    
    
    # 子機の名前をシリアルナンバーから取得
    sub_name = get_query_record(dynamodb, table_sub, sn)
    sub_name = sub_name['name']
    
    # タイムスタンプ更新
    watchdog_write(dynamodb, table_base, imsi, False)

    # 通知送信
    contents = sub_name + 'が発信されました\n\n' + info
    post_line_notify(api, contents)
    return


def alert_boot(dynamodb, table_base, imsi):
    '''
    起動アラートを発信する
    dynamodb = boto3.resource('dynamodb')
    table_base = dynamodb.Table(table_name親機)
    IMSI = 発信機親機IMSI
    '''
    # imsiからAPIを取得
    base_result = get_query_record(dynamodb, table_base, imsi)
    api = base_result['LineNotifyApi']
    base_name = base_result['name']

    # 通知送信
    contents = base_name + 'が起動しました'
    post_line_notify(api, contents)
    return

    
def rx_decode(data):
    '''
    loraからのデータから受信データを16進数から文字列に変換してstrで返す
    
    data = '+TEST: LEN:21, RSSI:-113, SNR:-6\n+TEST: RX "6A333134742B76322F35323A36303A44323A45382F"'
    '''
    sn_index = []
    sn_index.append(data.find('RX')+4)
    sn_index.append(data.rfind('"'))
    sn = data[sn_index[0]:sn_index[1]].encode()
    sn = binascii.unhexlify(sn).decode('utf-8')
    return sn


def rx_info(data):
    '''
    loraからのデータの付属情報を返す
    data = '+TEST: LEN:21, RSSI:-113, SNR:-6\n+TEST: RX "6A333134742B76322F35323A36303A44323A45382F"'
    '''
    index = []
    index.append(data.find('RSSI'))
    index.append(data.rfind('+TEST')-2)
    data_info = data[index[0]:index[1]]
    return data_info


def take_sn(data):
    '''
    受信データからシリアルナンバーを抽出する
    data = 'j314t+v2/52:60:D2:E8/'
    '''
    index = []
    index.append(data.find('/')+1)
    index.append(data.rfind('/'))
    data_info = data[index[0]:index[1]]
    return data_info
    


### main
def lambda_handler(event, context):
    #post_line_notify('6PXw02i28OwCMycNcdpZ8KqlJZUWP8BcFn5rz9xuBql', 'プログラム実行') ##########test
    table_name_base = 'Trap_notify_Kamigamo_base'
    table_name = 'Trap_notify_Kamigamo'
    #try:
    if event['dt'] == 'wdc':   ### タイマーwatchdog監視
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(table_name_base)
        watchdog_check(dynamodb, table)

    elif event['dt'] == 'wdr':   ### WatchDog受信
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(table_name_base)
        watchdog_write(dynamodb, table, event['IMSI'], True)

    elif event['dt'] == 'wdu':   ### 起動受信
        dynamodb = boto3.resource('dynamodb')
        table_base = dynamodb.Table(table_name_base)
        watchdog_write(dynamodb, table_base, event['IMSI'], False)
        alert_boot(dynamodb, table_base, event['IMSI'])
    
    elif event['dt'] == 'alt':
        dynamodb = boto3.resource('dynamodb')
        table_base = dynamodb.Table(table_name_base)
        table_sub = dynamodb.Table(table_name)
        alert(dynamodb, table_base, table_sub, event['IMSI'], event['txt'])
        
        
        
    return {'statusCode': 200}
    #except:
        # エラーSMS
        #return {'statusCode': 500}

# {"dt": "wdc"}
# wdc -> ウォッチドッグ確認 {"dt": "wdc"}
# wdr -> ウォッチドック受信 {"dt": "wdr", "IMSI":"IMSI:testnumber"}
# wdu -> 起動通信(timestampのみ更新) {"dt": "wdu", "IMSI":"IMSI:testnumber"}
# alt -> アラート {"dt": "alt", "IMSI":"IMSI:testnumber", "txt":"テキスト"}