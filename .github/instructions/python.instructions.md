---
description: 'Python coding conventions and guidelines'
applyTo: '**/*.py'
---

<!-- 
Copied from: https://github.com/github/awesome-copilot/blob/main/instructions/python.instructions.md 
Adapted to fit the current project's needs.
-->

# Python Coding Conventions

## Python Instructions

- Write clear and concise comments for each function.
- Ensure functions have descriptive names and include type hints.
- Use meaningful variable names that reflect their purpose.
- Follow PEP 8 style guidelines for formatting and structure.
- Include error handling with appropriate exceptions.
- Provide docstrings following slightly modified Google Style Docstring conventions (see Docstring example at the end).
- Use the python 3.10+ syntax for type annotations (e.g., `list[str]`, `dict[str, int]`, `set[str]`).
- Break down complex functions into smaller, more manageable functions.
- Add appropriate logging where necessary for debugging and monitoring.
- Log exceptions where caught, not when they are raised. Include exception details in the log if user needs to be informed.
- Include media id as `[media_id]` in the log message, Frontend app logic uses this media id to link the log to relevant media item.


## General Instructions

- Always prioritize readability and clarity.
- For algorithm-related code, include explanations of the approach used.
- Write code with good maintainability practices, including comments on why certain design decisions were made.
- Handle edge cases and write clear exception handling.
- For libraries or external dependencies, mention their usage and purpose in comments.
- Use consistent naming conventions and follow language-specific best practices.
- Write concise, efficient, and idiomatic code that is also easily understandable.

## Code Style and Formatting

- Follow the **PEP 8** style guide for Python.
- Maintain proper indentation (use 4 spaces for each level of indentation).
- Ensure lines do not exceed 79 characters.
- Place function and class docstrings immediately after the `def` or `class` keyword.
- Use blank lines to separate functions, classes, and code blocks where appropriate.

## Edge Cases and Testing

- Always include test cases for critical paths of the application.
- Account for common edge cases like empty inputs, invalid data types, and large datasets.
- Include comments for edge cases and the expected behavior in those cases.
- Write unit tests for functions and document them with docstrings explaining the test cases.

## Example of Proper Documentation

Docstring Example:
```python
def function_name(param1: int, param2: str) -> bool:
    """Brief description of the function. \n
    Args:
        param1 (int): Description of param1.
        param2 (str): Description of param2.
            - Optional additional details about param2.
            - 'all' can be used to indicate all items.
            - 'none' / '' (empty string) can be used to indicate no items.
            - 'recent' can be used to indicate recently added items.
    Returns:
        bool: Description of the return value.
    Yields:
        Description of what is yielded. (for generator functions)
    Raises:
        ValueError: Description of the error condition.
    """
    pass
```
