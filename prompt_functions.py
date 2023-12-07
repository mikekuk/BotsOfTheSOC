import json

def load_questions(file: str) -> dict:
    """
    Loads JSON of questions list.
    
    Exaple use: questions = load_questions("Questions.json")
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


def get_prompt(idx:int, questions: dict) -> str:
    """
    Generates prompt from questions dict and index.
    To be used with load_questions.
    
    Example use: 
        questions = load_questions("Questions.json")
        prompt = get_prompt(4, questions)
    """

    questions_list = _sort_questions(questions)

    def get_question(idx: int) -> str:
        return questions[questions_list[idx]]['Question']
    
    def get_answer(idx: int) -> str:
        return questions[questions_list[idx]]['Answer']
    
    def get_number(idx: int) -> str:
        return questions[questions_list[idx]]['Number']
    
    def get_hint(idx: int) -> str:
        hint = questions[questions_list[idx]]['Hints']
        if hint == "":
            return hint
        else:
            return f"Hint: {hint}"
    

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

        background += f"\t{x_number}: {x_question}\n\tAnswer: {X_answer}\n"
        count +=1
    
    # Compile prompt
    question_string = f"{background}\n\nTask: {get_question(idx)}\n\n{get_hint(idx)}"

    return question_string

def get_answer(idx: int, questions: dict) -> str:
    """
    Returns answer for question from idx and questons dict.
    """

    questions_list = _sort_questions(questions)
    return questions[questions_list[idx]]['Answer']