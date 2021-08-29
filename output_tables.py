import streamlit as st
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode, JsCode
import pandas as pd

class App:
    def __init__(self, df, metadata):
        self.base_data = df
        self.data = df
        self.metadata = metadata
        self.selected_columns = []

    def get_selected_columns(self):
        """
        displays a multiselectbox and fills it with all available columns
        """
        def get_columns_dic()->dict:
            """
            returns a dictionary of all columns in the form: {id, label}
            """
            _df = self.metadata['columns']
            result = dict(zip( list(_df['id']), list(_df['label']) ))
            return result

        columns = get_columns_dic()
        sel_columns = st.multiselect("Felder", list(columns.keys()),
                                        format_func=lambda x: columns[x],
                                        default=columns.keys()) 
        return self.metadata['columns'].query('id in @sel_columns')
    
    def apply_additional_filters(self):
        def get_col_name(col_id):
            col_name = self.metadata['columns'][self.metadata['columns']['id'] == col_id]
            return col_name.iloc[0]['label']

        def get_lookup_fields(col_name, add_all_item):
            result = list(self.data[col_name].unique())
            result.sort()
            if add_all_item:
                result = ['<Alle>'] + result
            return result

        if (self.metadata['table']['has_filter']):
            filter = self.metadata['table']['filter']
            if filter['column'] in list(self.selected_columns['id']):            
                filter['col_name'] = get_col_name(filter['column'])
                if filter['type'] in [6,7]:
                    filter['lookup'] = get_lookup_fields(filter['col_name'], filter['type'] == 6)
                if int(filter['type']) == 4:
                    filter['value'] = st.text_input(filter['label'])
                elif int(filter['type']) == 5:
                    filter['value'] = st.number_input(filter['label'],
                        min_value=filter['min'],
                        max_value=filter['max'],
                        value=filter['max'])
                elif int(filter['type']) == 6:
                    filter['value'] = st.selectbox(filter['label'], options=filter['lookup'])
                elif int(filter['type']) == 7:
                    filter['value'] = st.multiselect(filter['label'], options=filter['lookup'], default=filter['lookup'])
                    filter['value'] =  [i.replace("'","''") for i in filter['value']] 
                elif int(filter['type']) == 8:
                    filter['value'] = st.select_slider(filter['label'])
                if filter['value'] != '<Alle>':
                    self.data = self.data[ self.data[filter['col_name']] == str(filter['value'])]
            

    def show_table(self):
        """
        displays the selected columns in a table
        """

        def get_format():
            gb = GridOptionsBuilder.from_dataframe(self.data)
            gb.configure_default_column(groupable=False, value=True, enableRowGroup=False, aggFunc='sum', editable=False)
            gb.configure_grid_options(domLayout='normal')
            formatted_columns = self.selected_columns[self.selected_columns['column_format']!='{}']
            for index, row in formatted_columns.iterrows():
                if row['column_format'] != {}:
                    x = row['column_format']
                    gb.configure_column(row['label'], type=x['type'], precision=x['precision'])
            return gb.build()

        if len(self.data)>0:
            gridOptions = get_format()
            AgGrid(self.data,gridOptions=gridOptions)
        else:
            st.markdown('keine Daten gefunden')

    def get_table(self, sel_columns):
        """
        limits the columns to the selected columns
        """
        def column_ids_to_names():
            ids = sel_columns
            df = self.metadata['columns'].query('id in @ids')
            return df['label']

        sel_column_names = column_ids_to_names()
        return self.base_data[sel_column_names]

    def aggregate(self):
        def get_melt_columns():
            agg_value_cols = self.selected_columns.query('stat_func.notnull()')
            agg_group_cols = self.selected_columns.query('stat_func.isnull()')
            func = agg_value_cols.iloc[0]['stat_func']
            return agg_group_cols, func
        
        def has_removed_cols():
            return len(self.selected_columns) != len(self.metadata['columns'])

        if has_removed_cols() & self.metadata['table']['has_agg_function_column']:
            agg_group_cols, func = get_melt_columns()
            self.data = self.data.groupby(list(agg_group_cols['label'])).agg(func).reset_index()      

    def show_menu(self):
        self.selected_columns = self.get_selected_columns() 
        self.data = self.get_table(list(self.selected_columns['id']))
        self.apply_additional_filters()
        self.aggregate()
        self.show_table()