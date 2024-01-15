import json
import csv
import os
from autogen.token_count_utils import count_token
from prompt_functions import load_questions, get_prompts, extract_answer
from agents import groupchat, manager, user_proxy, splunker
from config import QUESTIONS, SERIES, LOG, SEED, MODEL
from ai_functions import markerbot


questions = load_questions(QUESTIONS)
questions = questions[SERIES]
prompts, answers = get_prompts(questions)

for i in range(len(prompts)):

    user_proxy.initiate_chat(
        manager,
        message=prompts[i],
    )

    answer = extract_answer(splunker.last_message()["content"])

    result = markerbot(questions[i]['Question'], answer, questions[i]['Answer'])

    messages = groupchat.messages
    tokens = count_token(input=messages, model=MODEL)

    with open(f"Message-Seed_{SEED}-Question_{questions[i]['Number']}.json", "w") as f:
        f.write(json.dumps(messages))

    row_to_append = [questions[i]['Number'], SEED, result, questions[i]['Points'], questions[i]['Answer'], answer, tokens]

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
