from textwrap import dedent, indent
from openai import OpenAI


def query_model(prompt: list[dict[str, str]], options: dict):
    """
    Queries the language model with the given options and returns the response.

    Parameters:
    - prompt: A list of dictionaries containing the messages to be sent to the model.
    Each dictionary should have a 'role' key (e.g., 'user', 'assistant') and a 'content' key with the message content.
    - options: A dictionary containing options for the query.

    Returns:
    - The response from the language model as the completion object.
    """
    client = OpenAI()
    return client.chat.completions.create(messages=prompt, **options)


def ask_llm_for_one_response(prompt: str, options: dict) -> str:
    """
    Asks the language model for a single response based on the provided prompt and options.

    Parameters:
    - prompt: The prompt to be sent to the language model.
    - options: A dictionary containing options for the query.

    Returns:
    - The response from the language model as a string.
    """
    response = query_model([{"role": "user", "content": prompt}], options)
    return response.choices[0].message.content


def ask_llm_for_one_code(prompt: str, options: dict) -> str:
    """
    Asks the language model for a single code response based on the provided prompt and options.

    Parameters:
    - prompt: The prompt to be sent to the language model.
    - options: A dictionary containing options for the query.

    Returns:
    - The code part of the response from the language model as a string.
    """
    whole_response = ask_llm_for_one_response(prompt, options)
    if "```" in whole_response:
        if "```python" in whole_response:
            code_start = whole_response.index("```python") + 9
        else:
            code_start = whole_response.index("```") + 3
        code_end = whole_response.rindex("```")
        return whole_response[code_start:code_end].strip()
    else:
        return whole_response.strip()


def get_indentation(code_piece: str) -> str:
    """
    Gets the indentation of the first line of the given code piece.

    Parameters:
    - code_piece: The code piece from which to extract the indentation.

    Returns:
    - The indentation of the first line of the code piece as a string.
    """
    lines = code_piece.split("\n")
    if lines:
        for i in range(len(lines)):
            if lines[i].strip() != "":
                return lines[i][: len(lines[i]) - len(lines[i].lstrip())]
    return ""


def replace_code_piece(
    file_content: str, piece_start: int, piece_end: int, new_code: str
) -> str:
    """
    Replaces a piece of code in the file content with the new code.

    Parameters:
    - file_content: The content of the file being processed.
    - piece_start: The starting line of the code piece to be replaced.
    - piece_end: The ending line of the code piece to be replaced.
    - new_code: The new code to replace the old code.

    Returns:
    - The file content with the replaced code.
    """
    file_lines = file_content.split("\n")
    indentation = get_indentation("\n".join(file_lines[piece_start:piece_end]))
    new_code_with_indentation = indent(dedent(new_code), indentation)
    return "\n".join(
        file_lines[:piece_start] + [new_code_with_indentation] + file_lines[piece_end:]
    )
