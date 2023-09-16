import click, os, json
from toolbox.logger import Log
from toolbox.misc import set_terminal_width
from .iam import get_latest_profile
import .extract_commands

@click.group('extract', invoke_without_command=True, help='extract the command tree for AWS CLI', context_settings={'help_option_names':['-h','--help'], 'max_content_width': set_terminal_width()})
@click.pass_context
def extract(ctx):
    pass

@extract.command(help='manually refresh the AWS CLI command tree', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def commands(ctx):
    aws_output = extract_commands.get_aws_help_output()
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
        aws_service_output = get_aws_help_output(service)
        if aws_service_output:
            commands, options = extract_elements_for_service(aws_service_output)
            description = extract_description(aws_service_output)
            aws_data["aws"]["subcommands"].update({service: {"commands": commands, "description": description}})
            save_to_json(aws_data, 'aws_command_data.json')

            # Fetch options for each command
            for command, command_info in commands.items():
                aws_command_output = get_aws_help_output(service, command)
                _, command_options = extract_elements_for_service(aws_command_output)
                command_description = extract_description(aws_command_output)
                command_info["options"] = command_options
                command_info["description"] = command_description
                save_to_json(aws_data, 'aws_command_data.json')

