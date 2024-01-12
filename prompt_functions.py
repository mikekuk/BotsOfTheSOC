import json

def load_questions(file: str) -> list[dict[str, any]]:
    """
    Loads JSON of questions list.
    
    Example use: questions = load_questions("Questions.json")
    """
    with open(file, 'r') as json_file:
        questions_raw = json_file.read()

    return json.loads(questions_raw)

def _sort_questions(questions: dict) -> list:
    """
    Helper function to create ordered list form dict
    """
    question_keys = questions.keys()
    questions_list = sorted(list(question_keys))

    return questions_list

def get_prompts(questions: list) -> tuple[list, list]:
    """
    Generates lists of prompts and answers from questions list of dicts.
    To be used with load_questions.
    
    Example use: 
        questions = load_questions("Questions.json")
        questions = questions[series]
        prompts, answers = get_prompts(questions)
    """

    def get_question(idx: int) -> str:
        return questions[idx]['Question']
    
    def get_answer(idx: int) -> str:
        return questions[idx]['Answer']
    
    def get_number(idx: int) -> str:
        return questions[idx]['Number']
    
    def get_hint(idx: int) -> str:
        hint = questions[idx]['Hints']
        if hint == "":
            return hint
        else:
            return f"Hint: {hint}"
        
    def get_prompt(idx: int) -> str:
    
        question_string = f"{get_question(idx)}\n\n{get_hint(idx)}"

        # Retrun just first question of no background required
        if idx == 0:
            return question_string

        # Generate and append background
        count = 0
        background = "Background:\n"

        while idx != count:
            x_question = get_question(count)
            X_answer = get_answer(count)
            x_number = get_number(count)

            background += f"{x_number} - {x_question}\nAnswer: {X_answer}\n"
            count +=1
        
        # Compile prompt
        question_string = f"{background}\n\nTask:{get_number(idx)} - {get_question(idx)}\n\n{get_hint(idx)}"

        return question_string
    
    prompts = []
    answers = []
    
    for i, question in enumerate(questions):
        prompts.append(get_prompt(i))
        answers.append(get_answer(i))

    return prompts, answers


def extract_answer(input_string: str):

    if type(input_string) != str:
        return None

    start_substring = "Answer:"
    end_substring = "TERMINATE"
    
    start_index = input_string.find(start_substring)
    end_index = input_string.find(end_substring)
    
    if start_index != -1 and end_index != -1:
        start_index += len(start_substring)
        extracted_text = input_string[start_index:end_index].strip()
        return extracted_text
    else:
        return None
