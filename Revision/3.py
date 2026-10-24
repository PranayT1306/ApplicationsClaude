import anthropic
import json
import os
import oracledb

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(BASE_DIR, 'json.config')

with open(config_path, 'r') as c:
    params = json.load(c)["params"]

client = anthropic.Anthropic(
    api_key=params["anthropic_api_key"]
)

oracledb.init_oracle_client(lib_dir=r"C:\instantclient_21_11")
conn=oracledb.connect(
    user=params["oracle_user"],
    password=params["oracle_password"],
    dsn=params['oracle_dsn']
)
print ('claude connected')
print('oracle connected')

question = "Get all employees from IT department"

try:
    message = client.messages.create(    # ✅ same line!
        model="claude-sonnet-4-6",
        max_tokens=500,                   # ✅ integer!
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
6. NO semicolon at end!""",
        messages=[{
            "role": "user",
            "content": question
        }]
    )
    print(message.content[0].text)
    sql=message.content[0].text

except Exception as e:
    print(f"Error: {e}")

sql = sql.strip().rstrip(';')
print(f"{question}")
print(f"{sql}")
try:
 
 cursor=conn.cursor()
 cursor.execute(sql)
 results=cursor.fetchall()
 print (f"results :{results}")

except Exception as e:
   print(f"error {e}")

