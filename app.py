import streamlit as st
import mysql.connector
from mysql.connector import Error
import pandas as pd

st.set_page_config(page_title="Demon", page_icon="")

def get_connection():
    secrets = st.secrets["mysql"]
    return mysql.connector.connect(
        host=secrets["host"],
        user=secrets["user"],
        password=secrets["password"],
        database=secrets["database"],
    )

def insert_measurement(label: str, value: float):
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        INSERT INTO measurements (label, value)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE
            value = value + VALUES(value)
    """
    cursor.execute(query, (label, value))
    conn.commit()
    cursor.close()
    conn.close()

def clear_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE measurements")
    conn.commit()
    cursor.close()
    conn.close()

@st.cache_data
def load_data():
    conn = get_connection()
    df = pd.read_sql("SELECT id, label, value FROM measurements", conn)
    conn.close()
    return df

st.title("Streamlit/MySQL -demo")
st.write("Dis valuable data cometh from sql database.")

st.subheader("Add stuff to database")

with st.form("add_measurement"):
    new_label = st.text_input("Label (for example: 'Raccoon')")
    new_value = st.number_input("Value", step=1.0)
    submitted = st.form_submit_button("Save to database")

if submitted:
    if not new_label:
        st.warning("Give at least LABEL")
    else:
        insert_measurement(new_label, new_value)
        load_data.clear()
        st.success("Data saved and refreshed")

st.subheader("Database tools")

col1, col2 = st.columns(2)

with col1:
    if st.button("Refresh database"):
        load_data.clear()
        st.info("Data refreshed")

with col2:
    with st.expander("Clear database (requires password)"):
        pwd = st.text_input("Password", type="password")
        if st.button("Clear ALL data"):
            if pwd == st.secrets["mysql"]["password"]:
                clear_table()
                load_data.clear()
                st.success("Database cleared")
            else:
                st.error("Wrong password. Nothing was cleared")

st.subheader("Database data")

df = load_data()

if df.empty:
    st.info("Database is empty or data could not be loaded.")
else:
    st.dataframe(df, use_container_width=True)
    if "label" in df.columns and "value" in df.columns:
        st.bar_chart(df.set_index("label")["value"])
