import json
import os
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)

class Option:
    def __init__(self, name, helptext):
        self.name = name
        self.helptext = helptext

class CommandTree:
    def __init__(self, node=None, helptext=None, children=None, local_flags=None):
        self.node = node
        self.help = helptext
        self.children = children if children else []
        self.local_flags = local_flags if local_flags else []

class Parser:
    def __init__(self, apiFile, root_name):
        try:
            self.json_api = apiFile
            self.schema = dict()
            self.global_flags = list()
            self.root_name = root_name
            with open(self.json_api) as api:
                self.schema = json.load(api)
            self.ast = CommandTree(root_name)  # Set to dynamic root name
            root_schema = self.schema.get(root_name)
            if root_schema is None:
                logger.error(f"{root_name} is not in the schema")
            else:
                self.ast = self.build(self.ast, root_schema)
        except Exception as ex:
            logger.error(f"Exception while initializing Parser: {ex}")


    def set_api_file(self, api_file):
        self.json_api = api_file

        with open(self.json_api) as api:
            self.schema = json.load(api)

        api_schema = self.schema.get(self.json_api.split('/')[-1].split('.')[0])

        if api_schema:
            self.ast = self.build(self.ast, api_schema)
        else:
            print(f"{self.json_api.split('/')[-1].split('.')[0]} is not in the schema")

    def get_top_level_commands(self):
        return [node.node for node in self.ast.children]

    def build(self, root, schema):
        try:
            if schema.get("subcommands") and schema["subcommands"]:
                for subcmd, childSchema in schema["subcommands"].items():
                    child = CommandTree(node=subcmd)
                    child = self.build(child, childSchema)
                    root.children.append(child)
    
            for name, desc in schema.get("options", {}).items():
                root.local_flags.append(Option(name, desc.get("help") or desc.get("description")))
    
            for arg in schema.get("args", []):
                node = CommandTree(node=arg)
                root.children.append(node)
    
            root.help = schema.get("help") or schema.get("description")
            return root
        except:
            pass
    
    def parse_tokens(self, tokens):
        if len(tokens) == 1:
            return [], tokens, {"oci": self.ast.help}
        else:
            tokens.reverse()

        parsed, unparsed, _ = self.treewalk(self.ast, parsed=[], unparsed=tokens)

        current_node = self.get_node_from_tokens(parsed)
        suggestions = {child.node: child.help for child in current_node.children}
        suggestions.update({flag.name: flag.helptext for flag in current_node.local_flags})

        if not suggestions and unparsed:
            unparsed.pop()
            parsed.reverse()
            unparsed.extend(parsed)
            return self.treewalk(self.ast, parsed=[], unparsed=unparsed)
        else:
            return parsed, unparsed, suggestions

    def get_node_from_tokens(self, parsed_tokens):
        current_node = self.ast

        for token in parsed_tokens:
            if token.startswith("--") or token.startswith("-"):  # Skip options
                continue
            for child in current_node.children:
                if child.node == token:
                    current_node = child
                    break
        return current_node

    def treewalk(self, root, parsed, unparsed):
        suggestions = {}

        if not unparsed:
            return parsed, unparsed, suggestions

        token = unparsed.pop().strip()

        if root.node == token:
            parsed.append(token)

            if self.peek_for_option(unparsed):
                parsed_opts, unparsed, suggestions = self.eval_options(root, [], unparsed[:])
                if parsed_opts:
                    parsed.extend(parsed_opts)

            if unparsed and not self.peek_for_option(unparsed):
                for child in root.children:
                    parsed_subtree, unparsed, child_suggestions = self.treewalk(child, [], unparsed[:])
                    if parsed_subtree:
                        parsed.extend(parsed_subtree)
                        suggestions.update(child_suggestions)
                        break
                else:
                    for child in root.children:
                        suggestions[child.node] = child.help
        else:
            unparsed.append(token)

        return parsed, unparsed, suggestions

    def peek_for_option(self, unparsed):
        if unparsed and (unparsed[-1].startswith("--") or unparsed[-1].startswith("-")):
            return True
        return False

    def eval_options(self, root, parsed, unparsed):
        suggestions = {}

        while unparsed:
            token = unparsed.pop().strip()

            parts = token.partition('=')
            if parts[-1] != '':  # parsing for --option=value type input
                token = parts[0]

            all_flags = root.local_flags + self.global_flags
            found = False

            for flag in all_flags:
                if flag.name == token:
                    parsed.append(token)
                    found = True
                    break

            if not found:
                unparsed.append(token)
                break

        for flag in all_flags:
            suggestions[flag.name] = flag.helptext

        return parsed, unparsed, suggestions

