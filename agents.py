import autogen
from splunk_functions import functions, function_mapping
from system_messages import sense_checker_system_message, planner_system_message, assistant_system_message
from config import MODEL, SEED, ROUNDS, TEMPERATURE



config_list = autogen.config_list_from_json(
    "OAI_CONFIG_LIST",
    filter_dict={
        "model": [
            MODEL,
            ],
    },
)


llm_config={
    "seed": SEED,  # seed for caching and reproducibility
    "config_list": config_list,  # a list of OpenAI API configuration,
    "temperature": TEMPERATURE,
    # "functions": functions
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
    system_message=sense_checker_system_message
)

user_proxy.register_function(
    function_map=function_mapping
)

# create an AssistantAgent named "splunker"
splunker = autogen.AssistantAgent(
    name="Splunk_analyst",
    system_message = assistant_system_message,
    llm_config={
        "seed": SEED,  # seed for caching and reproducibility
        "config_list": config_list,  # a list of OpenAI API configuration
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
    llm_config=llm_config
)

chat_agents = [
    user_proxy,
    splunker,
    sense_check
]

groupchat = autogen.GroupChat(agents=chat_agents, messages=[], max_round=ROUNDS)
manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)