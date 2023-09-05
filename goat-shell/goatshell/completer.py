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
    def __init__(self):
        self.inline_help = True
        min_input_len = 0

        try:
            DATA_DIR = os.path.dirname(os.path.realpath(__file__))
            DATA_PATH = os.path.join(DATA_DIR, 'data/oci.json')

            with open(DATA_PATH) as json_file:
                self.goat_dict = json.load(json_file)
            self.parser = Parser(DATA_PATH)
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
                _, _, suggestions = self.parser.parse_tokens(tokens)
                if suggestions is None:
                    logger.error("suggestions are None")
                    return
                for key in fuzzyfinder(document.get_word_before_cursor(), suggestions.keys()):
                    yield Completion(key, -len(document.get_word_before_cursor()), display=key, display_meta=suggestions.get(key, ""))
            else:
                for initial_suggestion in ['oci']:
                    yield Completion(initial_suggestion)

        except Exception as ex:
            logger.error(f"Exception in get_completions: {ex}")

    async def get_completions_async(self, document, complete_event):
        logger.debug("Entering get_completions")
        # Wrap synchronous method in an async call.
        completions = await asyncio.to_thread(self.get_completions, document, complete_event)
        for completion in completions:
            yield completion
