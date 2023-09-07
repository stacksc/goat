from __future__ import absolute_import, unicode_literals, print_function
import json
import os

import logging
logger = logging.getLogger(__name__)

class Option(object):
    def __init__(self, name, helptext):
        self.name = name
        self.helptext = helptext

class CommandTree(object):
    def __init__(self, node=None, helptext=None, children=None, localFlags=None):
        self.node = node
        self.help = helptext
        self.children = children if children else list()
        self.localFlags = localFlags if localFlags else list()

    def __str__(self):
        return "Node: %s, Help: %s\n Flags: %s\n Children: %s" % (self.node, self.help, self.localFlags, self.children)

class Parser(object):
    def __init__(self, apiFile):
        try:
            self.json_api = apiFile
            self.schema = dict()
            self.globalFlags = list()
            with open(self.json_api) as api:
                self.schema = json.load(api)
            self.ast = CommandTree("oci")
            oci_schema = self.schema.get("oci")
            if oci_schema is None:
                logger.error("oci is not in the schema")
            else:
                self.ast = self.build(self.ast, oci_schema)
        except Exception as ex:
            logger.error(f"Exception while initializing Parser: {ex}")

    def get_top_level_commands(self):
        return [node.node for node in self.ast.children]

    def build(self, root, schema):
        try:
            if schema.get("subcommands") and schema["subcommands"]:
                for subcmd, childSchema in schema["subcommands"].items():
                    child = CommandTree(node=subcmd)
                    child = self.build(child, childSchema)
                    root.children.append(child)
            # Add options and arguments to the current node (root)
            try:
                for name, desc in schema.get("options", {}).items():
                    root.localFlags.append(Option(name, desc["help"]))
            except:
                pass
            try:
                for arg in schema.get("args", []):
                    node = CommandTree(node=arg)
                    root.children.append(node)
            except:
                pass
            root.help = schema.get("help")
            return root
        except:
            pass

    def print_tree(self, root, indent=0):
        indentter = '{:>{width}}'.format(root.node, width=indent)
        print(indentter)
        for child in root.children:
            self.print_tree(root=child, indent=indent+2)

    def parse_tokens(self, tokens):
        if len(tokens) == 1:
            return list(), tokens, {"oci": self.ast.help}
        else:
            tokens.reverse()
        parsed, unparsed, suggestions = self.treewalk(self.ast, parsed=list(), unparsed=tokens)
        if not suggestions and unparsed:
            logger.debug("unparsed tokens remain, possible value encountered")
            unparsed.pop()
            parsed.reverse()
            unparsed.extend(parsed)
            logger.debug("resuming treewalk with tokens: %s", unparsed)
            return self.treewalk(self.ast, parsed=list(), unparsed=unparsed)
        else:
            return parsed, unparsed, suggestions

    def treewalk(self, root, parsed, unparsed):
        suggestions = dict()
        if not unparsed:
            logger.debug("no tokens left unparsed. returning %s, %s", parsed, suggestions)
            return parsed, unparsed, suggestions
        token = unparsed.pop().strip()
        logger.debug("begin parsing at %s w/ tokens: %s", root.node, unparsed)

        if root.node == token:
            logger.debug("root node: %s matches next token:%s", root.node, token)
            parsed.append(token)

            if self.peekForOption(unparsed):  # check for localFlags and globalFlags
                logger.debug("option(s) upcoming %s", unparsed)
                parsed_opts, unparsed, suggestions = self.evalOptions(root, list(), unparsed[:])
                if parsed_opts:
                    logger.debug("parsed option(s): %s", parsed_opts)
                    parsed.extend(parsed_opts)

            if unparsed and not self.peekForOption(unparsed):  # unparsed bits without options
                logger.debug("begin subtree %s parsing", root.node)
                for child in root.children:
                    parsed_subtree, unparsed, child_suggestions = self.treewalk(child, list(), unparsed[:])
                    if parsed_subtree:  # subtree returned further parsed tokens
                        parsed.extend(parsed_subtree)
                        logger.debug("subtree at: %s has matches. %s, %s", child.node, parsed, unparsed)
                        suggestions.update(child_suggestions)
                        break
                else:
                    logger.debug("no matches in subtree: %s. returning children as suggestions", root.node)
                    for child in root.children:
                        suggestions[child.node] = child.help
        else:
            logger.debug("no token or option match. Current node: %s, Token: %s", root.node, token)
            unparsed.append(token)

        logger.debug("current state - parsed: %s, unparsed: %s, suggestions: %s", parsed, unparsed, suggestions)
        return parsed, unparsed, suggestions

    def peekForOption(self, unparsed):
        if unparsed and unparsed[-1].startswith("--"):
            return True
        return False

    def evalOptions(self, root, parsed, unparsed):
        logger.debug("parsing options at tree: %s with p:%s, u:%s", root.node, parsed, unparsed)
        suggestions = dict()
    
        while unparsed:
            token = unparsed.pop().strip()
    
            parts = token.partition('=')
            if parts[-1] != '':  # parsing for --option=value type input
                token = parts[0]
    
            allFlags = root.localFlags + self.globalFlags
            found = False
    
            for flag in allFlags:
                if flag.name == token:
                    logger.debug("matched token: %s with flag: %s", token, flag.name)
                    parsed.append(token)
                    found = True
                    break
    
            if not found:
                logger.debug("no flags match for token: %s", token)
                unparsed.append(token)
                break
    
        for flag in allFlags:
            suggestions[flag.name] = flag.helptext
    
        logger.debug("options parsed: %s, remaining unparsed: %s", parsed, unparsed)
        return parsed, unparsed, suggestions
    
if __name__ == '__main__':
    oci_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/oci.json')
    parser = Parser(oci_json_path)
    p, _, s = parser.treewalk(parser.ast, parsed=list(), unparsed=['--', 'oci'])
    print(p, s)
