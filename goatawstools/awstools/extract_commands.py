import sys, os
import re
import subprocess
import json
from toolbox import misc

def save_to_json(data, filename="aws.json"):
    save_path = misc.get_save_path(filename)
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def clean_output(text):
    while '\x08' in text:
        idx = text.index('\x08')
        text = text[:idx-1] + text[idx+1:]
    return text

def extract_elements_for_service(aws_output):
    commands_pattern = re.compile(r'^\s*o\s+([\w-]+)', re.MULTILINE)
    options_pattern = r'(--[\w-]+)\s+\((\w+)\)'

    commands = {}
    options = {}
    arguments = {}

    current_service = None
    current_command = None

    for line in aws_output.split("\n"):
        command_match = re.search(commands_pattern, line)
        if command_match:
            current_service = command_match.group(1)
            commands[current_service] = {}
            current_command = None

        subcommand_match = re.search(r'^\s*o\s+([a-zA-Z0-9-]+)', line)
        if subcommand_match:
            current_command = subcommand_match.group(1)
            commands[current_service][current_command] = {}

        options_match = re.findall(options_pattern, line, re.MULTILINE)
        if options_match:
            if current_command:
                commands[current_service][current_command]["options"] = dict(options_match)
            else:
                options.update(options_match)

    return commands, options

def extract_description(aws_output):
    description_pattern = re.compile(r'\s*DESCRIPTION\s*([\s\S]*?)\n\n', re.MULTILINE)
    match = re.search(description_pattern, aws_output)
    if match:
        description = match.group(1).strip()
        return description
    return ""

def get_aws_help_output(service="", command=""):
    try:
        if command:
            print(f"EXECUTING: aws {service} {command} help")
            aws_help_output = subprocess.check_output(["aws", service, command, "help"], text=True, stderr=subprocess.STDOUT)
        elif service:
            print(f"EXECUTING: aws {service} help")
            aws_help_output = subprocess.check_output(["aws", service, "help"], text=True, stderr=subprocess.STDOUT)
        else:
            print(f"EXECUTING: aws help")
            aws_help_output = subprocess.check_output(["aws", "help"], text=True, stderr=subprocess.STDOUT)
        return (0, clean_output(aws_help_output))  # 0 indicates success
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while fetching AWS CLI help: {str(e)}")
        return (-1, None)  # -1 indicates an error, and no output

