import autogen
from openai import OpenAI
import os
import csv
from splunk_functions import splunk_query, get_fields, functions
from system_messages import assistant_system_message, sense_checker_system_message, planner_system_message, assistant_system_message_short
from prompt_functions import load_questions, get_prompts, extract_answer
import dotenv

SEED = 42
QUESTIONS = 'Questions.json'
LOG = 'log.csv'

dotenv.load_dotenv(".env")
key=os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=key)

# username=os.getenv('SPLUNK_UN')
# password=os.getenv('SPLUNK_PW')


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
    human_input_mode="NEVER",
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

# marker = autogen.AssistantAgent(
#     name="marker",
#     system_message = "Evaluate student answers against a textbook answer. Return True of correct and False if incorrect",
#     llm_config=llm_config_turbo
# )



groupchat = autogen.GroupChat(agents=[user_proxy, splunker, sense_check], messages=[], max_round=30)
manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config_turbo)
# 
# prompt = input("Write a prompt:\n")

questions = load_questions(QUESTIONS)

prompts, answers = get_prompts(questions)

for i in range(len(prompts)):

    user_proxy.initiate_chat(
        manager,
        message=prompts[i],
    )

    response = str(extract_answer(splunker.last_message()["content"]))

    string = f"Student answer: {response}, Textbook: {answers[i]}"



    response = client.chat.completions.create(
    model="gpt-4-1106-preview",
    messages=[
        {"role": "system", "content": "Evaluate student answers against a textbook answer. Return True of correct and False if incorrect"},
        {"role": "user", "content": string},
    ]
    )

    result = response.choices[0].message.content

    string_to_append = f"{i}, {result}, {string}"

    # TODO: Add number of tokens and number of messages used.

        # Check if the file exists
    if not os.path.exists(LOG):
        # If the file doesn't exist, create it and write the header row (if needed)
        with open(LOG, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(["index", "result", "answer_given", "answer_correct"])  # Replace with your column names

    # Open the CSV file in append mode
    with open(LOG, 'a', newline='') as csvfile:
        # Create a CSV writer object
        csv_writer = csv.writer(csvfile)
        
        # Append the string as a new row
        csv_writer.writerow([string_to_append])


# if __name__ == "__main__":
#     # the assistant receives a message from the user_proxy, which contains the task description
#     # TODO: Make iterations to work over all questions.
#     # TODO: Make marker.
#     user_proxy.initiate_chat(
#         manager,
#         message=prompts[0],
#     )


