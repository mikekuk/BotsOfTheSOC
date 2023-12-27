import dotenv
import os
from openai import OpenAI


dotenv.load_dotenv(".env")
key=os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=key)


def markerbot(student: str, textbook: str) -> str:
    """
    Takes in student and text book answer and uses GPT4 for fuzzy matching to mark the answer.

    Returns string ot "True" or "False".
    """

    # Marks answer with marker bot
    string = f"Student answer: {str(student)}, Textbook: {textbook}"
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[
            {"role": "system", "content": "Evaluate student answers against a textbook answer. Return True of correct and False if incorrect or no answer is given. Only reply True or False, never anything else."},
            {"role": "user", "content": string},
        ]
    )
    result = response.choices[0].message.content
    
    return result

