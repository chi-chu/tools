import pandas as pd
import pymysql
import numpy as np
import sys
import time

import ctypes  
  
STD_INPUT_HANDLE = -10  
STD_OUTPUT_HANDLE= -11  
STD_ERROR_HANDLE = -12  
  
FOREGROUND_BLACK = 0x0  
FOREGROUND_BLUE = 0x01 # text color contains blue.  
FOREGROUND_GREEN= 0x02 # text color contains green.  
FOREGROUND_RED = 0x04 # text color contains red.  
FOREGROUND_INTENSITY = 0x08 # text color is intensified.  
  
BACKGROUND_BLUE = 0x10 # background color contains blue.  
BACKGROUND_GREEN= 0x20 # background color contains green.  
BACKGROUND_RED = 0x40 # background color contains red.  
BACKGROUND_INTENSITY = 0x80 # background color is intensified.  

ctypes.windll.kernel32.SetConsoleTextAttribute(ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE),
             FOREGROUND_RED | FOREGROUND_INTENSITY)
        
print('Worning you should use id to del   online')
print('Worning reminber to bakeup data')
print('Bakeup data')
print('Bakeup data')
print('Bakeup data')
print('Bakeup data')
print('Bakeup data')
#use this for red text for linux
#print('This is a \033[1;35m test \033[0m!')
ctypes.windll.kernel32.SetConsoleTextAttribute(ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE),
             FOREGROUND_RED | FOREGROUND_GREEN | FOREGROUND_BLUE)
#time.sleep(5)

copytradeDB = {"host":"192.168.8.34", "database":"copytrading", 
                    "user":"root", "password":"my-secret-pw", "port":3326, "charset":"utf8"}

dbobj = pymysql.connect(host=copytradeDB['host'], database=copytradeDB['database'], user=copytradeDB['user'],
                    password=copytradeDB['password'], port=copytradeDB['port'], charset=copytradeDB['charset'])
cursor = dbobj.cursor()

try:
    #first edit the name
    namedit = pd.read_excel('C:\\Users\\a\\Desktop\\select___from_t_broker.xls',
            usecols=["BrokerID", "Name","CompanyName"], 
            skipfooter=2082,
            )
    for index, row in namedit.iterrows():
        cursor.execute("update t_broker set CompanyName='%s' where BrokerID=%d" % (row["CompanyName"],row["BrokerID"]))
        pass
    dbobj.commit()

    del_broker_data = pd.read_excel("C:\\Users\\a\\Desktop\\全经纪商维护表.xlsx",
            usecols=["BrokerID", "Name","Operation（1保留 2合并）"], 
            #dtype={"Operation（1保留 2合并）":np.int32},
            )
    #print(del_broker_data["Operation（1保留 2合并）"].dropna().astype(np.int))
    #print(del_broker_data[np.isnan(del_broker_data["Operation（1保留 2合并）"])].index)
    del_broker_data.drop(del_broker_data[np.isnan(del_broker_data["Operation（1保留 2合并）"])].index, inplace=True)
    #or use  .apply(xxxx,  pd.to_numberic)
    del_broker_data["Operation（1保留 2合并）"] = del_broker_data["Operation（1保留 2合并）"].astype(np.int)
    
    for index, row in del_broker_data.iterrows():
        if row["Operation（1保留 2合并）"] == 1:
            continue
        else:
            #for test use
            sql = "select BrokerID from t_broker where Name ='%s'" % row["Name"]
            cursor.execute(sql)
            data = cursor.fetchone()
            print(data)
            if data is not None:
                samsql = "select id from sam.t_app where broker_id = %d" % data[0]
                cursor.execute(samsql)
                samdata = cursor.fetchone()
                if samdata is None:
                    #del this t_broker   t_mt4_server
                    cursor.execute("delete from t_broker where BrokerID=%d" % data[0])
                    cursor.execute("delete from sam.t_mt4_server where broker_id=%d" % data[0])
                    #print("name :"+ str(row) +" has no appuser")
                    pass
                else:
                    
                    print('======'+str(row)+"==="+str(data)+"======")
                    pass
            else:
                print("Not find borker data  ROW", str(row))
                pass
    dbobj.commit()
except Exception as e:
    print('row :' + str(row)+ str(e))
finally:
    dbobj.close()
    pass

print("finish task!")
