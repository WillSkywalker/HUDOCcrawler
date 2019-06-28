import os
import pandas as pd
import pdftotext
from config import Config
from sqlalchemy import create_engine
from sqlalchemy.dialects import mysql


DIRECTORY = os.path.dirname(os.path.abspath(__file__))


def make_eng_txt(article, doctype, docname, raw_text=False):
    filename = os.path.join(DIRECTORY, 'docs/', doctype, str(article)+'/', docname.replace('/', '_'))
    print(filename)
    if os.path.exists(filename+'.txt'):
        with open(filename+'.txt') as f:
            text = f.read()
    else:
        with open(filename+'.pdf', "rb") as f:
            try:
                pdf = []
                for idx, page in enumerate(pdftotext.PDF(f)):
                    lines = page.split('\n')
                    if lines[0].strip()[:2].strip() == str(idx+1) or lines[0].strip()[-2:].strip() == str(idx+1):
                        pdf.append(' '.join(lines[1:]))
                    else:
                        pdf.append(' '.join(lines))
                text = "\n".join(pdf)
                with open(filename[:-4]+'.txt', 'w') as g:
                    g.write(text)
            except pdftotext.Error:
                return '' if raw_text else []
    if raw_text:
        if type(text) != str:
            return ''
        return text

    text = text.split('\n')
    lines = []
    for line in text:
        if line != '' and line != '\t*':
            for word in line.split():
                lines.append(word)
    return lines


def update_database(col, article=0, lang='ENG'):
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, encoding='utf-8', echo=True)
    collections = pd.read_csv(os.path.join(DIRECTORY, 'Article%d_%s_%s.csv' % (article, 'COMMUNICATEDCASES', lang)))
    decisions = pd.read_csv(os.path.join(DIRECTORY, 'Article%d_%s_%s.csv' % (article, 'DECISIONS', lang)))
    judgements = pd.read_csv(os.path.join(DIRECTORY, 'Article%d_%s_%s.csv' % (article, 'JUDGMENTS', lang)))

    def get_text(doctype):
        def func(docname):
            return make_eng_txt(article, doctype, docname, raw_text=True)
        return func

    dtype_dict = {'docname': mysql.TEXT(unicode=True),
                  'url': mysql.TEXT(unicode=True),
                  'text': mysql.LONGTEXT(unicode=True),
                  'extractedappno': mysql.LONGTEXT}

    collections['text'] = list(map(get_text('COMMUNICATEDCASES'), collections['docname'].tolist()))
    collections.to_sql('%d_CommunicatedCases' % article, engine, if_exists='replace', dtype=dtype_dict)
    del collections

    decisions['text'] = list(map(get_text('DECISIONS'), decisions['docname'].tolist()))
    decisions.to_sql('%d_Decisions' % article, engine, if_exists='replace', dtype=dtype_dict)
    del decisions

    judgements['text'] = list(map(get_text('JUDGMENTS'), judgements['docname'].tolist()))
    print(len(judgements['text']))
    judgements.to_sql('%d_Judgments' % article, engine, if_exists='replace', dtype=dtype_dict)

    with engine.connect() as con:
        con.execute('alter table %d_CommunicatedCases add column `id` int(10) unsigned PRIMARY KEY AUTO_INCREMENT;' % article)
        con.execute('alter table %d_Decisions add column `id` int(10) unsigned PRIMARY KEY AUTO_INCREMENT;' % article)
        con.execute('alter table %d_Judgments add column `id` int(10) unsigned PRIMARY KEY AUTO_INCREMENT;' % article)


if __name__ == '__main__':
    update_database()
