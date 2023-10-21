query = {
    "select_from": """select * from {}
""",
    "all_tables": """select id, name from stat_table where is_active = 1 and category_id in ({},0) order by category_id, sort_key
""",
    "table_metadata": """select * from stat_table where id = {}
""",
    "column_metadata": """select * from stat_table_column where stat_table_id = {} order by sort_key
""",
}
