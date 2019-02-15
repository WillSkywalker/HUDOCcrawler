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



if __name__ == '__main__':
    get_document('001-189791', 'CASE OF SA-CAPITAL OY v. FINLAND')

