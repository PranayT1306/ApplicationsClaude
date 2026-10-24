import anthropic
import json
import os

BASE_DIR=os.path.dirname(__file__)
CONFIG_PATH=os.path.join(BASE_DIR,"json.config")
with open(CONFIG_PATH,'r') as c:
    params=json.load(c)["params"]

tools=[
    {
        "name":"get_inventory_details",
        "description":"Get status of inventory item ",
                "input_schema":{
            "type":"object",
            "properties":{
                "item_number":{
                    "type":"string",
                    "description":  "The Item number to check, e.g. A15487"
                }
            },
            "required":["item_number"]
        }
    }
    ]

client=anthropic.Anthropic(
    api_key=params["anthropic_api_key"]
)

def get_inventory_details(item_number):
    """ function fake data"""
    fake_data = {
        "A15487": "OBSOLETE",
        "A15488": "ACTIVE",
        "A15489": "INACTIVE"
    }
    return fake_data.get(item_number, "ITEM NOT FOUND")

# ── STEP 3: Ask Claude ────────────────────
print("Sending question to Claude...")

response=client.messages.create(
        model="claude-sonnet-4-6",
    max_tokens=1000,
    system="You are an Oracle EBS assistant. Use tools to fetch real data.",
    tools=tools,
    messages=[
        {"role": "user", "content": "What is the status of ITEM A15488?"}
    ]

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
    result = get_inventory_details(tool_input["item_number"])
    print(f"Function result: {result}")
      # ── STEP 6: Send result back to Claude ──
    final_response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system="You are an Oracle EBS assistant. Use tools to fetch real data.",
        tools=tools,
        messages=[
            {"role": "user", "content": "What is the status of  ITEM A15488?"},
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