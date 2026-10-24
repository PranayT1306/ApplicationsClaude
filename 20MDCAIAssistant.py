import anthropic
import streamlit as st
import os
import json
import oracledb

BASE_DIR=os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH=os.path.join(BASE_DIR,'json.config')
with open(CONFIG_PATH,'r') as c:
    params=json.load(c)["params"]
oracledb.init_oracle_client(lib_dir=r"C:\instantclient_21_11")

# Connecting Claude
try:
    client=anthropic.Anthropic(api_key=params["anthropic_api_key"])
    print(f"Claude Connected")
except Exception as e:
    print(f"Issue in connecting Claude {e}")

# Oracle Connection
try:
    conn=oracledb.connect(
        user=params["oracle_user"],
        password=params["oracle_password"],
        dsn=params["oracle_dsn"]
    )
    print("Oracle Database Connected!!")
except Exception as e:
    print(f"Oracle Connect error {e}")


def create_item(item_number, description, master_org_code, child_org_code, template_name, uom_code):
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


def create_supplier(vendor_name, terms_name, currency_code, site_code,
                    address_line1, address_line2, city, state, zip, country,
                    contact_first_name, contact_last_name, contact_email):
    

    try:
        cursor = conn.cursor()

        # OUT parameters
        x_vendor_id         = cursor.var(oracledb.NUMBER)
        x_vendor_site_id    = cursor.var(oracledb.NUMBER)
        x_vendor_contact_id = cursor.var(oracledb.NUMBER)
        x_status            = cursor.var(oracledb.STRING)
        x_message           = cursor.var(oracledb.STRING)

        plsql = """
            BEGIN
                xx_ap_create_supplier_prc(
                    p_vendor_name        => :vendor_name,
                    p_terms_name         => :terms_name,
                    p_currency_code      => :currency_code,
                    p_site_code          => :site_code,
                    p_address_line1      => :address_line1,
                    p_address_line2      => :address_line2,
                    p_city               => :city,
                    p_state              => :state,
                    p_zip                => :zip,
                    p_country            => :country,
                    p_contact_first_name => :contact_first_name,
                    p_contact_last_name  => :contact_last_name,
                    p_contact_email      => :contact_email,
                    p_commit             => 'Y',
                    x_vendor_id          => :x_vendor_id,
                    x_vendor_site_id     => :x_vendor_site_id,
                    x_vendor_contact_id  => :x_vendor_contact_id,
                    x_status             => :x_status,
                    x_message            => :x_message
                );
            END;
        """
        cursor.execute(plsql, {
            "vendor_name":         vendor_name.upper(),
            "terms_name":          terms_name,
            "currency_code":       currency_code,
            "site_code":           site_code,
            "address_line1":       address_line1,
            "address_line2":       address_line2,
            "city":                city,
            "state":               state,
            "zip":                 zip,
            "country":             country,
            "contact_first_name":  contact_first_name,
            "contact_last_name":   contact_last_name,
            "contact_email":       contact_email,
            "x_vendor_id":         x_vendor_id,
            "x_vendor_site_id":    x_vendor_site_id,
            "x_vendor_contact_id": x_vendor_contact_id,
            "x_status":            x_status,
            "x_message":           x_message
        })

        status  = x_status.getvalue()
        message = x_message.getvalue()

        if status == 'S':
            vid  = x_vendor_id.getvalue()
            vsid = x_vendor_site_id.getvalue()
            return f"✅ Supplier {vendor_name} created! Vendor ID: {vid} | Site ID: {vsid} | {message}"
        else:
            return f"❌ Supplier creation failed: {message}"

    except Exception as e:
        return f"❌ Supplier creation error: {str(e)}"

def create_customer(customer_name, address1, address2, city, state, postal_code, country,
                    contact_first_name, contact_last_name, contact_job_title,
                    contact_email, contact_area_code, contact_phone):
    try:
        cursor = conn.cursor()

        # OUT parameters
        x_cust_account_id     = cursor.var(oracledb.NUMBER)
        x_account_number      = cursor.var(oracledb.STRING)
        x_party_id            = cursor.var(oracledb.NUMBER)
        x_cust_acct_site_id   = cursor.var(oracledb.NUMBER)
        x_bill_to_site_use_id = cursor.var(oracledb.NUMBER)
        x_ship_to_site_use_id = cursor.var(oracledb.NUMBER)
        x_status              = cursor.var(oracledb.STRING)
        x_message             = cursor.var(oracledb.STRING)

        plsql = """
            BEGIN
                xx_ar_create_customer_prc(
                    p_customer_name       => :customer_name,
                    p_address1            => :address1,
                    p_address2            => :address2,
                    p_city                => :city,
                    p_state               => :state,
                    p_postal_code         => :postal_code,
                    p_country             => :country,
                    p_contact_first_name  => :contact_first_name,
                    p_contact_last_name   => :contact_last_name,
                    p_contact_job_title   => :contact_job_title,
                    p_contact_email       => :contact_email,
                    p_contact_area_code   => :contact_area_code,
                    p_contact_phone       => :contact_phone,
                    x_cust_account_id     => :x_cust_account_id,
                    x_account_number      => :x_account_number,
                    x_party_id            => :x_party_id,
                    x_cust_acct_site_id   => :x_cust_acct_site_id,
                    x_bill_to_site_use_id => :x_bill_to_site_use_id,
                    x_ship_to_site_use_id => :x_ship_to_site_use_id,
                    x_status              => :x_status,
                    x_message             => :x_message
                );
            END;
        """
        cursor.execute(plsql, {
            "customer_name":        customer_name.upper(),
            "address1":             address1,
            "address2":             address2,
            "city":                 city,
            "state":                state,
            "postal_code":          postal_code,
            "country":              country,
            "contact_first_name":   contact_first_name,
            "contact_last_name":    contact_last_name,
            "contact_job_title":    contact_job_title,
            "contact_email":        contact_email,
            "contact_area_code":    contact_area_code,
            "contact_phone":        contact_phone,
            "x_cust_account_id":    x_cust_account_id,
            "x_account_number":     x_account_number,
            "x_party_id":           x_party_id,
            "x_cust_acct_site_id":  x_cust_acct_site_id,
            "x_bill_to_site_use_id":x_bill_to_site_use_id,
            "x_ship_to_site_use_id":x_ship_to_site_use_id,
            "x_status":             x_status,
            "x_message":            x_message
        })

        status  = x_status.getvalue()
        message = x_message.getvalue()

        if status == 'S':
            cid  = x_cust_account_id.getvalue()
            anum = x_account_number.getvalue()
            return f"✅ Customer {customer_name} created! Account ID: {cid} | Account#: {anum} | {message}"
        else:
            return f"❌ Customer creation failed: {message}"

    except Exception as e:
        return f"❌ Customer creation error: {str(e)}"

tools_create_item = [{
    "name": "create_item",
    "description": "Create a new inventory item in Oracle EBS by calling the item import procedure",
    "input_schema": {
        "type": "object",
        "properties": {
            "item_number":    {"type": "string", "description": "Item number e.g. PRANAYTEST2027"},
            "description":    {"type": "string", "description": "Item description e.g. Test Item for Practice"},
            "master_org_code":{"type": "string", "description": "Master organization e.g. V1"},
            "child_org_code": {"type": "string", "description": "Child organization e.g. H1"},
            "template_name":  {"type": "string", "description": "Template name e.g. Purchased Item"},
            "uom_code":       {"type": "string", "description": "Unit of measure e.g. EA"}
        },
        "required": ["item_number", "description", "master_org_code", "child_org_code", "template_name", "uom_code"]
    }
}]

tools_create_supplier = [{
    "name": "create_supplier",
    "description": "Create a new Supplier in Oracle EBS",
    "input_schema": {
        "type": "object",
        "properties": {
            "vendor_name":        {"type": "string", "description": "Vendor name e.g. Tech Supplies Pvt Ltd"},
            "terms_name":         {"type": "string", "description": "Payment terms e.g. Net 30"},
            "currency_code":      {"type": "string", "description": "Currency code e.g. USD"},
            "site_code":          {"type": "string", "description": "Supplier site code e.g. HYD-MAIN"},
            "address_line1":      {"type": "string", "description": "Address line 1"},
            "address_line2":      {"type": "string", "description": "Address line 2"},
            "city":               {"type": "string", "description": "City e.g. Hyderabad"},
            "state":              {"type": "string", "description": "State e.g. Telangana"},
            "zip":                {"type": "string", "description": "ZIP e.g. 500006"},
            "country":            {"type": "string", "description": "Country code e.g. IN"},
            "contact_first_name": {"type": "string", "description": "Contact first name"},
            "contact_last_name":  {"type": "string", "description": "Contact last name"},
            "contact_email":      {"type": "string", "description": "Contact email"}
        },
        "required": ["vendor_name", "terms_name", "currency_code", "site_code",
                     "address_line1", "address_line2", "city", "state", "zip",
                     "country", "contact_first_name", "contact_last_name", "contact_email"]
    }
}]

tools_create_customer = [{
    "name": "create_customer",
    "description": "Create a new customer in Oracle EBS",
    "input_schema": {
        "type": "object",
        "properties": {
            "customer_name":       {"type": "string", "description": "Customer name e.g. Pranay Pvt Ltd"},
            "address1":            {"type": "string", "description": "Address line 1"},
            "address2":            {"type": "string", "description": "Address line 2"},
            "city":                {"type": "string", "description": "City e.g. Hyderabad"},
            "state":               {"type": "string", "description": "State e.g. Telangana"},
            "postal_code":         {"type": "string", "description": "Postal/ZIP code e.g. 500032"},
            "country":             {"type": "string", "description": "Country code e.g. IN"},
            "contact_first_name":  {"type": "string", "description": "Contact first name"},
            "contact_last_name":   {"type": "string", "description": "Contact last name"},
            "contact_job_title":   {"type": "string", "description": "Job title e.g. Purchase Manager"},
            "contact_email":       {"type": "string", "description": "Contact email"},
            "contact_area_code":   {"type": "string", "description": "Area code e.g. 040"},
            "contact_phone":       {"type": "string", "description": "Phone number e.g. 87654321"}
        },
        "required": ["customer_name", "address1", "address2", "city", "state",
                     "postal_code", "country", "contact_first_name", "contact_last_name",
                     "contact_job_title", "contact_email", "contact_area_code", "contact_phone"]
    }
}]

tools = tools_create_item + tools_create_supplier + tools_create_customer


def call_function(name, inputs):
    if name == "create_item":
        return create_item(
            inputs["item_number"], inputs["description"],
            inputs["master_org_code"], inputs["child_org_code"],
            inputs["template_name"], inputs["uom_code"]
        )
    elif name == "create_supplier":
      return create_supplier(
        inputs["vendor_name"],
        inputs["terms_name"],
        inputs["currency_code"],
        inputs["site_code"],          # ← this key must exist in the tool definition
        inputs["address_line1"],
        inputs["address_line2"],
        inputs["city"],
        inputs["state"],
        inputs["zip"],
        inputs["country"],
        inputs["contact_first_name"],
        inputs["contact_last_name"],
        inputs["contact_email"]
     )
    elif name == "create_customer":
     return create_customer(
        inputs["customer_name"], inputs["address1"], inputs["address2"],
        inputs["city"], inputs["state"], inputs["postal_code"], inputs["country"],
        inputs["contact_first_name"], inputs["contact_last_name"],
        inputs["contact_job_title"], inputs["contact_email"],
        inputs["contact_area_code"], inputs["contact_phone"]
    )
    return f"Unknown tool: {name}"




def ask_claude(messages):
    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            system="You are an Oracle EBS AI Assistant. Help users create inventory items, suppliers and customers.",
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
                    try:
                        result = call_function(block.name, block.input)
                    except Exception as e:
                        result = f"❌ Tool error: {str(e)}"
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })
            messages.append({"role": "user", "content": tool_results})

# ── SIDEBAR ──
with st.sidebar:
    st.title("🤖 Pranay Enterprise AI Assistant")
    st.success("✅ Oracle Connected")
    st.success("✅ Claude Connected")
    st.markdown("---")
    st.markdown("**Available Tools:**")
    st.markdown("- ➕ Create Item")
    st.markdown("- ➕ Create Supplier")
    st.markdown("- ➕ Create Customer")
    st.markdown("---")
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.session_state.claude_messages = []
        st.rerun()

# ── MAIN ──
st.title("Pranay Enterprise AI Assistant 🤖")
st.subheader("Master Data Conversion AI Assistant")
st.caption("Create Items, Suppliers and Customers in Oracle EBS via chat!")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "claude_messages" not in st.session_state:
    st.session_state.claude_messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("e.g. Create supplier Pranay Tiwari, terms Net 30, currency USD, address..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.claude_messages.append({"role": "user", "content": prompt})
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                answer = ask_claude(st.session_state.claude_messages)
            except Exception as e:
                # Reset corrupted message history
                st.session_state.claude_messages = [{"role": "user", "content": prompt}]
                answer = f"⚠️ Error occurred and chat was reset. Please try again. ({str(e)[:100]})"
            st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.session_state.claude_messages.append({"role": "assistant", "content": answer})