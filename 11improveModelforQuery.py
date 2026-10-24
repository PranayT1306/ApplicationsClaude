import streamlit as st
import anthropic
import os
import pandas as pd
import oracledb
import json

BASE_DIR =os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH=os.path.join(BASE_DIR,'json.config')
with open(CONFIG_PATH,'r') as c:
    params=json.load(c)["params"]
oracledb.init_oracle_client(lib_dir=r"C:\instantclient_21_11")

# Group tables by business module!
EBS_MODULES = {
    "Purchasing": [
        "PO_HEADERS_ALL",
        "PO_LINES_ALL",
        "PO_DISTRIBUTIONS_ALL",
        "AP_SUPPLIERS", 
        "AP_INVOICES_ALL"
    ],
    "Payables": [
        "AP_INVOICES_ALL",
        "AP_INVOICE_LINES_ALL",
        "AP_PAYMENTS_ALL",
        "AP_SUPPLIERS"
    ],
    "SUPPLIERS": [
        "AP_SUPPLIERS",
        "AP_SUPPLIER_SITES_ALL"
   
    ],
    
    "CUSTOMERS": [
        "HZ_PARTIES",
        "HZ_CUST_ACCOUNTS",
        "HZ_CUST_ACCT_SITES_ALL",
        "HZ_CUST_SITE_USES_ALL",
        "HZ_PARTY_SITES"
   
    ],
    "Inventory": [
        "MTL_SYSTEM_ITEMS_B",
        "MTL_ONHAND_QUANTITIES",
        "MTL_TRANSACTIONS_TEMP",
        "MTL_PARAMETERS"
    ],
    "Order Management": [
        "OE_ORDER_HEADERS_ALL",
        "OE_ORDER_LINES_ALL",
        "OE_PRICE_ADJUSTMENTS"
    ]
}

def get_table_columns(cursor, table_name):
    """Get columns for multiple table_name!"""
       # query ALL_TAB_COLUMNS
    # return column names
    
    all_table_info = ""
    
    for tableName in table_name:
        cursor.execute("""
            SELECT column_name, data_type
            FROM all_tab_columns
            WHERE table_name = :tname
           
            ORDER BY column_id
        """, {"tname": tableName.upper()})
        
        cols = cursor.fetchall()
        col_list = ", ".join([c[0] for c in cols])
        
        all_table_info += f"""
Table: {tableName}
Columns: {col_list}
"""

    return all_table_info



def build_system_prompt(cursor, module):
    """Build system prompt with real columns"""
    
    # Get tables for selected module
    tables = EBS_MODULES[module]
    
    # Get real columns for all tables
    table_info = get_table_columns(cursor, tables)
    
    # Build system prompt
    system_prompt = f"""You are Oracle EBS R12.2 Technical Expert.

Available tables and ACTUAL columns:
{table_info}

STRICT RULES:
1. Use ONLY columns listed above
2. Oracle style joins (no ANSI)
3. Always use table aliases
4. Limit to 100 rows using ROWNUM
5. Plain SQL only
6. No markdown
7. No code blocks
8. No backticks
9. No semicolon at end"""

    return  system_prompt

def generate_sql(client, question, system_prompt):
    """Generate SQL using Claude API"""
    
    # Call Claude API
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        temperature=0,
        system=system_prompt,
        messages=[{
            "role": "user",
            "content": question
        }]
    )
    
    # Clean SQL output
    sql = message.content[0].text
    sql = sql.replace('```sql', '')
    sql = sql.replace('```', '')
    sql = sql.strip()
    sql = sql.rstrip(';')
    
    return sql


def clean_dataframe(df):
    # Convert all columns to string first
    # Then remove non-printable characters
    for col in df.columns:
        df[col] = df[col].apply(
            lambda x: ''.join(
                char for char in str(x) 
                if char.isprintable()
            ) if x is not None else ''
        )
    return df
# ── STREAMLIT UI ────────────────────────
st.title("PranayAI Assistant 🤖")
st.write("Ask questions about Oracle EBS!")

# Module selector
module = st.selectbox(
    "Select Business Area:",
    list(EBS_MODULES.keys())
)

# Question input
question = st.text_input(
    "Ask your question:",
    placeholder="e.g. Show pending POs"
)

if st.button("Ask AI 🤖"):
    if question:
        with st.spinner("Thinking..."):
            try:
                # Connect
                client = anthropic.Anthropic(
                    api_key=params['anthropic_api_key']
                )
                conn = oracledb.connect(
                    user=params['oracle_user'],
                    password=params['oracle_password'],
                    dsn=params['oracle_dsn']
                )
                cursor = conn.cursor()
                
                # Build prompt + generate SQL
                system_prompt = build_system_prompt(
                    cursor, module)
                sql = generate_sql(
                    client, question, system_prompt)
                
                # Show SQL
                with st.expander("View SQL"):
                    st.code(sql, language='sql')
                
                # Execute
                cursor.execute(sql)
                results = cursor.fetchall()
                cols = [c[0] for c in 
                       cursor.description]
                df = pd.DataFrame(
                    results, columns=cols)
                
                # Show results
                st.success(f"Found {len(df)} rows!")
                st.dataframe(df)
                
                # Excel download
                df = clean_dataframe(df)
                excel_path = os.path.join(
                    BASE_DIR, "results.xlsx")
                df.to_excel(excel_path, 
                           index=False,
                           engine='xlsxwriter')
                
                with open(excel_path, 'rb') as f:
                    st.download_button(
                        "Download Excel 📊",
                        data=f,
                        file_name="results.xlsx",
                        mime="application/vnd.ms-excel"
                    )
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")
    else:
        st.warning("Please enter a question!")