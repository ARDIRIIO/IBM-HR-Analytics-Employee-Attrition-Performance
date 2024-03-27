'''
=================================================
Milestone 3

Nama  : Rio Ardiarta Makhiyyuddin
Batch : FTDS-003-SBY

Program ini dibuat untuk melakukan automatisasi transform dan load data dari PostgreSQL ke ElasticSearch. Adapun dataset yang dipakai adalah dataset mengenai penjualan mobil di Indonesia selama tahun 2020.

Dataset : https://www.kaggle.com/datasets/pavansubhasht/ibm-hr-analytics-attrition-dataset

docker-compose -f airflow.yaml up -d
=================================================
'''

# Import Libraries
from airflow.models import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from sqlalchemy import create_engine
import pandas as pd
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

def load_csv_to_postgres():
    '''
    membuat csv raw menjadi tabel di posgresql menggunakan sql alchemy
    '''
    # Tidak bisa membuat server baru seperti airflow
    database = "postgres"
    username = "postgres"
    password = "postgres"
    host = "localhost"

    # Membuat URL koneksi PostgreSQL
    postgres_url = f"postgresql+psycopg2://{username}:{password}@{host}/{database}"

    # Gunakan URL ini saat membuat koneksi SQLAlchemy
    engin = create_engine(postgres_url)
    conn = engin.connect()

    df = pd.read_csv('C:/Users/lenovo/Documents/HACKTIV8/PHASE 2/EXAM/MILESTONE 3/P2M3_rio_ardiarta_data_raw.csv')
    # Using if_exists='replace' to have the table replaced if it already exists
    df.to_sql('table_m3', conn, index=False, if_exists='replace') 

def data_fetch():
    # fetch data
    '''
    mengambil dataset melalui tabel postgresql > menjadi dataframe > dikembalikan menjadi csv data baru
    '''

    engine = create_engine("postgresql+pyscopg2://postgres@postgres/postgres")
    conn = engine.connect()

    df = pd.read_csv("select * from table_m3", conn)
    df.to_csv('C:/Users/lenovo/Documents/HACKTIV8/PHASE 2/EXAM/MILESTONE 3/P2M3_rio_ardiarta_data_new.csv', sep=',', index=False)

def preprocessing():
    data = pd.read_csv('C:/Users/lenovo/Documents/HACKTIV8/PHASE 2/EXAM/MILESTONE 3/P2M3_rio_ardiarta_data_new.csv')

    # Drop specific columns
    columns_to_drop = ['EmployeeCount', 'Over18', 'DailyRate', 'HourlyRate', 'MonthlyRate',
                       'StandardHours', 'StockOptionLevel'] # Replace column with the names of the columns you want to drop
    data.drop(columns=columns_to_drop, inplace=True)

    # Clean Data
    data.dropna(inplace=True)
    data.drop_duplicates(inplace=True)

    # Change all column names to lowercase
    data.columns = data.columns.str.lower()

    # Save the cleaned data to a new csv file
    data.to_csv('C:/Users/lenovo/Documents/HACKTIV8/PHASE 2/EXAM/MILESTONE 3/P2M3_rio_ardiarta_data_clean.csv', index=False)

def upload_to_elasticsearch():
    '''
    Upload cleaned data to elasticsearch in bulk for later visualization in kibana.
    '''
    es = Elasticsearch("http://ealsticsearch:9200")
    df = pd.read_csv('C:/Users/lenovo/Documents/HACKTIV8/PHASE 2/EXAM/MILESTONE 3/P2M3_rio_ardiarta_data_clean.csv')
    
    # Persiapkan data untuk index
    actions = [
        {"_op_type": "index", "_index": "table_m3", "_id": i+1, "_source": doc.to_dict()}
        for i, doc in df.iterrows()
    ]

    # Gunakan bulk index untuk mengirimkan data
    success, failed = bulk(es, actions=actions, index="table_m3")

    print(f"Successfully indexed: {success}")

default_args = {
    'owner': 'Ardi',
    'start_date': datetime(2024, 3, 25, 12, 00) - timedelta(hours=7)
    }

with DAG(
    "P2M3_rio_ardiarta_DAG",
    description='Milestone_3',
    schedule_interval='15 9 * * *', # Triggered at 9:15AM
    default_args=default_args,
    catchup=False) as dag:

    # Task 1
    load_csv_task = PythonOperator(
            task_id='load_csv_to_postgres',
            python_callable=load_csv_to_postgres)
    
    # Task 2
    fetching_data = PythonOperator(
            task_id='fetching_data',
            python_callaable=data_fetch)
    
    # Task 3
    edit_data = PythonOperator(
            task_id='edit_data',
            python_callable=preprocessing)
    
    # Task 4
    upload_data = PythonOperator(
            task_id='upload_data_elastic',
            python_callable=upload_to_elasticsearch)

    # proses task airflow
    load_csv_task >> fetching_data >> edit_data >> upload_data
