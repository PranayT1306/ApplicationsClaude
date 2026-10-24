import streamlit as st
import anthropic
import json
import os
import oracledb
import pandas as pd

BASE_DIR=os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH=os.path.join(BASE_DIR,'json.config')
with open(CONFIG_PATH,'r') as c:
    params=json.load(c)["params"]
oracledb.init_oracle_client(lib_dir=r"C:\instantclient_21_11")
st.title("Pranay AI Assistant")
st.write("Ask questions about Oracle EBS in plain English!")
question=st.text_input("Ask your question:",placeholder="e.g. Show top 100 active vendors")
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
if st.button("Generate & Execute"):
    if question:
        with st.spinner("Claude is thinking ............."):
            try:
                print("Trying to connect to Claude")
                client=anthropic.Anthropic(
                    api_key=params["anthropic_api_key"]
                )
                print("Connected to Claude")
                message=client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=1500,
                    temperature=0,
                      system="""You are Oracle EBS Technical Expert R12.2.10.
                STRICT RULES:
                1. Return ONLY plain SQL query
                2. NO markdown
                3. NO code blocks
                4. NO backticks
                5. NO ```sql tags
                6. NO explanations
                7. NO semicolon at end
                8. Plain text SQL only!
                9. NO ANSII JOINS""",
                    messages=[{
                        "role":"user",
                        "content":question
                    }]


                )
                sql=message.content[0].text
                sql=sql.strip().rstrip(';')
                print(f"Generated SQL: {sql}")
                 # Show generated SQL
                st.subheader("Generated SQL:")
                st.code(sql, language='sql')
                conn=oracledb.connect(
                    user=params["oracle_user"],
                    password=params["oracle_password"],
                    dsn=params["oracle_dsn"]
                )

                cursor=conn.cursor()
                cursor.execute(sql)
                results=cursor.fetchall()
                columns=[col[0] for col in cursor.description]
                df=pd.DataFrame(results, columns=columns)
                st.subheader(f"Results: {len(df)} rows")
                st.dataframe(df)

                excel_path=os.path.join(BASE_DIR,"results.xlsx")
                df = clean_dataframe(df)
                df.to_excel(
                  excel_path, 
                 index=False,
                  engine='xlsxwriter'    # ✅ handles special chars!
                             )
                with open(excel_path, 'rb') as f:
                    st.download_button(
                        label="Download Excel 📊",
                        data=f,
                        file_name="query_results.xlsx",
                        mime="application/vnd.ms-excel"
                    )

            except  Exception as e:
                st.error(f"Error: {str(e)}")
    else:
        st.warning("Please enter a question!")
     
 
