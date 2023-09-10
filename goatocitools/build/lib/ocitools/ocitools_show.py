import click
from configstore.configstore_ctrl import _show as configshow
from .oci_config import OCIconfig
from .iam import get_latest_profile

@click.command(help='display configuration data for ocitools and ocicli')
@click.argument('target', required=True, type=click.Choice(['all_config', 'oci_config' ]))
@click.pass_context
def show(ctx, target):
    profile_name = ctx.obj['PROFILE'].lower()
    if profile_name is None:
        profile_name = 'DEFAULT'
    if target == 'all_config':
        configshow('ocitools', profile_name)
    if target == 'oci_config':
        OCI_CONFIG = OCIconfig()
        OCI_CONFIG.display('config', profile_name)
