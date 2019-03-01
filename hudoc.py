#!/usr/bin/env python3

import os
import time
import logging
import argparse
import grequests
import requests
import pandas
from urllib.parse import unquote

DOC_PDF_URL = 'https://hudoc.echr.coe.int/app/conversion/pdf?library=ECHR&id=%s&filename=%s.pdf'
LIST_WITH_ARTICLE_URL = 'https://hudoc.echr.coe.int/app/query/results?query=contentsitename:ECHR AND (NOT (doctype=PR OR doctype=HFCOMOLD OR doctype=HECOMOLD)) AND ((languageisocode="%s")) AND ((article=%d)) AND ((documentcollectionid="%s"))&select=sharepointid,Rank,ECHRRanking,itemid,docname,doctype,application,appno,conclusion,importance,originatingbody,typedescription,kpdate,extractedappno,doctypebranch,respondent&sort=&start=%d&length=%d&rankingModelId=1111111-0000-0000-0000-0000'
LIST_FULL_URL = 'https://hudoc.echr.coe.int/app/query/results?query=contentsitename:ECHR AND (NOT (doctype=PR OR doctype=HFCOMOLD OR doctype=HECOMOLD)) AND ((languageisocode="%s")) AND ((documentcollectionid="%s"))&select=sharepointid,Rank,ECHRRanking,itemid,docname,doctype,application,appno,conclusion,importance,originatingbody,typedescription,kpdate,extractedappno,doctypebranch,respondent&sort=&start=%d&length=%d&rankingModelId=1111111-0000-0000-0000-0000'

s = requests.session()
if not os.path.isdir('docs'):
    os.mkdir('docs')


def get_document(item_id, doc_name):
    res = s.get(DOC_PDF_URL % (item_id, doc_name))
    with open('docs/'+doc_name, 'wb') as f:
        f.write(res.content)


def get_document_list(col, article_no=None, lang='ENG'):
    if article_no:
        HEAD_URL = LIST_WITH_ARTICLE_URL % (lang, article_no, col, 0, 20)
    else:
        HEAD_URL = LIST_FULL_URL % (lang, col, 0, 20)

    res = s.get(HEAD_URL)
    length = res.json()['resultcount']
    print(length)
    docs = []
    # docs = pandas.DataFrame(columns=['name', 'id', 'appno', 'date', 'type', 'branch', 'conclusion', 'respondent', 'url'])
    for i in range(0, length, 1000):
        if article_no:
            resp = s.get(LIST_WITH_ARTICLE_URL % (lang, article_no, col, i, 1000))
        else:
            resp = s.get(LIST_FULL_URL % (lang, col, i, 1000))
        data = resp.json()
        for result in data['results']:
            res = result['columns']
            res['url'] = DOC_PDF_URL % (res['itemid'], res['docname'])
            docs.append(res)

    if i:
        if article_no:
            resp = s.get(LIST_WITH_ARTICLE_URL % (lang, article_no, col, i, 1000))
        else:
            resp = s.get(LIST_FULL_URL % (lang, col, i, 1000))
        data = resp.json()
        for result in data['results']:
            res = result['columns']
            res['url'] = DOC_PDF_URL % (res['itemid'], res['docname'])
            docs.append(res)

    df = pandas.DataFrame(data=docs)
    df.to_csv('Article%d_%s_%s.csv' % (article_no, col, lang))


def save_file(col, article_no):
    def wrapper(response, **kwargs):
        # print(response.__dict__)
        filename = unquote(response.url.split('filename=')[-1]).replace("/", "_")
        path = 'docs/%s/%s/' % (col, article_no)
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        with open(path+filename, 'wb') as f:
            f.write(response.content)
        response.close()
    return wrapper


def download_documents(col, article_no, lang='ENG'):
    def handler(r, msg):
        print('Error!')
        print(msg)
        print(r.url)
        print('Retrying...')
        try:
            save_file(col, article_no)(requests.get(r.url))
        except:
            logging.warning(r.url)
            print('Failed. File URL has been recorded in logging file.')

        if os.path.exists(unquote(r.url.split('filename=')[-1])):
            print('Successful.')

    df = pandas.read_csv('Article%d_%s_%s.csv' % (article_no, col, lang))
    urls = df['url'].tolist()
    for i in range(0, len(urls), 20):
        reqs = (grequests.get(url, callback=save_file(col, article_no), stream=False, timeout=50) for url in urls[i:i+20]
                if not os.path.exists('docs/%s/%s/%s' % (col, article_no, url.split('filename=')[-1].replace("/", "_"))))
        grequests.map(reqs, exception_handler=handler)
        print('%d%% finished... (%d out of %d)' % ((i/len(urls))*100, i, len(urls)))
        time.sleep(3)


def main():
    parser = argparse.ArgumentParser(description='Download cases from HUDOC')
    parser.add_argument('collection', type=str, help='Type of documents. Options: DECISIONS, JUDGMENTS, RESOLUTIONS')
    parser.add_argument('article', type=int, nargs='?', default=0,
                        help='The ECHR Article you want to investigate (default: all cases)')
    parser.add_argument('language', type=str, nargs='?', default='ENG',
                        help='Language code (default: ENG)')
    parser.add_argument('-d', '--download', help='Download pdf documents', action='store_true')
    parser.add_argument('-u', '--update', help='Update cases', action='store_true')
    args = vars(parser.parse_args())
    logging.basicConfig(filename='log_%d.log' % time.time(), level=logging.INFO, format='%(message)s')

    if args['update'] or not os.path.exists('Article%d_%s_%s.csv' % (args['article'], args['collection'], args['language'])):
        get_document_list(args['collection'], args['article'], args['language'])

    if args['download']:
        download_documents(args['collection'], args['article'], args['language'])


if __name__ == '__main__':
    main()
