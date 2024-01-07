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
MAX_CHAR_RETURN = 50000 # Sets the target max number of chars to return from Splunk for log results. This only effects results that exceed the max row count.
MAX_ROW_RETURN = 200 # Sets the max number of rows to return from Splunk

load_dotenv(".env")


# To use the function, you must first create a Splunk service connection:



# Python helper functions

def get_results_json(query:str, earliest_time:str, latest_time:str, count:int=0) -> list[dict]:
        
        """
        Executes splunk search and returns json.

        Arguments:
        SPL query, start time (format YYYY-MM-DDTHH:MM:SS.mmm+ZZ:ZZ), end time (same format), and the max number of search request to return (0 is all).

        Returns:
        JSON completable List of dicts.
        """


        # Connect to Splunk
        splunk_service = connect(
            host=SPLUNK_HOST,
            port=SPLUNK_PORT,
            username=os.getenv('SPLUNK_UN'),
            password=os.getenv('SPLUNK_PW')
        )

        # Execute the query
        job = splunk_service.jobs.create(query, earliest_time=earliest_time, latest_time=latest_time, exec_mode='blocking', count=count)

        # Wait for the job to complete
        job.refresh()
        while not job.is_done():
            pass

        # Get the results and convert them to JSON
        result_stream = job.results(output_mode='json', count=count)
        _results_json = json.loads(result_stream.read().decode('utf-8'))

        # Cleanup
        job.cancel()

        results_json = _results_json['results']
        return results_json
    

def splunk_query(query: str, earliest_time:str="2017-07-31T20:15:00.000+00:00", latest_time:str="2017-08-31T23:59:59.000+00:00") -> str:

    # Set reduced flag to track if the returned results has been redacted to save tokens.
    reduced = False

    # Append leading search if not present
    if query[:7] != "search ":
        query = "search " + query
  
    try:
        results_json = get_results_json(query, earliest_time, latest_time)
    except Exception as e:
        # General error handling
        return f"An error occurred: {str(e)}"
    
    results_count = len(results_json)
    pipe_count = len(query.split('|'))

    return_string = ""
    empty_results_return_string = "This search returned no results. If this is unexpected, try broadening your search to explore the data."

    # Handel searches with no results and only one pipe
    if results_count == 0 and pipe_count == 1:
        return empty_results_return_string

    # Handel searches with no results and multiple pipes by checking for the last pipe to return any results.
    elif results_count == 0 and pipe_count > 1:
        while results_count == 0 and pipe_count > 1:
            split_query = query.split('|')
            query = '|'.join(split_query[:-1])
            results_json = get_results_json(query, earliest_time, latest_time, count=10)
            results_count = len(results_json)


        if results_count == 0:
            return f"{empty_results_return_string}. The first part of the search '{query}' also returned no results."
        else:
            return_string = f"{empty_results_return_string} The last part of the search to return any results was '{query}'. "

    results_string = json.dumps(results_json)
    results_string_len = len(results_string)

    # Handel results with too many rows.    
    if results_count > MAX_ROW_RETURN:
        reduced == True
        results_json = results_json[:MAX_ROW_RETURN]
        results_string = json.dumps(results_json)
        results_string_len = len(results_string)
    
    
    # Handel long results within row limit.
    if results_string_len > MAX_CHAR_RETURN:
        reduced = True
        while results_string_len > MAX_CHAR_RETURN and len(results_json) > 1:
            results_json = results_json[:-1]
      
    # Update string
    results_string = json.dumps(results_json)

    # Append an explainer if the results have been reduced.
    if reduced:
        reduced_json_count = len(results_json)
        return_string += f"This search returned {results_count} results. Here are the first {reduced_json_count}:\n"
    
    # Add the final results and return.
    return_string += results_string

    return return_string


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
        "description": "Use this function to query Splunk spl. Input should be a fully formed spl query. Search iteratively by first exploring the data and available fields. Do not assume all felids are correctly parsed. All data is in index botsv2",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": f"""
                            SPL query extracting info to answer the user's question.
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
    # {
    #     "name": "get_fields",
    #     "description": "Returns a json all availble felids in a sourcetype. The output contains the field name and coverage as a percentage, where 1 means all records have the field.",
    #     "parameters": {
    #         "type": "object",
    #         "properties": {
    #             "sourcetype": {
    #                 "type": "string",
    #                 "description": "The name of the sourcetype.",
    #             },
    #         },
    #         "required": ["sourcetype"],
    #     },
    # },
]

function_mapping={
    'splunk_query': splunk_query,
    # "get_fields": get_fields
}