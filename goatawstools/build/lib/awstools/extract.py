import click, os, json, re, sys, gnureadline, subprocess
from toolbox.logger import Log
from toolbox.misc import set_terminal_width, get_save_path
from .iam import get_latest_profile
import signal
import atexit
from pathlib import Path

@click.group('extract', invoke_without_command=True, help='extract the command tree for AWS CLI', context_settings={'help_option_names':['-h','--help'], 'max_content_width': set_terminal_width()})
@click.pass_context
def extract(ctx):
    pass

@extract.command(help='manually refresh the AWS CLI command tree', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def commands(ctx):

    json_file = get_save_path("aws.json")

    # Register cleanup function to handle the SIGINT (Ctrl_C) and SIGTERM signals
    signal.signal(signal.SIGINT, lambda signum, frame: (cleanup(), sys.exit(1)))
    signal.signal(signal.SIGTERM, lambda signum, frame: (cleanup(), sys.exit(1)))

    if not prompt_user_to_continue():
        print("INFO: exiting the script now...")
        exit()

    aws_output = get_aws_help_output()
    cleaned_output = clean_output(aws_output)
    global_options = extract_global_options(cleaned_output)

    start = cleaned_output.find("AVAILABLE SERVICES")
    end = cleaned_output.find("SEE ALSO")

    services = []
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

    aws_data["aws"]["options"] = global_options
    for service in services:
        if not service.islower() or service == "help":
            continue

        aws_service_output = get_aws_help_output(service)
        if not aws_service_output:
            continue

        commands, _ = extract_elements_for_service(aws_service_output)
        print(f"Exploring {service}")
        if commands:
            aws_data["aws"]["subcommands"][service] = {
                "command": service,
                "help": clean_description(extract_description(aws_service_output)),
                "options": {},
                "subcommands": {}
            }

        for command, command_info in commands.items():
            if not command.islower():
                continue

            print(f"\tExploring {service} {command}")
            aws_command_output = get_aws_help_output(service, command)
            if not aws_command_output:
                continue

            local_options = extract_local_options(aws_command_output)
            if local_options:
                aws_data["aws"]["subcommands"][service]["subcommands"][command] = {
                    "options": local_options,
                    "help": clean_description(extract_description(aws_command_output))
                }

        save_to_json(aws_data, json_file)

def prompt_user_to_continue():
    """Prompts the user to decide if they want to continue the process."""
    print("INFO: this process will take approximately 3-4 hours to complete.")
    choice = input("INFO: do you want to continue? [yes/no]: ").strip().lower()

    if choice == "yes":
        return True
    elif choice == "no":
        return False
    else:
        print("INFO: invalid choice. Please enter 'yes' or 'no'.")
        return prompt_user_to_continue()  # Recursively ask until a valid choice is made.

def save_to_json(data, filename):
    """Save data to a JSON file."""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

def clean_output(text):
    while '\x08' in text:
        idx = text.index('\x08')
        text = text[:idx-1] + text[idx+1:]
    return text

def extract_global_options(aws_output):
    """Extract global options from the AWS CLI help output."""
    lines = aws_output.split("\n")

    options = {}
    current_option = None
    description_lines = []

    for line in lines:
        option_match = re.match(r'^\s*(--[\w-]+)\s+\((\w+)\)', line)
        if option_match:
            if current_option:  # Save the previous option
                options[current_option] = {
                    "name": current_option,
                    "help": " ".join(description_lines).strip()
                }
                description_lines = []

            current_option = option_match.group(1)
        elif current_option:
            description_lines.append(line.strip())

    # Save the last option, if any
    if current_option:
        options[current_option] = {
            "name": current_option,
            "help": " ".join(description_lines).strip()
        }

    return options

def extract_local_options(text):
    options = {}

    # Check if both "OPTIONS" and "GLOBAL OPTIONS" are present, and extract the content between them
    start_index = text.find("OPTIONS")
    end_index = text.find("GLOBAL OPTIONS")

    if start_index == -1 or end_index == -1:
        return options

    local_options_text = text[start_index:end_index]

    lines = local_options_text.split("\n")
    current_option = None
    current_description = []

    for line in lines:
        option_match = re.match(r'^\s*(--[\w-]+)\s+\((\w+)\)', line)
        if option_match:
            if current_option:  # Save the previous option's description
                full_description = ' '.join(current_description).strip()
                first_sentence = extract_first_sentence(full_description)
                options[current_option]["help"] = first_sentence
                current_description = []

            current_option = option_match.group(1)
            option_type = option_match.group(2)
            options[current_option] = {"type": option_type, "help": ""}
        elif current_option:
            current_description.append(line.strip())

    # Save the last option's description, if any
    if current_option and current_description:
        full_description = ' '.join(current_description).strip()
        first_sentence = extract_first_sentence(full_description)
        options[current_option]["help"] = first_sentence

    return options

def extract_elements_for_service(aws_output):
    commands_pattern = re.compile(r'^\s*o\s+([\w-]+)', re.MULTILINE)
    options_pattern = r'(--[\w-]+)\s+\((\w+)\)'

    commands = {}
    options = {}

    current_service = None
    current_command = None
    current_option = None
    option_description = []

    for line in aws_output.split("\n"):
        command_match = re.search(commands_pattern, line)
        if command_match:
            current_service = command_match.group(1)
            commands[current_service] = {"command": current_service, "options": {}, "subcommands": {}}
            current_command = None
            continue

        subcommand_match = re.search(r'^\s*o\s+([a-zA-Z0-9-]+)', line)
        if subcommand_match:
            current_command = subcommand_match.group(1)
            commands[current_service]["subcommands"][current_command] = {"command": current_command, "options": {}}
            continue

        option_match = re.search(options_pattern, line)
        if option_match:
            # Store the previous option's description, if any
            if current_option:
                options[current_option]['help'] = ' '.join(option_description).strip()
                option_description = []

            current_option = option_match.group(1)
            option_type = option_match.group(2)
            options[current_option] = {"name": current_option, "type": option_type, "help": ""}
            continue

        if current_option:
            option_description.append(line.strip())

    # Save the last option's description, if any
    if current_option and option_description:
        options[current_option]['help'] = ' '.join(option_description).strip()

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

def cleanup(filename="aws.json"):
    save_path = get_save_path(filename)
    if os.path.isfile(filename):
        os.remove(filename)

def clean_description(desc):
    # Normalize whitespace
    desc = ' '.join(desc.split())

    # Extract the first sentence
    match = re.match(r'^(.*?[.!?])', desc)
    if match:
        return match.group(1)
    return desc

def extract_first_sentence(description):
    match = re.match(r"^(.*?[.!?])", description)
    if match:
        return match.group(1).strip()
    return description.strip()
