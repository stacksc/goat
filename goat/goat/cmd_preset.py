import click, json, os
from toolbox.logger import Log
from configstore.configstore import Config
from .presets.jenkins import jenkins_preset
from toolbox.misc import set_terminal_width, detect_environment

@click.group(help='manage built-in and custom presets', context_settings={'help_option_names':['-h','--help'], 'max_content_width': set_terminal_width()})
@click.option('-d', '--debug', help="0 = no output, 1 = default, 2 = debug on", default='1', type=click.Choice(['0', '1', '2']))
def preset(debug):
    log = Log('goat.log', debug)
    pass

@preset.command(help='add new data:key pairs to presets', context_settings={'help_option_names':['-h','--help'], 'max_content_width': set_terminal_width()})
@click.argument('type', required=True, type=click.Choice(['config', 'metadata']))
@click.argument('module', required=True)
@click.argument('data_pairs', nargs=-1, type=str, required=True)
def add(type, module, data_pairs):
    for DATA_PAIR in data_pairs:
        DATA_PAIR = DATA_PAIR.split(':',1)
        KEY = DATA_PAIR[0]
        VALUE = DATA_PAIR[1]
        if type == 'config':
            RESULT = Config(module).update_config(VALUE, KEY, 'preset')
        elif type == 'metadata':
            RESULT = Config(module).update_metadata(VALUE, KEY, 'preset')
        else:
            RESULT = False
    return RESULT


#@preset.command(help='load built-in presets for enabled modules', context_settings={'help_option_names':['-h','--help'], 'max_content_width': set_terminal_width()})
def init():
    # put any tools in here that shouldn't use presets in prod
    if detect_environment() == 'non-gc':
        RESULT = Config('jenkinstools').create_preset(jenkins_preset)
    else:
        RESULT = False
    return RESULT

@preset.command(help='delete given keys from presets', context_settings={'help_option_names':['-h','--help'], 'max_content_width': set_terminal_width()})
@click.argument('type', required=True, type=click.Choice(['config', 'metadata']))
@click.argument('module', required=True)
@click.argument('key_names', nargs=-1, type=str, required=True)
def delete(type, module, key_names):
    for KEY in key_names:
        if type == 'config':
            RESULT = Config(module).clear_config(KEY, 'preset')
        elif type == 'metadata':
            RESULT = Config(module).clear_metadata(KEY, 'preset')
        else:
            RESULT =  False
    return RESULT

@preset.command(help='clear preset attached to a specific module', context_settings={'help_option_names':['-h','--help'], 'max_content_width': set_terminal_width()})
@click.argument('module')
def clear(module):
    RESULT = Config(module).clear_preset()
    return RESULT

@preset.command(help='load a preset from a given file and upload it to a specific module', context_settings={'help_option_names':['-h','--help'], 'max_content_width': set_terminal_width()})
@click.argument('module')
@click.argument('preset_file', type=click.File('rb'))
def load(module, preset_file):
    PRESET_DATA = json.loads(preset_file.read())
    RESULT = Config(module).create_preset(PRESET_DATA)
    return RESULT

