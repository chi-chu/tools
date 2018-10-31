# -*- coding: utf-8 -*-

'''
desc:   python多进程 协程异步IO http请求
        python 无法实现共享mysql连接池。。
        shareMysqlPools = multiprocessing.Manager().list(mysqlPools)
        (暂未向面向对象编写。。。)
        taskkill /F /im python.exe
author: luyue
mail:   544625106@qq.com
'''

import multiprocessing
import os
import asyncio
import aiohttp
import pymysql
import time
import json
import argparse

#数据库配置
settings = {"host":"127.0.0.1", "database":"test", "user":"root", "password":"root", "port":3306, "charset":"utf8"}

def showHelp():
    parser = argparse.ArgumentParser(description='HTTP request Command: multiprocess and Coroutine, etc.')
    parser.add_argument('-p', type=int, help='How many process to start, you`d better write The CPU core number')
    parser.add_argument('-y', type=int, help='How many Coroutine to wait for http data')
    args = parser.parse_args()
    if args.p is None or args.y is None:
        parser.print_help()
        exit()
    else:
        return args


def getMysql():
    global settings 
    return pymysql.connect(host=settings['host'], database=settings['database'], user=settings['user'],
            password=settings['password'], port=settings['port'], charset=settings['charset'])

def yieldtrans(i, pdata):
    try:
        mydb = getMysql()
        cursor = mydb.cursor()
        while True:
            cursor.execute('select * from translatetask where status=1 and mod(id, '
                        + str(pdata[0])+ ') = '+ str(i) +' limit '+ str(pdata[0]*pdata[1]))
            taskdata = cursor.fetchall()
            if taskdata == ():
                #time.sleep(5)
                #print(mydb.ping(reconnect=True))
                raise Exception('Process '+str(i)+' Now time no task..')
            loop = asyncio.get_event_loop()
            tasks = [httptask(mydb, host) for host in taskdata]
            loop.run_until_complete(asyncio.wait(tasks))
    except Exception as e:
        print(str(e))
    finally:
        if mydb.ping(reconnect=False):
            mydb.close()
        return
    

async def httptask(mydb, host):
    print('http to  %s...' % host[1])
    payload = {'123':123}
    try:
        async with aiohttp.ClientSession() as session:
            #resp = await session.post(url=host, data=json.dumps(payload))
            resp = await session.get(url=host[1], 
                headers = {"Proxy-Connection": "keep-alive", 
                            "Pragma": "no-cache", 
                            "Cache-Control": "no-cache", 
                            "User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36", 
                            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8", 
                            "DNT": "1", 
                            "Accept-Encoding": "gzip, deflate, sdch", 
                            "Accept-Language": "zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4"})
            if resp.status != 200:
                print('id=', host[0], host[1], 'CURL error http status:', resp.status)
                transdata = None
            else:
                transdata = await resp.text()
                #print(transdata)
                #print(resp.headers)
    except asyncio.TimeoutError:
        print("Timeout, skipping {}".format(host[1]))
    except Exception as e:
        print(host[1], 'Something wrong with curl server', str(e))
    finally:
        mydb.cursor().execute('update translatetask set status=status+1 where id='+ str(host[0]))
        mydb.commit()
    

if __name__ == '__main__':
    pcsetting = showHelp()
    start = time.time()
    try:
        p = multiprocessing.Pool(pcsetting.p)
        for i in range(pcsetting.p):
            p.apply_async(yieldtrans, args=(i, [pcsetting.p, pcsetting.y]))
        p.close()
        p.join()
        print('All subprocesses done.')
    except Exception as e:
        print(str(e))
    else:
        pass
    finally:
        end = time.time()
        print('script run time:', str(end-start),'seconds exit')
    
    

    