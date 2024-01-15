import json
import csv
import os
from autogen.token_count_utils import count_token
from prompt_functions import load_questions, get_prompts, extract_answer
from agents import user_proxy, splunker
from config import QUESTIONS, SERIES, LOG, SEED, MODEL, RUN_NAME
from ai_functions import markerbot

run_name = f"{RUN_NAME}_Series-{SERIES}_Seed-{SEED}"

questions = load_questions(QUESTIONS)
questions = questions[SERIES]
prompts, answers = get_prompts(questions)

dir = f"runs/{run_name}"

log = f"{dir}/{LOG}"

os.makedirs(dir, exist_ok=True)

for i in range(len(prompts)):

    user_proxy.initiate_chat(
        splunker,
        message=prompts[i],
    )

    answer = extract_answer(splunker.last_message()["content"])

    result = markerbot(questions[i]['Question'], answer, questions[i]['Answer'])

    messages = list(dict(user_proxy.chat_messages).values())[0]
    tokens = count_token(input=messages, model=MODEL)

    with open(f"{dir}/Message-Seed_{SEED}-Question_{questions[i]['Number']}.json", "w") as f:
        f.write(json.dumps(messages))

    row_to_append = [questions[i]['Number'], SEED, result, questions[i]['Points'], questions[i]['Answer'], answer, tokens]

        # Check if the file exists
    if not os.path.exists(LOG):
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
