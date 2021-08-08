import streamlit as st
import sqlite3
from sqlite3 import Error
import pandas as pd
from st_aggrid import AgGrid

__version__ = '0.0.1' 
__author__ = 'Lukas Calmbach'
__author_email__ = 'lcalmbach@gmail.com'
VERSION_DATE = '2021-06-12'
my_name = 'delphi-bs'
my_kuerzel = "dbs"
GIT_REPO = 'https://github.com/lcalmbach/delphi-bs'
conn = {}
config = {} # dictionary mit allen Konfigurationseinträgen
APP_INFO = f"""<div style="background-color:powderblue; padding: 10px;border-radius: 15px;">
    <small>App created by <a href="mailto:{__author_email__}">{__author__}</a><br>
    version: {__version__} ({VERSION_DATE})<br>
    <a href="{GIT_REPO}">git-repo</a>
    """

conn = {}
DB_FILE_PATH = "delphi-bs.sqlite3"
conn = sqlite3.connect(DB_FILE_PATH)
settings = {}

def execute_query(query: str, cn) -> pd.DataFrame:
    """
    Executes a query and returns a dataframe with the results
    """

    ok= False
    result = None
    try:
        result = pd.read_sql_query(query, cn)
        ok = True
    except Exception as ex:
        print(ex)

    return result

def get_tables(cat):
    sql = f"select id, table_name from stat_table where category_id = {cat} order by category_id, sort_key"
    df = execute_query(sql,conn)
    result = dict(zip( list(df['id']), list(df['table_name']) ))
    return result

def get_categories():
    sql = f"select id, name from category order by name"
    df = execute_query(sql,conn)
    result = dict(zip( list(df['id']), list(df['name']) ))
    return result

def get_table_name(table_id):
    sql = f"select table_name from stat_table where id = {table_id}"
    df = execute_query(sql,conn)
    return df.iloc[0]['table_name']

def get_group_fields(column_id_list):
    csv_list = result = ','.join(map(str,column_id_list))

    sql = f"select name from stat_table_column where id in ({csv_list}) order by sort_key"
    df = execute_query(sql,conn)
    result = ','.join(df['name'])
    return result

def get_data(group_field_ids, sum_field, table_id):
    table_name = get_table_name(table_id)
    group_fields = get_group_fields(group_field_ids)
    sql = f"select {group_fields}, sum({sum_field}) as anzahl from {table_name} group by {group_fields} order by {group_fields}"
    df = execute_query(sql,conn)
    return df

def get_fields(table_id):
    sql = f"select id, name from stat_table_column where stat_table_id = {table_id} and col_type_id <> 3 order by sort_key"
    df = execute_query(sql,conn)
    result = dict(zip( list(df['id']), list(df['name']) ))
    return result


def get_sum_fields(table_id):
    sql = f"select name from stat_table_column where stat_table_id = {table_id} and col_type_id = 3 order by sort_key"
    df = execute_query(sql,conn)
    result = ",".join(df['name'])
    return result


def show_filter():
    all_categories = get_categories()
    settings['category'] = st.selectbox("Kategorie", list(all_categories.keys()),
                                        format_func=lambda x: all_categories[x])    
    tables = get_tables(settings['category'])
    settings['table'] = st.selectbox("Tabelle", list(tables.keys()),
                                        format_func=lambda x: tables[x])    
    fields = get_fields(settings['table'])
    settings['group_columns'] = st.multiselect("Felder", list(fields.keys()),
                                        format_func=lambda x: fields[x],
                                        default=fields.keys()) 
    sumfields =  get_sum_fields(settings['table'])  
    
    df = get_data(settings['group_columns'],  sumfields, settings['table'])  
    return df

   
def main():
    st.set_page_config(
        page_title=my_name,
        page_icon="ℹ",
        layout="wide",
    )
    df = show_filter()
    
    st.markdown(
    '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.5.3/dist/css/bootstrap.min.css" integrity="sha384-TX8t27EcRE3e/ihU7zmQxVncDAy5uIKz4rEkgIXeMed4M0jlfIDPvg6uqKI2xXr2" crossorigin="anonymous">',
    unsafe_allow_html=True,
    )
    query_params = st.experimental_get_query_params()
    tabs = ["Tabelle", "Grafik", "Metadaten"]
    if "tab" in query_params:
        active_tab = query_params["tab"][0]
    else:
        active_tab = "Tabelle"

    if active_tab not in tabs:
        st.experimental_set_query_params(tab="Home")
        active_tab = "Home"

    li_items = "".join(
        f"""
        <li class="nav-item">
            <a class="nav-link{' active' if t==active_tab else ''}" href="/?tab={t}">{t}</a>
        </li>
        """
        for t in tabs
    )
    tabs_html = f"""
        <ul class="nav nav-tabs">
        {li_items}
        </ul>
    """

    st.markdown(tabs_html, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    if active_tab == "Tabelle":
        AgGrid((df))
        

if __name__ == "__main__":
    main()





