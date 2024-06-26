# Description: Helper functions for the tutor agent.
from pathlib import Path
from typing import Tuple
from dataclasses import dataclass
import json

from openai import Client
from IPython.display import display, Markdown


@dataclass
class Question:
    """
    Dataclass to represent a question object.
    """
    question_id: str
    question: str
    concepts_tested: list[str]
    good_answer: str
    common_mistakes: list[str]


def get_questions_and_answers(q_store_path: Path, a_store_path: Path) -> Tuple[dict,dict]:
    """
    Load questions and answers from the question and answer stores.

    Args:
        q_store_path (Path): The path to the question store.
        a_store_path (Path): The path to the answer store.

    Returns:
        Tuple[dict, dict]: A tuple containing the questions and answers dictionaries.
    """
    questions = {}
    answers = {}

    # Load questions from the question store
    with open(q_store_path, 'r') as q_store:
        question_dict = json.load(q_store)
        questions = {}
        for q_id, q_data in question_dict.items():
            questions[q_id] = Question(q_id, **q_data)

    # Load answers from the answer store
    with open(a_store_path, 'r') as a_store:
        answers = json.load(a_store)

    return questions, answers


def create_content(question: Question, student_answer: str) -> str:
    """
    Generate the prompt content for the question answer pair
    """
    concepts = "\n\t- " + "\n\t- ".join(question.concepts_tested)
    common_mistakes = "\n\t- " + "\n\t- ".join(question.common_mistakes)
    return (
        "Input:\n"
        + f'Exam Question: "{question.question}"\n'
        + f'Student Answer: "{student_answer}"\n'
        + f"Concepts Tested: {concepts}\n"
        + f'Example Good Answer: "{question.good_answer}"\n'
        + f"Common mistakes: {common_mistakes}\n"
    )


def print_bot_response(client, messages):
    """
    Prints the message content with annotations replaced by footnotes.

    Args:
        message (Message): The message object containing the content and annotations.

    Returns:
        str: The message content with footnotes added.
    """
    # Extract the message content
    message_content = messages.data[0].content[0].text
    annotations = message_content.annotations
    citations = []

    # Iterate over the annotations and add footnotes
    for index, annotation in enumerate(annotations):
        # Replace the text with a footnote
        message_content.value = message_content.value.replace(annotation.text, f' [{index}]')

        # Gather citations based on annotation attributes
        if (file_citation := getattr(annotation, 'file_citation', None)):
            cited_file = client.files.retrieve(file_citation.file_id)
            citations.append(f'[{index}] {file_citation.quote} from {cited_file.filename}')
        elif (file_path := getattr(annotation, 'file_path', None)):
            cited_file = client.files.retrieve(file_path.file_id)
            citations.append(f'[{index}] Click <here> to download {cited_file.filename}')

    # Add footnotes to the end of the message before displaying to user
    message_content.value += '\n' + '\n'.join(citations)
    display(Markdown(message_content.value))
    return message_content.value


def get_guidance_and_feedback(client: Client, content: str, tutor_agent_id, temperature, thread_id=None, show_run=False):
    """
    Creates a thread with the tutor agent, sends a message with the content (the question and answer input), and retrieves the reponse based on the bot's intructions.

    Args:
        content (str): The content of the question.
        tutor_agent_id (str): The ID of the tutor agent.
        thread_id (str, optional): The ID of the thread. If not provided, a new thread will be created.
        show_run (bool, optional): Whether to display the run object. Defaults to False.

    Returns:
        str: The ID of the thread - used to continue the conversation.
    """
    # Create a thread with the tutor agent
    if thread_id is None:
        thread = client.beta.threads.create()
        thread_id = thread.id

    # Attach the question content to the thread
    client.beta.threads.messages.create(
        thread_id=thread_id, # type: ignore
        role="user",
        content=content,
    )

    # Create a run object to execute the message on the thread with the tutor agent
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread_id, # type: ignore
        assistant_id=tutor_agent_id,
        temperature=temperature,
    )

    if run.status == 'completed':
        messages = client.beta.threads.messages.list(
            thread_id=thread_id # type: ignore
        )
        display(Markdown("**Bot Message**:\n"))
        print_bot_response(client, messages)
    else:
        print(run.status)
    
    if show_run:
        attrs_to_show = ['status', 'temperature', 'tools', 'usage']
        run_str = "\n**Run object attributes**:\n"
        for attr in attrs_to_show:
            run_str += f"- {attr}: {getattr(run, attr)}\n"
        display(Markdown(run_str))

    return thread_id, messages, run