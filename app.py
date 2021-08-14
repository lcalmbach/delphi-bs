import streamlit as st
import sqlite3
from sqlite3 import Error
import pandas as pd
import altair as alt
from st_aggrid import AgGrid
import json

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
    settings['dic_columns'] = dict(zip(list(df['id']), list(df['name'])))
    return result, result_no_label


def get_data(group_field_ids, sum_fields, table_id):
    def get_criteria():
        if settings['has_filter']:
            if settings['filter']['type']==7: 
                lst_expr = f"','".join(settings['filter']['value'])
                criteria = f"WHERE {settings['filter']['field']} in ('{lst_expr}')"
        else:
            criteria = ''
        return criteria

    table_name = get_table_name(table_id)
    group_fields, group_fields_no_label = get_group_fields(group_field_ids)
    
    sql = f"select {group_fields}, {sum_fields} from {table_name} {get_criteria()} group by {group_fields_no_label} order by {group_fields_no_label}"
    # st.write(sql)
    df = execute_query(sql,conn)
    return df


def get_fields(table_id):
    sql = f"select id, name from stat_table_column where stat_table_id = {table_id} and col_type_id <> 3 order by sort_key"
    df = execute_query(sql,conn)
    result = dict(zip( list(df['id']), list(df['name']) ))
    return result


def get_sum_fields(table_id):
    sql = f"select name, label from stat_table_column where stat_table_id = {table_id} and col_type_id = 3 order by sort_key"
    df = execute_query(sql,conn)
    df['col_expression'] = "sum(" + df['name'] + ') as \'' + df['label'] + '\''
    #df['col_expression_no_label'] = "sum(" + df['name'] + ')'
    result_str = ",".join(list(df['col_expression']))
    result_lst = list(df['label'])
    return result_str, result_lst


def show_filter():
    def get_filter_lookup():
        sql = f"select spital from spitaeler group by spital order by spital"
        df = execute_query(sql,conn)
        return list(df['spital'])

    def get_metadata():
        sql = f"select * from stat_table where id = {settings['table']}"
        df = execute_query(sql,conn)
        settings['has_filter'] = df.iloc[0]['filter'] != None
        if settings['has_filter']:
            settings['filter'] = json.loads(df.iloc[0]['filter']) 
            if settings['filter']['type'] in (6,7):
                settings['filter']['lookup'] = get_filter_lookup()

    all_categories = get_categories()
    settings['category'] = st.selectbox("Kategorie", list(all_categories.keys()),
                                        format_func=lambda x: all_categories[x])    
    tables = get_tables(settings['category'])
    settings['table'] = st.selectbox("Tabelle", list(tables.keys()),
                                        format_func=lambda x: tables[x])
    get_metadata()    
    fields = get_fields(settings['table'])
    settings['group_columns'] = st.multiselect("Felder", list(fields.keys()),
                                        format_func=lambda x: fields[x],
                                        default=fields.keys()) 
    settings['sumfields'], settings['sumfields_no_label'] =  get_sum_fields(settings['table'])  
    
    if settings['has_filter']>0:
        if settings['filter']['type'] == 4:
            settings['filter']['value'] = st.text_input(settings['filter']['label'])
        elif settings['filter']['type'] == 5:
            settings['filter']['value'] = st.number_input(settings['filter']['label'])
        elif settings['filter']['type'] == 6:
            settings['filter']['value'] = st.select(settings['filter']['label'], options=settings['filter']['lookup'])
        elif settings['filter']['type'] == 7:
            settings['filter']['value'] = st.multiselect(settings['filter']['label'], options=settings['filter']['lookup'], default=settings['filter']['lookup'])
        elif settings['filter_field_type'] == 8:
            settings['filter']['value'] = st.select_slider(settings['filter']['label'])
    

def get_plot_options():
    sql = f"select chart, chart_options from stat_table where id = {settings['table']}"
    df = execute_query(sql, conn)
    plot_options = json.loads(df.iloc[0]['chart_options'])
    return df.iloc[0]['chart'], plot_options


def get_chart(df, plot_type, plot_options):
    def plot_barchart():
        if 'color' in plot_options:
            chart = alt.Chart(df).mark_bar().encode(
                x=plot_options['x'], 
                y=plot_options['y'],
                color = plot_options['color'],
                tooltip=plot_options['tooltip']
            )
        else:
            chart = alt.Chart(df).mark_bar().encode(
                x=plot_options['x'], 
                y=plot_options['y'],
                tooltip=plot_options['tooltip']
            )
        return chart

    def plot_linechart():
        if 'color' in plot_options:
            chart = alt.Chart(df).mark_line().encode(
                x=plot_options['x'], 
                y=plot_options['y'],
                color = plot_options['color'],
                tooltip=plot_options['tooltip']
            )
        else:
            chart = alt.Chart(df).mark_line().encode(
                x=plot_options['x'], 
                y=plot_options['y'],
                tooltip=plot_options['tooltip']
            ) #.configure_legend(orient='bottom',direction="vertical")
        return chart

    if plot_type == 'bar':
        chart = plot_barchart()
    elif plot_type == 'line':
        chart = plot_linechart()
    return chart.properties(width = 600)


def get_metadata(df):
    sql = f"select * from stat_table where id =  {settings['table']}"
    df_table = execute_query(sql,conn)
    
    sql = f"select * from stat_table_column where stat_table_id =  {settings['table']}"
    df_columns = execute_query(sql,conn)
    column_expression = '<br><br><table><tr><th>Spalte</th><th>Beeschreibung</th></tr>'
    for index, row in df_columns.iterrows():
        column_expression += f"<tr><td>{row['label']}</td><td>{row['description']}</td></tr>"
    column_expression += '</table>'
    
    table_expression = f"**Beschreibung**: {df_table.iloc[0]['description']}<br>**Datenquelle**: {df_table.iloc[0]['data_source']}"
    if len( df_columns[df_columns['name'] == 'jahr']) > 0:
        min = df['Jahr'].min()
        max = df['Jahr'].max()
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
        if plot_options['groupby']=='parameter':
            for par in settings['sumfields_no_label']:
                df_melted = df[['Jahr','Spital', par]].melt(id_vars=['Jahr','Spital'], value_vars=[par],
                var_name= 'Legende', value_name=par)
                df_melted = df_melted[df_melted['Spital'] != 'Total']
                plot_options['y']=f"{par}:Q"
                plot_options['tooltip']=[plot_options['x'],par]
                plot_options['color']=f"Spital:N"
                chart = get_chart(df_melted, plot_type, plot_options)
                st.altair_chart(chart)
        else:
            plot_options['tooltip']=[plot_options['x'],plot_options['y']]
            chart = get_chart(df, plot_type, plot_options)
            st.altair_chart(chart)
    elif action.lower() == 'metadaten':
        table_expression = get_metadata(df)
        st.markdown(table_expression, unsafe_allow_html=True)

    st.markdown(APP_INFO, unsafe_allow_html=True)

if __name__ == "__main__":
    main()





