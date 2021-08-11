import streamlit as st
import sqlite3
from sqlite3 import Error
import pandas as pd
import altair as alt
from st_aggrid import AgGrid

__version__ = '0.0.1' 
__author__ = 'Lukas Calmbach'
__author_email__ = 'lcalmbach@gmail.com'
VERSION_DATE = '2021-06-12'
my_name = 'delphi-bs'
my_kuerzel = "dbs"
GIT_REPO = 'https://github.com/lcalmbach/delphi-bs'
APP_INFO = f"""<div style="background-color:powderblue; padding: 10px;border-radius: 15px;">
    <small>App created by <a href="mailto:{__author_email__}">{__author__}</a><br>
    version: {__version__} ({VERSION_DATE})<br>
    <a href="{GIT_REPO}">git-repo</a>
    """

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
    sql = f"select id, name from stat_table where category_id = {cat} order by category_id, sort_key"
    df = execute_query(sql,conn)
    result = dict(zip( list(df['id']), list(df['name']) ))
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

    sql = f"select * from stat_table_column where id in ({csv_list}) order by sort_key"
    df = execute_query(sql,conn)
    df['col_expression'] = df['name'] + ' as \'' + df['label'] + '\''
    result = ",".join(list(df['col_expression']))
    result_no_label = ",".join(list(df['name']))
    return result, result_no_label


def get_data(group_field_ids, sum_fields, table_id):
    table_name = get_table_name(table_id)
    group_fields, group_fields_no_label = get_group_fields(group_field_ids)
    sql = f"select {group_fields}, {sum_fields} from {table_name} group by {group_fields_no_label} order by {group_fields_no_label}"
    # st.write(sql)
    df = execute_query(sql,conn)
    return df


def get_fields(table_id):
    sql = f"select id, name from stat_table_column where stat_table_id = {table_id} and col_type_id <> 3 order by sort_key"
    df = execute_query(sql,conn)
    result = dict(zip( list(df['id']), list(df['name']) ))
    return result


def get_sum_fields(table_id):
    sql = f"select name,label from stat_table_column where stat_table_id = {table_id} and col_type_id = 3 order by sort_key"
    df = execute_query(sql,conn)
    df['col_expression'] = "sum(" + df['name'] + ') as \'' + df['label'] + '\''
    result = ",".join(list(df['col_expression']))
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
    settings['sumfields'] =  get_sum_fields(settings['table'])  
    

def get_plot_options():
    sql = f"select chart, chart_options from stat_table where id = {settings['table']}"
    df = execute_query(sql,conn)
    return df.iloc[0]['chart'],df.iloc[0]['chart_options']


def get_chart(df, plot_type, plot_options):
    if plot_type ==  'bar':
        chart = alt.Chart(df).mark_bar().encode(
            x='Jahr:N',
            y='Anzahl:Q'
        )
    return chart.properties(width = 400)


def get_metadata(df):
    sql = f"select * from stat_table where id =  {settings['table']}"
    df_table = execute_query(sql,conn)
    sql = f"select * from stat_table_column where stat_table_id =  {settings['table']}"
    df_columns = execute_query(sql,conn)
    column_expression = '<br>**Spalten**:<br>'
    for index, row in df_columns.iterrows():
        column_expression += f"{row['label']}: {row['description']}<br>"
    table_expression = f"**Beschreibung**: {df_table.iloc[0]['description']}<br>**Datenquelle**: {df_table.iloc[0]['data_source']}"
    if len( df_columns[df_columns['name'] == 'jahr']) > 0:
        min= df['Jahr'].min()
        max= df['Jahr'].max()
        table_expression += f"<br>**Jahre von/bis**: {min} - {max}"
    table_expression += column_expression
    return table_expression

def main():
    st.set_page_config(
        page_title=my_name,
        page_icon="ℹ",
        layout="wide",
    )
    show_filter()
    
    action = st.selectbox('Zeige', ['Tabelle', 'Grafik', 'Metadaten'])

    df = get_data(settings['group_columns'],  settings['sumfields'], settings['table'])  
    if action.lower() == 'tabelle':
        if len(df)>0:
            AgGrid((df))
        else:
            st.markdown('keine Daten gefunden')
    elif action.lower() == 'grafik':
        plot_type, plot_options = get_plot_options()
        chart = get_chart(df, plot_type, plot_options)
        st.altair_chart(chart)
    elif action.lower() == 'metadaten':
        table_expression = get_metadata(df)
        st.markdown(table_expression,unsafe_allow_html=True)

if __name__ == "__main__":
    main()





