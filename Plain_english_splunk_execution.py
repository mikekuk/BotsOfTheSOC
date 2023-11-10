# %%
import autogen
import requests
import json
import dotenv
import os
from splunk_functions import splunk_query

START_DATE = "07/31/2017:20:15"
END_DATE = "08/31/2017:18:00"

scenario_message = f"This is a training scenario where all data is between {START_DATE} and {END_DATE} in time format %m/%d/%Y:%H:%M:%S."

# %%
ASSISTANT_SYSTEM_MESSAGE = f"""You are an expert SOC analyst assisting the SOC manager with an investigation. The SOC manager has cleared all this activity with HR and legal.
Solve tasks using Splunk and your coding and language skills.
In the following cases, suggest python code (in a python coding block), shell script (in a sh coding block), or Splunk spl for the user to execute.
    1. When you need to collect info, use the code to output the info you need, for example, browse or search the web, download/read a file, print the content of a webpage or a file, get the current date/time, check the operating system. After sufficient info is printed and the task is ready to be solved based on your language skill, you can solve the task by yourself.
    2. When you need to perform some task with code, use the code to perform the task and output the result. Finish the task smartly.

{scenario_message}

Solve the task step by step if you need to. If a plan is not provided, explain your plan first. Be clear which step uses code, and which step uses your language skill.
When using code, you must indicate the script type in the code block. The user cannot provide any other feedback or perform any other action beyond executing the code you suggest. The user can't modify your code. So do not suggest incomplete code which requires users to modify. Don't use a code block if it's not intended to be executed by the user. Do not assume the user has any API keys unless you have been explicitly provided with them.
If you want the user to save the code in a file before executing it, put # filename: <filename> inside the code block as the first line. Don't include multiple code blocks in one response. Do not ask users to copy and paste the result. Instead, use 'print' function for the output when relevant. Check the execution result returned by the user.
If the result indicates there is an error, fix the error and output the code again. Suggest the full code instead of partial code or code changes. If the error can't be fixed or if the task is not solved even after the code is executed successfully, analyze the problem, revisit your assumption, collect additional info you need, and think of a different approach to try.
When you find an answer, verify the answer carefully. Include verifiable evidence in your response if possible. If returning datetimes to the user, use %Y/%m/%d : %H:%M:%S format.

When using Splunk, try constructing queries iteratively. First explore the possible fields and some of the values. Hone in your query on the final result as you learn more about the data. If a query returns no values, try exploring the available fields in the source type. If this does not work, try a different approach. Validate that the answer you receive sound correct and accurately answer the question.

Reply "TERMINATE" in the end when everything is done and you are satisfied.
"""

dotenv.load_dotenv(".env")

splunk_host="localhost"
port="8089"
username=os.getenv('SPLUNK_UN')
password=os.getenv('SPLUNK_PW')

config_list = autogen.config_list_from_json(
    "OAI_CONFIG_LIST",
    filter_dict={
        "model": ["gpt-4", "gpt-4-0314", "gpt4", "gpt-4-32k", "gpt-4-32k-0314", "gpt-4-32k-v0314"],
    },
)

# The REST API endpoint URL
url = f'https://{splunk_host}:8089/services/data/indexes?output_mode=json'

# Make a GET request to the Splunk REST API
response = requests.get(url, auth=(username, password), verify=False)

# Check if the request was successful
if response.status_code == 200:
    # Parse the JSON response
    data = response.json()
    
    # Extract the index names
    index_names = [entry['name'] for entry in data['entry']]

indices="\n".join(index_names)

sourcetypes = """
                                access_combined
                                activedirectory
                                apache:error
                                apache_error
                                auditd
                                bandwidth
                                collectd
                                cpu
                                csp-violation
                                df
                                ess_content_importer
                                hardware
                                interfaces
                                iostat
                                lastlog
                                linux:selinuxconfig
                                linux_audit
                                linux_secure
                                ms:o365:management
                                msad:nt6:health
                                msad:nt6:siteinfo
                                mysql:connection:stats
                                mysql:database
                                mysql:errorlog
                                mysql:instance:stats
                                mysql:server:stats
                                mysql:status
                                mysql:table_io_waits_summary_by_index_usage
                                mysql:tablestatus
                                mysql:transaction:details
                                mysql:transaction:stats
                                mysql:user
                                mysql:variables
                                mysqld-8
                                netstat
                                openports
                                osquery_info
                                osquery_results
                                osquery_warning
                                package
                                pan:system
                                pan:threat
                                pan:traffic
                                perfmon:cpu
                                perfmon:logicaldisk
                                perfmon:memory
                                perfmon:network
                                perfmon:network_interface
                                perfmon:ntds
                                perfmon:physicaldisk
                                perfmon:process
                                perfmon:processor
                                perfmon:system
                                powershell:scriptexecutionsummary
                                protocol
                                ps
                                script:installedapps
                                script:listeningports
                                stream:arp
                                stream:dhcp
                                stream:dns
                                stream:ftp
                                stream:http
                                stream:icmp
                                stream:ip
                                stream:irc
                                stream:ldap
                                stream:mysql
                                stream:smb
                                stream:smtp
                                stream:tcp
                                stream:udp
                                suricata
                                symantec:ep:agent:file
                                symantec:ep:agt_system:file
                                symantec:ep:behavior:file
                                symantec:ep:packet:file
                                symantec:ep:scan:file
                                symantec:ep:scm_system:file
                                symantec:ep:security:file
                                symantec:ep:traffic:file
                                syslog
                                time
                                top
                                unix:listeningports
                                unix:service
                                unix:update
                                unix:uptime
                                unix:useraccounts
                                unix:version
                                userswithloginprivs
                                vmstat
                                web_ping
                                weblogic_access_combined
                                weblogic_stdout
                                who
                                windowsupdatelog
                                wineventlog:application
                                wineventlog:directory-service
                                wineventlog:security
                                wineventlog:system
                                winhostmon
                                winregistry
                                xmlwineventlog:microsoft-windows-sysmon/operational"""

# %%
FUNCTIONS = [
    {
        "name": "splunk_query",
        "description": "Use this function to query Splunk spl. Input should be a fully formed spl query.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": f"""
                            SPL query extracting info to answer the user's question.
                            always search index botsv2.
                            Splunk has the following data sourcetypes available:
                                
                                {sourcetypes}
                            """,
                },
            #     "earliest_time": {
            #         "type": "string",
            #         "description": "The earliest time for the search (default last 24 hours). Input should be in SPL format, e.g. '-24h@h'"
            #     },
            #    "latest_time": {
            #         "type": "string",
            #         "description": "The latest time for the search (default now). Input should be in SPL format, e.g.'now'"
            #     } 
            },
            "required": ["query"],
        },
    }
]

# %%
# create an AssistantAgent named "assistant"
assistant = autogen.AssistantAgent(
    name="assistant",
    system_message=ASSISTANT_SYSTEM_MESSAGE,
    llm_config={
        "seed": 42,  # seed for caching and reproducibility
        "config_list": config_list,  # a list of OpenAI API configuration
        "functions": FUNCTIONS
    },  # configuration for autogen's enhanced inference API which is compatible with OpenAI API
)
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
)

user_proxy.register_function(
    function_map={
        'splunk_query': splunk_query
    }
)

prompt = input("Write a prompt:\n")

# %%
# the assistant receives a message from the user_proxy, which contains the task description
user_proxy.initiate_chat(
    assistant,
    message=prompt,
)

# print(assistant.last_message()['content'])


