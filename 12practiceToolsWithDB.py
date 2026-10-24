import anthropic
import os
import json
import oracledb
import pandas as pd

BASE_DIR=os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH=os.path.join(BASE_DIR,'json.config')
with open(CONFIG_PATH,'r') as c:
    params=json.load(c)["params"]
oracledb.init_oracle_client(lib_dir=r"C:\instantclient_21_11")

try:
 conn=oracledb.connect(
                user=params['oracle_user'],
                password=params['oracle_password'],
                dsn=params['oracle_dsn'])
 print("Oracle db connected successfully")
except Exception as e:
  print(f"Having issue in connecting Oracle db {e}")

tools=[
    {
           "name":"get_item_onhand_details",
        "description":"Get onhand information of inventory item ",
                "input_schema":{
            "type":"object",
            "properties":{
                "item_number":{
                    "type":"string",
                    "description":  "The onhand quantity of Item number to check, e.g. A15487"
                }
            },
            "required":["item_number"]
        }

}
]

def get_item_onhand_details(item_number):
   """ Item Onhand info"""
   sql = """select msib.segment1 item_number, 
         sum(moq.transaction_quantity) onhand_qty
         from mtl_system_items_b msib, 
              mtl_onhand_quantities moq 
         where moq.inventory_item_id = msib.inventory_item_id 
         and moq.organization_id = msib.organization_id 
         and msib.segment1 = :item_number
         group by msib.segment1"""
   cursor=conn.cursor()
   cursor.execute(sql, {"item_number": item_number})
   results=cursor.fetchall()
   if results:
    item, qty = results[0]
    return f"Item: {item}, Onhand Quantity: {qty}"
   else:
    return f"Item {item_number} not found in onhand quantities"

try:
    client=anthropic.Anthropic(
        api_key=params["anthropic_api_key"]

    )
    print("Claude API Successfully Validated")
except Exception as e:
    print(f"Error Connecting to Claude {e}")  

response=client.messages.create(
 model="claude-sonnet-4-6",
    max_tokens=1000,
    system="You are an Oracle EBS assistant. Use tools to fetch real data.",
    tools=tools,
      messages=[
        {"role": "user", "content": "What is the onhand quantity  of ITEM CM11222?"}]
)

print(f"Stop reason: {response.stop_reason}")
print(f"Response: {response.content}")

# ── STEP 4: Check if Claude wants a tool ──
# ── STEP 4: Check if Claude wants a tool ──

if response.stop_reason == "tool_use":
    
    # FIX: Loop to find the ToolUseBlock (not TextBlock)
    tool_use = None
    for block in response.content:
        if block.type == "tool_use":
            tool_use = block
            break
    
    tool_name = tool_use.name
    tool_input = tool_use.input
    print(f"\nClaude wants to call: {tool_name}")
    print(f"With parameters: {tool_input}")
        # ── STEP 5: YOU execute the function ──
    result = get_item_onhand_details(tool_input["item_number"])
    print(f"Function result: {result}")
      # ── STEP 6: Send result back to Claude ──
    final_response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system="You are an Oracle EBS assistant. Use tools to fetch real data.",
        tools=tools,
        messages=[
            {"role": "user", "content": "What is the onhand quantity  of ITEM CM11222?"},
            {"role": "assistant", "content": response.content},
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": result
                    }
                ]
            }
        ]
    )
    
    print(f"\nFinal Answer: {final_response.content[0].text}")









