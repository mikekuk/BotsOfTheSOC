import pandas as pd
from splunklib.client import connect
from splunklib.results import ResultsReader
import io
from dotenv import load_dotenv
import os
import json
import logging
from datetime import datetime
import re

# Configure the logging settings
logging.basicConfig(filename='splunk_log', level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')




INDEX = "botsv2"
SPLUNK_HOST="localhost"
SPLUNK_PORT="8089"
MAX_CHAR_RETURN = 10000 # Sets the target max number of chars to return from Splunk for log results. This only effects results that exceed the max row count.
MAX_ROW_RETRUN = 200 # Sets the max number of rows to return from Splunk

load_dotenv(".env")


# To use the function, you must first create a Splunk service connection:
service = connect(
    host=SPLUNK_HOST,
    port="8089",
    username=os.getenv('SPLUNK_UN'),
    password=os.getenv('SPLUNK_PW')
)


# Python helper functions


def splunk_query(query, earliest_time="2017-07-31T20:15:00.000+00:00", latest_time="2017-08-31T18:00:00.000+00:00", dataframe=False, splunk_service=service):
    """
    Execute a Splunk query and return the results as a pandas DataFrame.

    Parameters:
    - splunk_service: The authenticated Splunk service connection.
    - query: The Splunk search query string.
    - earliest_time: The earliest time for the search.
    - latest_time: The latest time for the search.

    Returns:
    - df: pandas DataFrame containing the results of the query.
    """
       # Log the function call with parameters and timestamp
    log_entry = f"Query: {query}, Earliest Time: {earliest_time}, Latest Time: {latest_time}, Dataframe: {dataframe}, Splunk Service: {splunk_service}"
    logging.info(log_entry)

    # Run a one-shot search and return the results as a reader object
    rr = splunk_service.jobs.export(
        f"search {query}",
        earliest_time=earliest_time,
        latest_time=latest_time,
        output_mode="csv"
    )

    # Use a StringIO object to convert byte stream to a string stream
    csv_content = io.StringIO(rr.read().decode('utf-8'))

    try:
        df = pd.read_csv(csv_content)
    except pd.errors.EmptyDataError:
        # Catches empty search results
        return "This search returned no results."
        # Handle the error, for example, by initializing an empty DataFrame or taking some other action
    except Exception as e:
        # This will catch any other exceptions that are raised.
        print(f"An error occurred: {e}")
    
    # Catch very large returns to save tokens
    if len(df) > MAX_ROW_RETRUN:
        summary = df.describe(include='all')
        summary = summary.loc[['unique','top']].to_json()
        rows = 10
        return_sting = f"Your search returned {len(df)} rows. Consider a more refined search. Here is a summary in JSON: \n{summary} and the first {rows} rows:\n {df.loc[:rows].to_string()}"
        while len(return_sting) >= MAX_CHAR_RETURN:
            # print(f"[+] Rows: {rows} - Len: {len(return_sting)}") # Used for debugging
            rows -= 1
            return_sting = f"Your search returned {len(df)} rows. Consider a more refined search. Here is a summary in JSON: \n{summary} and the first {rows} rows:\n {df.loc[:rows].to_string()}"
            if rows == 1:
                break
    else:
        return_sting = df.to_string()


    # Strip excess whitespace to save tokens.
    return_sting = re.sub(r'\s{12,}', ' ', return_sting)
    return_sting = "\n".join([line.rstrip() for line in return_sting.splitlines()])


    if len(return_sting) > MAX_CHAR_RETURN:
        return_sting = f"The search returned a long result. This is truncated to the first {MAX_CHAR_RETURN} characters.\n\n {return_sting[:MAX_CHAR_RETURN]}"


    if dataframe:
        # Create a pandas DataFrame from the CSV content
        return df
    else:
        return return_sting

with open(f"{INDEX}_splunk_field.json", "r") as f:
    raw_json = f.read()

fields_dict= json.loads(raw_json)


def get_sourcetypes():
    return list(fields_dict.keys())

def get_fields(sourcetype):
    return fields_dict[sourcetype]


# AutoGen functions

sourcetypes = "\n".join(get_sourcetypes())

functions = [
    {
        "name": "splunk_query",
        "description": "Use this function to query Splunk spl. Input should be a fully formed spl query. Search iteratively by first exploring the data and available fields. Do not assume all felids are correctly parsed.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": f"""
                            SPL query extracting info to answer the user's question.
                            ALWAYS search index 'botsv2'. When first using a new sourcetype, start by exploring the possible fields.
                            Never use time selectors in the search, instead us the earliest_time and latest_time properties to set search windows.
                            Splunk has the following data sourcetypes available:
                                
                                {sourcetypes}
                            """,
                },
                "earliest_time": {
                    "type": "string",
                    "description": "The earliest time for the search. Input should be in ISO datetime format."
                },
               "latest_time": {
                    "type": "string",
                    "description": "The latest time for the search. Input should be in ISO datetime format."
                } 
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_fields",
        "description": "Returns a json all availble felids in a sourcetype. The output contains the field name and coverage as a percentage, where 1 means all records have the field.",
        "parameters": {
            "type": "object",
            "properties": {
                "sourcetype": {
                    "type": "string",
                    "description": "The name of the sourcetype.",
                },
            },
            "required": ["sourcetype"],
        },
    },
]