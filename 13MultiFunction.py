import anthropic
import os
import json
import oracledb

# ─────────────────────────────────────────
# 1. CONFIG & DB CONNECTION
# ─────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "json.config")

oracledb.init_oracle_client(lib_dir=r"C:\instantclient_21_11")

with open(CONFIG_PATH, 'r') as c:
    params = json.load(c)["params"]

try:
    conn = oracledb.connect(
        user=params['oracle_user'],
        password=params['oracle_password'],
        dsn=params['oracle_dsn']
    )
    print("✅ Oracle DB connected successfully")
except Exception as e:
    print(f"❌ Oracle connection failed: {e}")
    exit()

# ─────────────────────────────────────────
# 2. CLAUDE CLIENT
# ─────────────────────────────────────────
try:
    client = anthropic.Anthropic(api_key=params["anthropic_api_key"])
    print("✅ Claude API connected successfully")
except Exception as e:
    print(f"❌ Claude API failed: {e}")
    exit()

# ─────────────────────────────────────────
# 3. TOOL DEFINITIONS (flat dicts, not lists)
# ─────────────────────────────────────────
tool_item_details = {
    "name": "get_item_details",
    "description": "Get inventory item description, unit of measure, and status from Oracle EBS",
    "input_schema": {
        "type": "object",
        "properties": {
            "item_number": {
                "type": "string",
                "description": "The inventory item number, e.g. CM11222"
            }
        },
        "required": ["item_number"]
    }
}

tool_item_onhand = {
    "name": "get_item_onhand_details",
    "description": "Get current onhand quantity of an inventory item from Oracle EBS",
    "input_schema": {
        "type": "object",
        "properties": {
            "item_number": {
                "type": "string",
                "description": "The inventory item number, e.g. CM11222"
            }
        },
        "required": ["item_number"]
    }
}

tool_item_cost = {
    "name": "get_item_cost",
    "description": "Get standard frozen cost of an inventory item from Oracle EBS",
    "input_schema": {
        "type": "object",
        "properties": {
            "item_number": {
                "type": "string",
                "description": "The inventory item number, e.g. CM11222"
            }
        },
        "required": ["item_number"]
    }
}

# Flat list — this is what Claude API expects
tools = [tool_item_details, tool_item_onhand, tool_item_cost]

# ─────────────────────────────────────────
# 4. PYTHON FUNCTIONS (actual DB queries)
# ─────────────────────────────────────────
def get_item_details(item_number):
    """Get item description, UOM, status from Oracle EBS"""
    try:
        sql = """
            SELECT segment1, description, primary_unit_of_measure, inventory_item_status_code
            FROM   mtl_system_items_b
            WHERE  segment1 = :item_number
            AND    rownum = 1
        """
        cursor = conn.cursor()
        cursor.execute(sql, {"item_number": item_number})
        result = cursor.fetchone()
        if result:
            item, desc, uom, status = result
            return f"Item: {item} | Description: {desc} | UOM: {uom} | Status: {status}"
        else:
            return f"Item {item_number} not found in Oracle EBS"
    except Exception as e:
        return f"Database error: {str(e)}"


def get_item_onhand_details(item_number):
    """Get onhand quantity from Oracle EBS"""
    try:
        sql = """
            SELECT msib.segment1,
                   SUM(moq.transaction_quantity) onhand_qty
            FROM   mtl_system_items_b msib,
                   mtl_onhand_quantities moq
            WHERE  moq.inventory_item_id = msib.inventory_item_id
            AND    moq.organization_id   = msib.organization_id
            AND    msib.segment1         = :item_number
            GROUP BY msib.segment1
        """
        cursor = conn.cursor()
        cursor.execute(sql, {"item_number": item_number})
        result = cursor.fetchone()
        if result:
            item, qty = result
            return f"Item: {item} | Onhand Quantity: {qty}"
        else:
            return f"Item {item_number} has no onhand stock"
    except Exception as e:
        return f"Database error: {str(e)}"


def get_item_cost(item_number):
    """Get frozen standard cost from Oracle EBS"""
    try:
        sql = """
          
select distinct msi.segment1 "ITEM_NUM",
msi.description "ITEM_DESCRIPTION",

cic.item_cost "UNIT COST"

from mtl_system_items_b msi,
cst_cost_types cct,
cst_item_costs cic,
org_organization_definitions ood,
gl_code_combinations_kfv gcc,
gl_code_combinations_kfv gcc1,
FND_LOOKUP_VALUES flv
WHERE 1=1
AND cct.cost_type_id = cic.cost_type_id
AND cic.inventory_item_id = msi.inventory_item_id
AND cic.organization_id = msi.organization_id
AND msi.organization_id = ood.organization_id
AND gcc.CHART_OF_ACCOUNTS_ID = ood.CHART_OF_ACCOUNTS_ID
AND gcc.CODE_COMBINATION_ID =msi.COST_OF_SALES_ACCOUNT
AND gcc1.CHART_OF_ACCOUNTS_ID = ood.CHART_OF_ACCOUNTS_ID
AND gcc1.CODE_COMBINATION_ID =msi.expense_account
AND flv.lookup_type = 'MTL_PLANNING_MAKE_BUY'
and flv.LOOKUP_CODE=msi.PLANNING_MAKE_BUY_CODE
AND flv.LANGUAGE='US'
and cct.cost_type ='Frozen'
and msi.PLANNING_MAKE_BUY_CODE=2
  AND    msi.segment1         = :item_number
and cic.MATERIAL_OVERHEAD_COST is not null
        """
        cursor = conn.cursor()
        cursor.execute(sql, {"item_number": item_number})
        result = cursor.fetchone()
        if result:
            item, desc, cost = result
            return f"Item: {item} | Description: {desc} | Unit Cost: {cost}"
        else:
            return f"Item {item_number} has no frozen cost defined"
    except Exception as e:
        return f"Database error: {str(e)}"


# ─────────────────────────────────────────
# 5. FUNCTION DISPATCHER
# ─────────────────────────────────────────
def call_function(name, inputs):
    if name == "get_item_details":
        return get_item_details(inputs["item_number"])
    elif name == "get_item_onhand_details":
        return get_item_onhand_details(inputs["item_number"])
    elif name == "get_item_cost":
        return get_item_cost(inputs["item_number"])
    else:
        return f"Unknown function: {name}"


# ─────────────────────────────────────────
# 6. MULTI-TOOL LOOP
# ─────────────────────────────────────────
user_question = "Give me complete information for item SB90207 — details, onhand quantity, and cost"

messages = [{"role": "user", "content": user_question}]

print(f"\n🔍 Question: {user_question}\n")

while True:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system="You are an Oracle EBS assistant. Use the available tools to fetch real data and give a complete answer.",
        tools=tools,
        messages=messages
    )

    print(f"Stop reason: {response.stop_reason}")

    # If Claude is done — print final answer
    if response.stop_reason == "end_turn":
        for block in response.content:
            if hasattr(block, "text"):
                print(f"\n✅ Final Answer:\n{block.text}")
        break

    # If Claude wants to call tools
    if response.stop_reason == "tool_use":

        # Add Claude's response to messages
        messages.append({"role": "assistant", "content": response.content})

        # Collect ALL tool results in one list
        tool_results = []

        for block in response.content:
            if block.type == "tool_use":
                print(f"🔧 Calling tool: {block.name} | Input: {block.input}")

                # Execute the Python function
                result = call_function(block.name, block.input)
                print(f"   Result: {result}")

                # Add to tool results list
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result
                })

        # Send ALL tool results back to Claude in ONE message
        messages.append({"role": "user", "content": tool_results})