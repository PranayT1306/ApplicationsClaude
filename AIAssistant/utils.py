import anthropic
import streamlit as st
import oracledb
import os
import json
import datetime


# ─── CONFIG ───────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'json.config')

with open(CONFIG_PATH, 'r') as c:
    params = json.load(c)["params"]

oracledb.init_oracle_client(lib_dir=r"C:\instantclient_21_11")

CLAUDE_MODEL  = "claude-sonnet-4-6"
SYSTEM_PROMPT = "You are an Oracle EBS AI Assistant. Help users create inventory items, suppliers and customers."

# ─── 1. CONSTANTS (top of utils.py, under CONFIG) ─────────────────
PO_ORG_ID        = 204      # Vision Operations
PO_USER_ID       = 1318     # apps context for PO creation
PO_RESP_ID       = 50578    # Purchasing responsibility
PO_RESP_APPL_ID  = 201
 
 

# ─── CLAUDE CLIENT ────────────────────────────────────
@st.cache_resource
def get_claude_client():
    try:
        client = anthropic.Anthropic(api_key=params["anthropic_api_key"])
        print("Claude Connected")
        return client
    except Exception as e:
        st.error(f"❌ Claude connection failed: {e}")
        st.stop()

# ─── ORACLE CONNECTION ────────────────────────────────
@st.cache_resource
def get_db_connection():
    try:
        conn = oracledb.connect(
            user=params["oracle_user"],
            password=params["oracle_password"],
            dsn=params["oracle_dsn"]
        )
        print("Oracle Database Connected!!")
        return conn
    except Exception as e:
        st.error(f"❌ Oracle connection failed: {e}")
        st.stop()

# ─── PL/SQL FUNCTIONS ─────────────────────────────────
def create_item(item_number, description, master_org_code, child_org_code, template_name, uom_code):
    conn = get_db_connection()
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
            "item_number":     item_number.upper(),
            "description":     description,
            "master_org_code": master_org_code,
            "child_org_code":  child_org_code,
            "template_name":   template_name,
            "uom_code":        uom_code
        })
        conn.commit()
        return f"✅ Item {item_number} created successfully!"
    except Exception as e:
        conn.rollback()
        return f"❌ Item creation failed: {str(e)}"


def create_supplier(vendor_name, terms_name, currency_code, site_code,
                    address_line1, address_line2, city, state, zip, country,
                    contact_first_name, contact_last_name, contact_email):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
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
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
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
            "customer_name":         customer_name.upper(),
            "address1":              address1,
            "address2":              address2,
            "city":                  city,
            "state":                 state,
            "postal_code":           postal_code,
            "country":               country,
            "contact_first_name":    contact_first_name,
            "contact_last_name":     contact_last_name,
            "contact_job_title":     contact_job_title,
            "contact_email":         contact_email,
            "contact_area_code":     contact_area_code,
            "contact_phone":         contact_phone,
            "x_cust_account_id":     x_cust_account_id,
            "x_account_number":      x_account_number,
            "x_party_id":            x_party_id,
            "x_cust_acct_site_id":   x_cust_acct_site_id,
            "x_bill_to_site_use_id": x_bill_to_site_use_id,
            "x_ship_to_site_use_id": x_ship_to_site_use_id,
            "x_status":              x_status,
            "x_message":             x_message
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

 
def save_scrap_to_oracle(header, lines):
    """Insert scrap form header and lines into Oracle EBS tables."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # ── Insert Header ──────────────────────────────────────
        header_id_var = cursor.var(int)

        cursor.execute("""
            INSERT INTO XXBSDM_SCRAP_HEADERS (
                SCRAP_HEADER_ID,
                WORK_ORDER,
                COST_CENTER,
                PRODUCTION_LINE,
                ORACLE_ASSEMBLY,
                SHIFT,
                CREATED_BY,
                CREATION_DATE,
                LAST_UPDATED_BY,
                LAST_UPDATE_DATE
            ) VALUES (
                XXBSDM_SCRAP_HEADERS_S.NEXTVAL,
                :work_order,
                :cost_center,
                :production_line,
                :oracle_assembly,
                :shift,
                :created_by,
                SYSDATE,
                :created_by,
                SYSDATE
            ) RETURNING SCRAP_HEADER_ID INTO :header_id
        """, {
            "work_order"      : header.get("work_order", ""),
            "cost_center"     : header.get("cost_center", ""),
            "production_line" : header.get("production_line", ""),
            "oracle_assembly" : header.get("oracle_item_assembly", ""),
            "shift"           : header.get("shift", ""),
            "created_by"      : PO_USER_ID,
            "header_id"       : header_id_var
        })

        header_id = header_id_var.getvalue()[0]

        # ── Insert Lines ───────────────────────────────────────
        for line in lines:
            # Clean qty values — remove ? if present
            scrap_qty_raw = str(line.get("Scrap Qty", "0")).replace("?", "").strip()
            bom_qty_raw   = str(line.get("BOM Qty",   "0")).replace("?", "").strip()

            try:
                scrap_qty = float(scrap_qty_raw) if scrap_qty_raw else 0
                bom_qty   = float(bom_qty_raw)   if bom_qty_raw   else 0
            except ValueError:
                scrap_qty = 0
                bom_qty   = 0

            cursor.execute("""
                INSERT INTO XXBSDM_SCRAP_LINES (
                    SCRAP_LINE_ID,
                    SCRAP_HEADER_ID,
                    ORACLE_ITEM_NUM,
                    ITEM_CODE,
                    DESCRIPTION,
                    BOM_QTY,
                    SCRAP_QTY,
                    CREATED_BY,
                    CREATION_DATE,
                    LAST_UPDATED_BY,
                    LAST_UPDATE_DATE
                ) VALUES (
                    XXBSDM_SCRAP_LINES_S.NEXTVAL,
                    :header_id,
                    :oracle_item_num,
                    :item_code,
                    :description,
                    :bom_qty,
                    :scrap_qty,
                    :created_by,
                    SYSDATE,
                    :created_by,
                    SYSDATE
                )
            """, {
                "header_id"       : header_id,
                "oracle_item_num" : str(line.get("Oracle Item #", "")),
                "item_code"       : str(line.get("Item Code", "")),
                "description"     : str(line.get("Description", "")),
                "bom_qty"         : bom_qty,
                "scrap_qty"       : scrap_qty,
                "created_by"      : PO_USER_ID,
            })

        conn.commit()
        return {
            "status"         : "S",
            "header_id"      : header_id,
            "lines_inserted" : len(lines)
        }

    except Exception as e:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        return {"status": "E", "message": str(e)}

    finally:
        try:
            if cursor:
                cursor.close()
        except Exception:
            pass
        try:
            if conn:
                conn.close()
        except Exception:
            pass

def create_po(vendor_num, vendor_site_code, buyer_emp_num, ship_to_location,
              lines, bill_to_location=None, comments=None,
              approval_status="INCOMPLETE"):
    conn   = get_db_connection()
    cursor = conn.cursor()
 
    # Procedure waits for POXPOPDOI (up to 10 min); widen timeout for this call only
    old_timeout = conn.call_timeout
    conn.call_timeout = 11 * 60 * 1000
 
    try:
        # Apps context on this session
        cursor.callproc("fnd_global.apps_initialize",
                        [PO_USER_ID, PO_RESP_ID, PO_RESP_APPL_ID])
 
        # Package record / table types
        hdr_type  = conn.gettype("XX_PO_CREATE_PKG.PO_HEADER_REC")
        tbl_type  = conn.gettype("XX_PO_CREATE_PKG.PO_LINE_TBL")
        line_type = tbl_type.element_type
 
        hdr = hdr_type.newobject()
        hdr.ORG_ID           = PO_ORG_ID
        hdr.VENDOR_NUM       = vendor_num
        hdr.VENDOR_SITE_CODE = vendor_site_code
        hdr.BUYER_EMP_NUM    = buyer_emp_num
        hdr.SHIP_TO_LOCATION = ship_to_location
        hdr.BILL_TO_LOCATION = bill_to_location or ship_to_location
        hdr.COMMENTS         = comments or "Created by EBS AI Assistant"
 
        line_tbl = tbl_type.newobject()
        for idx, ln in enumerate(lines, start=1):
            rec = line_type.newobject()
            rec.LINE_NUM         = idx
            rec.LINE_TYPE        = "Goods"      # PL/SQL record defaults don't apply from Python
            rec.ITEM_NUMBER      = ln.get("item_number")
            rec.ITEM_DESCRIPTION = ln.get("item_description")
            rec.UOM_CODE         = ln.get("uom_code")
            rec.QUANTITY         = ln["quantity"]
            rec.UNIT_PRICE       = ln["unit_price"]
            rec.NEED_BY_DATE     = datetime.datetime.strptime(ln["need_by_date"], "%Y-%m-%d")
            rec.SHIP_TO_ORG_CODE = ln["ship_to_org_code"]
            rec.DESTINATION_TYPE = ln.get("destination_type", "EXPENSE")
            rec.CHARGE_ACCOUNT   = ln.get("charge_account")
            line_tbl.setelement(idx, rec)
 
        out_po_number = cursor.var(oracledb.STRING)
        out_po_id     = cursor.var(oracledb.NUMBER)
        out_req_id    = cursor.var(oracledb.NUMBER)
        out_status    = cursor.var(oracledb.STRING)
        out_message   = cursor.var(oracledb.STRING, 4000)
 
        cursor.callproc("XX_PO_CREATE_PKG.CREATE_PO", keyword_parameters={
            "p_header":          hdr,
            "p_lines":           line_tbl,
            "p_approval_status": approval_status,
            "x_po_number":       out_po_number,
            "x_po_header_id":    out_po_id,
            "x_request_id":      out_req_id,
            "x_status":          out_status,
            "x_message":         out_message,
        })
        # No conn.commit() needed - the procedure commits before submitting POXPOPDOI
 
        return {"po_number":   out_po_number.getvalue(),
                "po_header_id": out_po_id.getvalue(),
                "request_id":  out_req_id.getvalue(),
                "status":      out_status.getvalue(),
                "message":     out_message.getvalue()}
 
    except Exception as e:
        return {"status": "E", "message": str(e)}
 
    finally:
        conn.call_timeout = old_timeout
        cursor.close()

# ─── TOOL DEFINITIONS ─────────────────────────────────
tools_create_item = [{
    "name": "create_item",
    "description": "Create a new inventory item in Oracle EBS by calling the item import procedure",
    "input_schema": {
        "type": "object",
        "properties": {
            "item_number":     {"type": "string", "description": "Item number e.g. PRANAYTEST2027"},
            "description":     {"type": "string", "description": "Item description e.g. Test Item for Practice"},
            "master_org_code": {"type": "string", "description": "Master organization e.g. V1"},
            "child_org_code":  {"type": "string", "description": "Child organization e.g. H1"},
            "template_name":   {"type": "string", "description": "Template name e.g. Purchased Item"},
            "uom_code":        {"type": "string", "description": "Unit of measure e.g. EA"}
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
            "customer_name":      {"type": "string", "description": "Customer name e.g. Pranay Pvt Ltd"},
            "address1":           {"type": "string", "description": "Address line 1"},
            "address2":           {"type": "string", "description": "Address line 2"},
            "city":               {"type": "string", "description": "City e.g. Hyderabad"},
            "state":              {"type": "string", "description": "State e.g. Telangana"},
            "postal_code":        {"type": "string", "description": "Postal/ZIP code e.g. 500032"},
            "country":            {"type": "string", "description": "Country code e.g. IN"},
            "contact_first_name": {"type": "string", "description": "Contact first name"},
            "contact_last_name":  {"type": "string", "description": "Contact last name"},
            "contact_job_title":  {"type": "string", "description": "Job title e.g. Purchase Manager"},
            "contact_email":      {"type": "string", "description": "Contact email"},
            "contact_area_code":  {"type": "string", "description": "Area code e.g. 040"},
            "contact_phone":      {"type": "string", "description": "Phone number e.g. 87654321"}
        },
        "required": ["customer_name", "address1", "address2", "city", "state",
                     "postal_code", "country", "contact_first_name", "contact_last_name",
                     "contact_job_title", "contact_email", "contact_area_code", "contact_phone"]
    }
}]


tools_create_po=[{
    "name": "create_po",
    "description": (
        "Create a Standard Purchase Order in Oracle EBS. "
        "Use only after the user has confirmed supplier, site, buyer and line details."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "vendor_num":       {"type": "string", "description": "Supplier number (AP_SUPPLIERS.SEGMENT1)"},
            "vendor_site_code": {"type": "string", "description": "Supplier purchasing site code"},
            "buyer_emp_num":    {"type": "string", "description": "Buyer employee number"},
            "ship_to_location": {"type": "string", "description": "Ship-to location code"},
            "bill_to_location": {"type": "string", "description": "Bill-to location code"},
            "comments":         {"type": "string", "description": "PO header description"},
            "approval_status":  {"type": "string", "enum": ["INCOMPLETE", "APPROVED", "INITIATE APPROVAL"],
                                 "description": "Default INCOMPLETE"},
            "lines": {
                "type": "array",
                "description": "PO lines, one distribution each",
                "items": {
                    "type": "object",
                    "properties": {
                        "item_number":      {"type": "string", "description": "Item number; omit for description-only lines"},
                        "item_description": {"type": "string"},
                        "uom_code":         {"type": "string"},
                        "quantity":         {"type": "number"},
                        "unit_price":       {"type": "number"},
                        "need_by_date":     {"type": "string", "description": "YYYY-MM-DD"},
                        "ship_to_org_code": {"type": "string", "description": "Inventory org code, e.g. V1"},
                        "destination_type": {"type": "string", "enum": ["EXPENSE", "INVENTORY"]},
                        "charge_account":   {"type": "string", "description": "Concatenated GL segments, e.g. 01-000-1410-0000-000"}
                    },
                    "required": ["quantity", "unit_price", "need_by_date", "ship_to_org_code"]
                }
            }
        },
        "required": ["vendor_num", "vendor_site_code", "buyer_emp_num", "ship_to_location", "lines"]
    }
}
 ]
# ─── DISPATCHER ───────────────────────────────────────
def call_function(name, inputs):
    if name == "create_item":
        return create_item(
            inputs["item_number"], inputs["description"],
            inputs["master_org_code"], inputs["child_org_code"],
            inputs["template_name"], inputs["uom_code"]
        )
    elif name == "create_supplier":
        return create_supplier(
            inputs["vendor_name"], inputs["terms_name"],
            inputs["currency_code"], inputs["site_code"],
            inputs["address_line1"], inputs["address_line2"],
            inputs["city"], inputs["state"], inputs["zip"],
            inputs["country"], inputs["contact_first_name"],
            inputs["contact_last_name"], inputs["contact_email"]
        )
    elif name == "create_customer":
        return create_customer(
            inputs["customer_name"], inputs["address1"], inputs["address2"],
            inputs["city"], inputs["state"], inputs["postal_code"], inputs["country"],
            inputs["contact_first_name"], inputs["contact_last_name"],
            inputs["contact_job_title"], inputs["contact_email"],
            inputs["contact_area_code"], inputs["contact_phone"]
        )
    elif name == "create_po":
      result = create_po(
        inputs["vendor_num"], inputs["vendor_site_code"],
        inputs["buyer_emp_num"], inputs["ship_to_location"],
        inputs["lines"],
        inputs.get("bill_to_location"),
        inputs.get("comments"),
        inputs.get("approval_status", "INCOMPLETE")
    )
    if result["status"] == "S":
        return f"✅ PO Created! PO#: {result['po_number']} | PO ID: {result['po_header_id']} | Req ID: {result['request_id']}"
    else:
        return f"❌ PO creation failed: {result['message']}"
    return f"Unknown tool: {name}"

# ─── ASK CLAUDE ───────────────────────────────────────
def ask_claude(messages, tools):
    client = get_claude_client()
    while True:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=2000,
            system=SYSTEM_PROMPT,
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
                        "type":        "tool_result",
                        "tool_use_id": block.id,
                        "content":     result
                    })
            messages.append({"role": "user", "content": tool_results})