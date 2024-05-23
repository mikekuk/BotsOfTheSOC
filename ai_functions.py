import dotenv
import os
from openai import OpenAI
from config import MODEL
import google.generativeai as genai



dotenv.load_dotenv(".env")
key=os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=key)
genai.configure(api_key=os.environ["GEMINI_API_KEY"])


def get_response(system_message: str, prompt: str) -> str:
    "Gets a one short response from GPT-4 with system message and prompt."
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt},
        ]
    )
    return response.choices[0].message.content


def markerbot(question: str, student: str, textbook: str) -> str:
    """
    Takes in student and text book answer and uses GPT4 for fuzzy matching to mark the answer.

    Arguments:
        Question, Student answer, Text book answer.

    Returns string ot "True" or "False".
    """

    system_message = "Evaluate student answers against a textbook answer. Return True of correct and False if incorrect or no answer is given. The answer does not need to match every character, as long as it is clear the student is on the right track. Only reply True or False, never anything else."
    string = f"Question: {question}, Student answer: {str(student)}, Textbook: {textbook}"

    return get_response(system_message, string)





def summarize_data(data:str, question:str="") -> str:
    """
    Summaries data to save tokens
    """

    generation_config = {
        "temperature": 0.3,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }
    safety_settings = [
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_NONE",
        },
    ]

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        safety_settings=safety_settings,
        generation_config=generation_config,
    )

    chat_session = model.start_chat(
        history=[]
    )

    additional_message = ""

    if question != "":
        additional_message = f"Include any information that may be relevant to answer the following question: {question}"

    system_message = f"Summarize this data and provide all key insights. ALWAYS include a summary of the data structure and all field names. Sum up any human readable sections in the data. {additional_message}"

    prompt = system_message + "\n\n" + data
    response = chat_session.send_message(prompt)

    return response.text
 

    
    
