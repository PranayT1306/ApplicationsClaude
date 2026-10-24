import anthropic
import oracledb
import os
import json

BASE_DIR=os.path.dirname(os.path.abspath(__file__))
config_path=os.path.join(BASE_DIR,'json.config')
with open (config_path,'r') as c:
    params=json.load(c)["params"]

client=anthropic.Anthropic(
    api_key=params["anthropic_api_key"]
)
oracledb.init_oracle_client(lib_dir=r"C:\instantclient_21_11")
conn=oracledb.connect(
    user=params['oracle_user'],
    password=params['oracle_password'],
    dsn=params['oracle_dsn']
)

cursor=conn.cursor()
cursor.execute('select 1 from dual')
print(cursor.fetchone())
print("oracle connected!")