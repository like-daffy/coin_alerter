import ast
import requests
from slacker import Slacker
import schedule
import time
import telegram

percent = 1.5 # BTC 변동 퍼센트 default 1.5%
rapid_percent = 5 # BTC 급변 퍼센트 default 5%
alert_once_percent = 1 # 알람 발생 후 alert_once_percent 변동 시 알람을 재발생시킴 default 1%

percent_alt = 1 # 알트 코인 변동 퍼센트 default 1%
rapid_percent_alt = 2 # 알트 코인 급변 퍼센트 default 2%


# 바이낸스 가격 정보를 가져오는 변수 선언
usd = [] # 바이낸스의 코인 가격을 텍스트 형태로 가져오는 임시 변수
coin_name = [] # 바이낸스의 코인 이름을 입력하는 변수
usdt_conv = [] # 바이낸스의 코인 현재 가격을 입력하는 변수, float 값
history_binance = [] # 바이낸스 코인별 60분 동안의 가격 정보를 입력하는 리스트, 이중배열로 이뤄짐
latest_value = [] # 바이낸스 코인 마지막으로 알림이 발생했을 때의 가격
counter_min = [] # 바이낸스 코인 알림 발생후 카운트 다운 (1분 단위로, 카운트 다운이 0일 시 다시 울림)
_30min_ago = [] # 바이낸스 30분 전 가격을 저장하는 변수
_15min_ago = [] # 바이낸스 15분 전 가격을 저장하는 변수
_5min_ago = [] # 바이낸스 5분 전 가격을 저장하는 변수
percent_30min = [] # 바이낸스 30분 전과 현재 변화율을 저장하는 변수
percent_15min = [] # 바이낸스 15분 전과 현재 변화율을 저장하는 변수
percent_5min = [] # 바이낸스 5분 전과 현재 변화율을 저장하는 변수
alert_on = [] # 바이낸스 코인 중 알람이 울렸다면 True, 울리지 않았다면 False 정보를 저장하는 변수
latest_before_value = [] # 바이낸스 코인 중 마지막으로 발생한 알람 시점의 퍼센트를 저장하는 변수


# 텔레그램 chat id 정보를 저장할 변수 선언
telgm_list = []  # 텔레그램 첫번째 채팅방 chat id 리스트
telgm_list_alt = []  # 텔레그램 두번째 채팅방 chat id 리스트

# 슬랙에 메시지를 보낼 수 있게 token을 준비
slack_token = '<토큰>'
slack = Slacker(slack_token)
slack_channel = "<채널 고유 ID>"
slack_channel_alt = "<채널 고유 ID>"
slack.chat.post_message(slack_channel, "BTC 변동 알림봇을 시작합니다.")
slack.chat.post_message(slack_channel_alt, "알트 코인 변동 알림봇을 시작합니다.")

# 텔레그램의 chat id를 추가하는 telegram_chat_id_add 함수 선언
def telegram_chat_id_add(updates, telgm_default_list, telgm_extra):
    telgm_list = []
    for telgm_i in updates:
        try:
            telgm_list.append(telgm_i['message']['chat']['id'])
        except Exception as e:
            telgm_list.append(telgm_i['channel_post']['chat']['id'])
    telgm_list = list(set(telgm_list))
    return telgm_list

# 텔레그램 업데이트 후 chat id를 telgm_list 첫번째 채팅방에 추가
telgm_token = '<텔레그램 토큰>'
telgm_bot = telegram.Bot(token = telgm_token)
telgm_updates = telgm_bot.get_updates()
telgm_list = telegram_chat_id_add(telgm_updates)

# 텔레그램 업데이트 후 chat id를 telgm_list_alt 두번째 채팅방에 추가
telgm_token_alt = '<텔레그램 토큰>'
telgm_bot_alt = telegram.Bot(token=telgm_token_alt)
telgm_updates_alt = telgm_bot_alt.get_updates()
telgm_list = telegram_chat_id_add(telgm_updates, telgm_default_list, [])

# 바이낸스 api 호출
binance_url = '<바이낸스 api URL>'
response = requests.get(binance_url)

# 알림봇 시작 알림
start_message_btc = "BTC 변동 알림봇을 재기동 합니다."
start_message_alt = "알트 코인 변동 알림봇을 재기동 합니다."
slack.chat.post_message(slack_channel, start_message_btc)
slack.chat.post_message(slack_channel_alt, start_message_alt)
try:
    for telgm_i in telgm_list:
        telgm_bot.sendMessage(chat_id=telgm_i, text=start_message_btc)
except:
    pass

try:
    for telgm_i in telgm_list_alt:
        telgm_bot_alt.sendMessage(chat_id=telgm_i, text=start_message_alt)
except:
    pass

# param의 첫째값 (0번째 값)은 BTC-USDT로 입력
param = [{'symbol': 'BTCUSDT'}, {'symbol': 'ETHUSDT'}, {'symbol': 'ETCUSDT'}, {'symbol': 'LTCUSDT'},
         {'symbol': 'BCHUSDT'}, {'symbol': 'EOSUSDT'}, {'symbol': 'DASHUSDT'}]

# 바이낸스의 코인 이름 입력
for coin_no in range(0, len(param)):
    coin_name_temp = param[coin_no]['symbol']
    coin_name_temp = coin_name_temp.replace('USDT','')
    coin_name.append(coin_name_temp)
    alert_on.append(False)
    latest_before_value.append(0)
    res = requests.get(binance_url + '/api/v3/avgPrice', params=param[coin_no])
    usd.append(ast.literal_eval(res.text))
    usdt_conv.append(float(usd[coin_no]["price"]))
    history_binance.append([])
    latest_value.append(0)
    counter_min.append(0)
    _30min_ago.append(0)
    _15min_ago.append(0)
    _5min_ago.append(0)
    percent_30min.append(0)
    percent_15min.append(0)
    percent_5min.append(0)

# 바이낸스 코인 가격 60분 - [0] ~ [59] 까지 현재 시세로 초기화
for coin_no in range(0, len(param)):
    for i in range(0, 60):
        history_binance[coin_no].append(usdt_conv[coin_no])

# 코인 파라매터 값을 함수로 값 전달
def call_value_param():
    return param

# 메시지를 일괄로 보내는 함수
def message_center(alert_message, coin_name):
    slack_message(alert_message, coin_name)
    telgm_message(alert_message, coin_name)

# 텔레그램 메시지를 보내는 함수
def telgm_message(alert_message, coin_name_check):
    global telgm_list, telgm_list_alt
    coin_name_check = coin_name_check[0:3]
    try:
        if coin_name_check == "BTC":
            for telgm_i in telgm_list:
                telgm_bot.sendMessage(chat_id=telgm_i, text=alert_message)
        else:
            for telgm_i in telgm_list_alt:
                telgm_bot_alt.sendMessage(chat_id=telgm_i, text=alert_message)
    except:
        pass

# 슬랙 메시지를 보내는 함수
def slack_message(alert_message, coin_name_check):
    coin_name_check = coin_name_check[0:3]
    if coin_name_check == "BTC":
        try:
            slack.chat.post_message(slack_channel, alert_message)
        except:
            pass
    else:
        try:
            slack.chat.post_message(slack_channel_alt, alert_message)
        except:
            pass

# 현재가격을 체크한 후 알람을 발생하는 함수
def current_percent(term, coin_no, coin_name, updown, value, alert_on):
    if alert_on == True:
        updown = ""
    if updown == "+":
        alert_message = str(term) + "분 기준 " + coin_name + " 상승, 퍼센트는 " + str('%.4f' % value) + " % 입니다."
        message_center(alert_message, coin_name)
        return 30
    if updown == "-":
        alert_message = str(term) + "분 기준 " + coin_name + " 하락, 퍼센트는 " + str('%.4f' % value) + " % 입니다."
        message_center(alert_message, coin_name)
        return 30
    if updown == "r+":
        alert_message = str(term) + "분 기준 " + coin_name + " 빠른 상승, 퍼센트는 " + str('%.4f' % value) + " % 입니다."
        message_center(alert_message, coin_name)
        return 30
    if updown == "r-":
        alert_message = str(term) + "분 기준 " + coin_name + " 빠른 하락, 퍼센트는 " + str('%.4f' % value) + " % 입니다."
        message_center(alert_message, coin_name)
        return 30
    return counter_min[coin_no]

# 알람이 발생한 이후 일정 퍼센트 이상 추가 변동이 있었는지 체크하는 함수
def check_alert_once(coin_no, latest_value):
    try:
        if abs(latest_before_value[coin_no] - latest_value) < alert_once_percent:
            return True
        else:
            return False
    except:
        return False

# "체크필요" 알림이 발생할 시 값을 리턴하는 함수
def check_latest_percent(latest_value, coin_no, alert_on):
    if alert_on == False:
        return latest_value
    else:
        return latest_before_value[coin_no]

# 스캐쥴러 함수
def job():
    global latest_before_value
    global counter_min
    global _30min_ago, _15min_ago, _5min_ago
    global percent_30min, percent_15min, percent_5min
    global alert_on
    global history_binance
    param = call_value_param()

    # 알람을 False 로 초기화
    for i in range(0, len(param)):
        alert_on[i] = False

    # 바이낸스 코인마다 가장 오래된 값은 버리고, 업데이트된 값을 입력
    for coin_no in range(0, len(param)):
        try:
            res = requests.get(binance_url + '/api/v3/avgPrice', params=param[coin_no])
            usd[coin_no] = (ast.literal_eval(res.text))
            usdt_conv[coin_no] = float(usd[coin_no]["price"])
            history_binance[coin_no].pop(0)
            history_binance[coin_no].append(str(usdt_conv[coin_no]))
        except:
            pass

    # 바이낸스의 비트코인은 1시간, 30분, 15분별로 값 입력, 변동률 계산
    _1hour_ago_btc = float(history_binance[0][0])
    _30min_ago_btc = float(history_binance[0][30])
    _15min_ago_btc = float(history_binance[0][45])
    percent_1hour_btc = float((usdt_conv[0] - _1hour_ago_btc) / usdt_conv[0] * 100)
    percent_30min_btc = float((usdt_conv[0] - _30min_ago_btc) / usdt_conv[0] * 100)
    percent_15min_btc = float((usdt_conv[0] - _15min_ago_btc) / usdt_conv[0] * 100)

    # 바이낸스 비트코인 이외의 코인은 30분, 15분, 5분별로 값 입력, 변동률 계산
    for coin_no in range(1, len(param)):
        _30min_ago[coin_no] = float(history_binance[coin_no][30])
        _15min_ago[coin_no] = float(history_binance[coin_no][45])
        _5min_ago[coin_no] = float(history_binance[coin_no][55])
        percent_30min[coin_no] = float((usdt_conv[coin_no] - _30min_ago[coin_no]) / usdt_conv[coin_no] * 100)
        percent_15min[coin_no] = float((usdt_conv[coin_no] - _15min_ago[coin_no]) / usdt_conv[coin_no] * 100)
        percent_5min[coin_no] = float((usdt_conv[coin_no] - _5min_ago[coin_no]) / usdt_conv[coin_no] * 100)

    # 바이낸스 BTC 변화율 체크후 알람 발생
    if percent_15min_btc > rapid_percent and alert_on[0] == False:
        alert_on[0] = check_alert_once(0, percent_15min_btc)
        counter_min[0] = current_percent(15, 0, coin_name[0], "r+", percent_15min_btc, alert_on[0])
        latest_before_value[0] = check_latest_percent(percent_15min_btc, 0, alert_on[0])
        alert_on[0] = True
    if percent_15min_btc < (-rapid_percent) and alert_on[0] == False:
        alert_on[0] = check_alert_once(0, percent_15min_btc)
        counter_min[0] = current_percent(15, 0, coin_name[0], "r+", percent_15min_btc, alert_on[0])
        latest_before_value[0] = check_latest_percent(percent_15min_btc, 0, alert_on[0])
        alert_on[0] = True
    if percent_30min_btc > percent and alert_on[0] == False:
        alert_on[0] = check_alert_once(0, percent_30min_btc)
        counter_min[0] = current_percent(30, 0, coin_name[0], "+", percent_30min_btc, alert_on[0])
        latest_before_value[0] = check_latest_percent(percent_30min_btc, 0, alert_on[0])
        alert_on[0] = True
    if percent_30min_btc < (-percent) and alert_on[0] == False:
        alert_on[0] = check_alert_once(0, percent_30min_btc)
        counter_min[0] = current_percent(30, 0, coin_name[0], "-", percent_30min_btc, alert_on[0])
        latest_before_value[0] = check_latest_percent(percent_30min_btc, 0, alert_on[0])
        alert_on[0] = True
    if percent_1hour_btc > percent and alert_on[0] == False:
        alert_on[0] = check_alert_once(0, percent_1hour_btc)
        counter_min[0] = current_percent(60, 0, coin_name[0], "+", percent_1hour_btc, alert_on[0])
        latest_before_value[0] = check_latest_percent(percent_1hour_btc, 0, alert_on[0])
        alert_on[0] = True
    if percent_1hour_btc < (-percent) and alert_on[0] == False:
        alert_on[0] = check_alert_once(0, percent_1hour_btc)
        counter_min[0] = current_percent(60, 0, coin_name[0], "-", percent_1hour_btc, alert_on[0])
        latest_before_value[0] = check_latest_percent(percent_1hour_btc, 0, alert_on[0])
        alert_on[0] = True

    # 바이낸스 알트 코인 변화율 체크후 알람 발생
    for coin_no in range(1, len(param)):
        if percent_5min[coin_no] > rapid_percent_alt and alert_on[coin_no] == False:
            alert_on[coin_no] = check_alert_once(coin_no, percent_5min[coin_no])
            counter_min[coin_no] = current_percent(5, coin_no, coin_name[coin_no], "r+",
                                                   percent_5min[coin_no], alert_on[coin_no])
            latest_before_value[coin_no] = check_latest_percent(percent_5min[coin_no], coin_no, alert_on[coin_no])
            alert_on[coin_no] = True
        if percent_5min[coin_no] < (-rapid_percent_alt) and alert_on[coin_no] == False:
            alert_on[coin_no] = check_alert_once(coin_no, percent_5min[coin_no])
            counter_min[coin_no] = current_percent(5, coin_no, coin_name[coin_no], "r-",
                                                   percent_5min[coin_no], alert_on[coin_no])
            latest_before_value[coin_no] = check_latest_percent(percent_5min[coin_no], coin_no, alert_on[coin_no])
            alert_on[coin_no] = True
        if percent_15min[coin_no] > percent_alt and alert_on[coin_no] == False:
            alert_on[coin_no] = check_alert_once(coin_no, percent_15min[coin_no])
            counter_min[coin_no] = current_percent(15, coin_no, coin_name[coin_no], "+",
                                                   percent_15min[coin_no], alert_on[coin_no])
            latest_before_value[coin_no] = check_latest_percent(percent_15min[coin_no], coin_no, alert_on[coin_no])
            alert_on[coin_no] = True
        if percent_15min[coin_no] < (-percent_alt) and alert_on[coin_no] == False:
            alert_on[coin_no] = check_alert_once(coin_no, percent_15min[coin_no])
            counter_min[coin_no] = current_percent(15, coin_no, coin_name[coin_no], "-",
                                                   percent_15min[coin_no], alert_on[coin_no])
            latest_before_value[coin_no] = check_latest_percent(percent_15min[coin_no], coin_no, alert_on[coin_no])
            alert_on[coin_no] = True
        if percent_30min[coin_no] > percent_alt and alert_on[coin_no] == False:
            alert_on[coin_no] = check_alert_once(coin_no, percent_30min[coin_no])
            counter_min[coin_no] = current_percent(30, coin_no, coin_name[coin_no], "+", percent_30min[coin_no], alert_on[coin_no])
            latest_before_value[coin_no] = check_latest_percent(percent_30min[coin_no], coin_no, alert_on[coin_no])
            alert_on[coin_no] = True
        if percent_30min[coin_no] < (-percent_alt) and alert_on[coin_no] == False:
            alert_on[coin_no] = check_alert_once(coin_no, percent_30min[coin_no])
            counter_min[coin_no] = current_percent(30, coin_no, coin_name[coin_no], "-", percent_30min[coin_no], alert_on[coin_no])
            latest_before_value[coin_no] = check_latest_percent(percent_30min[coin_no], coin_no, alert_on[coin_no])
            alert_on[coin_no] = True

    # 1분이 지날때마다 카운터를 1분씩 줄이며, 알림 울린 뒤 30분이 지났을 시 마지막 알람 발생 시 가격을 초기화
    for coin_no in range(0, len(param)):
        if counter_min[coin_no] != 0:
            counter_min[coin_no] -= 1
        elif counter_min[coin_no] == 0:
            latest_before_value[coin_no] = 0

schedule.every(1).minutes.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)
