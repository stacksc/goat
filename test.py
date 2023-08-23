from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.shortcuts import CompleteStyle

# Create a custom completer with your choices
choices = [
    'Python',
    'JavaScript',
    'Java',
    'C++',
    'MySQL',
    'MongoDB',
    'SQLite',
]

custom_completer = WordCompleter(choices, ignore_case=True)

# Prompt the user using custom completer
selected_language = prompt('Select a programming language: ',
                           completer=custom_completer,
                           complete_style=CompleteStyle.COLUMN,
                           default='Python')

print("Selected Programming Language:", selected_language)
