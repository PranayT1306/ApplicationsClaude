import anthropic
import os
import json


BASE_DIR=os.path.dirname(os.path.abspath(__file__))
config_path=os.path.join(BASE_DIR,'json.config')
with open (config_path,'r') as c: 
 params=json.load(c)["params"]
 
client=anthropic.Anthropic(
    api_key=params['anthropic_api_key']
  )

try:
 message=client.messages.create(
 model="claude-sonnet-4-6",
 max_tokens=500,
 system="You are Oracle SQL Expert, Return only Plain SQL. No explanations.",
 messages=[{
  "role":"user",
  "content":"write sql to get all the employees"
 }]
  )
 print(message.content[0].text)
except Exception as e:
 print(f"error is ",e)