# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import requests
import lxml.etree
import io

# Consts
USER_AGENT = 'repairer/myhome'
ACCEPT_CONTENT = 'text/html; charset=utf-8'

TARGET_URL = 'https://www.kdez74.ru/HouseSearch/CutOffs'

# xPathes
XPATH_GOOD = '//*[@id="MainContent"]/div'
XPATH_TABLE = '//*[@id="cutoff_table"]'
XPATH_TABLE_ROWS = './/tbody/tr'
XPATH_TABLE_COLS = './/td'
XPATH_TEXT = './/text()'

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

    # @table - [<Element table at 0x...>, ]
    table = root.xpath(XPATH_TABLE)
    if len(table) == 0:

        text = []
        for nodes in root.xpath(XPATH_GOOD):
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
