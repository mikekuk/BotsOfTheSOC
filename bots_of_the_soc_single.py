import json
import csv
import os
from datetime import datetime
from autogen.token_count_utils import count_token
from prompt_functions import load_questions, get_prompts, extract_answer
from agents import user_proxy, splunker
from config import QUESTIONS, SERIES, LOG, SEED, MODEL, RUN_NAME, TEMPERATURE
from ai_functions import markerbot, get_response

today = datetime.now().strftime('%Y-%m-%d')

run_name = f"{today}-{RUN_NAME}_Series-{SERIES}_Seed-{SEED}_Temp-{TEMPERATURE}"

questions = load_questions(QUESTIONS)
questions = questions[SERIES]
prompts, answers = get_prompts(questions)

dir = f"runs/{run_name}"

log = f"{dir}/{LOG}"

os.makedirs(dir, exist_ok=True)

def assign_splunker(task:str):
    user_proxy.initiate_chat(splunker, message=task)
    answer = extract_answer(splunker.last_message()["content"])
    summary = get_response("A helpful AI assistant.", f"Summarize the key information in this investigation. Include any insights into the Splunk data and key facts that maybe useful in future investigations: {list(dict(user_proxy.chat_messages).values())[0]}")

    return f"Answer: {answer}\nSummary of investigation: {summary}"

if __name__ == "__main__":

    for i in range(len(prompts)):

        assign_splunker(prompts[i])
        
        answer = extract_answer(splunker.last_message()["content"])

        result = markerbot(questions[i]['Question'], answer, questions[i]['Answer'])

        messages = list(dict(user_proxy.chat_messages).values())[0]
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
