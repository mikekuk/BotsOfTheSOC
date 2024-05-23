from splunklib.client import connect
from splunklib.results import ResultsReader
from dotenv import load_dotenv
import json
import logging
from datetime import datetime
import re
import os
from ai_functions import summarize_data, get_response
from config import INDEX, SPLUNK_HOST, SPLUNK_PORT, MAX_CHAR_RETURN, MAX_ROW_RETURN, START_DATE, END_DATE

# Configure the logging settings
logging.basicConfig(filename='splunk_log', level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

load_dotenv(".env")

start_date_obj = datetime.strptime(START_DATE, "%m/%d/%Y:%H:%M:%S")
iso_start_date = start_date_obj.isoformat()

end_date_obj = datetime.strptime(END_DATE, "%m/%d/%Y:%H:%M:%S")
iso_end_date = end_date_obj.isoformat()

splunk_base_commands = "splunk_commands.json"

# Python helper functions

def debug_query(query: str, error_msg: str) -> str:
    """
    Calls GPT-4 to try and debug an error.
    """
    prompt = f"I am trying the following Splunk query via a python function calling the API: {query}\nI get this error: {error_msg}\nJust explain the error in the query and suggest a fix. I cannot edit the python code."
    response = get_response("A helpful AI assistant", prompt)
    return response

def get_results_json(query:str, earliest_time:str = iso_start_date, latest_time:str = iso_end_date, count:int=0) -> list[dict]:
        
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
            username='admin' # For free license. Comment out, and uncomment the below two line if using the enterprise license.
            # username=os.getenv('SPLUNK_UN'),
            # password=os.getenv('SPLUNK_PW')
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

        results_json = _results_json
        return results_json

def splunk_query(query: str, earliest_time:str=iso_start_date, latest_time:str=iso_end_date, question:str="") -> str:

    # Handel know errors in data:
    if "sourcetype=stream:smtp" in query:
        return "Remember there is a known error with stream:smtp. Use macro `smtp` instead."
    if ("earliest" in query) or ("latest" in query):
        return "Use earliest_time and latest_time arguments in the function, rather than inserting tme into the SPL."


    # Set reduced flag to track if the returned results has been redacted to save tokens.
    reduced = False

    # Append leading search if not present
    if query[:7] not in ["search ", "tstats"]:
        query = f'search {query}'
  
    try:
        response_json = get_results_json(query, earliest_time, latest_time)
        results_json = response_json["results"]

    except Exception as e:
        # General error handling
        error_msg = str(e)
        return f"The query returned an error: {error_msg}.\n {debug_query(query, error_msg)}"
    

    if len(response_json["results"]) > 0:
        fields_str = "The search contained the following fields:\n" + "\n ".join([x['name'] for x in response_json["fields"]]) + "\n\nAnd following results:\n"
    else:
        fields_str = "No fields found"

    results_count = len(results_json)

    split_query = query.split('|')
    pipe_count = len(split_query)

    return_string = ""
    empty_results_return_string = "This search returned no results. If this is unexpected, try broadening your search or use 'fieldsummary | table field' to confirm the correct field names."

    # Handel searches with no results and only one pipe
    if results_count == 0 and pipe_count == 1:
        return empty_results_return_string

    # Handel searches with no results and multiple pipes by checking for the last pipe to return any results.
    elif results_count == 0 and pipe_count > 1:
        while results_count == 0 and pipe_count > 1:
            query = '|'.join(split_query[:-1])
            split_query = query.split('|')
            pipe_count = len(split_query)
            response_json = get_results_json(query, earliest_time, latest_time, count=50)
            results_json = response_json['results']
            if 'fields' in response_json.keys():
                fields_str = "This search contained following fields: " + "\n".join([x['name'] for x in response_json["fields"]]) + "\n" + "\n\nAnd following results:\n"
            else:
                fields_str = "No fields found\n"
            results_count = len(results_json)

        if results_count == 0:
            return f"{empty_results_return_string} The first part of the search '{query}' also returned no results."
        else:
            reduced = True
            return_string = f"{empty_results_return_string} The last part of the search to return any results was '{query}'. "

    results_string = json.dumps(results_json)
    results_string_len = len(results_string)

    # Handel results with too many rows.    
    if results_count > MAX_ROW_RETURN:
        reduced = True
        results_json = results_json[:MAX_ROW_RETURN]
        results_string = json.dumps(results_json)
        results_string_len = len(results_string)
    
    # Handel long results within row limit.
    if results_string_len > MAX_CHAR_RETURN * 2:
        reduced = True
        while results_string_len > (MAX_CHAR_RETURN * 2) and len(results_json) > 1:
            results_json = results_json[:-1]
            results_string = json.dumps(results_json)
            results_string_len = len(results_string)
            
      
    # Update string
    results_string = json.dumps(results_string)

    # Handel long responses with GPT4 summarization
    if len(results_string) > MAX_CHAR_RETURN:
        _results_string = f"This search returned over {MAX_CHAR_RETURN} characters long. It has been summarized below:\n"
        results_string = _results_string + summarize_data(results_string, question=question)

    # # Append an explainer if the results have been reduced.
    if reduced:
        reduced_json_count = len(results_json)
        return_string += f"This search returned {results_count} results. \nConsider a more refined search. Here are the fields and first {reduced_json_count} results:\n"
    
    # Add the final results and return.
    # return_string += fields_str
    return_string += results_string
    return return_string


with open(f"{INDEX}_splunk_field.json", "r") as f:
    raw_json = f.read()

fields_dict= json.loads(raw_json)

def get_sourcetypes() -> list[str]:
    return list(fields_dict.keys())

def get_fields(sourcetype) -> dict:
    return fields_dict[sourcetype]

with open(splunk_base_commands, "r") as f:
    commands = f.read()
    commands = json.loads(commands)

def list_commands() -> list[str]:
    """
    Lists all the base Splunk commands by name.

    Returns a list of command names as strings
    """
    return [item["Command"] for item in commands] 

def describe_command(command_name:str):
    """
    Describes a command.

    Inputs the command name.

    Returns a JSON dict of with details and an example.
    """
    for command in commands:
        if command["Command"] == command_name:
            return command
    return "Command not found"

# AutoGen functions

sourcetypes = "\n".join(get_sourcetypes())

functions = [
    {
        "name": "splunk_query",
        "description": f"Use this function to query Splunk spl. Input should be a fully formed spl query. Search iteratively by first exploring the data and available fields. Do not assume all felids are correctly parsed. All data is in index {INDEX}",
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
                },
                "question": {
                    "type": "string",
                    "description": "The original question given to be answered. This will provide context when summering long responses."
                } 
            },
            "required": ["query"],
        },
    },
    # {
    #     "name": "get_fields",
    #     "description": "Returns a json all available felids in a sourcetype. The output contains the field name and coverage as a percentage, where 1 means all records have the field.",
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
    {
        "name": "list_commands",
        "description": "Lists all the available Splunk base commands.",
        "parameters":{
            "type": "object",
            "properties": {},
            "required": []
        },
    },
    {
        "name": "describe_command",
        "description": "Provides details and an example for a given command by name.",
        "parameters":{
            "type": "object",
            "properties": {
                "command_name": {
                    "type": "string",
                    "description": "The name of the command."
                },
            },
            "required": ["command_name"]
        }
    }
]

function_mapping={
    "splunk_query": splunk_query,
    # "get_fields": get_fields,
    "list_commands": list_commands,
    "describe_command": describe_command
}