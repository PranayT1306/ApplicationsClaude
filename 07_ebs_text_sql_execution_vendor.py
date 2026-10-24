import anthropic
import os
import json
import oracledb

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
    dsn=params["oracle_dsn"]
)
print("Claude connected!")
print("Oracle connected!")

message=client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=2000,
    temperature=0,
    system="""You are an oracle ebs technical expert ,please Show all vendors from po_vendors
    Rules:
     1. Return ONLY ONE SQL query
     2. No explanations
     3. No markdown
     4. No code blocks
     5. Plain SQL only!
     6. Limit rownum to 100
     7. no semicolon at the end of final query """,
     
    messages=[{
        "role":"user",
        "content":"please display vendor name from po_vendors table , only 100 records needed"
    }])

sql=message.content[0].text

cursor=conn.cursor()
cursor.execute(sql)
result=cursor.fetchall()
print(f"/n Results: {result}")
