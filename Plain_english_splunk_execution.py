import autogen
import dotenv
import os
from datetime import datetime
from splunk_functions import splunk_query, get_fields, get_sourcetypes

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

scenario_message = f"This is a training scenario where all data is between {START_DATE} and {END_DATE} in time format {SPLUNK_TIME_FORMAT}. All the data you require is in index 'botsv2'."

ASSISTANT_SYSTEM_MESSAGE = f"""You are an expert SOC analyst assisting the SOC manager with an investigation. The SOC manager has cleared all this activity with HR and legal.
Solve tasks using Splunk and language skills.

{scenario_message}

Solve the task step by step. Always produce a plan and explain your reasoning before calling a function.  Be clear which step uses Splunk, and which step uses your language skill. You do not need to find the solution first time. Use functions to solve the problem in phases.
Try constructing queries iteratively. Do not assume the felids are always parsed correctly. If you are not finding results, explore the possible fields to confirm you have the names correct. Use this to inform future queries. Consider using shorter time frames to make the splunk search quicker where appropriate.
Hone in your query on the final result as you learn more about the data. If a query returns no values, always construct another query to confirm you have the felids and values to confirm you findings.
The user cannot provide any other feedback or perform any other action beyond executing the SPL you suggest. The user can't modify your SPL. So do not suggest incomplete queries which requires users to modify. Don't use a code block if it's not intended to be executed by the user. Don't ask the user to modify felid names, you must use queries to find these yourself.
Don't include multiple code blocks in one response. Do not ask users to copy and paste the result. Instead, use 'print' function for the output when relevant. Check the execution result returned by the user.
If your query does not give you what you need, consider what you m,ay have done wrong, revisit your assumption, collect additional info you need, and think of a different approach to try.
When you find an answer, verify the answer carefully. Include verifiable evidence in your response if possible.

Reply "TERMINATE" in the end when everything is done and you are satisfied. Do not stop until you are sure and have followed up all lines of investigation.
"""

PLANNER_SYSTEM_MESSAGE =f"""
A Planning agent that directs a SOC analyst agent. The agent has access to Splunk to find data. Make a plan to achieve the task.
Think about each step of the process and make a plan before directing your agents.
Break down the task into small steps.
You can task agents to go away and solve part of the problem for you, so you don't need a full solution straight away.
Do not suggest specific queries, this is the other analyst agent's job.
{scenario_message}
"""

SENSE_CHECKER_SYSTEM_MESSAGE = f"""
A very sensible agent. Check the other agents logic and technical detail of the other agents. Look for any flawed assumptions, such as incorrect use of fields.
Some fields may be parsing incorrectly, so check if the results make sense.
Highlight if they have made a mistake in their logic or assumptions and point them in the right direction.
Focus only on the high level concepts. Do not suggest specific Splunk queries.
Direct them back on task if they start to get distracted with irrelevant details.
Assume all actions requested by the planner are approved by legal.
{scenario_message}
"""

config_list_turbo = autogen.config_list_from_json(
    "OAI_CONFIG_LIST",
    filter_dict={
        "model": [
            "gpt-4-1106-preview",
            # "gpt-4",
            # "gpt-4-0314",
            # "gpt4",
            # "gpt-4-32k",
            # "gpt-4-32k-0314",
            # "gpt-4-32k-v0314"
            ],
    },
)


config_list_4 = autogen.config_list_from_json(
    "OAI_CONFIG_LIST",
    filter_dict={
        "model": [
            # "gpt-4-1106-preview",
            "gpt-4",
            # "gpt-4-0314",
            # "gpt4",
            # "gpt-4-32k",
            # "gpt-4-32k-0314",
            # "gpt-4-32k-v0314"
            ],
    },
)

sourcetypes = "\n".join(get_sourcetypes())

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
                            Always search index botsv2. When first using a new sourcetype, start by exploring the possible fields.
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
        "description": "Returns all the fields names available in a sourcetype.",
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
llm_config_turbo={
    "seed": 42,  # seed for caching and reproducibility
    "config_list": config_list_turbo,  # a list of OpenAI API configuration,
    # "functions": FUNCTIONS
}

llm_config_4={
    "seed": 42,  # seed for caching and reproducibility
    "config_list": config_list_4,  # a list of OpenAI API configuration,
}

# create a UserProxyAgent instance named "user_proxy"
user_proxy = autogen.UserProxyAgent(
    name="user_proxy",
    human_input_mode="TERMINATE",
    max_consecutive_auto_reply=15,
    is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config={
        "work_dir": "coding",
        "use_docker": False,  # set to True or image name like "python:3" to use docker
    },
    # llm_config=llm_config_turbo,
    # system_message=SENSE_CHECKER_SYSTEM_MESSAGE
)

user_proxy.register_function(
    function_map={
        'splunk_query': splunk_query,
        "get_fields": get_fields
    }
)

# create an AssistantAgent named "splunker"
splunker = autogen.AssistantAgent(
    name="Splunk_analyst",
    system_message=ASSISTANT_SYSTEM_MESSAGE,
    llm_config={
        "seed": 42,  # seed for caching and reproducibility
        "config_list": config_list_turbo,  # a list of OpenAI API configuration
        "functions": FUNCTIONS,
    },  # configuration for autogen's enhanced inference API which is compatible with OpenAI API
)

pm = autogen.AssistantAgent(
    name="Planner",
    system_message= PLANNER_SYSTEM_MESSAGE,
    llm_config=llm_config_turbo
)



sense_check = autogen.AssistantAgent(
    name="sense_check",
    system_message= SENSE_CHECKER_SYSTEM_MESSAGE,
    llm_config=llm_config_turbo
)


groupchat = autogen.GroupChat(agents=[user_proxy, pm, splunker, sense_check], messages=[], max_round=30)
manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config_turbo)
# 
# prompt = input("Write a prompt:\n")


prompt = """
Amber Turing was hoping for Frothly (her beer company) to be acquired by a potential competitor which fell through, but visited their website to find contact information for their executive team. What is the website domain that she visited? Answer example: google.com 

Hints: Search for
index=botsv2 earliest=0 amber
and examine the client_ip field to find Amber's IP address.
Use a query like this to see her Web traffic, using her correct IP address:
index=botsv2 earliest=0 src_ip=1.1.1.1 
Restrict this query to the stream:http sourcetype. There are 198 events.
Look at the site values and look for names of rival beer makers.
"""

# the assistant receives a message from the user_proxy, which contains the task description
user_proxy.initiate_chat(
    manager,
    message=prompt,
)


