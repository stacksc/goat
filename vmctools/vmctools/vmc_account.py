import click, json
from .vmcclient import vmc
from .vmc_misc import get_operator_context
from toolbox.logger import Log
from configstore.configstore import Config

CONFIG = Config('csptools')

@click.group('account', help='manage AWS accounts used in VMC', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def account(ctx):
    ctx.ensure_object(dict)
    ctx.obj['profile'] = ctx.parent.params['user_profile']
    pass

@account.command('import', help='import AWS account into VMC', context_settings={'help_option_names':['-h','--help']})
@click.argument('aws_account_number', required=True)
@click.option('-o', '--daily_org', help='override org name/id for daily checks', required=False, default=None)
@click.option('-t', '--payer_account_type', help='overrife default payer account type', required=False, default='INTERNAL')
@click.option('-r', '--role_name', help='override role name for daily checks', required=False, default=None)
@click.pass_context
def account_import(ctx, aws_account_number, daily_org, payer_account_type, role_name):
    auth, user_profile = get_operator_context(ctx)
    VMC = vmc(auth, user_profile)
    if daily_org is not None:
        DALY_ORG = daily_org
    else:
        DAILY_ORG = VMC.CONFIG.get_var('daily_org', 'config', 'DAILY_ORG_ID', ctx['profile'])
    if role_name is not None:
        ROLE_NAME = role_name
    else:
        ROLE_NAME = VMC.CONFIG.get_var('daily_role_name', 'config', 'PAYER_ROLE_LABEL', ctx['profile'])
    ROLE_ARN=f"arn:aws-us-gov:iam::{aws_account_number}:role/{ROLE_NAME}"
    RESULT = VMC.account_import(aws_account_number, DAILY_ORG, payer_account_type, ROLE_ARN)
    if RESULT == []:
        Log.critical('empty response from VMC. something went wrong. check UI/logs')
    else:
        Log.info(json.dumps(RESULT, indent=2))

@account.command('associate', help='associate an AWS account with a VMC org', context_settings={'help_option_names':['-h','--help']})
@click.argument('aws_account_id', required=True)
@click.argument('org_id', required=True)
@click.option('-r', '--raw', 'raw', help="display raw json; dont reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def account_associate(ctx, aws_account_id, org_id, raw):
    auth, user_profile = get_operator_context(ctx)
    VMC = vmc(auth, user_profile)
    RESULT = VMC.account_associate(aws_account_id, org_id, raw)
    if RESULT == []:
        Log.critical('empty response from VMC. something went wrong. check UI/logs')
    else:
        Log.info(json.dumps(RESULT, indent=2))

@account.command('disassociate', help='disassociate an AWS account with a VMC org', context_settings={'help_option_names':['-h','--help']})
@click.argument('aws_account_id', required=True)
@click.argument('org_id', required=True)
@click.option('-r', '--raw', 'raw', help="display raw json; dont reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def account_disassociate(ctx, aws_account_id, org_id, raw):
    auth, user_profile = get_operator_context(ctx)
    VMC = vmc(auth, user_profile)
    RESULT = VMC.account_disassociate(aws_account_id, org_id, raw)
    if RESULT == []:
        Log.critical('empty response from VMC. something went wrong. check UI/logs')
    else:
        Log.info(json.dumps(RESULT, indent=2))

@account.command('delete', help='delete an AWS account from VMC', context_settings={'help_option_names':['-h','--help']})
@click.argument('aws_account_id', required=True)
@click.pass_context
def account_delete(ctx, aws_account_id):
    auth, user_profile = get_operator_context(ctx)
    VMC = vmc(auth, user_profile)
    RESULT = VMC.account_delete(aws_account_id)
    if RESULT == []:
        Log.critical('empty response from VMC. something went wrong. check UI/logs')
    else:
        Log.info(json.dumps(RESULT, indent=2))

@account.group('show', help='show info about AWS account(s)', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def account_show(ctx):
    pass

def account_show_details(ctx, aws_account_id, raw):
    auth, user_profile = get_operator_context(ctx)
    VMC = vmc(auth, user_profile)
    RESULT = VMC.account_show_details(aws_account_id, raw)
    if RESULT == []:
        Log.critical('empty response from VMC. something went wrong. check UI/logs')
    else:
        Log.info(json.dumps(RESULT, indent=2))

@account_show.command('all', help='show all AWS accounts added to VMC', context_settings={'help_option_names':['-h','--help']})
@click.option('-s', '--state', 'account_state', help='only list accounts in a specific state', type=click.Choice(['ACTIVE', 'DELETED']), default=None)
@click.option('-n', '--numbers', 'numbers_only', help='limit the output to only aws account numbers', is_flag=True, default=False)
@click.option('-r', '--raw', 'raw', help="display raw json; dont reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def account_show_all(ctx, account_state, numbers_only, raw):
    auth, user_profile = get_operator_context(ctx)
    VMC = vmc(auth, user_profile)
    RESULT = VMC.account_show_all(account_state, numbers_only, raw)
    Log.info(json.dumps(RESULT, indent=2))

