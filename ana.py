import json
import re
from time import sleep
import yaml

import requests
from lxml import html
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.keys import Keys


options = ChromeOptions()
# ヘッドレスモードを有効にする（次の行をコメントアウトすると画面が表示される）。
options.add_argument('--headless')
# ChromeのWebbrowserオブジェクトを作成する。
browser = Chrome(options=options)
browser.set_window_size(1024, 800)

# anaのトップ画面を開く。
browser.get('https://www.ana.co.jp/ja/jp/')

# IDとパスワードを入力して送信する。
f = open('config/ana_private.yaml', 'r+')
private_conf = yaml.load(f)

input_element = browser.find_element_by_class_name('input-id')
input_element.send_keys(private_conf.get('custno'))
input_element_pass = browser.find_element_by_class_name('input-pw')
input_element_pass.send_keys(private_conf.get('password'))
input_element_pass.send_keys(Keys.RETURN)

# ログイン確認画面で次の画面へのリンクをクリックする
browser.find_element_by_xpath('//*[@id="contents"]/div/div/form/div[3]/div/div[2]/p/a').click()

# 検索画面へ
browser.find_element_by_xpath('//*[@id="Gnav"]/ul/li[5]/a').click()

# browser.save_screenshot('/tmp/ana/chrome_search_results2-1.png')
browser.find_element_by_xpath('//*[@id="module-privilege"]/div/div[1]/ul/li[3]').click()
sleep(0.3)
# browser.save_screenshot('/tmp/ana/chrome_search_results2-2.png')
browser.find_element_by_xpath('//*[@id="module-privilege"]/div/div[2]/div[3]/div/dl/dd[1]/ul/li[1]/a').click()
sleep(0.3)
# browser.save_screenshot('/tmp/ana/chrome_search_results2-3.png')
browser.find_element_by_xpath('//*[@id="conditionInput"]/ul[2]/li[2]/a').click()
sleep(0.3)
# browser.save_screenshot('/tmp/ana/chrome_search_results2-4.png')

# 出発日1
browser.find_element_by_xpath('//*[@id="requestedSegment:0:departureDate:field_pctext"]').click()
# browser.save_screenshot('/tmp/ana/chrome_search_results2-5.png')
browser.find_element_by_xpath('//*[@id="calsec2"]/table/tbody/tr[4]/td[1]/a').click()

# 出発地1
browser.find_element_by_xpath('//*[@id="requestedSegment1"]/dl[2]/dd/a[2]').click()
browser.find_element_by_xpath('//*[@id="requestedSegment:0:departureAirportCode:field_region_62"]').click()
# browser.save_screenshot('/tmp/ana/chrome_search_results2-6.png')
browser.find_element_by_xpath('//*[@id="BKK+"]').click()
# 到着地1
browser.find_element_by_xpath('//*[@id="requestedSegment1"]/dl[3]/dd/a[2]').click()
browser.find_element_by_xpath('//*[@id="TYO"]').click()
# 出発日2
browser.find_element_by_xpath('//*[@id="requestedSegment:1:departureDate:field_pctext"]').click()
browser.find_element_by_xpath('//*[@id="calsec2"]/table/tbody/tr[4]/td[2]/a').click()
# 出発地2
browser.find_element_by_xpath('//*[@id="requestedSegment2"]/dl[2]/dd/a[2]').click()
browser.find_element_by_xpath('//*[@id="TYO"]').click()
# 到着地2
browser.find_element_by_xpath('//*[@id="requestedSegment2"]/dl[3]/dd/a[2]').click()
browser.find_element_by_xpath('//*[@id="requestedSegment:1:arrivalAirportCode:field_region_62"]').click()
browser.find_element_by_xpath('//*[@id="BKK+"]').click()
# browser.save_screenshot('/tmp/ana/chrome_search_results3-1.png')

# 検索
browser.find_element_by_xpath('//*[@id="searchForm"]/div[2]/p[2]/input').click()
browser.save_screenshot('/tmp/ana/chrome_search_results3-2.png')

text = browser.page_source.encode('utf-8')
dom = html.fromstring(text)
xpath = "//tr[@class='oneWayDisplayPlan']"

messages = []  # type: list
for flight in dom.xpath(xpath):
    path_for_flight_type = "th[@class='timeSchedule']/div[@class='timeScheduleFooter']/p[@class='flightScheduleToggle']"
    path_for_flight_type_b = "th[@class='timeSchedule']/div[@class='timeScheduleFooter hasStarAlliance']/p[@class='flightScheduleToggle']"
    flight_type = flight.find(path_for_flight_type)
    if flight_type is None:
        flight_type = flight.find(path_for_flight_type_b)
    if flight_type is None:
        continue
    if flight_type.text.strip() != '直行便':
        continue
    path_for_time = "th[@class='timeSchedule']/p[@class='flightTime']"
    time = flight.find(path_for_time).text_content().strip()
    time = re.sub('\n|\t', ' ', time)
    time = re.sub(' +', ' ', time)

    if '翌日' not in time:
        continue

    path_for_business = "*[2]"
    business = flight.find(path_for_business).text_content()
    business = re.sub('\n|\t', ' ', business)
    business = re.sub(' +', ' ', business)
    messages.append(time + ' ' + business)

slack_webhook_url = private_conf.get('slack_webhook_url')
requests.post(slack_webhook_url, data=json.dumps({
    'text': '\n'.join(messages),
    'username': '特典航空券チェッカー',
}))
