import json
import csv
import os
from datetime import datetime
import autogen
from autogen.token_count_utils import count_token
from prompt_functions import load_questions, get_prompts, extract_answer
from config import QUESTIONS, SERIES, LOG, SEED, MODEL, RUN_NAME, TEMPERATURE
from bots_of_the_soc_single import assign_splunker
from system_messages import planner_system_message, sense_checker_system_message
from agents import llm_config, config_list
from ai_functions import markerbot

today = datetime.now().strftime('%Y-%m-%d')

run_name = f"{today}-{RUN_NAME}_functionCall_Series-{SERIES}_Seed-{SEED}_Temp-{TEMPERATURE}"

questions = load_questions(QUESTIONS)
questions = questions[SERIES]
prompts, answers = get_prompts(questions)

dir = f"runs/{run_name}"

log = f"{dir}/{LOG}"

os.makedirs(dir, exist_ok=True)

functions_mapping = {
    "assign_analyst": assign_splunker
}

functions = [
    {
        "name": "assign_analyst",
        "description": "Assigns an analyst with a task to complete and returns the findings. The analyst has access to Splunk and can conduct its own investigations. Returns the answer and a summary of its findings.",
        "parameters": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "A description of the task the analyst has to conduct. This should include all relevant context and hints."
                }
            },
            "required": ["task"]
        }
    },
]


pm = autogen.AssistantAgent(
    name="Planner",
    system_message = planner_system_message,
    llm_config={
        "seed": SEED,  # seed for caching and reproducibility
        "config_list": config_list,  # a list of OpenAI API configuration
        "functions": functions,
    },  # configuration for autogen's enhanced inference API which is compatible with OpenAI API
)


# create a UserProxyAgent instance named "user_proxy"
user_proxy_high = autogen.UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    is_termination_msg=lambda x: x.get("content", "") and "TERMINATE" in x.get("content", "").rstrip(),
    code_execution_config={
        "work_dir": "coding",
        "use_docker": False,  # set to True or image name like "python:3" to use docker
    },
    llm_config=llm_config,
    system_message=sense_checker_system_message
)

user_proxy_high.register_function(
    function_map=functions_mapping
)

if __name__ == "__main__":

    for i in range(len(prompts)):

        continue_conv = bool(i != 0)

        user_proxy_high.initiate_chat(
            pm,
            message=prompts[i],
            clear_history=continue_conv
        )
        
        answer = extract_answer(pm.last_message()["content"])

        result = markerbot(questions[i]['Question'], answer, questions[i]['Answer'])

        messages = list(dict(user_proxy_high.chat_messages).values())[0]
        tokens = count_token(input=messages, model=MODEL)

        with open(f"{dir}/Message-Seed_{SEED}-Question_{questions[i]['Number']}.json", "w") as f:
            f.write(json.dumps(messages))

        row_to_append = [questions[i]['Number'], SEED, result, questions[i]['Points'], questions[i]['Answer'], str(answer).replace("\n", "\t").replace(",", ";"), tokens]

            # Check if the file exists
        if not os.path.exists(log):
            # If the file doesn't exist, create it and write the header row (if needed)
            with open(log, 'w', newline='') as csvfile:
                csv_writer = csv.writer(csvfile)
                csv_writer.writerow(["index", "seed","result", "points", "answer_given", "answer_correct", "token_count"])

        # Open the CSV file in append mode
        with open(log, 'a', newline='') as csvfile:
            # Create a CSV writer object
            csv_writer = csv.writer(csvfile)
            
            # Append the string as a new row
            csv_writer.writerow(row_to_append)
