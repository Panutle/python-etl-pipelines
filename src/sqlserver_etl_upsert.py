import os
import pyodbc
import pandas as pd
from sqlalchemy import create_engine
from urllib.parse import quote_plus
from dotenv import load_dotenv

# โหลดค่าจากไฟล์ .env
load_dotenv()

# Global Credentials for SQL Server
SERVER = os.getenv('SQL_SERVER')
DATABASE = os.getenv('SQL_DATABASE')
USERNAME = os.getenv('SQL_USER')
PASSWORD = os.getenv('SQL_PASSWORD')

#Connect to Database
def Connect():
    conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=' + SERVER + ';DATABASE=' + DATABASE + ';UID=' + USERNAME + ';PWD=' + PASSWORD)
    return conn

#Select Name Columns
def Sel_Name_Col(conn, N_Table):
    SQL_COLUMNS = f'''
    select COLUMN_NAME
    from INFORMATION_SCHEMA.COLUMNS
    where TABLE_NAME='{N_Table}'
    '''
    col = conn.cursor().execute(SQL_COLUMNS).fetchall()
    col_ = [i[0] for i in col]
    return col_

#Select Data
def Sel_Data(conn, N_Table):
    SQL_QUERY = f"""
    SELECT *
    FROM [dbo].[{N_Table}]
    """
    data = conn.cursor().execute(SQL_QUERY).fetchall()
    return data

#Create DF
def DF(data, col_):
    aa = {}
    for i in range(len(col_)):
        aa[col_[i]] = [j[i] for j in data]
    df = pd.DataFrame(aa)
    return df

#Transform DF
def DF_2(df):
    df_2 = df.drop([0])
    df_2[' '] = df_2[' '].replace('Delete','Free')
    return df_2

#Export to sql
def Exp_to_sql(df, Name):
    conn_str = quote_plus('DRIVER={ODBC Driver 17 for SQL Server};SERVER=' + SERVER + ';DATABASE=' + DATABASE + ';UID=' + USERNAME + ';PWD=' + PASSWORD)
    engine = create_engine(f'mssql+pyodbc:///?odbc_connect={conn_str}')
    
    df.to_sql(f'{Name}', schema= 'dbo', con= engine, index=False, if_exists='replace')
    print(f'Exported to {Name} Successfully')

#Upsert Data
def Upsert_data(conn, N_Table_Target, N_Table_Source, Col_Condition, col_):
    SQL_QUERY_3 = f'''
    MERGE INTO [dbo].[{N_Table_Target}] AS Target
    USING [dbo].[{N_Table_Source}]	AS Source
    ON Source.{Col_Condition} = Target.{Col_Condition}
    WHEN MATCHED THEN 
        UPDATE SET
        {','.join([f'Target.{i} = Source.{i}' for i in col_])}
    WHEN NOT MATCHED THEN
        INSERT (
            {','.join(col_)}
            ) 
        VALUES (
        {','.join([f'Source.{i}' for i in col_])}
        );
    '''
    conn.cursor().execute(SQL_QUERY_3)
    conn.commit()
    print(f'Upsert from {N_Table_Source} to {N_Table_Target} Successfully')

#Main Func
def main():
    # เปลี่ยนชื่อตัวแปรให้สื่อความหมายชัดเจนขึ้น
    table_target = 'data_test_Q'
    table_upsert = 'data_test_Q_2'
    table_source = ' ' # ชื่อตารางต้นทาง (แก้ไขให้เป็นชื่อตารางจริง)
    col_condition = 'pID'

    conn = Connect()

    col_ = Sel_Name_Col(conn, table_source)
    data = Sel_Data(conn, table_source)

    df = DF(data, col_)
    df_2 = DF_2(df)

    Exp_to_sql(df, table_target)
    Exp_to_sql(df_2, table_upsert)

    Upsert_data(conn, table_upsert, table_target, col_condition, col_)

if __name__ == "__main__":
    main()