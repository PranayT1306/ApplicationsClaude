import anthropic
import os
import oracledb
import json
import streamlit as st 

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

   # ─────────────────────────────────────────
# 2. EBS TOOL FUNCTIONS
# ─────────────────────────────────────────
def get_item_details(item_number):
    sql = """SELECT segment1 item_number, description,
                    inventory_item_status_code status,
                    primary_uom_code uom
             FROM mtl_system_items_b
             WHERE segment1 = :item_number
             AND rownum = 1"""
    cursor = conn.cursor()
    cursor.execute(sql, {"item_number": item_number})
    row = cursor.fetchone()
    if row:
        return f"Item: {row[0]} | Description: {row[1]} | Status: {row[2]} | UOM: {row[3]}"
    return f"Item {item_number} not found"

def get_item_onhand(item_number):
    sql = """SELECT msib.segment1, moq.subinventory_code,
                    SUM(moq.transaction_quantity) qty
             FROM mtl_onhand_quantities moq
             JOIN mtl_system_items_b msib
               ON moq.inventory_item_id = msib.inventory_item_id
              AND moq.organization_id = msib.organization_id
             WHERE msib.segment1 = :item_number
             GROUP BY msib.segment1, moq.subinventory_code"""
    cursor = conn.cursor()
    cursor.execute(sql, {"item_number": item_number})
    rows = cursor.fetchall()
    if rows:
        lines = [f"Subinv: {r[1]} | Qty: {r[2]}" for r in rows]
        return f"Onhand for {item_number}:\n" + "\n".join(lines)
    return f"No onhand found for {item_number}"



def create_item(item_number, description, master_org_code,
                child_org_code, template_name, uom_code):
    try:
        cursor = conn.cursor()
        plsql = """
            BEGIN
                xx_item_import_sample(
                    :item_number, :description,
                    :master_org_code, :child_org_code,
                    :template_name, :uom_code
                );
            END;
        """
        cursor.execute(plsql, {
            "item_number": item_number.upper(),
            "description": description,
            "master_org_code": master_org_code,
            "child_org_code": child_org_code,
            "template_name": template_name,
            "uom_code": uom_code
        })
        conn.commit()
        return f"✅ Item {item_number} created successfully!"
    except Exception as e:
        conn.rollback()
        return f"❌ Item creation failed: {str(e)}"

# ─────────────────────────────────────────
# 3. TOOL DEFINITIONS
# ─────────────────────────────────────────
tools =[
     {
    "name": "get_item_details",
    "description": "get inventory details from oracle EBS",
    "input_schema": {           # ✅ wrap in input_schema
        "type": "object",
        "properties": {
            "item_number": {"type": "string", "description": "Item number e.g. AS54888"}
        },
        "required": ["item_number"]
    }
},
            {
        "name": "get_item_onhand",
        "description": "Get item onhand quantity from Oracle EBS inventory",
        "input_schema": {
            "type": "object",
            "properties": {
                "item_number": {"type": "string", "description": "Item number e.g. AS54888"}
            },
            "required": ["item_number"]
        }
                
    },
 {
        "name": "create_item",
        "description": "Create a new inventory item in Oracle EBS",
        "input_schema": {
            "type": "object",
            "properties": {
                "item_number":     {"type": "string", "description": "Unique item number"},
                "description":     {"type": "string", "description": "Item description"},
                "master_org_code": {"type": "string", "description": "Master org e.g. V1"},
                "child_org_code":  {"type": "string", "description": "Child org e.g. H1"},
                "template_name":   {"type": "string", "description": "Template e.g. Purchased Item"},
                "uom_code":        {"type": "string", "description": "UOM e.g. EA"}
            },
            "required": ["item_number", "description", "master_org_code",
                         "child_org_code", "template_name", "uom_code"]
        }
    }

]

# ─────────────────────────────────────────
# 4. DISPATCHER
# ─────────────────────────────────────────
def call_function(name, inputs):
    if name == "get_item_details":
        return get_item_details(inputs["item_number"])
    elif name == "get_item_onhand":
        return get_item_onhand(inputs["item_number"])
    elif name == "create_item":
        return create_item(
            inputs["item_number"], inputs["description"],
            inputs["master_org_code"], inputs["child_org_code"],
            inputs["template_name"], inputs["uom_code"]
        )
    return f"Unknown tool: {name}"
# ─────────────────────────────────────────
# 5. CLAUDE WITH TOOLS
# ─────────────────────────────────────────

def ask_claude(messages):
    """Run claude with tools --handles tool use loop"""
    while True:
        response=client.messages.create(
                model="claude-sonnet-4-6",
            max_tokens=2000,
            system="You are an Oracle EBS AI Assistant. Help users query inventory and create items.",
            tools=tools,
            messages=messages
        )
        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = call_function(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })
            messages.append({"role": "user", "content": tool_results})
# Sidebar
with st.sidebar:
    st.title("🤖 Pranay Enterprise AI Assistant")
    st.success("✅ Oracle Connected")
    st.success("✅ Claude Connected")
    st.markdown("---")
    st.markdown("**Available Tools:**")
    st.markdown("- 📦 Item Details")
    st.markdown("- 📊 Item Onhand")
    st.markdown("- ➕ Create Item")
    st.markdown("---")
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.session_state.claude_messages = []
        st.rerun()

st.title("Pranay Enterprise AI Assistant 🤖")
st.caption("Ask me about inventory,  create new items!")
# ── SESSION STATE ──
if "messages" not in st.session_state:
    st.session_state.messages = []        # for display

if "claude_messages" not in st.session_state:
    st.session_state.claude_messages = [] # for Claude API

# ── DISPLAY CHAT HISTORY ──
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt:=st.chat_input("Ask about EBS... e.g. 'Show me details for item AS54888'"):
                          # Show user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Add to Claude messages
    st.session_state.claude_messages.append({"role": "user", "content": prompt})

    # Get Claude response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            answer = ask_claude(st.session_state.claude_messages)
            st.markdown(answer)

    # Save assistant response
    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.session_state.claude_messages.append({"role": "assistant", "content": answer})
