import dotenv
import os
from openai import OpenAI


dotenv.load_dotenv(".env")
key=os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=key)


def get_response(system_message: str, prompt: str) -> str:
    "Gets a one short response from GPT-4 with system message and prompt."
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt},
        ]
    )
    return response.choices[0].message.content


def markerbot(student: str, textbook: str) -> str:
    """
    Takes in student and text book answer and uses GPT4 for fuzzy matching to mark the answer.

    Returns string ot "True" or "False".
    """

    system_message = "Evaluate student answers against a textbook answer. Return True of correct and False if incorrect or no answer is given. Only reply True or False, never anything else."
    string = f"Student answer: {str(student)}, Textbook: {textbook}"

    return get_response(system_message, string)

def summarize_data(data:str) -> str:
    """
    Summaries data to save tokens
    """
    system_message = "You are a helpful AI security operations assistant. Summarize this data and provide all key insights. ALWAYS include a summary of the data structure and all field names. Sum up any human readable sections in the data."
    return get_response(system_message, data)