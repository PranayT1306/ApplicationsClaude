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

message=client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=500,
    messages=[{
        "role":"user",
        "content":"what is oracle ebs in 3 lines?"
                }]
)
print(message.content[0].text)