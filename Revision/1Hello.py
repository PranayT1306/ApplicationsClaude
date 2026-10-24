import anthropic
import os
import json
import oracledb

BASE_DIR=os.path.dirname(os.path.abspath(__file__))
config_path=os.path.join(BASE_DIR,'json.config')
with open (config_path,'r') as c:
    params=json.load(c)["params"]


## This is extracting and passing anthropic api key value 
client=anthropic.Anthropic(
     api_key=params["anthropic_api_key"]
 )  

try:
    message=client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=100,
        messages=[{
            "role":"user",
            "content":"Hello Claude , nice to meet you , Im Pranay Tiwari , starting learning python , flask api and now eaget to use CLaude api"
        }]
    )
    print(message.content[0].text)
except Exception as e: 
    print(f"error {e}")
