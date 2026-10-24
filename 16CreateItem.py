import anthropic
import os
import oracledb
import json

BASE_DIR=os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH=os.path.join(BASE_DIR,'json.config')
with open (CONFIG_PATH,'r') as c:
    params=json.load(c)["params"]
oracledb.init_oracle_client(lib_dir=r"C:\instantclient_21_11")

try:
    client=anthropic.Anthropic(api_key=params["anthropic_api_key"])
    print(f"Anthropic Connection Successful")
except  Exception as e:
    print(f"Anthropic connection failed {e}")

try:
 conn=oracledb.connect(
    user=params["oracle_user"],
                       password=params["oracle_password"],
                       dsn=params["oracle_dsn"] 
      
        )
 print(f"Oracle Connection Successful")
except Exception as e:
   print(f"oracle connection failure {e}")

tool_create_item={
   "name":"create_item",
   "description":"Create a new inventory item in Oracle EBS by calling the item import procedure",
   "input_schema":{
      "type":"object",
      "properties":{
           "item_number": {
                "type": "string",
                "description": "The unique item number to create, e.g. PRANAYTEST2027"
            },
            "description": {
                "type": "string",
                "description": "Item description, e.g. TEST2ITEM"
            },
                 "master_org_code": {
                "type": "string",
                "description": "Master organization , e.g. V1"
            },
            "child_org_code": {
                "type": "string",
                "description": "Child Organization , e.g. H1"
            },
              "template_name": {
                "type": "string",
                "description": "Template name is  , e.g. Purchased Item"
            },
              "uom_code": {
                "type": "string",
                "description": "Child Organization , e.g. EA"
            } 
      },
      "required": ["item_number", "description", "master_org_code", "child_org_code",
                     "template_name ", "uom_code"]


               }



   }

tools = [tool_create_item]

def create_item(item_number,description,master_org_code,child_org_code,template_name,uom_code):
   try:
      """calling plsql function to import items"""
      cursor=conn.cursor()
      plsql= """
            BEGIN
                xx_item_import_sample(
                    :item_number,
                    :description,
                    :master_org_code,
                    :child_org_code,
                    :template_name,
                    :uom_code
                );
            END;
        """
      cursor.execute(plsql,{
                    "item_number" :item_number,
                    "description":description,
                    "master_org_code" :master_org_code,
                    "child_org_code":child_org_code,
                    "template_name" :template_name,
                    "uom_code" :uom_code
      })
      conn.commit()   # ← IMPORTANT: commit the INSERT
      return f"✅ Item created successfully! Item Number: {item_number} | Description: {description} | UOM: {uom_code}"
   
   except Exception as e:
        conn.rollback()
        return f"❌ Item creation failed: {str(e)}"
   


# ─────────────────────────────────────────
# 5. DISPATCHER
# ─────────────────────────────────────────
def call_function(name, inputs):
    if name == "create_item":
        return create_item(
            inputs["item_number"],
            inputs["description"],
            inputs["master_org_code"],
            inputs["child_org_code"],
            inputs["template_name"],
            inputs["uom_code"]
        )
    else:
        return f"Unknown function: {name}"
    
    # ─────────────────────────────────────────
# 6. MAIN LOOP
# ─────────────────────────────────────────
user_question = """Create a new inventory item with the following details:
    Item Number  : PRANAYClaudeAIITEM
    Description  : This item created through Claude API
    Master Org Code    : V1
    Child Org Code  : H1
    Template Name: Purchased Item
    UOM          : EA"""

messages = [{"role": "user", "content": user_question}]

print(f"\n🔍 Request: {user_question}\n")

while True:
    response=client.messages.create(
     model="claude-sonnet-4-6",
        max_tokens=1000,
        system="You are an Oracle EBS assistant. Use the create_item tool to create inventory items as requested.",
        tools=tools,
        messages=messages

    )
    print(f"Stop reason: {response.stop_reason}")

    if response.stop_reason == "end_turn":
        for block in response.content:
            if hasattr(block, "text"):
                print(f"\n✅ Final Answer:\n{block.text}")
        break

    if response.stop_reason == "tool_use":
        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"\n🔧 Claude calling tool: {block.name}")
                print(f"   Parameters: {json.dumps(block.input, indent=2)}")

                result = call_function(block.name, block.input)
                print(f"   DB Result: {result}")

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result
                })

        messages.append({"role": "user", "content": tool_results})


      