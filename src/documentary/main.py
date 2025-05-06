from textwrap import dedent
from .utils import replace_code_piece, ask_llm_for_one_code, ask_llm_for_one_response


def isomorphisize(
    file_content: str,
    function_start: int,
    function_end: int,
    docstring_start: int,
    docstring_end: int,
    LLM_options: dict,
    documentary_options: dict,
) -> str:
    """
    Improves the docstring of the specified function using documentary approach.

    Parameters:
    - file_content: The content of the file being processed.
    - function_start: The starting line of the function in the file content.
    - function_end: The line after the function in the file content.
    - docstring_start: The starting line of the docstring in the function.
    - docstring_end: The line after the docstring in the function.
    - LLM_options: A dictionary containing options for the language model.
    - documentary_options: A dictionary containing options for the documentary process.
        - iterations: The number of iterations to run to improve the docstring.
        - docstring_size_limit: The size limit for the new docstring as a fraction of the original function length.

    Returns:
    - The improved docstring.
    """
    all_code_lines = file_content.split("\n")
    context = "\n".join(all_code_lines[:function_start] + all_code_lines[function_end:])
    function_header = "\n".join(all_code_lines[function_start:docstring_start])
    function_docstring = "\n".join(all_code_lines[docstring_start:docstring_end])
    function_body = "\n".join(all_code_lines[docstring_end:function_end])

    if "iterations" in documentary_options:
        iterations = documentary_options["iterations"]
    else:
        iterations = 0

    if "docstring_size_limit" in documentary_options:
        docstring_size_limit = documentary_options["docstring_size_limit"]
    else:
        docstring_size_limit = 0

    orig_function_length = function_end - docstring_end

    new_docstring = function_docstring
    prompt_for_body = dedent(
        f"""
        In the file containing
        ```python
        {context}
        ```
        generate the body of the function
        ```python
        {function_header}
        {new_docstring}
        ```
        Only output the body, with correct indentation. Do not repeat the function signature or docstring.
        """
    )
    generated_body = ask_llm_for_one_code(prompt_for_body, LLM_options)
    prompt_for_equivalency = dedent(
        f"""
        Are the following two code pieces equivalent?
        ```python
        {function_header}
        {function_body}
        ```
        and
        ```python
        {function_header}
        {generated_body}
        ```
        Just answer with "yes" or "no".
        """
    )
    equivalency = ask_llm_for_one_response(prompt_for_equivalency, LLM_options)

    for i in range(iterations):
        if "yes" in equivalency.lower():
            break
        prompt_for_new_docstring = dedent(
            f"""
            In the file containing
            ```python
            {context}
            ```
            the correct implementation of the function
            ```python
            {function_header}
            ```
            is
            ```python
            {function_header}
            {function_body}
            ```
            However, using the docstring
            ```python
            {new_docstring}
            ```
            the following body was implemented
            ```python
            {function_header}
            {generated_body}
            ```
            First, describe all the differences between the correct implementation and the second implementation, with an emphasis on parts missed in the second code piece from the correct implementation.
            Then, update the docstring to describe enough details to implement the correct body, with an emphasis on missed aspects.
            Specifically, include any custom functions (with their signature) used, or attributes of custom classes accessed. Also include any checks and/or error handling that is needed.
            Be as specific as possible.
            Do not add more than {int(docstring_size_limit * orig_function_length)} lines to the existing docstring.
            Output only the docstring inside triple backticks.
            """
        )
        new_docstring = ask_llm_for_one_code(prompt_for_new_docstring, LLM_options)
        if len(new_docstring.split("\n")) > len(function_docstring.split("\n")) + int(
            docstring_size_limit * orig_function_length
        ):
            new_docstring = "\n".join(
                new_docstring.split("\n")[
                    : len(function_docstring.split("\n"))
                    + int(docstring_size_limit * orig_function_length)
                ]
            )
        prompt_for_body = dedent(
            f"""
            In the file containing
            ```python
            {context}
            ```
            generate the body of the function
            ```python
            {function_header}
            {new_docstring}
            ```
            Only output the body, with correct indentation. Do not repeat the function signature or docstring.
            """
        )
        generated_body = ask_llm_for_one_code(prompt_for_body, LLM_options)
        prompt_for_equivalency = dedent(
            f"""
            Are the following two code pieces equivalent?
            ```python
            {function_header}
            {function_body}
            ```
            and
            ```python
            {function_header}
            {generated_body}
            ```
            Just answer with "yes" or "no".
            """
        )
        equivalency = ask_llm_for_one_response(prompt_for_equivalency, LLM_options)

    return new_docstring


def isomorphisize_and_replace(
    file_content: str,
    function_start: int,
    function_end: int,
    docstring_start: int,
    docstring_end: int,
    LLM_options: dict,
    documentary_options: dict,
) -> tuple[str, int, int]:
    """
    Isomorphisize function to improve the docstring of a function in the file content and replace the docstring.

    Parameters:
    - file_content: The content of the file being processed.
    - function_start: The starting line of the function in the file content.
    - function_end: The line after the function in the file content.
    - docstring_start: The starting line of the docstring in the function.
    - docstring_end: The line after the docstring in the function.
    - LLM_options: A dictionary containing options for the language model.
    - documentary_options: A dictionary containing options for the documentary process.
        - iterations: The number of iterations to run to improve the docstring.
        - docstring_size_limit: The size limit for the new docstring as a fraction of the original function length.

    Returns:
    - The updated file content with improved docstring.
    """
    new_docstring = isomorphisize(
        file_content,
        function_start,
        function_end,
        docstring_start,
        docstring_end,
        LLM_options,
        documentary_options,
    )

    return (
        replace_code_piece(file_content, docstring_start, docstring_end, new_docstring),
        docstring_start,
        docstring_start + len(new_docstring.split("\n")),
    )


def isomorphisize_file(
    file_content: str,
    LLM_options: dict,
    documentary_options: dict,
) -> str:
    """
    Isomorphisize tall docstrings of functions.

    Parameters:
    - file_content: The content of the file being processed.
    - LLM_options: A dictionary containing options for the language model.
    - documentary_options: A dictionary containing options for the documentary process.
        - iterations: The number of iterations to run to improve the docstring.
        - docstring_size_limit: The size limit for the new docstring as a fraction of the original function length.

    Returns:
    - The updated file content with improved docstrings.
    """
    pass
