import pandas as pd
from splunklib.client import connect
from splunklib.results import ResultsReader
import io
from dotenv import load_dotenv
import os
import json


INDEX = "botsv2"

load_dotenv(".env")


# To use the function, you must first create a Splunk service connection:
service = connect(
    host="localhost",
    port="8089",
    username=os.getenv('SPLUNK_UN'),
    password=os.getenv('SPLUNK_PW')
)


def splunk_query(query, earliest_time="2017-07-31T20:15:00.000+00:00", latest_time="2017-08-31T18:00:00.000+00:00", dataframe=False, splunk_service=service):
    """
    Execute a Splunk query and return the results as a pandas DataFrame.

    Parameters:
    - splunk_service: The authenticated Splunk service connection.
    - query: The Splunk search query string.
    - earliest_time: The earliest time for the search (default last 24 hours).
    - latest_time: The latest time for the search (default now).

    Returns:
    - df: pandas DataFrame containing the results of the query.
    """
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
    if len(df) > 100:
        summary = df.describe(include='all')
        summary = summary.loc[['unique','top']].to_json()
        return_sting = f"Your search returned {len(df)} rows. Here is a summary in JSON. You may want to consider a more refined search: {summary}"
        return return_sting

    if dataframe:
        # Create a pandas DataFrame from the CSV content
        return df
    else:
        return df.to_string()

with open(f"{INDEX}_splunk_field.json", "r") as f:
    raw_json = f.read()

fields_dict= json.loads(raw_json)


def get_sourcetypes():
    return list(fields_dict.keys())

def get_fields(sourcetype):
    return fields_dict[sourcetype]