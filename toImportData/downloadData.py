import pandas as pd
import mysql.connector
import os
from pathlib import Path

# Define root path
root_dir = Path(__file__).resolve().parent
data_directory = root_dir / "data"
federal_account_directory = root_dir / "data2"

# Database configuration
db_host = "localhost"
db_user = "sujaya"
db_password = "Password0!"
new_db_name = "finaldropna2"

# mySQL connection
db_connection = mysql.connector.connect(
    host=db_host,
    user=db_user,
    password=db_password,
    ssl_disabled=True
)
cursor = db_connection.cursor()

try:
    cursor.execute(f"CREATE DATABASE {new_db_name}")
    print(f"Database {new_db_name} created successfully.")
except mysql.connector.Error as err:
    print(f"Error creating database {new_db_name}: {err}")

# Use the new database
cursor.execute(f"GRANT ALL PRIVILEGES ON {new_db_name}.* TO 'sujaya'@'localhost';")
cursor.execute(f"USE {new_db_name}")

# Define schema
schema = """
CREATE TABLE Agency(
    Agency_Identifier VARCHAR(255) NOT NULL UNIQUE,
    Agency_Name VARCHAR(255) NOT NULL UNIQUE,
    PRIMARY KEY (Agency_Identifier)
);

CREATE TABLE Federal_Account(
    Main_Account_Code VARCHAR(255) NOT NULL UNIQUE,
    Account_Title TEXT,
    Agency_Name VARCHAR(255) NOT NULL,
    PRIMARY KEY (Main_Account_Code)
);

CREATE TABLE Award(
    Prime_Award_ID VARCHAR(255) NOT NULL UNIQUE,
    Obligation_Amount DECIMAL(20,2) NOT NULL,
    Outlayed_Amount DECIMAL(20,2) NOT NULL,
    Primary_Place TEXT NOT NULL,
    Agency_Identifier VARCHAR(255),
    Object_Class TEXT,
    PRIMARY KEY (Prime_Award_ID)
);

CREATE TABLE Recipient(
    Recipient_UEI VARCHAR(255) NOT NULL,
    Recipient_Name TEXT,
    PRIMARY KEY (Recipient_UEI)
);

CREATE TABLE Covid_Related(
    Prime_Award_ID VARCHAR(255) NOT NULL UNIQUE,
    Covid_Obligated_Amount DECIMAL(20,2) NOT NULL,
    Covid_Outlayed_Amount DECIMAL(20,2) NOT NULL,
    PRIMARY KEY (Prime_Award_ID)
);

CREATE TABLE Non_Covid_Related(
    Prime_Award_ID VARCHAR(255) NOT NULL UNIQUE,
    PRIMARY KEY (Prime_Award_ID)
);

CREATE TABLE Award_Uses(
    Main_Account_Code VARCHAR(255) NOT NULL UNIQUE,
    Prime_Award_ID VARCHAR(255) NOT NULL,
    CONSTRAINT PK_Uses PRIMARY KEY (Main_Account_Code, Prime_Award_ID)
);

CREATE TABLE Program_Activity(
    Program_Reporting_Key VARCHAR(255) NOT NULL UNIQUE,
    Program_Name TEXT,
    PRIMARY KEY (Program_Reporting_Key)
);

CREATE TABLE Provides(
    Program_Reporting_Key VARCHAR(255) NOT NULL,
    Prime_Award_ID VARCHAR(255) NOT NULL,
    CONSTRAINT PK_Provides PRIMARY KEY (Program_Reporting_Key, Prime_Award_ID)
);

CREATE TABLE Receives(
    Recipient_UEI VARCHAR(255) NOT NULL,
    Prime_Award_ID VARCHAR(255) NOT NULL,
    CONSTRAINT PK_Receives PRIMARY KEY (Recipient_UEI, Prime_Award_ID)
);

-- @block
-- Adding the foreign keys

ALTER TABLE Federal_Account
ADD FOREIGN KEY (Agency_Name) REFERENCES Agency(Agency_Name);

ALTER TABLE Provides
ADD FOREIGN KEY (Program_Reporting_Key) REFERENCES Program_Activity(Program_Reporting_Key),
ADD FOREIGN KEY (Prime_Award_ID) REFERENCES Award(Prime_Award_ID);

ALTER TABLE Award
ADD FOREIGN KEY (Agency_Identifier) REFERENCES Agency(Agency_Identifier);

ALTER TABLE Covid_Related
ADD FOREIGN KEY (Prime_Award_ID) REFERENCES Award(Prime_Award_ID);

ALTER TABLE Non_Covid_Related
ADD FOREIGN KEY (Prime_Award_ID) REFERENCES Award(Prime_Award_ID);

ALTER TABLE Award_Uses
ADD FOREIGN KEY (Main_Account_Code) REFERENCES Federal_Account(Main_Account_Code),
ADD FOREIGN KEY (Prime_Award_ID) REFERENCES Award(Prime_Award_ID);

ALTER TABLE Receives
ADD FOREIGN KEY (Recipient_UEI) REFERENCES Recipient(Recipient_UEI),
ADD FOREIGN KEY (Prime_Award_ID) REFERENCES Award(Prime_Award_ID);

"""

# Apply schema
try:
    for statement in schema.split(';'):
        if statement.strip():
            cursor.execute(statement)
    print("Schema applied successfully.")
except mysql.connector.Error as err:
    print(f"Error applying schema: {err}")

# Function to insert data with ON DUPLICATE KEY UPDATE
def insert_data(table, data, update_columns):
    placeholders = ', '.join(['%s'] * len(data.columns))
    columns = ', '.join(data.columns)
    update_placeholders = ', '.join([f"{col}=VALUES({col})" for col in update_columns])
    sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {update_placeholders}"
    cursor.executemany(sql, [tuple(row) for row in data.values])  # Limit to 10,000 rows
    #for row in data.values:
    #    print (row)
    #    cursor.execute(sql, tuple(row))
    print(len(data.index))
    db_connection.commit()

#Function specifically for federal_accounts and award_uses to use INSERT IGNORE
def insert_data2(table, data):
    placeholders = ', '.join(['%s'] * len(data.columns))
    columns = ', '.join(data.columns)
    sql = f"INSERT IGNORE INTO {table} ({columns}) VALUES ({placeholders})"
    cursor.executemany(sql, [tuple(row) for row in data.values])  # Limit to 10,000 rows

    print(len(data.index))
    db_connection.commit()

def split_award_object_classes(df):
            rows = []
            for _, row in df.iterrows():
                objects = row['Object_Class'].split(';')
                for object in objects:
                    rows.append({
                        'Prime_Award_ID': row['Prime_Award_ID'],
                        'Obligation_Amount': row['Obligation_Amount'],
                        'Outlayed_Amount': row['Outlayed_Amount'],
                        'Primary_Place': row['Primary_Place'],
                        'Agency_Identifier': row['Agency_Identifier'],
                        'Object_Class': object
                    })
            return pd.DataFrame(rows)

#create list of main account codes
main_account_code_list = []

# Function to process and insert main data files
def process_main_data_file(filename):
    file_path = os.path.join(data_directory, filename)
    
    df = pd.read_csv(file_path, encoding="latin1", skipinitialspace=True, usecols=[
        "object_classes_funding_this_award", "funding_agency_code", "funding_agency_name",
        "recipient_name", "recipient_uei", "federal_accounts_funding_this_award",
        "primary_place_of_performance_state_name", "total_outlayed_amount_for_overall_award",
        "total_dollars_obligated", "award_id_piid",
        "obligated_amount_from_COVID-19_supplementals_for_overall_award",
        "outlayed_amount_from_COVID-19_supplementals_for_overall_award", "program_activities_funding_this_award"
    ])

    # Drop rows where any of the specified columns have null values
    
    df = df.dropna(subset=[
        "object_classes_funding_this_award", "funding_agency_code", "funding_agency_name",
        "recipient_name", "recipient_uei", "federal_accounts_funding_this_award",
        "primary_place_of_performance_state_name", "award_id_piid",
        "program_activities_funding_this_award"
    ])
    
    # Convert amount columns to decimal
    df['total_outlayed_amount_for_overall_award'] = df['total_outlayed_amount_for_overall_award'].astype(float)
    df['total_dollars_obligated'] = df['total_dollars_obligated'].astype(float)
    df['obligated_amount_from_COVID-19_supplementals_for_overall_award'] = df['obligated_amount_from_COVID-19_supplementals_for_overall_award'].astype(float)
    df['outlayed_amount_from_COVID-19_supplementals_for_overall_award'] = df['outlayed_amount_from_COVID-19_supplementals_for_overall_award'].astype(float)

    # Replace null values with 0
    df.fillna({
        'total_outlayed_amount_for_overall_award': 0,
        'total_dollars_obligated': 0,
        'obligated_amount_from_COVID-19_supplementals_for_overall_award': 0,
        'outlayed_amount_from_COVID-19_supplementals_for_overall_award': 0
    }, inplace=True)

    
    # Insert into Agency table
    agency_data = df[['funding_agency_code', 'funding_agency_name']].rename(columns={
        'funding_agency_code': 'Agency_Identifier',
        'funding_agency_name': 'Agency_Name'
    }).drop_duplicates()
    insert_data('Agency', agency_data, update_columns=['Agency_Name'])
    
    # Insert into Award table
    award_data = df[['total_dollars_obligated', 'total_outlayed_amount_for_overall_award',
                     'primary_place_of_performance_state_name', 'funding_agency_code', 'award_id_piid',
                     'object_classes_funding_this_award']].rename(columns={
        'award_id_piid': 'Prime_Award_ID',
        'total_dollars_obligated': 'Obligation_Amount',
        'total_outlayed_amount_for_overall_award': 'Outlayed_Amount',
        'primary_place_of_performance_state_name': 'Primary_Place',
        'funding_agency_code': 'Agency_Identifier',
        'object_classes_funding_this_award': 'Object_Class'
    }).drop_duplicates()
    expanded_award_data = split_award_object_classes(award_data)
    insert_data('Award', expanded_award_data, update_columns=['Obligation_Amount', 'Outlayed_Amount', 'Primary_Place', 'Agency_Identifier', 'Object_Class'])

    # Insert into Recipient table
    recipient_data = df[['recipient_name', 'recipient_uei']].rename(columns={
        'recipient_uei': 'Recipient_UEI',
        'recipient_name': 'Recipient_Name',
    }).drop_duplicates()
    insert_data('Recipient', recipient_data, update_columns=['Recipient_Name'])

    # Insert into Receives table
    receives_data = df[['recipient_uei', 'award_id_piid']].rename(columns={
        'recipient_uei': 'Recipient_UEI',
        'award_id_piid': 'Prime_Award_ID'
    }).drop_duplicates()
    insert_data('Receives', receives_data, update_columns=['Prime_Award_ID'])

    # Insert into Covid_Related table
    covid_related_data = df[df['obligated_amount_from_COVID-19_supplementals_for_overall_award'] > 0][['award_id_piid', 'obligated_amount_from_COVID-19_supplementals_for_overall_award',
                             'outlayed_amount_from_COVID-19_supplementals_for_overall_award']].rename(columns={
        'award_id_piid': 'Prime_Award_ID',
        'obligated_amount_from_COVID-19_supplementals_for_overall_award': 'Covid_Obligated_Amount',
        'outlayed_amount_from_COVID-19_supplementals_for_overall_award': 'Covid_Outlayed_Amount'
    }).drop_duplicates()
    insert_data('Covid_Related', covid_related_data, update_columns=['Covid_Obligated_Amount', 'Covid_Outlayed_Amount'])
    
    # Insert into Non_Covid_Related table
    non_covid_related_data = df[df['obligated_amount_from_COVID-19_supplementals_for_overall_award'] == 0][['award_id_piid']].rename(columns={
        'award_id_piid': 'Prime_Award_ID'
    }).drop_duplicates()
    insert_data('Non_Covid_Related', non_covid_related_data, update_columns=['Prime_Award_ID'])

    # Process Program_Activity data
    program_activity_data = df['program_activities_funding_this_award'].str.split(':', expand=True)
    df['Program_Reporting_Key'] = program_activity_data[0].str.strip()
    df['Program_Name'] = program_activity_data[1].str.strip().str.split(';').str[0] if program_activity_data.shape[1] > 1 else ''

    # Insert data into Program_Activity table
    program_activity_data = df[['Program_Reporting_Key', 'Program_Name']].rename(columns={
        'Program_Reporting_Key': 'Program_Reporting_Key',
        'Program_Name': 'Program_Name'
    }).drop_duplicates()
    insert_data('Program_Activity', program_activity_data, update_columns=['Program_Name'])

    # Insert into Provides table
    provides_data = df[['Program_Reporting_Key', 'award_id_piid']].rename(columns={
        'Program_Reporting_Key': 'Program_Reporting_Key',
        'award_id_piid': 'Prime_Award_ID'
    }).drop_duplicates()
    insert_data('Provides', provides_data, update_columns=['Prime_Award_ID'])


# Function to process and insert federal account data
def process_federal_account_file(filename):
    file_path_fa = os.path.join(federal_account_directory, filename)
    federal_account_df = pd.read_csv(file_path_fa, encoding="latin1", skipinitialspace=True, usecols=[
        "federal_account_symbol", "federal_account_name", "owning_agency_name"
    ])
    
    federal_account_data = federal_account_df.rename(columns={
        "federal_account_symbol": "Main_Account_Code",
        "federal_account_name": "Account_Title",
        "owning_agency_name": "Agency_Name"
    }).drop_duplicates().dropna()
    insert_data2('Federal_Account', federal_account_data)

    global main_account_code_list
    main_account_code_list = federal_account_data["Main_Account_Code"].tolist()

#create special function for award_uses
def split_federal_accounts(df,main_account_code_list):
            rows = []
            for _, row in df.iterrows():
                accounts = row['Main_Account_Code'].split(';')
                for account in accounts:
                    if account in main_account_code_list:
                        rows.append({
                            'Main_Account_Code': account,
                            'Prime_Award_ID': row['Prime_Award_ID']
                        })
            return pd.DataFrame(rows)


def process_main_data_file_award_uses(filename,main_account_code_list):
    
    file_path = os.path.join(data_directory, filename)
    
    df = pd.read_csv(file_path, encoding="latin1", skipinitialspace=True, usecols=[
        "federal_accounts_funding_this_award", "award_id_piid",
    ]).dropna()

    award_uses_data = df[['federal_accounts_funding_this_award', 'award_id_piid']].rename(columns={
    'federal_accounts_funding_this_award': 'Main_Account_Code',
    'award_id_piid': 'Prime_Award_ID'
    }).drop_duplicates()

    expanded_award_uses_data = split_federal_accounts(award_uses_data,main_account_code_list)
    insert_data2('Award_Uses', expanded_award_uses_data)


# Process each CSV file in the main data directory
for filename in os.listdir(data_directory):
    if filename.endswith(".csv"):
        print(filename)
        process_main_data_file(filename)

# Process each CSV file in the federal account directory
for filename in os.listdir(federal_account_directory):
    if filename.endswith(".csv"):
        print(filename)
        process_federal_account_file(filename)


for filename in os.listdir(data_directory):
    if filename.endswith(".csv"):
        print(filename)
        process_main_data_file_award_uses(filename,main_account_code_list)


cursor.close()
db_connection.close()
print("All data loaded successfully into the database.")
