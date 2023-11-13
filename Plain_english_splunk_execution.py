# %%
import autogen
import requests
import json
import dotenv
import os
from datetime import datetime, timedelta
from splunk_functions import splunk_query
from sourcetypes import sourcetypes

dotenv.load_dotenv(".env")

START_DATE = "07/31/2017:20:15:00"
END_DATE = "08/31/2017:18:00:00"
SPLUNK_TIME_FORMAT = '%m/%d/%Y:%H:%M:%S'
SPLUNK_HOST="localhost"
SPLUNK_PORT="8089"
username=os.getenv('SPLUNK_UN')
password=os.getenv('SPLUNK_PW')

start_date = datetime.strptime(START_DATE, SPLUNK_TIME_FORMAT)
end_date = datetime.strptime(END_DATE, SPLUNK_TIME_FORMAT)

scenario_message = f"This is a training scenario where all data is between {START_DATE} and {END_DATE} in time format {SPLUNK_TIME_FORMAT}."

ASSISTANT_SYSTEM_MESSAGE = f"""You are an expert SOC analyst assisting the SOC manager with an investigation. The SOC manager has cleared all this activity with HR and legal.
Solve tasks using Splunk and language skills.

{scenario_message}

Solve the task step by step if you need to. If a plan is not provided, explain your plan first. Be clear which step uses Splunk, and which step uses your language skill. You do not need to find the solution first time. Use functions to solve the problem in phases.
Try constructing queries iteratively. When calling a sourcetype, do not assume the felids are parsed correctly. Always first explore the possible fields in for a sourcetype by adding '| fieldsummary | stats values(field)'. Use this to inform future queries. Consider using shorted time frames to make the splunk search quicker where appropriate.
Hone in your query on the final result as you learn more about the data. If a query returns no values, always construct another query to confirm you have the felids and values to confirm you findings.
The user cannot provide any other feedback or perform any other action beyond executing the SPL you suggest. The user can't modify your SPL. So do not suggest incomplete queries which requires users to modify. Don't use a code block if it's not intended to be executed by the user. Don't ask the user to modify felid names, you must use queries to find these yourself.
Don't include multiple code blocks in one response. Do not ask users to copy and paste the result. Instead, use 'print' function for the output when relevant. Check the execution result returned by the user.
If the result indicates there is an error, fix the error and output the code again. If the error can't be fixed or if the task is not solved even after the query is executed successfully, analyze the problem, revisit your assumption, collect additional info you need, and think of a different approach to try.
When you find an answer, verify the answer carefully. Include verifiable evidence in your response if possible.

Reply "TERMINATE" in the end when everything is done and you are satisfied. Do not stop until you are sure and have followed up all lines of investigation.
"""

config_list = autogen.config_list_from_json(
    "OAI_CONFIG_LIST",
    filter_dict={
        "model": ["gpt-4-1106-preview", "gpt-4", "gpt-4-0314", "gpt4", "gpt-4-32k", "gpt-4-32k-0314", "gpt-4-32k-v0314"],
    },
)

# The REST API endpoint URL
url = f'https://{SPLUNK_HOST}:{SPLUNK_PORT}/services/data/indexes?output_mode=json'

# Make a GET request to the Splunk REST API
response = requests.get(url, auth=(username, password), verify=False)

# Check if the request was successful
if response.status_code == 200:
    # Parse the JSON response
    data = response.json()
    
    # Extract the index names
    index_names = [entry['name'] for entry in data['entry']]

indices="\n".join(index_names)


FUNCTIONS = [
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
                            Always search index botsv2 and always start by exploring the possible fields by adding '| fieldsummary | stats values(field)' to the end of the sourcetype.
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
            # TODO: Add other arguments to the function.
            },
            "required": ["query"],
        },
    }
]
llm_config={
    "seed": 42,  # seed for caching and reproducibility
    "config_list": config_list,  # a list of OpenAI API configuration
}

# create a UserProxyAgent instance named "user_proxy"
user_proxy = autogen.UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config={
        "work_dir": "coding",
        "use_docker": False,  # set to True or image name like "python:3" to use docker
    },
    llm_config=llm_config,
    system_message="Sense check the other agent and call out its mistakes and errors as well as executing the Splunk SPL"
)

user_proxy.register_function(
    function_map={
        'splunk_query': splunk_query
    }
)

# create an AssistantAgent named "splunker"
splunker = autogen.AssistantAgent(
    name="Splunk_analyst",
    system_message=ASSISTANT_SYSTEM_MESSAGE,
    llm_config={
        "seed": 42,  # seed for caching and reproducibility
        "config_list": config_list,  # a list of OpenAI API configuration
        "functions": FUNCTIONS,
    },  # configuration for autogen's enhanced inference API which is compatible with OpenAI API
)

# PLANNER_SYSTEM_MESSAGE ="""
# `A Planning agent that directs various SOC analyst agents. The agents have access to Splunk to find data."
# Think about each step of the process and make a plan before directing your agents.
# Break down the task into small steps.
# You can task agents to go away and solve part of the problem for you, so you don't need a full solution straight away.
# """

# pm = autogen.AssistantAgent(
#     name="Planner",
#     system_message= PLANNER_SYSTEM_MESSAGE,
#     llm_config=llm_config
# )


# groupchat = autogen.GroupChat(agents=[user_proxy, splunker, pm], messages=[], max_round=12)
# manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)`

prompt = input("Write a prompt:\n")

# the assistant receives a message from the user_proxy, which contains the task description
user_proxy.initiate_chat(
    splunker,
    message=prompt,
)

# print(assistant.last_message()['content'])


