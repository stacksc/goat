import click
from  configstore.configstore_ctrl import _show as configshow
from .ec2 import _show as ec2show, orphaned_ebs_volumes as orphans, orphaned_ebs_snap_report as snap_report
from .s3 import _show as s3show
from .aws_config import AWSconfig
from .iam import get_latest_profile

@click.command(help='display configuration data for awstools and awscli')
@click.argument('target', required=True, type=click.Choice(['all_config', 'buckets', 'instances', 'public_ips', 'regions', 'all_cached', 'aws_config', 'aws_credentials', 'orphaned_ebs']))
@click.pass_context
def show(ctx, target):
    aws_profile_name = ctx.obj['PROFILE']
    aws_region_name = get_region(ctx, aws_profile_name)
    if aws_profile_name is None:
        aws_profile_name = 'default'
    if target == 'buckets':
        s3show('buckets', aws_profile_name, aws_region_name)
    if target == 'instances':
        ec2show('instances', aws_profile_name, aws_region_name, display=True)
    if target == 'public_ips':
        ec2show('public_ips', aws_profile_name, aws_region_name, display=True)
    if target == 'regions':
        ec2show('regions', aws_profile_name, aws_region_name, display=True)
    if target == 'all_cached':
        ec2show('all', aws_profile_name, aws_region_name, display=True)
    if target == 'all_config':
        configshow('awstools', aws_profile_name)
    if target == 'orphaned_ebs' or target == 'all':
        orphans(aws_profile_name)
        snap_report(aws_profile_name)
    if target == 'aws_config':
        AWS_CONFIG = AWSconfig()
        AWS_CONFIG.display('config', aws_profile_name)
    if target == 'aws_credentials':
        AWS_CONFIG = AWSconfig()
        AWS_CONFIG.display('creds', aws_profile_name)

def get_region(ctx, aws_profile_name):
    AWS_REGION = ctx.obj['REGION']
    if not AWS_REGION:
        AWS_REGION = S3.get_region_from_profile(aws_profile_name)
    return AWS_REGION
