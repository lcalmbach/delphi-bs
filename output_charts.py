import streamlit as st
import altair as alt
import pandas as pd


class App:
    def __init__(self, df, metadata):
        self.base_data = df
        self.metadata = metadata
        self.has_filter = self.filter = self.metadata["table"]["has_filter_chart"]
        self.filter = self.metadata["table"]["filter_chart"]

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
            result = self.metadata["columns"].query("chart_field_type == @col_type")

            return list(result["label"])

        def filter_data(key, values):
            if type(values) == list:
                self.data = self.data[self.data[key].isin(values)]
            else:
                self.data = self.data[self.data[key] == values]

        def get_filter_item(filter):
            if filter["type"] == 4:
                result = st.text_input(filter["label"])
            elif filter["type"] == 5:
                result = st.number_input(
                    filter["label"],
                    min_value=filter["min"],
                    max_value=filter["max"],
                    value=filter["default"],
                )
            elif filter["type"] == 6:
                lookup_list = self.get_unique_values(filter["field"])
                result = st.selectbox(filter["label"], options=lookup_list)
            elif filter["type"] == 7:
                lookup_list = self.get_unique_values(filter["field"])
                result = st.multiselect(filter["label"], options=lookup_list)
                result = [i.replace("'", "''") for i in result]
            elif filter["type"] == 8:
                result = st.select_slider(filter["label"])
            return result

        # if self.metadata['table']['chart_options']:
        if self.metadata["table"]["chart_options"]["force_options"]:
            ts = self.metadata["table"]["chart_options"]
            cfg["x"] = ts["x"]
            cfg["y"] = ts["y"]
            cfg["color"] = ts["color"] if "color" in ts else ""
            cfg["plot_group"] = ""
            if "plot_group" in ts:
                cfg["plot_group"] = ts["plot_group"]
            if self.has_filter:
                # if a filter has been defined:
                for filter in self.filter:
                    filter["value"] = get_filter_item(filter)
                    if len(filter["value"]) > 0:
                        filter_data(filter["field"], filter["value"])
        elif len(cfg["value_fields"]) == 1:
            cfg["plot_group"] = []
            x_cols = get_col_list("x")
            y_cols = get_col_list("y")
            color_cols = get_col_list("g")
            group_cols = get_col_list("g")
            col1, col2 = st.columns(2)
            cfg["x"] = col1.selectbox("X-Achse", x_cols)
            cfg["y"] = col2.selectbox("Y-Achse", y_cols)
            cfg["color"] = (
                col1.selectbox("Legende", color_cols) if len(color_cols) > 0 else ""
            )

            if cfg["color"] in group_cols:
                group_cols.remove(cfg["color"])
            if len(group_cols) > 0:
                cfg["plot_group"] = col2.selectbox(
                    "Gruppiere Grafiken nach:", group_cols
                )

            lst_color_items = (
                self.get_unique_values(cfg["color"]) if len(cfg["color"]) > 0 else []
            )

            if len(group_cols) > 0:
                lst_group_items = self.get_unique_values(cfg["plot_group"])

            if len(lst_color_items) > 0:
                cfg["color_filter"] = col1.multiselect(
                    f"Filter {cfg['color']}", lst_color_items
                )
                if len(cfg["color_filter"]) > 0:
                    filter_data(cfg["color"], cfg["color_filter"])

            if len(group_cols) > 0:
                cfg["group_filter"] = col2.multiselect(
                    f"Filter {cfg['plot_group']}", lst_group_items
                )
                if len(cfg["group_filter"]) > 0:
                    filter_data(cfg["plot_group"], cfg["group_filter"])
        else:
            x_cols = get_col_list("x")
            cfg["x"] = x_cols[0]
            cfg["color_filter"] = ""
            cfg["plot_group"] = []
            cfg["y"] = self.metadata["table"]["chart_options"]["melt_value_name"]
            cfg["color"] = self.metadata["table"]["chart_options"]["melt_var_name"]
            lst_color_items = self.get_unique_values(cfg["color"])
            cfg["color_filter"] = st.multiselect(
                f"Filter {cfg['color']}", lst_color_items
            )
            if len(cfg["color_filter"]) > 0:
                filter_data(cfg["color"], cfg["color_filter"])
        return cfg

    def melt_data(self, cfg):
        def get_col_list(tp):
            col_type = tp
            df = self.metadata["columns"]
            result = df.query("col_type.isin(@col_type)")

            return list(result["label"])

        def replace_value_fields():
            """if a dataset is melted for charting purpose, the columns are changed: n quantiative fields are melted to a variable and a value field.
            thes must be reflected in the columns metadata.
            """
            col_type = ["O", "N", "T"]
            df = self.metadata["columns"]
            df = df.query("col_type.isin(@col_type)")
            tab_id = df.iloc[0]["stat_table_id"]
            val_col = {
                "id": -1,
                "stat_table_id": tab_id,
                "name": self.metadata["table"]["chart_options"]["melt_value_name"],
                "label": self.metadata["table"]["chart_options"]["melt_value_name"],
                "sort_key": 100,
                "description": "",
                "col_type": "Q",
                "data_type": "float64",
                "chart_field_type": "y",
                "stat_func": "sum",
                "column_format": {},
            }
            val_col = pd.DataFrame([val_col])
            df = pd.concat([df, val_col], ignore_index=True)
            var_col = {
                "id": -2,
                "stat_table_id": tab_id,
                "name": self.metadata["table"]["chart_options"]["melt_value_name"],
                "label": self.metadata["table"]["chart_options"]["melt_var_name"],
                "sort_key": 100,
                "description": "",
                "col_type": "N",
                "data_type": "string",
                "chart_field_type": "g",
                "stat_func": None,
                "column_format": {},
            }
            var_col = pd.DataFrame([var_col])
            df = pd.concat([df, var_col], ignore_index=True)
            return df

        cfg["value_fields"] = get_col_list(["Q"])
        if len(cfg["value_fields"]) > 1:
            cfg["group_fields"] = get_col_list(["N", "O", "T"])
            self.data = self.base_data.melt(
                id_vars=cfg["group_fields"],
                value_vars=cfg["value_fields"],
                var_name=self.metadata["table"]["chart_options"]["melt_var_name"],
                value_name=self.metadata["table"]["chart_options"]["melt_value_name"],
            )
            self.metadata["columns"] = replace_value_fields()
            # regenenerate the qunatitative and group columns since this has changed.
            cfg["value_fields"] = get_col_list(["Q"])
            cfg["group_fields"] = get_col_list(["N", "O"])
        else:
            self.data = self.base_data
            cfg["group_fields"] = []
        return cfg

    def get_chart(self, df, cfg):
        """
        plots the data as a line or barchart
        """

        def plot_barchart():
            chart = (
                alt.Chart(df, title=title)
                .mark_bar()
                .encode(x=cfg["x_ax"], y=cfg["y_ax"], tooltip=cfg["tooltip"])
            )

            return chart

        def plot_linechart():
            if "color" in cfg:
                chart = (
                    alt.Chart(df, title=title)
                    .mark_line()
                    .encode(
                        x=cfg["x_ax"],
                        y=cfg["y_ax"],
                        color=cfg["color_ax"],
                        tooltip=cfg["tooltip"],
                    )
                )
            else:
                chart = (
                    alt.Chart(df)
                    .mark_line()
                    .encode(x=cfg["x_ax"], y=cfg["y_ax"], tooltip=cfg["tooltip"])
                )
            return chart

        title = cfg["title"] if "title" in cfg else ""
        if cfg["plot_type"] == "bar":
            chart = plot_barchart()
        elif cfg["plot_type"] == "line":
            chart = plot_linechart()
        return chart.properties(width=600)

    def prepare_chart_encoding(self, cfg):
        co = self.metadata["table"]["chart_options"]
        cfg["plot_type"] = self.metadata["table"]["chart"]
        if not co["force_options"]:
            x = cfg["x"]
            y = cfg["y"]
            c = cfg["color"] if "color" in cfg else ""
            x_type = self.metadata["columns"].query("label == @x").iloc[0]["col_type"]
            if len(cfg["value_fields"]) == 1:
                y_type = (
                    self.metadata["columns"].query("label == @y").iloc[0]["col_type"]
                )
                if c > "":
                    color_type = (
                        self.metadata["columns"]
                        .query("label == @c")
                        .iloc[0]["col_type"]
                    )
            else:
                y_type = "Q"
                color_type = "N"
            cfg["x_ax"] = alt.X(f"{cfg['x']}:{x_type}")
            cfg["y_ax"] = alt.Y(f"{cfg['y']}:{y_type}")
            cfg["color_ax"] = (
                alt.Color(f"{cfg['color']}:{color_type}") if cfg["color"] > "" else ""
            )
        else:
            cfg["x_ax"] = alt.X(f"{cfg['x']}")
            cfg["y_ax"] = alt.Y(f"{cfg['y']}")
            if cfg["color"] > "":
                cfg["color_ax"] = alt.Color(f"{cfg['color']}")
        if "sort_y" in co:
            cfg["y_ax"]["sort"] = co["sort_y"]
        if "sort_x" in co:
            cfg["x_ax"]["sort"] = co["sort_x"]
        if "x_axis_tick_freq" in co:
            min_x = self.data[cfg["x"]].min()
            max_x = self.data[cfg["x"]].max()
            step_x = co["x_axis_tick_freq"]
            axis = alt.Axis(values=list(range(min_x, max_x, step_x)))
            cfg["x_ax"]["axis"] = axis
        if "y_axis_tick_freq" in co:
            min_x = self.data[cfg["y"]].min()
            max_x = self.data[cfg["y"]].max()
            step_x = co["y_axis_tick_freq"]
            axis = alt.Axis(values=list(range(min_x, max_x, step_x)))
            cfg["y_ax"]["axis"] = axis
        cfg["color_ax"] = alt.Color(f"{cfg['color']}") if "color" in cfg else ""
        return cfg

    def show_charts(self, cfg):
        if len(cfg["plot_group"]) > 0:
            categories = self.get_unique_values(cfg["plot_group"])
            for kat in categories[:20]:
                cfg["title"] = str(kat)
                _df = self.data[self.data[cfg["plot_group"]] == kat]

                if ("color" in cfg) & (
                    self.metadata["table"]["chart_options"]["force_options"] == False
                ):
                    _df = (
                        _df.groupby([cfg["x"]] + [cfg["color"]])
                        .agg("sum")
                        .reset_index()
                    )
                cfg["tooltip"] = list(_df.columns)
                cfg = self.prepare_chart_encoding(cfg)
                chart = self.get_chart(_df, cfg)
                st.altair_chart(chart)
            if len(categories) > 20:
                st.info(
                    f"Es werden nur die ersten 20 Kategorien angezeigt. Es gibt insgesamt {len(categories)} Kategorien. Verwende die Filter um die Anzahl zu reduzieren."
                )
        else:
            cfg["tooltip"] = list(self.data.columns)
            cfg = self.prepare_chart_encoding(cfg)
            chart = self.get_chart(self.data, cfg)
            st.altair_chart(chart)

    def show_menu(self):
        cfg = {}
        cfg = self.melt_data(cfg)
        cfg = self.get_columns(cfg)
        cfg = self.prepare_chart_encoding(cfg)
        self.show_charts(cfg)
