#!/usr/bin/env python3
import re
import subprocess
import json

def save_to_json(data, filename):
    """Save data to a JSON file."""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

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
            aws_help_output = subprocess.check_output(["aws", service, command, "help"], text=True, stderr=subprocess.STDOUT)
        elif service:
            aws_help_output = subprocess.check_output(["aws", service, "help"], text=True, stderr=subprocess.STDOUT)
        else:
            aws_help_output = subprocess.check_output(["aws", "help"], text=True, stderr=subprocess.STDOUT)
        return clean_output(aws_help_output)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while fetching AWS CLI help: {str(e)}")
        return ""

if __name__ == "__main__":
    aws_output = get_aws_help_output()
    cleaned_output = clean_output(aws_output)

    start = cleaned_output.find("AVAILABLE SERVICES")
    end = cleaned_output.find("SEE ALSO")

    if start != -1 and end != -1:
        service_block = cleaned_output[start:end]
        services = re.findall(r'o (\w+)', service_block, re.MULTILINE)

    aws_data = {
        "aws": {
            "args": [],
            "command": "aws",
            "help": "",
            "options": {},
            "subcommands": {},
        }
    }

    print("Services:")
    for service in services:
        print(service)
        aws_service_output = get_aws_help_output(service)
        if aws_service_output:
            commands, options = extract_elements_for_service(aws_service_output)
            description = extract_description(aws_service_output)
            print(f"\nDescription for {service}:\n{description}")
            aws_data["aws"]["subcommands"].update({service: {"commands": commands, "description": description}})
            save_to_json(aws_data, 'aws_command_data.json')

            # Fetch options for each command
            for command, command_info in commands.items():
                aws_command_output = get_aws_help_output(service, command)
                _, command_options = extract_elements_for_service(aws_command_output)
                command_description = extract_description(aws_command_output)
                print(f"\nDescription for {service} {command}:\n{command_description}")
                command_info["options"] = command_options
                command_info["description"] = command_description
                save_to_json(aws_data, 'aws_command_data.json')

