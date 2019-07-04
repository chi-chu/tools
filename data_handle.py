import pandas as pd
import pymysql
import numpy as np


copytradeDB = {"host":"192.168.8.34", "database":"copytrading", 
                    "user":"root", "password":"my-secret-pw", "port":3326, "charset":"utf8"}

dbobj = pymysql.connect(host=copytradeDB['host'], database=copytradeDB['database'], user=copytradeDB['user'],
                    password=copytradeDB['password'], port=copytradeDB['port'], charset=copytradeDB['charset'])
cursor = dbobj.cursor()

try:
    del_broker_data = pd.read_excel("C:\\Users\\a\\Desktop\\全经纪商维护表.xlsx",
            usecols=["BrokerID", "Name","Operation（1保留 2合并）"], 
            #dtype={"Operation（1保留 2合并）":np.int32},
            )
    #print(del_broker_data["Operation（1保留 2合并）"].dropna().astype(np.int))
    #print(del_broker_data[np.isnan(del_broker_data["Operation（1保留 2合并）"])].index)
    del_broker_data.drop(del_broker_data[np.isnan(del_broker_data["Operation（1保留 2合并）"])].index, inplace=True)
    #or use  .apply(xxxx,  pd.to_numberic)
    del_broker_data["Operation（1保留 2合并）"] = del_broker_data["Operation（1保留 2合并）"].astype(np.int)
    print(del_broker_data)
    for index, row in del_broker_data.iterrows():
        if row["Operation（1保留 2合并）"] == 1:
            continue
        else:
            #for test use
            sql = "select BrokerID from t_broker where Name ='%s'" % row["Name"]
            cursor.execute(sql)
            data = cursor.fetchone()
            if data is not None:
                samsql = "select id from sam.t_app where broker_id = %d" % data[0]
                cursor.execute(samsql)
                samdata = cursor.fetchone()
                if samdata is None:
                    #del this t_broker   t_mt4_server
                    #cursor.execute("delete from t_broker where BrokerID=%d" % data[0])
                    #cursor.execute("delete from sam.t_mt4_server where broker_id=%d" % data[0])
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
