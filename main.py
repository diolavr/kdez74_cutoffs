# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import requests, lxml.etree, io, os, hashlib

# Consts
USER_AGENT = 'repairer/myhome'
ACCEPT_CONTENT = 'text/html; charset=utf-8'

TARGET_URL = 'https://www.kdez74.ru/HouseSearch/CutOffs'

# xPathes
XPATH_MAINCONTENT = '//*[@id="MainContent"]'
XPATH_GOOD = '//*[@id="MainContent"]/div'
XPATH_TABLE = '//*[@id="cutoff_table"]'
XPATH_TABLE_ROWS = './/tbody/tr'
XPATH_TABLE_COLS = './/td'
XPATH_TEXT = './/text()'

SUM_FILE = 'page.sum'

def readSum(file):
    if os.path.isfile(file):
        with open(file, 'r') as f:
            return f.read()
    return ''

def writeSum(file, value):
    if len(value) == 0:
        return 
        
    with open(file, 'w+') as f:
        f.write(value)
        f.flush()

def checkSum(s):
    if len(s) == 0:
        return False

    filesum = readSum(SUM_FILE)

    sum = hashlib.md5(s).hexdigest()
    
    if sum == filesum:
        return True

    writeSum(SUM_FILE, sum)

    return False

def main():

    headers = {
        'User-Agent': USER_AGENT,
        'Accept': ACCEPT_CONTENT
    }

    r = requests.get(TARGET_URL, headers=headers)

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

    string_data = main.xpath("string()")
    if checkSum(string_data.encode('utf-8')):
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

        # Если нет запланированных отключений
        msg = " ".join(text)
        print(msg)
        return

    tabletext = []
    # [<Element tr at 0x...>, ]
    for tr in table[0].xpath(XPATH_TABLE_ROWS):

        trtext = []
        # [<Element td at 0x...>, ]
        for td in tr.xpath(XPATH_TABLE_COLS):

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

        tabletext.append(' / '.join(trtext))
    # for tr (END)

    # Собрали список запланированных отключений
    print(tabletext)

if __name__ == '__main__':
    main()
