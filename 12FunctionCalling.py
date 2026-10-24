import anthropic
import json
import os

BASE_DIR=os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH=os.path.join(BASE_DIR,'json.config')
with open(CONFIG_PATH,'r')as c:
    params=json.load(c)["params"]

client=anthropic.Anthropic(
    api_key=params['anthropic_api_key']
)

tools=[
    {
        "name": "get_po_status",
        "description": "Get the status of a Purchase Order from Oracle EBS",
        "input_schema":{
            "type":"object",
            "properties":{
                "po_number":{
                    "type":"string",
                    "description":  "The PO number to check, e.g. 4500012345"
                }
            },
            "required":["po_number"]
        }
        
    }
]

# ── STEP 2: Your actual Python function ───
def get_po_status(po_number):
    # Fake data for now — Oracle comes later!
    fake_data = {
        "4500012345": "APPROVED",
        "4500012346": "PENDING",
        "4500012347": "CANCELLED"
    }
    return fake_data.get(po_number, "PO NOT FOUND")

# ── STEP 3: Ask Claude ────────────────────
print("Sending question to Claude...")

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1000,
    system="You are an Oracle EBS assistant. Use tools to fetch real data.",
    tools=tools,
    messages=[
        {"role": "user", "content": "What is the status of PO 4500012345?"}
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
    result = get_po_status(tool_input["po_number"])
    print(f"Function result: {result}")
    
    # ── STEP 6: Send result back to Claude ──
    final_response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system="You are an Oracle EBS assistant. Use tools to fetch real data.",
        tools=tools,
        messages=[
            {"role": "user", "content": "What is the status of PO 4500012345?"},
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