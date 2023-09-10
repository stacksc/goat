import click
from toolbox.logger import Log
from .configstore import Config
from toolbox.click_complete import complete_configstore_names
from toolbox import misc
from awstools.aws_config import AWSconfig
from ocitools.oci_config import OCIconfig

MESSAGE="Config Client" + misc.MOVE + "Current Profile: " + misc.GREEN + misc.UNDERLINE + 'N/A' + misc.RESET

@click.group(help=MESSAGE, context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-p', '--profile', help="name of the profile to use", required=False, default=None)
@click.pass_context
def cli(ctx, profile):
    ctx.ensure_object(dict)
    ctx.obj['PROFILE'] = profile
    pass

@cli.group(help="add data to a configstore", context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def add(ctx):
    pass

@cli.group(help="delete data saved in a configstore", context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def delete(ctx):
    pass

@cli.command(help="show records stored in a configstore; you can use profile and record names to narrow down the results", context_settings={'help_option_names':['-h','--help']})
@click.argument('configstore_name', nargs=-1, required=True, type=str, shell_complete=complete_configstore_names)
@click.pass_context
def show(ctx, configstore_name):
    profile = ctx.obj['PROFILE']
    configstore_name = ''.join(configstore_name)
    _show(configstore_name, profile)
    
def _show(configstore_name, profile_name=None):
    CONFIG = Config(configstore_name)
    RESULT = None
    if profile_name is not None:
        try:
            RESULT = CONFIG.display_profile(profile_name)
        except:
            pass
        if configstore_name == 'awstools' and profile_name != 'latest':
            AWS_CONFIG = AWSconfig()
            CONFIG.display_configstore()
            AWS_CONFIG.display('config', profile_name)
            AWS_CONFIG.display('creds', profile_name)
        elif configstore_name == 'ocitools':
            OCI_CONFIG = OCIconfig()
            OCI_CONFIG.display('config', profile_name)
    else:
        try:
            RESULT = CONFIG.display_configstore()
        except:
            pass
        if configstore_name == 'awstools':
            AWS_CONFIG = AWSconfig()
            AWS_CONFIG.display('config')
            AWS_CONFIG.display('creds')
        elif configstore_name == 'ocitools':
            OCI_CONFIG = OCIconfig()
            OCI_CONFIG.display('config', profile_name)
    return RESULT

@delete.command('profile', help="delete an entire profile stored in a configstore", context_settings={'help_option_names':['-h','--help']})
@click.argument('configstore_name', nargs=-1, required=True, type=str, shell_complete=complete_configstore_names)
@click.pass_context
def delete_profile(ctx, configstore_name):
    profile_name = ctx.obj['PROFILE']
    if configstore_name is not None:
        profile_name = misc.convertTuple(configstore_name)
    if profile_name is None:
        Log.critical("please provide a profile name")
    CONFIG = Config(configstore_name)
    RESULT = CONFIG.clear_profile(profile_name)
    return RESULT

@delete.command('property', help="delete a record stored in a configstore", context_settings={'help_option_names':['-h','--help']})
@click.argument('configstore_name', nargs=-1, required=True, type=str, shell_complete=complete_configstore_names)
@click.argument('record_name', required=True, default=None)
@click.pass_context
def delete_profile_record(ctx, configstore_name, record_name):
    profile_name = ctx.obj['PROFILE']
    if configstore_name is not None:
        profile_name = misc.convertTuple(configstore_name)
    if profile_name is None or record_name is None:
        Log.critical("please provide a profile name and a record name for removal")
    CONFIG = Config(configstore_name)
    RESULT = CONFIG.clear_config(profile_name, record_name)
    return RESULT

@add.command('profile', help="add a profile to a configstore", context_settings={'help_option_names':['-h','--help']})
@click.argument('configstore_name', nargs=-1, required=True, type=str, shell_complete=complete_configstore_names)
@click.pass_context
def add_profile(ctx, configstore_name):
    profile_name = ctx.obj['PROFILE']
    if configstore_name is not None:
        profile_name = misc.convertTuple(configstore_name)
    CONFIG = Config(configstore_name)
    RESULT = CONFIG.create_profile(profile_name)
    return RESULT

@add.command('property', help="add a record to a profile stored in a configstore", context_settings={'help_option_names':['-h','--help']})
@click.argument('configstore_name', nargs=-1, required=True, type=str, shell_complete=complete_configstore_names)
@click.argument('profile_name', required=True, default=None)
@click.argument('record_name', required=True, default=None)
@click.argument('record_value', required=True)
@click.pass_context
def add_profile_record(ctx, configstore_name, profile_name, record_name, record_value):
    profile_name = ctx.obj['PROFILE']
    if profile_name is None:
        Log.critical("please provide a profile name")
    CONFIG = Config(configstore_name)
    RESULT = CONFIG.update_config(record_value, record_name, profile_name)
    return RESULT

if __name__ == "__main__":
    cli(ctx)
