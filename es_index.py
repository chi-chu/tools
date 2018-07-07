# -*- coding: utf-8 -*-
import logging
from elasticsearch import Elasticsearch
from sqlalchemy import create_engine
import json
import time
settings = {
    'number_of_shards': 2,
    'number_of_replicas': 1,
    'analysis': {
        'char_filter': {},
        'tokenizer': {
            'username_tokenizer': {
                'type': 'ngram',
                'min_gram': 3,
                'max_gram': 10,
                'token_chars': ['letter', 'digit']
            },
            'serial_number_tokenizer': {
                'type': 'edge_ngram',
                'min_gram': 3,
                'max_gram': 7,
                'token_chars': ['letter', 'digit']
            },
            'title_tokenizer': {
                'type': 'classic',
                'max_token_length': 30
            },
            "comma_tokenizer": {
                "type": "pattern",
                "pattern": ","
            }
        },
        'filter': {},
        'analyzer': {
            'username_analyzer': {
                'type': 'custom',
                'tokenizer': 'username_tokenizer',
                'filter': ['lowercase']
            },
            'serial_number_analyzer': {
                'type': 'custom',
                'tokenizer': 'serial_number_tokenizer',
                'filter': ['lowercase']
            },
            'title_analyzer': {
                'type': 'custom',
                'tokenizer': 'title_tokenizer',
                'filter': ['lowercase'],
                'char_filter': ['html_strip']
            },
            'comma_analyzer': {
                'type': 'custom',
                'tokenizer': 'comma_tokenizer'
            }
        }
    }
}

mappings = {
    'data': {
        'dynamic': False,
        'properties': {
            'sp_code': {'type': 'keyword'},
            #...
        }
    }
}

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

es = Elasticsearch(hosts=[{'host': '127.0.0.1', 'port': 9200}], timeout=30, max_retries=10, retry_on_timeout=True)

db = create_engine('mysql://username:password@127.0.0.1/database?charset=utf8', encoding='utf8')

res = es.indices.create(index='supplier', body={'settings': settings, 'mappings': mappings})
logging.info(res)

pageIndex = 0
page = 100
while True:
    fetch_obj = db.execute('SELECT * FROM table limit %d,%d' % (pageIndex*page, page))
    supplierData = fetch_obj.fetchall()
    if not supplierData:
        break
    else:
        sourceArr = []
        for row in supplierData:
            doc = dict()
            doc['sp_code'] = row['sp_code']
            #...
            temp = {'index':{'_index': 'supplier', '_id' : row['sp_code'], '_type': 'data'}}    #index
                    #{"field1" : "value1"}
            #temp = {'create':{'_index': 'supplier', '_id' : row['sp_code'], '_type': 'data'}}  #create
                    #{"field2" : "value2"}
            #temp = {'update':{'_index': 'supplier', '_id' : row['sp_code'], '_type': 'data'}}  #update
                    #{ "doc" : {"field3" : "value3"}}
            #temp = {'delete':{'_index': 'supplier', '_id' : row['sp_code'], '_type': 'data'}}  #delete
            sourceArr.append(temp)
            sourceArr.append(doc)
        res = es.bulk(body= '\n'.join((json.dumps(doc)+'') for doc in sourceArr) + '\n')
        # res data form:
        # {"took": 30, "errors": false,"items": [
        #       {"index": {"_index": "test","_type": "_doc", "_id": "1","_version": 1,"result": "created","_shards": 
        #                   {"total": 2,"successful": 1,"failed": 0},"status": 201,"_seq_no" : 0,"_primary_term": 1}}]
        # }
        if res['errors'] != False:
            print('error accoured in executing task on page %d' % pageIndex)
            logging.info(res)
            time.sleep(5)
        pageIndex = pageIndex + 1

print('all task finish!')
