import streamlit as st


class App:
    def __init__(self, df, metadata):
        self.data = df
        self.metadata = metadata

    def get_metadata_text(self, df):
        """
        builds the metadata text consisting of a intro-text and a list of column-descriptions
        """
        table = self.metadata["table"]
        df_columns = self.metadata["columns"]

        column_expression = (
            "<br><br><table><tr><th>Spalte</th><th>Beschreibung</th></tr>"
        )
        for index, row in df_columns.iterrows():
            column_expression += (
                f"<tr><td>{row['label']}</td><td>{row['description']}</td></tr>"
            )
        column_expression += "</table>"
        table_expression = f"**Beschreibung**: {table['description']}<br>**Datenquelle**: {table['data_source']}"
        if len(df_columns[df_columns["label"] == "Jahr"]) > 0:
            min = df["Jahr"].min()
            max = df["Jahr"].max()
            table_expression += f"<br>**Jahre von/bis**: {min} - {max}"
        elif len(df_columns[df_columns["label"] == "Datum"]) > 0:
            min = df["Datum"].min()
            max = df["Datum"].max()
            table_expression += f"<br>**Daten von/bis**: {min} - {max}"
        table_expression += column_expression
        return table_expression

    def show_menu(self):
        table_expression = self.get_metadata_text(self.data)
        st.markdown(table_expression, unsafe_allow_html=True)
