#!/usr/bin/env python3
import subprocess
import re
import json

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
                if " " not in subcommand and subcommand.islower() and subcommand not in ignore_words and not any(c in subcommand for c in "!@#$%^&*()[]{};:,.<>?/\\|~`'\""):
                    top_level_commands.append(subcommand)

    return top_level_commands

def clean_output(output):
    """Remove special characters like bold and underline from the output."""
    return re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', output)

def run_az_help(command):
    try:
        print(f"Running: az {command} -h")  # Display the command being run
        output = subprocess.check_output(['az'] + command.split() + ['-h'], stderr=subprocess.STDOUT, text=True)
        return output
    except subprocess.CalledProcessError as e:
        print(f"Error running: az {command} -h")  # Display the command with an error message
        print(e.output)
        return e.output

def parse_az_help(output):
    command_tree = {
        "subcommands": {}
    }

    current_subcommand = ""

    lines = output.split('\n')
    current_section = None

    for line in lines:
        line = line.strip()

        if not line:
            continue

        if line.startswith("Command"):
            current_section = "command"
            continue
        elif line.startswith("Arguments"):
            current_section = "arguments"
            continue
        elif line.startswith("Global Arguments"):
            current_section = "global_arguments"
            continue

        if "Subgroups:" in line:
            current_section = "subcommands"
            continue

        if current_section == "command":
            parts = line.split(":", 1)
            if len(parts) == 2:
                command = parts[0].strip()
                description = parts[1].strip()
                # Skip entries that are not actual commands
                if command.isupper() and not command.startswith(" ") or "To" in command:
                    continue
                command_tree["subcommands"][command] = {"command": command, "description": description}
            else:
                current_subcommand = parts[0].strip()
        elif current_section == "subcommands":
            parts = line.split(":", 1)
            if len(parts) == 2:
                subcommand = parts[0].strip()
                description = parts[1].strip()
                if subcommand.isupper() and not subcommand.startswith(" ") or 'Door' in subcommand or 'http' in subcommand or "To" in subcommand:
                    continue
                if subcommand and subcommand != "To search AI knowledge base for examples, use":
                    current_subcommand = subcommand
                    # Skip entries that are not actual commands
                    if subcommand.isupper() and not subcommand.startswith(" "):
                        continue
                    command_tree["subcommands"][current_subcommand] = {"command": current_subcommand, "description": description}
                elif current_subcommand:
                    command_tree["subcommands"][current_subcommand]["description"] += f" {description}"

    return command_tree

az_help_output = run_az_help("")
command_tree = parse_az_help(az_help_output)

# Dump the command_tree to a JSON file
with open("az_command_tree.json", "w") as json_file:
    json.dump(command_tree, json_file, indent=2)

print("Command tree saved to 'az_command_tree.json'")

captured_output = {}
for command, details in command_tree['subcommands'].items():
    # Trim extra spaces in the command name
    clean_command = details['command'].strip().replace("[Preview]", "").strip().split(" ")[0]
    captured_output[clean_command] = []  # Initialize list for this command

    cmd = f"az {clean_command} -h"
    print(f"Running: {cmd}")

    completed_process = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    capture = False
    for line in completed_process.stdout.split("\n"):
        if line.startswith("Subgroups:") or line.startswith("Commands:"):
            capture = True
            continue  # Skip the Subgroups/Commands line itself

        if capture:
            # Stop capturing if we encounter an uppercase line
            if line.isupper():
                capture = False
                continue

            # Use regex to check if the line is in the format "word : description"
            if re.match(r"^[a-zA-Z0-9_-]+[ ]*:", line):
                command_name, description = line.split(":", 1)
                command_name = command_name.strip()
                description = description.strip()

                # Add to captured_output dictionary
                captured_output[clean_command].append({
                    "Command": command_name,
                    "Description": description
                })

# Print or process the captured_output as needed
print(captured_output)
