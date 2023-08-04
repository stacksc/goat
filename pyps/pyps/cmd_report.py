import click, json, tabulate, re
from jiratools.issue import extract_data_from_issue, review_issue, get_review_status, add_comment as comment
from jiratools.search import run_jql_query
from awstools.s3client import S3client
from toolbox.logger import Log
from toolbox.click_complete import complete_profile_names, complete_jira_profiles
from toolbox import misc

MESSAGE="VMware Report Module" + misc.MOVE + "Current Profile: " + misc.GREEN + misc.UNDERLINE + 'N/A' + misc.RESET
@click.group(help=MESSAGE, context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
def report():
    pass

@report.command('image-promotion', help='attempt to pull Transaction-ID from a given Jira ticket and use it to verify image promotion status', context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()})
@click.argument('jira_issue_keys', nargs=-1, type=str, required=True)
@click.option('-j', '--jira_profile', help='specify the name of jiraclient profile to use', default='default', required=False, shell_complete=complete_jira_profiles, show_default=True)
@click.option('-k', '--data_key', help='override the text used to identify txid in ticket description', default='Transaction-ID', required=False, show_default=True)
@click.option('-a', '--aws_profile', help='specify the name of awstools profile to use', type=str, required=False, default='vmcdelta', shell_complete=complete_profile_names, show_default=True)
@click.option('-b', '--bucket_name', help='override default bucket name to lookup', default='com.vmw.delta.us-gov-west-1.stg.repo.secured', required=False, show_default=True)
@click.option('-r', '--review', help="DISABLED | VMC Review & set to Yes or No based on promotion status", required=False, default=None, type=click.Choice(['Yes', 'No']))
@click.option('-l', '--launch', help="launch issue in browser for VMC Ops Review & ERB preparation", is_flag=True, default=False, required=False)
@click.option('-R', '--raw', help='dont include data from jira search and diplay just raw json result', is_flag=True, default=False, required=False)
def image_promotion(jira_issue_keys, data_key, jira_profile, aws_profile, bucket_name, raw, review, launch):
    try:
        DATA = extract_data_from_issue(jira_issue_keys, data_key, True, jira_profile)
        if DATA is None or len(DATA) == 0:
            Log.info('value for Transaction-ID not found in specified Jira ticket(s)')
    except:
        Log.info('unable to extract data from issue or issue key not found')
    S3 = S3client(aws_profile, in_boundary=False)
    if raw:
        RESULT = {}
    else:
        RESULT = []
    for ISSUE_KEY in jira_issue_keys:
        try:
            STATUS = get_review_status(ISSUE_KEY, jira_profile)
        except:
            STATUS = 'N/A'
        try:
            TRANSACTION_ID = DATA[ISSUE_KEY]
        except:
            TRANSACTION_ID = None
        if TRANSACTION_ID and TRANSACTION_ID != 'UNKNOWN' and TRANSACTION_ID != None:
            TRANSACTION_ID = escape_ansi(TRANSACTION_ID).strip()
            KEY = f"{TRANSACTION_ID}/files/artifacts-xfr.properties"
            try:
                TAGGING = S3.get_object_tagging(bucket_name, KEY)
            except:
                TAGGING = None
            if TAGGING:
                if not 'TagSet' in TAGGING:
                    Log.warn(f'failed to get object tagging from S3 for txid {TRANSACTION_ID} and jira {ISSUE_KEY}' )
                    continue
            else:
                Log.warn(f'failed to get object tagging from S3 for txid {TRANSACTION_ID} and jira {ISSUE_KEY}' )
                continue
            OUT = ""
            for SET in TAGGING['TagSet']:
                OUT = f"{OUT}{SET['Key']},{SET['Value']} "
            if raw:
                RESULT[ISSUE_KEY] = OUT
            else:
                try:
                    SEARCH_DATA = run_jql_query(None,[ISSUE_KEY],None,None,None,None,None,None,None,None,False,False,False,False,None,False,True,jira_profile,True)
                    LAUNCHER = find_url(SEARCH_DATA[0]['launcher'])
                    LAUNCHER = re.sub(f'{ISSUE_KEY}.*$', ISSUE_KEY, LAUNCHER[0])
                    if launch: 
                        click.launch(LAUNCHER)
                except:
                    Log.info(f'unable to perform JIRA issue search using issue key {ISSUE_KEY}')
                    continue
                if OUT:
                    SEARCH_DATA[0]['promotion status'] = OUT
                    SEARCH_DATA[0]['ops review'] = STATUS
                    if review is not None:
                        TEMPLATE = f"INFO: the image has been promoted for Transaction-ID {TRANSACTION_ID}, and VMC Ops Review needs completion for ticket {ISSUE_KEY}.\n      auto-approval disabled."
                    elif STATUS == "No":
                        TEMPLATE = f"INFO: the image has been promoted for Transaction-ID {TRANSACTION_ID}, and VMC Ops Review needs completion for ticket {ISSUE_KEY}.\n      auto-approval disabled."
                else:
                    SEARCH_DATA[0]['promotion status'] = 'UNKNOWN'
                    SEARCH_DATA[0]['ops review'] = STATUS
                    if review is not None:
                        TEMPLATE = f"INFO: the image was not promoted for Trasnaction-ID {TRANSACTION_ID} for ticket {ISSUE_KEY}. VMC Ops Review Required."
                    elif STATUS == "No":
                        TEMPLATE = f"INFO: the image was not promoted for Transaction-ID {TRANSACTION_ID} for ticket {ISSUE_KEY}. VMC Ops Review Required."
                RESULT.append(SEARCH_DATA[0])
        else:
            try:
                SEARCH_DATA = run_jql_query(None,[ISSUE_KEY],None,None,None,None,None,None,None,None,False,False,False,False,None,False,True,jira_profile,True)
            except:
                continue
            SEARCH_DATA[0]['promotion status'] = 'N/A'
            SEARCH_DATA[0]['ops review'] = STATUS
            LAUNCHER = find_url(SEARCH_DATA[0]['launcher'])
            LAUNCHER = re.sub(f'{ISSUE_KEY}.*$', ISSUE_KEY, LAUNCHER[0])
            if launch: 
                click.launch(LAUNCHER)
            RESULT.append(SEARCH_DATA[0])
            if review is not None:
                TEMPLATE = f"INFO: transaction-ID was not found on the page, and VMC Ops Review is required for {ISSUE_KEY}."
            elif STATUS == "No":
                TEMPLATE = f"INFO: transaction-ID was not found on the page, and VMC Ops Review is required for {ISSUE_KEY}."
    if raw:
        Log.info(json.dumps(RESULT, indent=2))
    else:
        Log.info(f"\n{tabulate.tabulate(RESULT, headers='keys', tablefmt='rst')}")

def find_url(line):

    URL_REGEX = r"""(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))"""

    matches = re.findall(URL_REGEX, line)
    return matches

def escape_ansi(line):
    ansi_escape = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', line)

