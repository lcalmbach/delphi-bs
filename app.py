import streamlit as st
import sqlite3
from sqlite3 import Error
import pandas as pd
import extra_streamlit_components as stx
import json
import requests
import output_tables as ot
import output_charts as oc
import output_metadata as om
from queries import query

__version__ = '0.0.1'
__author__ = 'Lukas Calmbach'
__author_email__ = 'lcalmbach@gmail.com'
VERSION_DATE = '2021-8-24'
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
metadata = {}
data = pd.DataFrame


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

def get_rename_obj(df_columns):
    """
    returns the "columns = {}" part of a pandas column rename statement object where a = column names
    and 'x' = column label
    e.g. df.rename(columns={'a'='x','b'='y' })
    """
    result = {}
    for index, row in df_columns.iterrows():
        result[row['name']] = row['label']
    return result
    
#@st.cache()
def get_url_df():
    """
    converts the json returned by an api call to data.bs
    """
    data = requests.get(metadata['table']['url']).json()
    data = data['records']
    df = pd.DataFrame(data)['fields']
    df = pd.DataFrame(x for x in df)
    
    return df


def get_data():
    """
    returns data from either a url request or from the local database. if the field url is filled in the table
    metadata, then a request is sent, otherwise there is a tablename and data is retrieved from this database-table
    """
    if metadata['table']['is_url']:
        df = get_url_df()
        df = complete_aggregated_df(df)
    else:
        table_name = metadata['table']['table_name']
        sql = query['select_from'].format(table_name)
        df = execute_query(sql,conn)
    
    #replace column names by labels which are henceforth used
    df = df.rename(columns = get_rename_obj(metadata['columns']))
    return df


def get_fields_dict()->dict:
    """
    returns a dictionary of all columns in the form: {id, label}
    """
    _df = metadata['table']['df_all_columns']
    result = dict(zip( list(_df['id']), list(_df['label']) ))
    return result


def get_table():
    """
    displays the category and tables widgets and allows the user to select a table
    """
    def get_tables_dict(cat):
        """
        Returns a dictionary of all available tables for a given category
        """

        sql = query['all_tables'].format(cat)
        df = execute_query(sql, conn)
        result = dict(zip( list(df['id']), list(df['name']) ))
        return result


    def get_categories_dict():
        """
        Returns a dict of all available categories. Each table belongs to a category such as population, 
        environment, health
        """

        sql = f"select id, name from category order by name"
        df = execute_query(sql,conn)
        result = dict(zip( list(df['id']), list(df['name']) ))
        return result


    all_categories = get_categories_dict()
    cat = st.selectbox("Kategorie", list(all_categories.keys()),
                                        format_func=lambda x: all_categories[x])    
    tables = get_tables_dict(cat)
    result = st.selectbox("Tabelle", list(tables.keys()),
                                        format_func=lambda x: tables[x])
    return result


def get_metadata(table_id):
    """
    returns the metadata for the selected table table
    """

    metadata = {}
    sql = query['table_metadata'].format(table_id)
    df = execute_query(sql,conn)
    metadata['table'] = df.query('id == @table_id').iloc[0]
    metadata['table']['is_url'] = metadata['table']['url'] != None
    metadata['table']['filter_chart'] = json.loads(metadata['table']['filter_chart'])
    metadata['table']['filter_table'] = json.loads(metadata['table']['filter_table'])
    metadata['table']['has_filter_chart'] = metadata['table']['filter_chart'] != []
    metadata['table']['has_filter_table'] = metadata['table']['filter_table'] != []
    metadata['table']['chart_options'] = json.loads(metadata['table']['chart_options'])
    metadata['table']['time_aggregation'] = json.loads(metadata['table']['time_aggregation'])
    
    sql = query['column_metadata'].format(table_id)
    df = execute_query(sql, conn)
    metadata['columns'] = df
    metadata['columns']['column_format'] = metadata['columns'].apply(lambda row: json.loads(row['column_format']), axis=1)
    metadata['table']['has_agg_function_column'] = len(metadata['columns'].query('stat_func.notnull()')) > 0
    metadata['table']['can_melt'] = len(metadata['columns'].query("chart_field_type == 'g'")) > 0
    return metadata

def complete_aggregated_df(df):
    """
    calculates a data column based on month and year (using mid month date)
    """

    def get_col_list(types):
        col_types = types
        df = metadata['columns']
        result = df.query("col_type.isin(@col_types)")

    ta = metadata['table']['time_aggregation']
    if ta != {}:
        df[ta['date_field']] = pd.to_datetime(df[ta['date_field']])
        for agg_field in ta['agg_fields']:
            if agg_field['interval'] == 'month':
                df['Tag'] = 15
                df[agg_field['name']] = df[ta['date_field']].dt.month
            if agg_field['interval']  == 'year':
                df[agg_field['name']]  = df[ta['date_field']].dt.year
            if agg_field['interval']  == 'date_month':
                df['day'] = 15
                df[agg_field['name']] = pd.to_datetime([f'{y}-{m}-{d}' for y, m, d in zip(df['Jahr'], df['Monat'], df['day'])])
        df = df.drop(['date', 'day'], axis=1)

        id_vars = ['Jahr','Monat','Datum_Monat','kategorie']
        df = df.groupby(by=ta['id_vars']).agg(func=ta['func']).reset_index()
    return df


def main():
    global metadata

    def init():
        st.set_page_config(
            page_title=my_name,
            page_icon="ℹ",
            layout="wide",
        )

    init()
    table_id = get_table()
    metadata = get_metadata(table_id)
    data = get_data()
    
    menu_options = [stx.TabBarItemData(id=1, title="Tabelle", description="")]
    if "Grafik" in metadata['table']["tab_options"]:
       menu_options.append(stx.TabBarItemData(id=2, title="Grafik", description=""))
    menu_options.append(stx.TabBarItemData(id=3, title="Metadaten", description=""))
    action = stx.tab_bar(menu_options, default=1)

    action = int(action)
    if action == 1:
        app = ot.App(data, metadata)
    elif action == 2:
        app = oc.App(data, metadata)
    elif action == 3:
        app = om.App(data, metadata)
    app.show_menu()
        
    st.markdown(APP_INFO, unsafe_allow_html=True)

if __name__ == "__main__":
    main()





