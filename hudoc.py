#!/usr/bin/env python3

import os
import requests
from bs4 import BeautifulSoup

s = requests.session()
if not os.path.isdir('docs'):
    os.mkdir('docs')

def get_document(item_id, doc_name):
    res = s.get('https://hudoc.echr.coe.int/app/conversion/docx/pdf?library=ECHR&id=%s&filename=%s.pdf' % (item_id, doc_name))
    with open('docs/'+doc_name, 'wb') as f:
        f.write(res.content)


def get_documents(col):
    res = s.get('https://hudoc.echr.coe.int/app/query/results?query=contentsitename%3AECHR%20AND%20(NOT%20(doctype%3DPR%20OR%20doctype%3DHFCOMOLD%20OR%20doctype%3DHECOMOLD))%20AND%20((languageisocode%3D%22ENG%22))%20AND%20((article%3D6))%20AND%20((documentcollectionid%3D%22%s%22))&select=sharepointid,Rank,ECHRRanking,languagenumber,itemid,docname,doctype,application,appno,conclusion,importance,originatingbody,typedescription,kpdate,kpdateAsText,documentcollectionid,documentcollectionid2,languageisocode,extractedappno,isplaceholder,doctypebranch,respondent,ecli,appnoparts,sclappnos&sort=&start=0&length=20&rankingModelId=11111111-0000-0000-0000-000000000000' % col)
    length =

if __name__ == '__main__':
    get_document('001-189791', 'CASE OF SA-CAPITAL OY v. FINLAND')

