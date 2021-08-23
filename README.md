# delphi-bs

## Introduction
delphi-bs is a lightweigth information system for statistics related to Basel/Switzerland. It provides fast access to a various relevant datasets published mainly on https://data.bs.ch and https://www.statistik.bs.ch/. The app is intended to be usable on mobile phones and tablets and therefore tries to minimize the clicks to find and visualize the data as tables and plots. You can try the app [here](https://delphi-bs.herokuapp.com/). If you have any comments and suggestions create an issue in this repo or send me a mail (lcalmbach@gmail.com).

## Programming and Framworks
delphi-bs is written in Python and uses the frameworks Streamlit and Altair. All data and metadata is stored in a SQLite database. Data from the OGD portal data.bs.ch is consumed with an API and therefore and simply rearranged and visualized by the app. Data from statistik.bs.ch and other sites does not have this convienient access and a copy of the tables must be stored in the database. These tables must be synced.
All metadata is stored in tables 
- stat_tab: holds all information related to the datasets. Datasets that are kept in the local database have a table_name entry, datasets where data is retrieved via a API call have an entry in the url fields.
- stat_tab_column

## Installation
In order to install the app on your machine.
1. Clone this repo
1. Create a virtual env, e.g. on Windows:
    ```
    > python -m venv .venv
    ```
1. Activate the virtual env:
    ```
    > env\scripts\activate
    ```
1. Install the dependencies 
    ```
    > pip intall -r requirements.txt
    ```
1. Start the app
    ```
    > streamlit run app.py
    ```
1. The app should open in your browser on http://localhost:8501/





