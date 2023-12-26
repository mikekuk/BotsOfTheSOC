import autogen
from autogen.token_count_utils import count_token
from openai import OpenAI
import json
import os
import csv
from splunk_functions import splunk_query, get_fields, functions
from system_messages import assistant_system_message, sense_checker_system_message, planner_system_message, assistant_system_message_short
from prompt_functions import load_questions, get_prompts, extract_answer
import dotenv

SEED = 0
QUESTIONS = 'Questions.json'
SERIES = 0
LOG = 'log.csv'
MODEL = "gpt-4-1106-preview"
ROUNDS = 20

dotenv.load_dotenv(".env")
key=os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=key)


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
    # "functions": functions
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

groupchat = autogen.GroupChat(agents=[user_proxy, splunker, sense_check], messages=[], max_round=ROUNDS)
manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)

questions = load_questions(QUESTIONS)
questions = questions[SERIES]
prompts, answers = get_prompts(questions)

for i in range(len(prompts)):

    user_proxy.initiate_chat(
        manager,
        message=prompts[i],
    )

    # Marks answer with marker bot
    response = str(extract_answer(splunker.last_message()["content"]))
    string = f"Student answer: {response}, Textbook: {answers[i]}"
    response = client.chat.completions.create(
    model="gpt-4-1106-preview",
    messages=[
        {"role": "system", "content": "Evaluate student answers against a textbook answer. Return True of correct and False if incorrect or no answer is given. Only reply True or False, never anything else."},
        {"role": "user", "content": string},
    ]
    )

    result = response.choices[0].message.content

    messages = groupchat.messages
    tokens = count_token(input=messages, model=MODEL)

    with open(f"Message-Seed_{SEED}-Question_{questions[i]['Number']}.json", "w") as f:
        f.write(json.dumps(messages))

    row_to_append = [questions[i]['Number'], SEED, result, questions[i]['Points'], questions[i]['Answer'], extract_answer(messages[-1]['content']), tokens]

        # Check if the file exists
    if not os.path.exists(LOG):
        # If the file doesn't exist, create it and write the header row (if needed)
        with open(LOG, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(["index", "seed","result", "points", "answer_given", "answer_correct", "token_count"])

    # Open the CSV file in append mode
    with open(LOG, 'a', newline='') as csvfile:
        # Create a CSV writer object
        csv_writer = csv.writer(csvfile)
        
        # Append the string as a new row
        csv_writer.writerow(row_to_append)

    groupchat.reset()
