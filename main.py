# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import io, os, hashlib
import logging, sys
import lxml.etree
import requests, json

TG_BOT_TOKEN = ''
TG_CHANNEL_ID= ''
TG_URL_MSG = 'https://api.telegram.org/bot{}/sendMessage?chat_id={}&text='.format(TG_BOT_TOKEN, TG_CHANNEL_ID)

# Consts
USER_AGENT = 'repairer/myhome'
ACCEPT_CONTENT = 'text/html; charset=utf-8'

FIAS_ID = ''
TARGET_URL = 'https://www.kdez74.ru/HouseSearch/CutOffs{}'.format("/"+FIAS_ID)

# xPathes
XPATH_MAINCONTENT = '//*[@id="MainContent"]'
XPATH_GOOD = '//*[@id="MainContent"]/div'
XPATH_TABLE = '//*[@id="cutoff_table"]'
XPATH_TABLE_ROWS = './/tbody/tr'
XPATH_TABLE_COLS = './/td'
XPATH_TEXT = './/text()'

SUM_FILE = 'page.sum'

logger = logging.getLogger("KDEZ74_CUTOFFS")
formatter = logging.Formatter(fmt="%(asctime)s %(name)s.%(levelname)s: %(message)s", datefmt="%Y.%m.%d %H:%M:%S")
handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(formatter)
logger.setLevel(logging.INFO)
logger.addHandler(handler)


def write_log(msg):
    logger.info(msg)

def read_file(file):
    if os.path.isfile(file):
        with open(file, 'r', encoding='utf-8') as fp:
            return fp.read()
    return ''

def write_file(file, text):
    with open(file, 'w+', encoding='utf-8') as f:
        f.write(text)
        f.flush()


def decode(text):
    j = {}

    try:
        j = json.loads(text)
    except Exception as e:
        write_log(e)
    
    return j

def encode(obj):
    t = ''

    try:
        t = json.dumps(obj)
    except Exception as e:
        write_log(e)

    return t

def load_sum():
    text = read_file(SUM_FILE)

    if len(text) == 0:
        return {}
    
    return decode(text)

def save_sum(j):
    text = encode(j)
    write_file(SUM_FILE, text)

def checksum(s):
    return hashlib.md5(s).hexdigest()

def send_msg(msg):
    if TG_BOT_TOKEN == '' or TG_CHANNEL_ID == '':
        return
    try:
        requests.get(TG_URL_MSG+msg)
    except Exception as e:
        logger.info(e)

def request_page():
    if FIAS_ID == '':
        return None
        
    headers = {
        'User-Agent': USER_AGENT,
        'Accept': ACCEPT_CONTENT
    }

    return requests.get(TARGET_URL, headers=headers)

def main():
 
    r = request_page()
    if r is None:
        print('empty FIAS_ID')
        return

    if r.status_code != requests.codes.ok:
        print('status_code not equal ', requests.codes.ok)
        return

    # @tree - <lxml.etree._ElementTree object at 0x...>
    tree = lxml.etree.parse(io.StringIO(r.text), lxml.etree.HTMLParser())

    # @root - <Element html at 0x...>
    root = tree.getroot()

    # @root - <Element div at 0x...>
    main = root.xpath(XPATH_MAINCONTENT)
    if len(main) == 0:
        print('cant found node {}'.format(XPATH_MAINCONTENT))
        return

    main = main[0]

    sums = load_sum()
    mainblock_file_sum = sums.get('mainblock', '')
    
    text_data = main.xpath("string()")
    string_data = text_data.encode('utf-8')
    mainblock_html_sum = checksum(string_data)
    if mainblock_file_sum == mainblock_html_sum:
        print('no changes')
        return

    # @table - [<Element table at 0x...>, ]
    table = main.xpath(XPATH_TABLE)
    if len(table) == 0:

        text = []
        for nodes in main.xpath(XPATH_GOOD):
            for n in nodes.xpath(XPATH_TEXT):
                t = n.strip()
                if len(t) == 0:
                    continue

                text.append(t)

        if len(text) == 0:
            print('cant found any nodes')
            return

        # Если нет зарегистрированных отключений
        msg = " ".join(text)
        sum = checksum(msg.encode('utf-8'))
        
        logger.info(msg)
        send_msg(msg)
        save_sum({ 'mainblock': mainblock_html_sum, 'notices': [] })
        return

    notices = sums.get('notices', [])
    # [<Element tr at 0x...>, ]
    for tr in table[0].xpath(XPATH_TABLE_ROWS):

        trtext = []
        # [<Element td at 0x...>, ]
        for td in tr.xpath(XPATH_TABLE_COLS)[1:]:

            tdtext = []
            for nodes in td.xpath(XPATH_TEXT):
                t = nodes.strip()
                if len(t) == 0:
                    continue

                tdtext.append(t)
            # for nodes (END)

            if len(tdtext) == 0:
                continue

            trtext.append(' '.join(tdtext))
        # for td (END)

        if len(trtext) == 0:
            continue
        
        rtext_string = ' / '.join(trtext)
        sum = checksum(rtext_string.encode('utf-8'))

        if sum not in notices:
            logger.info("{}".format(rtext_string))
            send_msg('\n'.join(trtext))
            notices.append(sum)

    # for tr (END)

    save_sum({ 'mainblock': mainblock_html_sum, 'notices': notices })

if __name__ == '__main__':
    main()
