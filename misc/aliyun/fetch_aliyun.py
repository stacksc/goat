#!/usr/bin/env python3
#!/usr/bin/env python3
import subprocess
import json
import re

def strip_ansi_codes(s):
    return re.sub(r'\x1b\[.*?m', '', s)

def get_aliyun_top_level_options():
    print("EXECUTING: aliyun --help")
    completed_process = subprocess.run(['aliyun', '--help'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    lines = strip_ansi_codes(completed_process.stdout.strip()).split('\n')
    start_line = [i for i, line in enumerate(lines) if "Flags:" in line][0] + 1
    options = {}
    for line in lines[start_line:]:
        parts = line.strip().split()
        if len(parts) >= 1:
            option_name = parts[0]
            options[option_name] = {}
    return options

def get_aliyun_services():
    print("EXECUTING: aliyun --help")
    completed_process = subprocess.run(['aliyun', '--help'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    lines = strip_ansi_codes(completed_process.stdout.strip()).split('\n')
    start_line = [i for i, line in enumerate(lines) if "Products:" in line][0] + 1
    services = [strip_ansi_codes(line.split()[0].strip()) for line in lines[start_line:] if line.strip() and "Use `aliyun --help` for more information." not in line]
    return services

def get_api_list_for_service(service):
    print(f"EXECUTING: aliyun {service} help")
    completed_process = subprocess.run([f'aliyun', f'{service}', 'help'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    lines = strip_ansi_codes(completed_process.stdout.strip()).split('\n')
    start_indices = [i for i, line in enumerate(lines) if "Available Api List:" in line]
    if not start_indices:
        return []

    start_line = start_indices[0] + 1
    api_lines = [strip_ansi_codes(line.strip().split(':')[0].strip()) for line in lines[start_line:] if not line.startswith("Run ") and "Use `aliyun --help` for more information." not in line]

    api_with_options = {}
    for api in api_lines:
        print(f"EXECUTING: aliyun {service} {api} help")
        # Run help command for each API to get its options
        completed_process = subprocess.run([f'aliyun', f'{service}', f'{api}', 'help'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        api_help_lines = strip_ansi_codes(completed_process.stdout.strip()).split('\n')

        param_start_indices = [i for i, line in enumerate(api_help_lines) if "Parameters:" in line]
        options = {}
        if param_start_indices:
            param_start_line = param_start_indices[0] + 1
            for line in api_help_lines[param_start_line:]:
                parts = line.strip().split()
                if len(parts) >= 3:
                    option_name, option_type, option_req = parts[:3]
                    options[option_name] = {
                        "name": option_name,
                        "type": option_type,
                        "required": option_req == "Required",
                        "help": ""
                    }
        api_with_options[api] = options

    return api_with_options

# Main program
top_level_options = get_aliyun_top_level_options()

command_tree = {
    "aliyun": {
        "args": [],
        "command": "aliyun",
        "help": "Alibaba Cloud command line interface, with support for multiple services.",
        "options": top_level_options,
        "subcommands": {}
    }
}

services = get_aliyun_services()
for service in services:
    clean_service = service.strip()
    command_tree["aliyun"]["subcommands"][clean_service] = {
        "command": clean_service,
        "subcommands": {}
    }
    apis_with_options = get_api_list_for_service(service)
    for api, options in apis_with_options.items():
        clean_api = api.strip()
        if not clean_api:
            continue
        command_tree["aliyun"]["subcommands"][clean_service]["subcommands"][clean_api] = {
            "command": clean_api,
            "subcommands": {},
            "options": options,
            "help": ""
        }

# Write to file
with open("aliyun_command_tree.json", "w") as f:
    json.dump(command_tree, f, indent=4)

