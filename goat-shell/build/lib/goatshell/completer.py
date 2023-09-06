from __future__ import absolute_import, unicode_literals, print_function
from subprocess import check_output
from prompt_toolkit.completion import Completer, Completion
from fuzzyfinder import fuzzyfinder
import logging
import shlex
import json
import os
import os.path
import asyncio

from goatshell.parser import Parser
logger = logging.getLogger(__name__)

class GoatCompleter(Completer):
    def __init__(self, parser):
        self.inline_help = True
        self.min_input_len = 0
        self.parser = parser

        try:
            DATA_DIR = os.path.dirname(os.path.realpath(__file__))
            DATA_PATH = os.path.join(DATA_DIR, 'data/oci.json')

            with open(DATA_PATH) as json_file:
                self.goat_dict = json.load(json_file)
            if self.goat_dict is None:
                logger.error("goat_dict is None")

            self.parser = Parser(DATA_PATH)
            if self.parser is None or not hasattr(self.parser, 'parse_tokens'):
                logger.error("Parser is not initialized correctly")

        except Exception as ex:
            logger.error(f"Exception while initializing GoatCompleter: {ex}")

    def get_completions(self, document, complete_event, smart_completion=True):
        try:
            tokens = shlex.split(document.text_before_cursor.strip())
            if tokens:
                if len(tokens) == 1 and tokens[0] == "oci":
                    if document.text_before_cursor.endswith("oci"):
                        # Add a space after "oci"
                        yield Completion("oci ", -document.cursor_position_col, display="oci ", display_meta="")
                    else:
                        # Auto-populate "oci" when the user hits Tab
                        yield Completion("oci", -document.cursor_position_col, display="oci", display_meta="")
    
                    subcommands = self.parser.ast.children
                    for subcmd in subcommands:
                        yield Completion(subcmd.node, display=subcmd.node, display_meta=subcmd.help)
                else:
                    parsed, unparsed, suggestions = self.parser.parse_tokens(tokens)
                    if suggestions is None:
                        logger.error("suggestions are None")
                        return
                    # Check if there are unparsed tokens to suggest completions for
                    if unparsed:
                        last_token = unparsed[-1]
                        if last_token.startswith("--"):
                            # Check if the document already ends with "--"
                            if not document.text_before_cursor.endswith("--"):
                                option_prefix = last_token  # Keep the '--' prefix
                                for key in fuzzyfinder(option_prefix, suggestions.keys()):
                                    # Provide completions without adding an extra '--'
                                    yield Completion(key, start_position=-len(option_prefix), display=key, display_meta=suggestions.get(key, ""))
                        else:
                            for key in fuzzyfinder(last_token, suggestions.keys()):
                                yield Completion(key, start_position=-len(last_token), display=key, display_meta=suggestions.get(key, ""))
            else:
                # Provide an initial suggestion of "oci " when the user hits TAB without typing anything
                if document.text_before_cursor.endswith("oci "):
                    yield Completion("oci ", -document.cursor_position_col, display="oci ", display_meta="")
                else:
                    # Auto-populate "oci" when the user starts typing "oci" and hits Tab
                    yield Completion("oci", -document.cursor_position_col, display="oci", display_meta="")
        except Exception as ex:
            logger.error(f"Exception in get_completions: {ex}")
    
    def evalOptions(self, root, parsed, unparsed):
        logger.debug("parsing options at tree: %s with p:%s, u:%s", root.node, parsed, unparsed)
        suggestions = dict()
        token = unparsed.pop().strip()
    
        parts = token.partition('=')
        if parts[-1] != '':  # parsing for --option=value type input
            token = parts[0]
    
        allFlags = root.localFlags + self.globalFlags
        for flag in allFlags:
            if flag.name == token.lstrip('-'):  # Remove the leading '-' character
                logger.debug("matched token: %s with flag: %s", token, flag.name)
                parsed.append(token)
                if self.peekForOption(unparsed):  # recursively look for further options
                    parsed, unparsed, suggestions = self.evalOptions(root, parsed, unparsed[:])
                break
        else:
            logger.debug("no flags match, returning allFlags suggestions")
            for flag in allFlags:
                suggestions[flag.name] = flag.helptext
    
        if suggestions:  # incomplete parse, replace token
            logger.debug("incomplete option: %s provided. returning suggestions", token)
            unparsed.append(token)
        return parsed, unparsed, suggestions

    async def get_completions_async(self, document, complete_event):
        logger.debug("Entering get_completions")
        # Wrap synchronous method in an async call.
        completions = await asyncio.to_thread(self.get_completions, document, complete_event)
        for completion in completions:
            yield completion
