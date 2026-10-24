import anthropic
import os
import json
import oracledb

BASE_DIR=os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH=os.path.join(BASE_DIR,'json.config')
with open (CONFIG_PATH,'r') as c:
    params=json.load(c)["params"]

try:
   client=anthropic.Anthropic(
   api_key=params['anthropic_api_key']
      )
   print(f"Claude Connected")
except Exception as e:
    print( f"Error in connection Claude {e}")

oracledb.init_oracle_client(lib_dir=r"C:\instantclient_21_11")

try:
    conn=oracledb.connect( 
     user=params['oracle_user'],
    password=params['oracle_password'],
    dsn=params['oracle_dsn']
    )
    print(f"oracle connected")
except Exception as e:
        print( f"Error in connection Oracle DB {e}")

message=client.messages.create(
     model="claude-sonnet-4-6",
     max_tokens=1500,
     temperature=0,
     system="""You are Oracle EBS Technical Expert R12.2.10.

STRICT RULES:
1. Return ONLY plain SQL query
2. NO markdown
3. NO code blocks
4. NO backticks
5. NO ```sql tags
6. NO explanations
7. NO semicolon at end
8. Plain text SQL only!""",
     messages=[
          {
          "role":"user",
          "content": """Write SQL to get top 100 active vendors 
    from ap_suppliers table.
    Use only these columns:
    VENDOR_ID, VENDOR_NAME, SEGMENT1, 
    VENDOR_TYPE_LOOKUP_CODE, ENABLED_FLAG,
    START_DATE_ACTIVE, END_DATE_ACTIVE,
    CREATION_DATE
    Filter: enabled_flag = 'Y'
    Limit: 100 rows using ROWNUM"""
         }
         ]
     )
sql=message.content[0].text
sql = sql.strip().rstrip(';')
print(f"Generated SQL: {sql}")
cursor=conn.cursor()
cursor.execute(sql)
results=cursor.fetchall()
print(f"Results:{results}")


