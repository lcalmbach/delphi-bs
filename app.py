import streamlit as st
import sqlite3
from sqlite3 import Error
import pandas as pd
import altair as alt
from st_aggrid import AgGrid
import json
import requests

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
    sql = f"select id, name from stat_table where category_id in ({cat},0) order by category_id, sort_key"
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
    csv_list = result = ','.join(map(str, column_id_list))

    sql = f"select * from stat_table_column where id in ({csv_list}) order by sort_key"
    df = execute_query(sql,conn)
    df['col_expression'] = df['name'] + ' as \'' + df['label'] + '\''
    result = ",".join(list(df['col_expression']))
    result_no_label = ",".join(list(df['name']))
    settings['dic_columns'] = dict(zip(list(df['id']), list(df['name'])))
    return result, result_no_label


def get_rename_obj(df_columns):
    result = {}
    for index, row in df_columns.iterrows():
        result[row['name']] = row['label']
    return result

def get_ordered_columns_list(df, field):
    #result =  ",".join(list(df[field]))
    result = list(df.sort_values('sort_key')[field])
    return result


def get_url_df():
    data = requests.get(settings['url']).json()
    data = data['records']
    df = pd.DataFrame(data)['fields']
    df = pd.DataFrame(x for x in df)
    df = df.rename(columns=get_rename_obj(settings['df_columns']))
    df_cols = settings['df_columns']
    # in some cases, we do not show show a column selection field, e.g. for must current covid cases, where the table is presented
    # as is
    if len(settings['group_columns'])>0:
        df_cols = df_cols[ df_cols['id'].isin(list(settings['group_columns'])) ]
    lst_fields = list(df_cols['label'])
    df = df[lst_fields]


    if settings['has_index']:
        df.set_index(settings['index_field'],inplace=True)
        df = df.T
        df.reset_index(inplace=True)
    else:
        if settings['has_filter']:
            if settings['filter']['type'] == 5: 
                df = df.astype({settings['filter']['field']: int})
                df = df[df[settings['filter']['field']] == int(settings['filter']['value'])]
    return df


def get_data(group_field_ids, sum_fields, table_id):
    def get_criteria():
        criteria = ''
        if settings['has_filter']:
            if settings['filter']['type'] == 7 and settings['filter']['value'] != []: 
                lst_expr = f"','".join(settings['filter']['value'])
                criteria = f"WHERE {settings['filter']['field']} in ('{lst_expr}')"
            elif settings['filter']['type'] == 6 and settings['filter']['value'] != '<Alle>':  
                criteria = f"WHERE {settings['filter']['field']} = '{settings['filter']['value']}'"
            elif settings['filter']['type'] == 5: 
                criteria = f"WHERE {settings['filter']['field']} = {settings['filter']['value']}"
            
        return criteria
    
    if settings['is_url']:
        df = get_url_df()
    else:
        group_fields, group_fields_no_label = get_group_fields(group_field_ids)
        sql = f"select {group_fields}, {sum_fields} from {settings['table_name']} {get_criteria()} group by {group_fields_no_label} order by {group_fields_no_label}"
        #st.write(sql)
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
    result_lst = list(df['name'])
    return result_str, result_lst


def get_filter_lookup(field, table):
    if settings['is_url'] == False:
        sql = f"select {field} from {table} group by {field} order by  {field}"
        df = execute_query(sql,conn)
    result = ['<Alle>'] + list(df[field])
    return result


def get_metadata():
    sql = f"select * from stat_table where id = {settings['table']}"
    df = execute_query(sql,conn)
    settings['df_table'] = df
    settings['table_name'] =  df.iloc[0]['table_name']
    settings['has_filter'] = df.iloc[0]['filter'] != None
    settings['is_url'] = df.iloc[0]['url'] != None
    settings['url'] = df.iloc[0]['url']
    settings['show_options'] = json.loads(df.iloc[0]['show_options']) 
    if settings['has_filter']:
        settings['filter'] = json.loads(df.iloc[0]['filter']) 
        if settings['filter']['type'] in (6,7):
            settings['filter']['lookup'] = get_filter_lookup(settings['filter']['field'], settings['table_name'])
    settings['has_index'] = df.iloc[0]['index_field'] != None
    if settings['has_index']:
        settings['index_field'] = df.iloc[0]['index_field']
    

    sql = f"select * from stat_table_column where stat_table_id = {settings['table']}"
    df = execute_query(sql,conn)
    settings['df_columns'] = df


def show_filter():
    all_categories = get_categories()
    settings['category'] = st.selectbox("Kategorie", list(all_categories.keys()),
                                        format_func=lambda x: all_categories[x])    
    tables = get_tables(settings['category'])
    settings['table'] = st.selectbox("Tabelle", list(tables.keys()),
                                        format_func=lambda x: tables[x])
    get_metadata()    
    fields = get_fields(settings['table'])
    if len(fields)>0:
        settings['group_columns'] = st.multiselect("Felder", list(fields.keys()),
                                        format_func=lambda x: fields[x],
                                        default=fields.keys()) 
    
    settings['sumfields'], settings['sumfields_no_label'] =  get_sum_fields(settings['table'])  
    
    if settings['has_filter']>0:
        if settings['filter']['type'] == 4:
            settings['filter']['value'] = st.text_input(settings['filter']['label'])
        elif settings['filter']['type'] == 5:
            settings['filter']['value'] = st.number_input(settings['filter']['label'],
                min_value=settings['filter']['min'],
                max_value=settings['filter']['max'],
                value=settings['filter']['max'])
        elif settings['filter']['type'] == 6:
            settings['filter']['value'] = st.selectbox(settings['filter']['label'], options=settings['filter']['lookup'])
        elif settings['filter']['type'] == 7:
            settings['filter']['value'] = st.multiselect(settings['filter']['label'], options=settings['filter']['lookup'], default=settings['filter']['lookup'])
            settings['filter']['value'] =  [i.replace("'","''") for i in settings['filter']['value']] 
        elif settings['filter']['type'] == 8:
            settings['filter']['value'] = st.select_slider(settings['filter']['label'])
    

def get_plot_options():
    sql = f"select chart, chart_options from stat_table where id = {settings['table']}"
    df = execute_query(sql, conn)
    plot_options = json.loads(df.iloc[0]['chart_options'])
    plot_options['x'] = alt.X(plot_options['x'])
    plot_options['y'] = alt.X(plot_options['y'])
    if 'sort_x' in plot_options:
        plot_options['x'].sort=plot_options['sort_x']
    if 'sort_y' in plot_options:
        plot_options['y'].sort=plot_options['sort_y']
    return df.iloc[0]['chart'], plot_options


def get_chart(df, plot_type, plot_options):
    def plot_barchart():
        if 'color' in plot_options:
            chart = alt.Chart(df).mark_bar().encode(
                x=plot_options['x'],
                y=plot_options['y'],
                color = plot_options['color'],
                #tooltip=plot_options['tooltip']
            )
        else:
            chart = alt.Chart(df).mark_bar().encode(
                x=plot_options['x'],
                y=plot_options['y'],
                #tooltip=plot_options['tooltip']
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


def get_metadata_text(df):
    sql = f"select * from stat_table where id =  {settings['table']}"
    df_table = execute_query(sql,conn)
    
    sql = f"select * from stat_table_column where stat_table_id =  {settings['table']}"
    df_columns = execute_query(sql,conn)
    column_expression = '<br><br><table><tr><th>Spalte</th><th>Beschreibung</th></tr>'
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
    settings['group_columns'] = {}
    settings['sumfields'] = {}
    settings['table'] = {}

    show_filter()
    action = st.selectbox('Zeige', settings['show_options'])
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
                plot_options['y']=alt.Y(f"{par}:Q", sort = 'x')
                plot_options['tooltip']=alt.X([plot_options['x'],par])
                plot_options['color']=f"Spital:N"
                chart = get_chart(df_melted, plot_type, plot_options)
                st.altair_chart(chart)
        if plot_options['groupby']=='selected_fields':
            chart_group_fields = settings['df_columns'][(settings['df_columns']['is_chart_group_by_field']==1) & (settings['df_columns']['id'].isin(settings['group_columns']))]
            chart_group_fields = list(chart_group_fields['label'])
            chart_index_field = list(settings['df_columns'][settings['df_columns']['is_chart_index_field']==1]['label'])[0]
            for field in chart_group_fields:
                df_chart = df[[chart_index_field,field]]
                plot_options['x']=alt.X(f"{field}:Q", sort = 'y')
                chart = get_chart(df_chart, plot_type, plot_options)
                st.altair_chart(chart)
        else:
            plot_options['tooltip']=[plot_options['x'],plot_options['y']]

            chart = get_chart(df, plot_type, plot_options)
            st.altair_chart(chart)
    elif action.lower() == 'metadaten':
        table_expression = get_metadata_text(df)
        st.markdown(table_expression, unsafe_allow_html=True)

    st.markdown(APP_INFO, unsafe_allow_html=True)

if __name__ == "__main__":
    main()





