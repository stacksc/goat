import click, os, json, re, sys, gnureadline, subprocess
from toolbox.logger import Log
from toolbox.misc import set_terminal_width, get_save_path
import signal
import atexit
from pathlib import Path

processed_commands = set()

@click.group('extract', invoke_without_command=True, help='extract the command tree for Azure CLI', context_settings={'help_option_names':['-h','--help'], 'max_content_width': set_terminal_width()})
@click.pass_context
def extract(ctx):
    pass

@extract.command(help='manually refresh the Azure CLI command tree', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def commands(ctx):
    json_file = get_save_path("az.json")

    # Register cleanup function to handle the SIGINT (Ctrl_C) and SIGTERM signals
    signal.signal(signal.SIGINT, lambda signum, frame: (cleanup(), sys.exit(1)))
    signal.signal(signal.SIGTERM, lambda signum, frame: (cleanup(), sys.exit(1)))

    if not prompt_user_to_continue():
        print("INFO: exiting the script now...")
        exit()

    # Set to track processed commands to avoid duplicates
    top_level_commands = get_top_level_commands()

    combined_data = {
        "az": {
            "args": [],
            "command": "az",
            "help": "The Azure command-line interface (Azure CLI) is a set of commands used to create and manage Azure resources. The Azure CLI is available across Azure services and is designed to get you working quickly with Azure, with an emphasis on automation.",
            "options": {},
            "subcommands": {}
        }
    }

    for top_level_command in top_level_commands:
        initial_data = recursive_parse(top_level_command, stop_condition="--cmd")
        if initial_data:
            combined_data["az"]["subcommands"][top_level_command] = initial_data

    # Save the combined data to a single JSON file
    with open(json_file, "w") as f:
        json.dump(combined_data, f, indent=2)

    print(f"INFO: data has been saved to a single JSON file here: {json_file}")

def listToStringWithoutBrackets(list1):
    return str(list1).replace('[','').replace(']','').replace("'", "").replace('{','').replace('}','')

def get_top_level_commands():
    az_help_output = run_az_help("")
    top_level_commands = []

    # Initialize current_section
    current_section = None
    ignore_words = {'and', 'as', 'default', 'for', 'in', 'is', 'it', 'of', 'to', 'with', 'if', 'the'}

    # Parse the top-level commands from the help output
    for line in az_help_output.split("\n"):
        line = line.strip()

        if "Commands" in line:
            current_section = "commands"
        elif "Arguments" in line:
            current_section = "arguments"
        elif current_section == "commands" and line:
            parts = line.split(" ", 1)
            if len(parts) == 2:
                subcommand, _ = parts
                subcommand = subcommand.strip()
                if " " not in subcommand and subcommand.islower() and subcommand not in ignore_words and not any(
                        c in subcommand for c in "!@#$%^&*()[]{};:,.<>?/\\|~`'\""):
                    top_level_commands.append(subcommand)

    return top_level_commands

# Helper function to clean up command-line output
def clean_output(output):
    return re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', output)

# Function to run 'az' command and fetch its help info
def run_az_help(command):
    try:
        print(f"RUNNING: az {command} -h")
        output = subprocess.check_output(['az'] + command.split() + ['-h'], stderr=subprocess.STDOUT, text=True)
        return clean_output(output)
    except subprocess.CalledProcessError as e:
        print(f"Error running az {command} -h")
        return ""

def prompt_user_to_continue():
    """Prompts the user to decide if they want to continue the process."""
    print("INFO: this process will take approximately 1 hour to complete.")
    choice = input("INFO: do you want to continue? [yes/no]: ").strip().lower()

    if choice == "yes":
        return True
    elif choice == "no":
        return False
    else:
        print("INFO: invalid choice. Please enter 'yes' or 'no'.")
        return prompt_user_to_continue()  # Recursively ask until a valid choice is made.

# Function to parse the 'az' help output and extract subcommands and options
def parse_az_help(output):
    parsed_data = {"args": [], "options": {}, "subcommands": {}}
    current_section = None
    option_description = ""
    command_description = ""

    if output == "":
        return parsed_data

    for line in output.split("\n"):
        line = line.strip()
        if '--cmd' in line:
            continue
        if "Subgroups" in line or "Commands" in line:
            current_section = "subcommands"
        elif "Arguments" in line:
            current_section = "arguments"
        elif "Global Arguments" in line:
            current_section = "global_arguments"
        elif current_section is None:
            # Capture the description for the top-level command
            command_description += line

        if current_section in ["arguments", "global_arguments"]:
            if line.startswith("--"):
                # New option found, save the previous option description
                if option_description:
                    option_parts = option_description.split(":", 1)
                    if len(option_parts) == 2:
                        option_name = option_parts[0].strip().split()[0]  # Take the first part as the option name
                        option_description = option_parts[1].strip()
                        if option_name.startswith("--"):
                            parsed_data["options"][option_name] = {"help": option_description}
                option_description = line
            else:
                # Append to the existing option description
                option_description += " " + line

        if current_section == "subcommands":
            parts = line.split(" ", 1)
            if len(parts) == 2:

                subcommand, description = parts
                subcommand = subcommand.strip()
                # Substitute "Groupaz" or "Commandaz" with "az" in the description
                description = description.replace("Groupaz", "az").replace("Commandaz", "az")
                description = listToStringWithoutBrackets(description.split(':')[-1:]).strip()

                # Check if the subcommand name consists of valid characters
                if re.match(r'^[a-zA-Z0-9_-]+$', subcommand) and not subcommand[0].isupper() and "To" not in subcommand:
                    # Skip subcommands with common words in the description
                    common_words = {'and', 'as', 'default', 'for', 'in', 'is', 'it', 'of', 'to', 'with', 'if', 'the'}
                    words = description.split()
                    if not any(word in common_words for word in words):
                        parsed_data["subcommands"][subcommand] = {"help": description, "command": subcommand, "args": [],
                                                                 "options": {}, "subcommands": {}}

    # Handle the last option description
    if option_description and option_description.startswith("--"):
        option_parts = option_description.split(":", 1)
        if len(option_parts) == 2:
            option_name = option_parts[0].strip().split()[0]  # Take the first part as the option name
            option_description = option_parts[1].strip()
            if option_name.startswith("--"):
                parsed_data["options"][option_name] = {"help": option_description}

    # Use the captured command description as the "help" field
    parsed_data["help"] = command_description.replace("Groupaz", "az").replace("Commandaz", "az")
    return parsed_data

def recursive_parse(command, stop_condition=None):
    if command in processed_commands:
        return None

    processed_commands.add(command)
    output = run_az_help(command)

    if not output:
        # Skip processing if the command returned an error
        return None

    parsed_data = parse_az_help(output)

    if command:
        last_part = command.split()[-1]
        current_data = {"command": last_part, "args": [], "options": {}, "subcommands": {}}
    else:
        current_data = {"command": "az", "args": [], "options": {}, "subcommands": {}}

    if stop_condition and stop_condition in parsed_data["options"]:
        return None
    if '--cmd' in parsed_data["options"]:
        return None

    current_data.update(parsed_data)
    for subcommand in parsed_data["subcommands"].keys():
        new_command = f"{command} {subcommand}".strip()
        sub_data = recursive_parse(new_command, stop_condition)
        if sub_data:
            current_data["subcommands"][subcommand] = sub_data

    return current_data

