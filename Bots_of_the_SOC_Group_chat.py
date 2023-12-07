import autogen
import dotenv
import os
from splunk_functions import splunk_query, get_fields, functions
from system_messages import assistant_system_message, sense_checker_system_message, planner_system_message, assistant_system_message_short
from prompt_functions import load_questions, get_prompt, get_answer

SEED = 40
QUESTIONS = 'Questions.json'

dotenv.load_dotenv(".env")


username=os.getenv('SPLUNK_UN')
password=os.getenv('SPLUNK_PW')


config_list_turbo = autogen.config_list_from_json(
    "OAI_CONFIG_LIST",
    filter_dict={
        "model": [
            "gpt-4-1106-preview",
            ],
    },
)


config_list_4 = autogen.config_list_from_json(
    "OAI_CONFIG_LIST",
    filter_dict={
        "model": [
            "gpt-4",
            # "gpt-4-0314",
            # "gpt4",
            # "gpt-4-32k",
            # "gpt-4-32k-0314",
            # "gpt-4-32k-v0314"
            ],
    },
)



llm_config_turbo={
    "seed": SEED,  # seed for caching and reproducibility
    "config_list": config_list_turbo,  # a list of OpenAI API configuration,
    # "functions": functions
}

llm_config_4={
    "seed": SEED,  # seed for caching and reproducibility
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
    system_message="A proxy capable of executing function calls only."
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
    system_message = assistant_system_message_short,
    llm_config={
        "seed": SEED,  # seed for caching and reproducibility
        "config_list": config_list_turbo,  # a list of OpenAI API configuration
        "functions": functions,
    },  # configuration for autogen's enhanced inference API which is compatible with OpenAI API
)

# pm = autogen.AssistantAgent(
#     name="Planner",
#     system_message = planner_system_message,
#     llm_config=llm_config_turbo
# )


sense_check = autogen.AssistantAgent(
    name="sense_check",
    system_message = sense_checker_system_message,
    llm_config=llm_config_turbo
)


groupchat = autogen.GroupChat(agents=[user_proxy, splunker, sense_check], messages=[], max_round=30)
manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config_turbo)
# 
# prompt = input("Write a prompt:\n")

questions = load_questions(QUESTIONS)

# TODO: Make iterations to work over all questions.

prompt = get_prompt(3, questions)


# the assistant receives a message from the user_proxy, which contains the task description
user_proxy.initiate_chat(
    manager,
    message=prompt,
)


