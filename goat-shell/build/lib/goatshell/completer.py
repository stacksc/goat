from prompt_toolkit.completion import Completer, Completion
from fuzzyfinder import fuzzyfinder
import shlex
import json
import os
import asyncio
from pathlib import Path
from . import misc
from toolbox.misc import get_save_path, attempt_load_custom_json

from goatshell.parser import Parser  # Replace this with your actual Parser import

import logging

logger = logging.getLogger(__name__)

class GoatCompleter(Completer):
    def __init__(self, parser):
        self.inline_help = True
        self.min_input_len = 0
        self.parser = parser
        self.current_json = None  # NEW: attribute to store the current JSON
        self.goat_dict = None

        # Dictionary mapping command tokens to their descriptions
        self.command_descriptions = {
            "aliyun": "Alibaba Cloud Command Line Interface",
            "aws": "Amazon Web Services",
            "az": "Microsoft Azure Cloud Platform",
            "gcloud": "Google Cloud Platform",
            "goat": "Local Goat Application",
            "oci": "Oracle Cloud Infrastructure",
            "ibmcloud": "IBM Cloud Infrastructure",
            "ovhai": "OVH AI & Public Cloud"
            # Add more commands and descriptions as needed
        }

    def load_json(self, provider):
        # Get the JSON path using the modularized function
        user_json_path = Path(get_save_path(provider)).with_suffix('.json')
    
        # If user's custom JSON does not exist, use the default one
        if not user_json_path.exists():
            if not attempt_load_custom_json(provider):
                # If failed to load user's custom JSON, use the system default
                user_json_path = Path(os.path.dirname(os.path.realpath(__file__))) / "data" / f"{provider}.json"

        try:
            with user_json_path.open() as json_file:
                self.goat_dict = json.load(json_file)
    
            self.parser = Parser(str(user_json_path), provider)
        except Exception as ex:
            logger.error(f"Exception while loading JSON for {provider}: {ex}")
    
    def get_completions(self, document, complete_event, smart_completion=True):
        tokens = shlex.split(document.text_before_cursor.strip())
    
        if not tokens:
            # Check if a command is available before suggesting it
            available_commands = ["aliyun", "aws", "az", "gcloud", "goat", "oci", "ibmcloud", "ovhai"]
            for command in available_commands:
                if misc.is_command_available(command):
                    yield Completion(command, display=command, display_meta=self.command_descriptions.get(command, ""))
            return
    
        first_token = tokens[0]
    
        if first_token in ["oci", "aws", "gcloud", "az", "goat", "aliyun", "ibmcloud", "ovhai"] and self.current_json != first_token:
            self.load_json(first_token)
            self.current_json = first_token
    
        if len(tokens) == 1 and first_token in ["oci", "aws", "gcloud", "az", "goat", "aliyun", "ibmcloud", "ovhai"]:
            subcommands = self.parser.ast.children
            for subcmd in subcommands:
                yield Completion(subcmd.node, display=subcmd.node, display_meta=subcmd.help)
            return
    
        parsed, unparsed, suggestions = self.parser.parse_tokens(tokens)
    
        if suggestions is None:
            logger.error("suggestions are None")
            return
    
        if unparsed:
            last_token = unparsed[-1]
    
            # Check if the last token is a global option with a value
            if last_token.startswith("--") and "=" in last_token:
                global_option, option_value = last_token.split("=")
    
                # Handle the global option and value here, e.g., navigate to the root of the tree
                # Your code to handle the global option and value goes here
    
            elif last_token.startswith("--") or last_token.startswith('-'):
                if not document.text_before_cursor.endswith("--") or not document.text_before_cursor.endswith('-'):
                    option_prefix = last_token
                    completions = fuzzyfinder(option_prefix, suggestions.keys())
                    for key in completions:
                        yield Completion(key, start_position=-len(option_prefix), display=key, display_meta=suggestions.get(key, ""))
            else:
                completions = fuzzyfinder(last_token, suggestions.keys())
                for key in completions:
                    yield Completion(key, start_position=-len(last_token), display=key, display_meta=suggestions.get(key, ""))
        else:
            for key in suggestions.keys():
                yield Completion(key, display=key, display_meta=suggestions.get(key, ""))

    async def get_completions_async(self, document, complete_event):
        logger.debug("Entering get_completions")
        completions = await asyncio.to_thread(self.get_completions, document, complete_event)
        for completion in completions:
            yield completion

