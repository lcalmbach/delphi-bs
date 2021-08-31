import streamlit as st
import altair as alt

class App:
    def __init__(self, df, metadata):
        self.base_data = df
        self.metadata = metadata
        self.has_filter = self.filter = self.metadata['table']['has_filter_chart']
        self.filter = self.metadata['table']['filter_chart']


    def get_unique_values(self, key):
        result = list(self.data[key].unique())
        result.sort()
        return result

    def get_columns(self, cfg):
        """
        builds the metadata text consisting of a intro-text and a list of column-descriptions
        """
        def get_col_list(tp):
            col_type = tp
            result = self.metadata['columns'].query("chart_field_type == @col_type")

            return list(result['label'])

        def filter_data(key, values):
            if type(values) == list:
                self.data = self.data[ self.data[key].isin(values) ]
            else:
                self.data = self.data[ self.data[key] == values ]

        def get_filter_item(filter):
            if filter['type'] == 4:
                result = st.text_input(filter['label'])
            elif filter['type'] == 5:
                result = st.number_input(filter['label'],
                    min_value=filter['min'],
                    max_value=filter['max'],
                    value=filter['default'])
            elif filter['type'] == 6:
                lookup_list =  self.get_unique_values(filter['field'])
                result = st.selectbox(filter['label'], options=lookup_list)
            elif filter['type'] == 7:
                lookup_list =  self.get_unique_values(filter['field'])
                result = st.multiselect(filter['label'], options=lookup_list)
                result =  [i.replace("'","''") for i in result] 
            elif filter['type'] == 8:
                result = st.select_slider(filter['label'])
            return result

        if "force_options" in self.metadata['table']['chart_options']:
            ts = self.metadata['table']['chart_options']
            cfg['x'] = ts['x']
            cfg['y'] = ts['y']
            cfg['plot_group'] = ts['plot_group']
            if self.has_filter:
                # if a filter has been defined:
                for filter in self.filter:
                    filter['value'] = get_filter_item(filter)
                    if len(filter['value']) > 0:
                        filter_data(filter['field'], filter['value'])
        elif len(cfg['value_fields']) == 1:
            x_cols = get_col_list('x')
            y_cols = get_col_list('y')
            color_cols = get_col_list('g')
            group_cols = get_col_list('g')
            col1, col2 = st.columns(2)
            cfg['x'] = col1.selectbox("X-Achse", x_cols)
            cfg['y'] = col2.selectbox("Y-Achse", y_cols)

            cfg['color'] = col1.selectbox("Legende", color_cols)
            group_cols.remove(cfg['color'])
            cfg['plot_group'] = col2.selectbox("Gruppiere Grafiken nach:", group_cols)
            
            lst_color_items = self.get_unique_values(cfg['color'])
            lst_group_items = self.get_unique_values(cfg['plot_group'])
            cfg['color_filter'] = col1.multiselect(f"Filter {cfg['color']}", lst_color_items)
            if len(cfg['color_filter']) > 0:
                filter_data(cfg['color'], cfg['color_filter'])
            cfg['group_filter'] = col2.multiselect(f"Filter {cfg['plot_group']}", lst_group_items)
            if len(cfg['group_filter']) > 0:
                filter_data(cfg['plot_group'], cfg['group_filter'])
        else:
            x_cols = get_col_list('x')
            cfg['x'] = x_cols[0]
            cfg['color_filter'] = ''
            cfg['plot_group'] = []
            cfg['y'] = self.metadata['table']['chart_options']['melt_value_name']
            cfg['color'] = self.metadata['table']['chart_options']['melt_var_name']
            lst_color_items = self.get_unique_values(cfg['color'])
            cfg['color_filter'] = st.multiselect(f"Filter {cfg['color']}", lst_color_items)
            if len(cfg['color_filter']) > 0:
                filter_data(cfg['color'], cfg['color_filter'])

        return cfg

    
    def melt_data(self,cfg):
        def get_col_list(tp):
            col_type = tp
            result = self.metadata['columns'].query("col_type.isin(@col_type)")
            return list(result['label'])
        
        cfg['value_fields'] = get_col_list(['Q'])
        if len(cfg['value_fields']) > 1:
            cfg['group_fields'] = get_col_list(['N','O'])
            self.data = self.base_data.melt(id_vars=cfg['group_fields'], value_vars=cfg['value_fields'],
                var_name = self.metadata['table']['chart_options']['melt_var_name'], value_name=self.metadata['table']['chart_options']['melt_value_name'])
        else:
            self.data = self.base_data
            cfg['group_fields'] = []
        return cfg


    def get_chart(self,df, cfg):
        """
        plots the data as a line or barchart
        """
        def plot_barchart():
            chart = alt.Chart(df, title = title).mark_bar().encode(
                x=cfg['x_ax'],
                y=cfg['y_ax'],
                tooltip=cfg['tooltip']
            )
            
            return chart

        def plot_linechart():
            if 'color' in cfg:
                chart = alt.Chart(df, title = title).mark_line().encode(
                    x=cfg['x_ax'],
                    y=cfg['y_ax'],
                    color = cfg['color_ax'],
                    tooltip=cfg['tooltip']
                )
            else:
                chart = alt.Chart(df).mark_line().encode(
                    x=cfg['x_ax'],
                    y=cfg['y_ax'],
                    tooltip=cfg['tooltip']
                )
            return chart

        title = cfg['title'] if 'title' in cfg else ''
        if cfg['plot_type'] == 'bar':
            chart = plot_barchart()
        elif cfg['plot_type'] == 'line':
            chart = plot_linechart()
        return chart.properties(width = 600)


    def prepare_chart_encoding(self,cfg):
        co = self.metadata['table']['chart_options']
        cfg['plot_type'] = self.metadata['table']['chart']
        if "force_options" not in co:
            x = cfg['x']
            y = cfg['y']
            c = cfg['color'] if 'color' in cfg else ''
            x_type = self.metadata['columns'].query("label == @x").iloc[0]['col_type']
            if len(cfg['value_fields'])==1:
                y_type = self.metadata['columns'].query("label == @y").iloc[0]['col_type']
                color_type = self.metadata['columns'].query("label == @c").iloc[0]['col_type']
            else:
                y_type = 'Q'
                color_type = 'N'
            cfg['x_ax'] = alt.X(f"{cfg['x']}:{x_type}")
            cfg['y_ax'] = alt.Y(f"{cfg['y']}:{y_type}")
            cfg['color_ax'] = alt.Color(f"{cfg['color']}:{color_type}") if 'color' in cfg else ''
        else:

            cfg['x_ax'] = alt.X(f"{cfg['x']}")
            cfg['y_ax'] = alt.Y(f"{cfg['y']}")
            if "sort_y" in co:
                cfg['y_ax']['sort']=co['sort_y']
            if "sort_x" in co:
                cfg['x_ax']['sort']=co['sort_x']
            cfg['color_ax'] = alt.Color(f"{cfg['color']}") if 'color' in cfg else ''
        return cfg

    def show_charts(self,cfg):
        if len(cfg['plot_group']) > 0:
            categories = self.get_unique_values(cfg['plot_group'])
            for kat in categories:
                cfg['title'] = kat
                _df = self.data[ self.data[cfg['plot_group']] == kat ]
                if 'color' in cfg:
                    _df = _df.groupby([cfg['x']] + [cfg['color']]).agg('sum').reset_index()   
                cfg['tooltip'] = list(_df.columns)
                cfg = self.prepare_chart_encoding(cfg)
                chart = self.get_chart(_df, cfg)
                st.altair_chart(chart)
        else:
            cfg['tooltip'] = list(self.data.columns)
            cfg = self.prepare_chart_encoding(cfg)
            chart = self.get_chart(self.data, cfg)
            st.altair_chart(chart)

    def show_menu(self):
        cfg = {}
        cfg = self.melt_data(cfg)
        cfg = self.get_columns(cfg)
        cfg = self.prepare_chart_encoding(cfg)
        # st.write((cfg))
        # st.write(self.data)
        self.show_charts(cfg)