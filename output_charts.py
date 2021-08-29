import streamlit as st
import altair as alt

class App:
    def __init__(self, df, metadata):
        self.base_data = df
        self.metadata = metadata


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
            self.data = self.data[ self.data[key].isin(values) ]

        x_cols = get_col_list('x')
        y_cols = get_col_list('y')
        color_cols = get_col_list('g')
        group_cols = get_col_list('g')
        if len(cfg['value_fields']) == 1:
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
            result = self.metadata['columns'].query("col_type == @col_type")
            return list(result['label'])
        
        value_fields = get_col_list('Q')
        if len(value_fields) > 0:
            group_fields = ['Jahr',]
            self.data = self.base_data.melt(id_vars=group_fields, value_vars=value_fields,
                var_name = self.metadata['table']['chart_options']['melt_var_name'], value_name=self.metadata['table']['chart_options']['melt_value_name'])
            cfg['value_fields'] = value_fields
            cfg['group_fields'] = value_fields
        else:
            self.data = self.base_data
            cfg['value_fields'] = []
            cfg['group_fields'] = []
        return cfg


    def get_chart(self,df, cfg):
        """
        plots the data as a line or barchart
        """
        def plot_barchart():
            chart = alt.Chart(df).mark_bar().encode(
                x=cfg['x'],
                y=cfg['y']
            )
            #if 'color' in cfg:
            #    chart.color = cfg['color']
            if 'tooltip' in cfg:
                    chart.tooltip=cfg['tooltip']
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
            #if 'tooltip' in cfg:
            #    chart.
            return chart

        title = cfg['title'] if 'title' in cfg else ''
        if cfg['plot_type'] == 'bar':
            chart = plot_barchart()
        elif cfg['plot_type'] == 'line':
            chart = plot_linechart()
        return chart.properties(width = 600)


    def prepare_chart_encoding(self,cfg):
        cfg['plot_type'] = self.metadata['table']['chart']
        x = cfg['x']
        y = cfg['y']
        c = cfg['color']
        x_type = self.metadata['columns'].query("label == @x").iloc[0]['col_type']
        if len(cfg['value_fields'])==1:
            y_type = self.metadata['columns'].query("label == @y").iloc[0]['col_type']
            color_type = self.metadata['columns'].query("label == @c").iloc[0]['col_type']
        else:
            y_type = 'Q'
            color_type = 'N'
        
        cfg['x_ax'] = alt.X(f"{cfg['x']}:{x_type}")
        cfg['y_ax'] = alt.Y(f"{cfg['y']}:{y_type}")
        cfg['color_ax'] = alt.Color(f"{cfg['color']}:{color_type}")

        return cfg

    def show_charts(self,cfg):
        if len(cfg['plot_group']) > 0:
            categories = self.get_unique_values(cfg['plot_group'])
            for kat in categories:
                cfg['title'] = kat
                _df = self.data[ self.data[cfg['plot_group']] == kat ]
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
        self.show_charts(cfg)

        