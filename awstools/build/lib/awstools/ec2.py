import click, os, gnureadline, csv
from toolbox.logger import Log
from .ec2client import EC2client
from toolbox.menumaker import Menu
from tabulate import tabulate
from configstore.configstore import Config
from toolbox.misc import set_terminal_width
from .iam import get_latest_profile, get_latest_region

CONFIG = Config('awstools')

# just something I've always included to make sure I'm using the right input method based on python version. Not really needed anymore, but old habits die hard
try: input = raw_input
except NameError: raw_input = input

@click.group('ec2', invoke_without_command=True, help='ec2 to manage the instances and related configuration', context_settings={'help_option_names':['-h','--help'], 'max_content_width': set_terminal_width()})
@click.option('-m', '--menu', help='use the menu to perform EC2 actions', is_flag=True, show_default=True, default=False, required=False)
@click.pass_context
def ec2(ctx, menu):
    if menu:
        ctx.obj['MENU'] = True
    else:
        ctx.obj['MENU'] = False

@ec2.command(help='manually refresh ec2 cached data', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
@click.argument('cache_type', required=False, default='all', type=click.Choice(['all', 'instances', 'public_ips', 'regions', 'auto']))
def refresh(ctx, cache_type):
    aws_profile_name = ctx.obj['PROFILE']
    aws_region = get_latest_region(aws_profile_name)
    _refresh(cache_type, aws_profile_name, aws_region)

def _refresh(cache_type, aws_profile_name, aws_region):
    try:    
        EC2 = get_EC2client(aws_profile_name, aws_region, auto_refresh=False)
        if cache_type == 'all':
            EC2.refresh(aws_profile_name, aws_region)
        if cache_type == 'instances':
            EC2.cache_instances(aws_profile_name, aws_region)
        if cache_type == 'public_ips':
            EC2.cache_public_ips(aws_profile_name, aws_region)
        if cache_type == 'regions':
            EC2.cache_regions(aws_profile_name, aws_region)
        if cache_type == 'auto':
            EC2.auto_refresh(aws_profile_name, aws_region)
        return True
    except:
        return False

@ec2.command(help='show the data stored in ec2 cache (instacnes, IPs, regions)', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
@click.argument('target', required=False, default='all', type=click.Choice(['all', 'instances', 'public_ips', 'regions', 'orphaned_ebs', 'orphaned_snaps']))
def show(ctx, target):
    aws_profile_name = ctx.obj['PROFILE']
    aws_region = get_latest_region(aws_profile_name)
    if ctx.obj["MENU"] and target == "instances":
        CACHED_INSTANCES = {}
        DATA = []
        for PROFILE in CONFIG.PROFILES:
            if PROFILE == 'latest':
                continue
            if PROFILE == aws_profile_name:
                EC2 = get_EC2client(aws_profile_name, aws_region, auto_refresh=False, cache_only=True)
                RES = EC2.show_cache(aws_profile_name, 'cached_instances', aws_region, display=False)
                for data in RES:
                    NAME = data["PrivateDnsName"].ljust(50)
                    IP = data["PrivateIpAddress"]
                    ID = data["InstanceId"]
                    details = NAME + "\t" + IP + "\t" + ID
                    DATA.append(details)
                break
        INPUT = 'Login Manager'
        CHOICE = runMenu(DATA, INPUT)
        if CHOICE:
            IP = CHOICE[0].split("\t")[1]
            Log.info(f"you chose to SSH to {IP} which will be implemented later...")
    elif ctx.obj["MENU"] and target == "orphaned_ebs":
        INPUT = 'ORPHANED EBS VOLUMES'
        EC2 = EC2client(aws_profile_name, aws_region='us-east-1', in_boundary=False, cache_only=False)
        CLIENT = EC2.SESSION.client('ec2')
        VOLUMES = CLIENT.describe_volumes()
        DATA = []
        for VOLUME in VOLUMES['Volumes']:
            if VOLUME['State'] == 'available':
                DETAILS = VOLUME['VolumeId'] + "\t" + str(VOLUME['Size']) + "\t" + VOLUME['VolumeType'] + "\t" + VOLUME['State']
                DATA.append(DETAILS)
        CHOICE = runMenu(DATA, INPUT)
        if CHOICE:
            ID = CHOICE[0].split("\t")[0]
            Log.info(f"you chose to work with {ID} which will be implemented later...")
    else:
        _show(target, aws_profile_name, aws_region, display=True)

def _show(target, aws_profile_name, aws_region, display):
    try:
        EC2 = get_EC2client(aws_profile_name, aws_region, auto_refresh=False, cache_only=True)
        if target == 'instances' or target == 'all':
            EC2.show_cache(aws_profile_name, 'cached_instances', aws_region, display)
        if target == 'public_ips' or target == 'all':
            EC2.show_cache(aws_profile_name, 'cached_public_ips', aws_region, display)
        if target == 'regions' or target == 'all':
            EC2.show_cache(aws_profile_name, 'cached_regions', aws_region, display)
        if target == 'orphaned_ebs' or target == 'all':
            orphaned_ebs_volumes(aws_profile_name)
        if target == 'orphaned_snaps':
            orphaned_ebs_snap_report(aws_profile_name, delete=False)
        return True
    except:
        return False

def orphaned_ebs_volumes(aws_profile_name):
    EC2 = EC2client(aws_profile_name, aws_region='us-east-1', in_boundary=False, cache_only=False)
    CLIENT = EC2.SESSION.client('ec2')
    VOLUMES = CLIENT.describe_volumes()
    ORPHANED_VOLUMES = {'VolumeId': [], 'VolumeSize': [], 'VolumeType': [], 'State': [], 'CreateTime': []}
    for VOLUME in VOLUMES['Volumes']:
        if VOLUME['State'] == 'available':
            ORPHANED_VOLUMES['VolumeId'].append(VOLUME['VolumeId'])
            ORPHANED_VOLUMES['VolumeSize'].append(VOLUME['Size'])
            ORPHANED_VOLUMES['VolumeType'].append(VOLUME['VolumeType'])
            ORPHANED_VOLUMES['State'].append(VOLUME['State'])
            ORPHANED_VOLUMES['CreateTime'].append(VOLUME['CreateTime'])
    Log.info(f'orphaned_ebs_volumes count: {len(ORPHANED_VOLUMES["VolumeId"])}')
    Log.info(f"orphaned_ebs_volumes \n{tabulate(ORPHANED_VOLUMES, headers='keys', tablefmt='rst')}\n")
    return ORPHANED_VOLUMES

@ec2.group('delete', help="Delete EC2 objects such as instances, EBS volumes or snapshots", context_settings={'help_option_names':['-h','--help']})
def delete():
    pass

@delete.command('orphaned_ebs', help="delete orphaned EBS volumes or snapshots", context_settings={'help_option_names':['-h','--help']})
@click.option('-v', '--volume', help='flag to delete orphaned EBS volumes', required=False, is_flag=True)
@click.option('-s', '--snapshot', help='flag to delete orphaned EBS snapshots', required=False, is_flag=True)
@click.pass_context
def delete_orphaned_ebs_volumes(ctx, volume, snapshot):
    aws_profile_name = ctx.obj['PROFILE']
    EC2 = EC2client(aws_profile_name, aws_region='us-east-1', in_boundary=False, cache_only=False)
    CLIENT = EC2.SESSION.client('ec2')
    VOLUMES = CLIENT.describe_volumes()
    if ctx.obj["MENU"] and volume is True:
        INPUT = 'ORPHANED EBS VOLUMES'
        DATA = []
        for VOLUME in VOLUMES['Volumes']:
            if VOLUME['State'] == 'available':
                DETAILS = VOLUME['VolumeId'] + "\t" + str(VOLUME['Size']) + "\t" + VOLUME['VolumeType'] + "\t" + VOLUME['State']
                DATA.append(DETAILS)
        CHOICE = runMenu(DATA, INPUT)
        if CHOICE:
            ID = CHOICE[0].split("\t")[0]
            USER_INPUT = input(f"Are you sure you want to delete the unorphaned EBS volume {ID}? [y/n]: ")
            if USER_INPUT.lower() == "y":
                CLIENT.delete_volume(VolumeId=ID)
                Log.info(f"The unorphaned EBS volume {ID} has been deleted.")
            elif USER_INPUT.lower() == "n":
                Log.info(f"The unorphaned EBS volumes {ID} will not be deleted.")
            else:
                Log.info("Please enter a valid value (y/n).")
    elif volume is True:
        USER_INPUT = input("Are you sure you want to delete the unorphaned EBS volumes? [y/n]: ")
        if USER_INPUT.lower() == "y":
            ORPHANED_VOLUMES = orphaned_ebs_volumes()
            for VOLUME in ORPHANED_VOLUMES:
                CLIENT.delete_volume(VolumeId=VOLUME)
            Log.info("The unorphaned EBS volumes have been deleted.")
        elif USER_INPUT.lower() == "n":
            Log.info("The unorphaned EBS volumes will not be deleted.")
        else:
            Log.info("Please enter a valid value (y/n).")
    if snapshot is True:
        orphaned_ebs_snap_report(aws_profile_name, delete=True)

def get_EC2client(aws_profile_name, aws_region='us-east-1', auto_refresh=True, cache_only=False):
    CLIENT = EC2client(aws_profile_name, aws_region, False, cache_only)
    if auto_refresh:
        CLIENT.auto_refresh(aws_profile_name)
    return CLIENT

def runMenu(DATA, INPUT):
    COUNT = 0
    FINAL = []
    TITLE = f'EC2 Menu: {INPUT}'
    for data in DATA:
        COUNT = COUNT + 1
        RESULTS = []
        RESULTS.append(data)
        FINAL.append(RESULTS)
    SUBTITLE = f'showing {COUNT} available object(s)'
    JOINER = '\t\t'
    FINAL_MENU = Menu(FINAL, TITLE, JOINER, SUBTITLE)
    CHOICE = FINAL_MENU.display()
    return CHOICE

def orphaned_ebs_snap_report(aws_profile_name, delete=False):

    import boto3
    from botocore.exceptions import ClientError
    from datetime import datetime, timedelta, timezone
    import sys

    CSV = '/tmp/' + aws_profile_name + '_snapshots.csv'
    IGNORE_DAYS = 0
    MYDATA = []
    EC2 = EC2client(aws_profile_name, aws_region='us-east-1', in_boundary=False, cache_only=False)
    EC2 = EC2.SESSION.client('ec2')
    SNAPSHOTS = EC2.describe_snapshots(OwnerIds=['self']).get('Snapshots', [])
    SNAPSHOTS = []
    RESPONSE = EC2.describe_snapshots(OwnerIds=['self'], MaxResults=1000)
    while True:
        SNAPSHOTS.extend(RESPONSE.get('Snapshots', []))
        TOKEN = RESPONSE.get('NextToken', '')
        if TOKEN == '':
            break
        RESPONSE = EC2.describe_snapshots(NextToken=TOKEN, OwnerIds=['self'], MaxResults=1000)
    if SNAPSHOTS:
        SNAPSHOTS.sort(key=lambda snapshot: snapshot['VolumeId'] + str(snapshot['StartTime']))
        V_PREV = None
        NUM_VOLUMES = 0
        NUM_VOLUMES_IGNORED = 0
        NUM_SNAP_VOL_IGNORED = 0
        NUM_SNAP_TOO_NEW = 0
        NUM_SNAP_COMPLIANCE = 0
        NUM_SNAP_AMI = 0
        NUM_SNAP_ORPHANS = 0
        IGNORE_VOLUME = False
        DELETE_CONFIRMED = False
        Log.info(f"please wait while generating a report; this might take a minute depending on the number of snapshots for {aws_profile_name}")
        for row in SNAPSHOTS:
            V = row['VolumeId']
            SID = row['SnapshotId']
            V_SIZE = row['VolumeSize']
            if V != V_PREV or V == 'vol-ffffffff':
                NUM_VOLUMES += 1
                V_PREV = V
                IGNORE_VOLUME = False
                if V != 'vol-ffffffff':
                    try:
                        VOLUMES = EC2.describe_volumes(VolumeIds=[V]).get('Volumes', [])
                        if VOLUMES:
                            NUM_VOLUMES_IGNORED += 1
                            IGNORE_VOLUME = True
                    except ClientError as e:
                        CODE = e.response.get('Error', {}).get('Code')
                        if CODE != 'InvalidVolume.NotFound':
                            raise
            if IGNORE_VOLUME:
                NUM_SNAP_VOL_IGNORED += 1
            else:
                TIMESTAMP = row['StartTime']
                if TIMESTAMP > datetime.now(timezone.utc) - timedelta(days=IGNORE_DAYS):
                    NUM_SNAP_TOO_NEW += 1
                    continue
                for tag in row.get('Tags', []):
                    if (tag.get('Key') == 'aws:backup:source-resource' or
                        tag.get('Key') == 'dlm:managed'):
                        NUM_SNAP_COMPLIANCE += 1
                        break
                else:
                    IMAGES = EC2.describe_images(
                                 Filters=[{'Name':'block-device-mapping.snapshot-id', 'Values':[SID]}]
                             ).get('Images', [])
                    if IMAGES:
                        NUM_SNAP_AMI += 1
                        continue  # Done with this snapshot as it's attached to an AMI, go to next row
                    NUM_SNAP_ORPHANS += 1
                    TS_STR = str(TIMESTAMP).split('.')[0].split('+')[0]  # Strip off ms & timezone info
                    if delete is True:
                        try:
                            if not DELETE_CONFIRMED:
                                print("You have chosen to delete matching snapshots.  It's recommended that you first run this "
                                      "script without the 'delete' function to get a report of snapshots that will be deleted.\n"
                                )
                                RESPONSE = raw_input('Are you sure you want to continue [Y/N]?: ').strip()
                                if RESPONSE == 'Y':
                                    DELETE_CONFIRMED = True
                                else:
                                    sys.exit()
                            EC2.delete_snapshot(SnapshotId=SID)
                        except ClientError as e:
                            if e.response.get('Error', {}).get('Code') != 'DryRunOperation':
                                raise  # Re-raise other exceptions
                        print('Deleted => ', end='')
                        Log.info(f'({V} / {SID}) => {TS_STR}')
                    MYDICT = {}
                    DESC = row.get('Description', '')
                    for tag in row.get('Tags', []):
                        if tag.get('Key') == 'Name':
                            DESC = tag.get('Value', '')
                            break
                    DESC = (DESC[:75] + '..') if len(DESC) > 75 else DESC
                    MYDICT['VolumeId'] = V
                    MYDICT['SnapshotId'] = SID
                    MYDICT['Description'] = DESC
                    MYDICT['Timestamp'] = TS_STR
                    MYDICT['VolumeSize'] = V_SIZE
                    MYDATA.append(MYDICT)
        print()
        if MYDATA:
            Log.info(f"\n{tabulate(MYDATA, headers='keys', tablefmt='fancy_grid')}")
            save_results(MYDATA, CSV)
            print(f"\nCSV RESULTS: {CSV}")
        print(f'\nTOTAL VOLUMES: {NUM_VOLUMES}')
        print(f'\tIgnored because volume still exists: {NUM_VOLUMES_IGNORED}')
        print(f'\nTOTAL SNAPSHOTS: {len(SNAPSHOTS)}')
        print(f'\tIgnored because volume was ignored: {NUM_SNAP_VOL_IGNORED}')
        print(f'\tOf remaining, ignored because too new: {NUM_SNAP_TOO_NEW}')
        print(f'\tOf remaining, ignored because managed by AWS Backup or Amazon Data Lifecycle Manager: {NUM_SNAP_COMPLIANCE}')
        print(f'\tOf remaining, ignored because linked to an AMI: {NUM_SNAP_AMI}')
        print(f"\tRemaining Orphans reported: {NUM_SNAP_ORPHANS}")
        print()
    else:
        Log.info(f'No snapshots in this region owned by {aws_profile_name}.')

def save_results(data, csvfile):
    ROWS = ['VolumeId', 'SnapshotId', 'Description', 'Timestamp', 'VolumeSize']
    with open(csvfile, 'w') as CSV:
        writer = csv.DictWriter(CSV, fieldnames=ROWS)
        writer.writeheader()
        writer.writerows(data)

