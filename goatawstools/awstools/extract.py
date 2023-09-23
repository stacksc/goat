import click, os, json, re, sys, gnureadline
from toolbox.logger import Log
from toolbox.misc import set_terminal_width, get_save_path
from .iam import get_latest_profile
from . import extract_commands
import signal
import atexit

def transform_subcommand(sub_data, command_name=None):
    transformed_subcommand = {
        "command": command_name,  # Add the "command" field
        "description": sub_data.get("description", ""),
        "options": {},
    }

    if "options" in sub_data:
        for option, option_data in sub_data["options"].items():
            transformed_subcommand["options"][option] = {"name": option, "help": option_data}

    if "commands" in sub_data:
        transformed_subcommand["subcommands"] = transform_data(sub_data["commands"])

    return transformed_subcommand

def transform_data(data):
    transformed_data = {}
    for cmd, cmd_data in data.items():
        transformed_data[cmd] = transform_subcommand(cmd_data, command_name=cmd)
    return transformed_data

def cleanup(filename="aws.json"):
    save_path = get_save_path(filename)
    if os.path.isfile(save_path):
        os.remove(save_path)

@click.group('extract', invoke_without_command=True, help='extract the command tree for AWS CLI', context_settings={'help_option_names':['-h','--help'], 'max_content_width': set_terminal_width()})
@click.pass_context
def extract(ctx):
    pass

@extract.command(help='manually refresh the AWS CLI command tree', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def commands(ctx):
    # Register cleanup function to run when we terminate normally
    atexit.register(cleanup)

    # Register cleanup function to handle the SIGINT (Ctr_C) and SIGTERM signals
    signal.signal(signal.SIGINT, lambda signum, frame: sys.exit(1))
    signal.signal(signal.SIGTERM, lambda signum, frame: sys.exit(1))

    if not prompt_user_to_continue():
        print("INFO: exiting the script now...")
        exit()
    error_code, aws_output = extract_commands.get_aws_help_output()
    cleaned_output = extract_commands.clean_output(aws_output)

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

    for service in services:
        error_code, aws_service_output = extract_commands.get_aws_help_output(service)
        if error_code != 0:
            print(f"INFO: failed to fetch help for {service}. Skipping...")
            continue  # Skip the current service and proceed to the next one
        commands, options = extract_commands.extract_elements_for_service(aws_service_output)
        description = extract_commands.extract_description(aws_service_output)
        aws_data["aws"]["subcommands"].update({service: {"commands": commands, "description": description}})
        extract_commands.save_to_json(aws_data, 'aws.json')

        # Fetch options for each command
        for command, command_info in commands.items():
            error_code, aws_command_output = extract_commands.get_aws_help_output(service, command)
            if error_code != 0:
                print(f"INFO: failed to fetch help for {service} {command}. Skipping...")
                continue # skip the current command and proceed to the next one
            _, command_options = extract_commands.extract_elements_for_service(aws_command_output)
            command_description = extract_commands.extract_description(aws_command_output)
            command_info["options"] = command_options
            command_info["description"] = command_description
            extract_commands.save_to_json(aws_data, 'aws.json')

def load_transform_and_save():
    """Load, transform, and save the AWS JSON data."""

    filename = get_save_path("aws.json")
    try:
        with open(filename, 'r') as f:
            aws_data = json.load(f)

        # Check if "aws" and "subcommands" exist in the JSON data
        if "aws" in aws_data and "subcommands" in aws_data["aws"]:
            # Transform the data
            transformed_data = transform_data(aws_data["aws"]["subcommands"])

            # Save the transformed data to a new JSON file
            with open(filename, 'w') as f:
                json.dump(transformed_data, f, indent=2)

            print(f"INFO: data has been transformed and saved to {filename}")
        else:
            print(f"WARN: invalid JSON structure. Please check your input JSON file {filename}")

    except Exception as e:
        print(f"ERROR: {e}")

def prompt_user_to_continue():
    """Prompts the user to decide if they want to continue the process."""
    print("INFO: this process will take approximately 2-3 hours to complete.")
    choice = input("INFO: do you want to continue? [yes/no]: ").strip().lower()

    if choice == "yes":
        return True
    elif choice == "no":
        return False
    else:
        print("INFO: invalid choice. Please enter 'yes' or 'no'.")
        return prompt_user_to_continue()  # Recursively ask until a valid choice is made.

