import click
from toolbox.logger import Log
from .configstore import Config
from toolbox.click_complete import complete_configstore_names
from toolbox import misc
from awstools.aws_config import AWSconfig
from ocitools.oci_config import OCIconfig
from goatshell.goatshell import get_all_configstore_names

all_stores = get_all_configstore_names()
MESSAGE="Config Client" + misc.MOVE + "Current Profile: " + misc.GREEN + misc.UNDERLINE + 'N/A' + misc.RESET

@click.group(help=MESSAGE, context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-p', '--profile', help="name of the profile to use", required=False, default=None)
@click.pass_context
def cli(ctx, profile):
    ctx.ensure_object(dict)
    ctx.obj['PROFILE'] = profile
    pass

@cli.command(help="show records stored in a configstore; you can use profile and record names to narrow down the results", context_settings={'help_option_names':['-h','--help']})
@click.option('-n', '--name', help="name of the configstore to use", required=True, type=click.Choice(all_stores))
@click.pass_context
def show(ctx, name):
    profile = ctx.obj['PROFILE']
    configstore_name = ''.join(name)
    all_stores = get_all_configstore_names()
    if configstore_name in all_stores:
        _show(configstore_name, profile)
    else:
        Log.warn(f'configuration store {configstore_name} does not exist.')
        exit(-1)

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

if __name__ == "__main__":
    cli(ctx)
