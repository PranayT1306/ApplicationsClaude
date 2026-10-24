import anthropic
import os
import oracledb
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "json.config")

with open(CONFIG_PATH, 'r') as c:
    params = json.load(c)["params"]

oracledb.init_oracle_client(lib_dir=r"C:\instantclient_21_11")

# ─────────────────────────────────────────
# 1. ORACLE CONNECTION
# ─────────────────────────────────────────
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
# 3. TOOL DEFINITIONS
# ─────────────────────────────────────────
tool1 = {
    "name": "get_cust_trx_info",
    "description": "Get Customer Transaction / Invoice information from Oracle EBS AR module",
    "input_schema": {
        "type": "object",
        "properties": {
            "account_number": {           # ← FIXED: was "item_number"
                "type": "string",
                "description": "The Customer Account Number, e.g. 1003"
            }
        },
        "required": ["account_number"]
    }
}

tool2 = {
    "name": "get_cust_payment_info",
    "description": "Get Customer Receipt and Payment information from Oracle EBS AR module",
    "input_schema": {
        "type": "object",
        "properties": {
            "account_number": {           # ← FIXED: was "item_number"
                "type": "string",
                "description": "The Customer Account Number, e.g. 1003"
            }
        },
        "required": ["account_number"]
    }
}

tools = [tool1, tool2]

# ─────────────────────────────────────────
# 4. PYTHON FUNCTIONS
# ─────────────────────────────────────────
def get_cust_trx_info(account_number):
    """Get Customer Invoice/Transaction info from Oracle EBS"""
    try:
        sql = """
            SELECT
                hou.name                                ou_name,
                ratx.trx_date                           trx_date,
                hp.party_name,
                hca.account_number,
                ratx.trx_number,
                ratx.interface_header_attribute1        sales_order_number,
                msib.segment1                           item,
                msib.description,
                SUM(ratxl.quantity_invoiced)            quantity,
                SUM(ratxl.unit_selling_price)           unit_price,
                SUM(ratxl.quantity_invoiced * ratxl.unit_selling_price) amount
            FROM
                hz_parties                hp,
                hz_cust_accounts          hca,
                ra_customer_trx_all       ratx,
                ra_customer_trx_lines_all ratxl,
                mtl_system_items_b        msib,
                hr_operating_units        hou,
                mtl_parameters            mp
            WHERE
                    hp.party_id              = hca.party_id
                AND hca.status               = 'A'
                AND ratx.bill_to_customer_id = hca.cust_account_id
                AND hou.organization_id      = ratx.org_id
                AND ratx.customer_trx_id     = ratxl.customer_trx_id
                AND msib.inventory_item_id   = ratxl.inventory_item_id
                AND mp.organization_id       = msib.organization_id
                AND hca.account_number       = :account_number
                   and rownum<4
            GROUP BY
                hou.name, ratx.trx_date, hp.party_name, hca.account_number,
                ratx.trx_number, ratx.interface_header_attribute1,
                msib.segment1, msib.description
            ORDER BY ratx.trx_date DESC
        """
        cursor = conn.cursor()
        cursor.execute(sql, {"account_number": account_number})
        results = cursor.fetchall()        # ← FIXED: fetchall not fetchone

        if results:
            output_lines = []
            for row in results:
                (ou_name, trx_date, party_name, acct_num, trx_number,
                 sales_order_number, item, description,
                 quantity, unit_price, amount) = row

                line = (
                    f"OU: {ou_name} | "
                    f"Trx Date: {trx_date} | "
                    f"Customer: {party_name} ({acct_num}) | "
                    f"Trx#: {trx_number} | "
                    f"SO#: {sales_order_number} | "
                    f"Item: {item} | "
                    f"Description: {description} | "
                    f"Qty: {quantity} | "
                    f"Unit Price: {unit_price} | "
                    f"Amount: {amount}"
                )
                output_lines.append(line)

            return "\n".join(output_lines)
        else:
            return f"No transactions found for customer {account_number}"

    except Exception as e:
        return f"Database error: {str(e)}"    # ← FIXED: now inside try block


def get_cust_payment_info(account_number):
    """Get Customer Receipt and Payment info from Oracle EBS"""
    try:
        sql = """
            SELECT
                hou.name                         operating_unit,
                acr.receipt_number,
                acr.receipt_date,
                acr.amount                       receipt_amount,
                acr.currency_code,
                hp.party_name                    customer_name,
                hca.account_number               customer_number,
                ratx.trx_number                  invoice_number,
                ratx.trx_date                    invoice_date,
                ratx.interface_header_attribute1 sales_order_number,
                ara.amount_applied,
                ara.apply_date,
                ara.application_type,
                aps.amount_due_original,
                aps.amount_due_remaining,
                CASE
                    WHEN aps.amount_due_remaining = 0
                        THEN 'FULLY PAID'
                    WHEN aps.amount_due_remaining < aps.amount_due_original
                        THEN 'PARTIALLY PAID'
                    WHEN aps.amount_due_remaining = aps.amount_due_original
                        THEN 'UNPAID'
                END                              payment_status,
                TRUNC(SYSDATE) - aps.due_date    days_overdue
            FROM
                hz_parties                     hp,
                hz_cust_accounts               hca,
                ar_cash_receipts_all           acr,
                ar_receivable_applications_all ara,
                ra_customer_trx_all            ratx,
                ar_payment_schedules_all       aps,
                hr_operating_units             hou
            WHERE
                    hp.party_id                    = hca.party_id
                AND hca.cust_account_id            = acr.pay_from_customer
                AND acr.cash_receipt_id            = ara.cash_receipt_id
                AND ara.status                     = 'APP'
                AND ara.application_type           = 'CASH'
                AND ara.applied_customer_trx_id    = ratx.customer_trx_id
                AND aps.customer_trx_id            = ratx.customer_trx_id
                AND aps.payment_schedule_id        = ara.applied_payment_schedule_id
                AND hou.organization_id            = acr.org_id
                AND hca.account_number             = :account_number
                and rownum<4
            ORDER BY
                acr.receipt_date DESC, acr.receipt_number
        """
        cursor = conn.cursor()
        cursor.execute(sql, {"account_number": account_number})
        results = cursor.fetchall()        # ← FIXED: fetchall not fetchone

        if results:
            output_lines = []
            for row in results:
                (operating_unit, receipt_number, receipt_date, receipt_amount,
                 currency_code, customer_name, customer_number, invoice_number,
                 invoice_date, sales_order_number, amount_applied, apply_date,
                 application_type, amount_due_original, amount_due_remaining,
                 payment_status, days_overdue) = row

                line = (
                    f"OU: {operating_unit} | "
                    f"Receipt#: {receipt_number} | "
                    f"Receipt Date: {receipt_date} | "
                    f"Receipt Amt: {receipt_amount} {currency_code} | "
                    f"Customer: {customer_name} ({customer_number}) | "
                    f"Invoice#: {invoice_number} | "
                    f"Invoice Date: {invoice_date} | "
                    f"SO#: {sales_order_number} | "
                    f"Applied: {amount_applied} | "
                    f"Apply Date: {apply_date} | "
                    f"Original: {amount_due_original} | "
                    f"Remaining: {amount_due_remaining} | "
                    f"Status: {payment_status} | "
                    f"Days Overdue: {days_overdue}"
                )
                output_lines.append(line)

            return "\n".join(output_lines)
        else:
            return f"No payment records found for customer {account_number}"

    except Exception as e:
        return f"Database error: {str(e)}"


# ─────────────────────────────────────────
# 5. DISPATCHER
# ─────────────────────────────────────────
def call_function(name, inputs):
    if name == "get_cust_trx_info":
        return get_cust_trx_info(inputs["account_number"])
    elif name == "get_cust_payment_info":
        return get_cust_payment_info(inputs["account_number"])
    else:
        return f"Unknown function: {name}"


# ─────────────────────────────────────────
# 6. MULTI-TOOL LOOP
# ─────────────────────────────────────────
user_question = "Give me complete AR information for customer account 1003 — all transactions and payment status"

messages = [{"role": "user", "content": user_question}]

print(f"\n🔍 Question: {user_question}\n")

while True:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system="You are an Oracle EBS AR assistant. Use tools to fetch real customer data and give a complete answer.",
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
                print(f"🔧 Calling: {block.name} | Input: {block.input}")
                result = call_function(block.name, block.input)
                print(f"   Result preview: {result[:100]}...")

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result
                })

        messages.append({"role": "user", "content": tool_results})