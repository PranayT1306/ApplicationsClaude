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
    dsn=params['oracle_dsn']
    )
print("Claude connected!")
print("Oracle connected!")
question = "Get all employees from IT department"

 
message=client.messages.create( 
   model="claude-sonnet-4-6",
    max_tokens=500,
    temperature=0,
    system="""You are Oracle SQL expert.
         Table: XXFLASK_EMPLOYEE_INFO
         Columns: XXID, NAME, DEPT, SALARY, CONTACT_INFO
         Rules:
         1. Return only one SQL query
         2. No code blocks
         3. No explanations
         4. No Markdown
         5. Plain SQL only!
         6. NO semicolon at end! 
         """,
         messages=[{
            "role":"user",
            "content":question
         }]
)
sql=message.content[0].text
sql = sql.strip().rstrip(';')
print(f"{question}")
print(f"{sql}")
cursor=conn.cursor()
cursor.execute(sql)
results=cursor.fetchall()
print(f"Results :{results}")