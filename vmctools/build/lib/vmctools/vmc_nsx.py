import click, json, pprint, re, sys, os, time, csv
from .sddcclient import sddc
from .vmc_misc import get_operator_context
from toolbox.logger import Log
from configstore.configstore import Config
from toolbox.menumaker import Menu
from toolbox.misc import SddcMenuResults as MenuResults
from csptools.cspclient import CSPclient
from tabulate import tabulate
from toolbox import misc

CSP = CSPclient()

@click.group('nsx', help='manage NSX making up the SDDC', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def nsx(ctx):
    pass

@nsx.command('edge-failover', help='perform edge failover actions for a specific SDDC', context_settings={'help_option_names':['-h','--help']})
@click.argument('sddc_id', required=False, default=None)
@click.option('-t', '--ticket', 'ticket', help="CSSD or CSCM ticket asssociated with the failover;", type=str, required=False, default='CSSD-1234', show_default=True)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def failover_edge(ctx, sddc_id, ticket, raw):
    Log.info("performing all necessary actions to failover edge")
    AUTH, PROFILE = get_operator_context(ctx)
    aws_ready = False
    version_only = False
    if sddc_id is None:
        DATA = []
        target_org, name = MenuResults(ctx)
        OUTPUT = CSP.org_show_sddcs(target_org, aws_ready, version_only, AUTH, PROFILE, raw)
        for I in OUTPUT:
            ID = I['id']
            NAME = I['name'].rjust(50)
            STRING = ID + '\t' + NAME
            DATA.append(STRING)
        INPUT = 'sddc manager'
        CHOICE = runMenu(DATA, INPUT)
        if CHOICE:
            CHOICE = ''.join(CHOICE)
            SDDC_NAME = CHOICE.split('\t')[1].strip()
            sddc_id = CHOICE.split('\t')[0]
            if SDDC_NAME:
                Log.info(f"gathering sddc information for {sddc_id} now, please wait...")
            else:
                Log.critical("please select an sddc-name to continue...")
        else:
            Log.critical("please select an sddc-name to continue...")

    SDDC = sddc(sddc_id, AUTH, PROFILE, None)
    Log.info(f"enabling SSH for NSX Edge in {SDDC_NAME}, please wait...")
    RESULT = SDDC.nsx_ssh_toggle('edge', 'start', ticket, raw=False)

    if RESULT == []:
        Log.critical('something went wrong when connecting to the SDDC')
    else:
        if RESULT['status'] != "FAILED":
            Log.info(RESULT['status'])
            for I in RESULT['data'].replace(",","\n").split('\n'):
                line = listToStringWithoutBrackets(I).replace('"','').split(':')
                if line[0] == "output":
                    Log.info(line[1].strip() + " => " + str(line[2:]))
                else:
                    Log.info(line[0].strip() + " => " + str(line[1:]))
        else:
            Log.json(json.dumps(RESULT, indent=2))
            Log.critical(f"nsx ssh toggle to start FAILED")

    Log.info("please wait while collecting NSX active edge information")
    RESULT = SDDC.nsx_show_active_edge(ticket, raw=False)
    FOUND = False
    NSX = {}
    if RESULT == []:
        Log.critical('something went wrong when connecting to the SDDC')
    else:
        NSX['ACTIVE'] = {}
        DICT = {}
        PATTERNS = ["sddc_state", "sddc_version", "org_id", "org_type", "sddc_id", "resource_type", "maintenance_mode", "ip_addresses", "node_display_name", "overall_status", "vm_name", "vm_host", "host_node_deployment_status", "node_id", "rebooted"]
        for I in filter_text(RESULT['data']['params']['SCRIPTDATA']['data'].replace(",","\n")).split('\n'):
            field = [I.replace('"','').split(':')]
            for D in PATTERNS:
                if D == field[0][0]:
                    FOUND = True
                    line = listToStringWithoutBrackets(I).replace('"','').split(':')
                    DICT[line[0].strip()] = line[1].strip()
                    if D == 'ip_addresses' or D == 'sddc_id' or D == 'node_id' or D == 'vm_name':
                        NSX['ACTIVE'].update({D: line[1].strip()})
                    if D == 'overall_status':
                        STATUS = line[1].strip()
                        if 'GREEN' in STATUS:
                            STATUS = misc.GREEN + misc.UNDERLINE + STATUS + misc.RESET
                        else:
                            STATUS = misc.RED + misc.UNDERLINE + STATUS + misc.RESET
                        NSX['ACTIVE'].update({D: STATUS})
                if D == 'rebooted': 
                    NSX['ACTIVE'].update({D: False})
        if FOUND is False:
            Log.critical(f'unable to find active NSX edges for {SDDC_NAME}')

    Log.info("please wait while collecting NSX standby edge information")
    RESULT = SDDC.nsx_show_standby_edge(ticket, raw=False)
    FOUND = False
    if RESULT == []:
        Log.critical('something went wrong when connecting to the SDDC')
    else:
        DICT = {}
        NSX['STANDBY'] = {}
        PATTERNS = ["sddc_state", "sddc_version", "org_id", "org_type", "sddc_id", "resource_type", "maintenance_mode", "ip_addresses", "node_display_name", "overall_status", "vm_name", "vm_host", "host_node_deployment_status", "node_id", "rebooted"]
        for I in filter_text(RESULT['data']['params']['SCRIPTDATA']['data'].replace(",","\n")).split('\n'):
            field = [I.replace('"','').split(':')]
            for D in PATTERNS:
                if D == field[0][0]:
                    FOUND = True
                    line = listToStringWithoutBrackets(I).replace('"','').split(':')
                    DICT[line[0].strip()] = line[1].strip()
                    if D == 'ip_addresses' or D == 'sddc_id' or D == 'node_id' or D == 'vm_name':
                        NSX['STANDBY'].update({D: line[1].strip()})
                    if D == 'overall_status':
                        STATUS = line[1].strip()
                        if 'GREEN' in STATUS:
                            STATUS = misc.GREEN + misc.UNDERLINE + STATUS + misc.RESET
                        else:
                            STATUS = misc.RED + misc.UNDERLINE + STATUS + misc.RESET
                        NSX['STANDBY'].update({D: STATUS})
                if D == 'rebooted': 
                    NSX['STANDBY'].update({D: False})
        if FOUND is False:
            Log.critical(f'unable to find active NSX edges for {SDDC_NAME}')

    NSX['VPN'] = {}
    type = 'local'
    Log.info("please wait while collecting NSX local vpn endpoints")
    RESULT = SDDC.nsx_vpn_endpoints(type, raw=False)

    if RESULT != []:
        DATADICT = {}
        PATTERNS = [ "resource_type", f"{type}_address", "id", "display_name" ]
        for I in filter_text(str(RESULT['nsx']).replace(",","\n")).split('\n'):
            field = [I.replace('"','').split(':')]
            line = listToStringWithoutBrackets(I).replace('"','').split(':')
            if line[0].strip() == f'{type}_address':
                IPADDRESS = line[1].strip()
                DATADICT[IPADDRESS] = {line[0].strip(): line[1].strip()}
                continue
            for D in PATTERNS:
                if D == field[0][0].strip().replace("'",""):
                    DATADICT[IPADDRESS].update({D: line[1].strip()})
        NSX['VPN'].update(DATADICT)
    else:
        Log.critical('something went wrong when connecting to the SDDC')

    DATADICT = {}
    DATA = []
    for I in NSX['VPN']:
        DATA.append(NSX['VPN'][I])
    if DATA:
        DATADICT = DATA
        Log.info(f"\n{tabulate(DATADICT, headers='keys', tablefmt='rst')}")

    type = 'peer'
    Log.info("please wait while collecting NSX peer vpn endpoints")
    RESULT = SDDC.nsx_vpn_endpoints(type, raw=False)

    NSX['VPN'] = {}
    if RESULT != []:
        DATADICT = {}
        PATTERNS = [ "resource_type", f"{type}_address", "id", "display_name" ]
        for I in filter_text(str(RESULT['nsx']).replace(",","\n")).split('\n'):
            field = [I.replace('"','').split(':')]
            line = listToStringWithoutBrackets(I).replace('"','').split(':')
            if line[0].strip() == f'{type}_address':
                IPADDRESS = line[1].strip()
                DATADICT[IPADDRESS] = {line[0].strip(): line[1].strip()}
            for D in PATTERNS:
                if D == field[0][0].strip().replace("'",""):
                    DATADICT[IPADDRESS].update({D: line[1].strip()})
        NSX['VPN'].update(DATADICT)
    else:
        Log.critical('something went wrong when connecting to the SDDC')

    DATADICT = {}
    DATA = []

    for I in NSX['VPN']:
        DATA.append(NSX['VPN'][I])
    if DATA:
        DATADICT = DATA
        Log.info(f"\n{tabulate(DATADICT, headers='keys', tablefmt='rst')}")

    RESULT = SDDC.nsx_vpn_sessions(raw)
    TOTAL_PRE = 0
    NSX['VPN'] = {}
    if RESULT != []:
        DATA = []
        DATADICT = {}
        PATTERNS = [ "resource_type", "tunnel_port_id", "id", "display_name", "local_endpoint_id", "peer_endpoint_id", "enabled" , "ip_addresses"]
        for I in filter_text(str(RESULT['nsx']).replace(",","\n")).split('\n'):
            field = [I.replace('"','').split(':')]
            line = listToStringWithoutBrackets(I).replace('"','').split(':')
            if line[0].strip() == 'results':
                try:
                    IPADDRESS = line[4].strip()
                    DATADICT[IPADDRESS] = {line[3].strip(): line[4].strip()}
                except:
                    break
            for D in PATTERNS:
                if D == field[0][0].strip().replace("'",""):
                    DATADICT[IPADDRESS].update({line[0].strip(): line[1].strip()})
                    if D == 'display_name' and line[1].strip() is not None:
                        TOTAL_PRE = TOTAL_PRE + 1
        NSX['VPN'].update(DATADICT)
    else:
        Log.critical('something went wrong when connecting to the SDDC')

    Log.info(f"total number of VPN sessions pre-failover: {TOTAL_PRE}")

    _get_policy_status(SDDC, raw)

    if raw:
        Log.json(json.dumps(NSX, indent=2))
    else:
        print()
        GET = ['ACTIVE', 'STANDBY']
        for D in GET:
            myfile = os.environ['HOME'] + '/' + f'edge_failover_{D}.csv'
            if os.path.isfile(myfile):
                os.remove(myfile)
            with open(myfile, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=NSX[D].keys())
                writer.writeheader()
                writer.writerow(NSX[D])
        for D in GET:
            myfile = os.environ['HOME'] + '/' + f'edge_failover_{D}.csv'
            if D != 'VPN':
                print(misc.MYBLUE + misc.UNDERLINE + D + misc.RESET)
                CMD = f'cat {myfile} | cut -d, -f 2- | tail -n 1 | tabulate -s, -f rst'
                os.system(CMD)
        print()

    ANS = input(f"INFO: would you like to reboot standby {NSX['STANDBY']['vm_name']}? [y/n]: ")
    if ANS == 'Y' or ANS == 'y':
        Log.info(f"rebooting {NSX['STANDBY']['vm_name']} now, please wait...")
        EDGE = listToStringWithoutBrackets(NSX['STANDBY']['vm_name'].split('-')[-1:])
        CMD = f"govops-vmc-tools sddc-nsx-ssh --sddc={NSX['STANDBY']['sddc_id']} --node=edge{EDGE} --ticket={ticket} --root --command='reboot'"
        print()
        Log.info(f"running command: {CMD}")
        print()
        os.system(CMD)
        NSX['STANDBY'].update({'rebooted': True})
    else:
        Log.info(f"skipping reboot of standby {NSX['STANDBY']['vm_name']}...")
        EDGE = listToStringWithoutBrackets(NSX['STANDBY']['vm_name'].split('-')[-1:])
        CMD = f"govops-vmc-tools sddc-nsx-ssh --sddc={NSX['STANDBY']['sddc_id']} --node=edge{EDGE} --ticket={ticket} --root --command='reboot'"
        print()
        Log.critical(f"skipping command: {CMD}")
        print()

    NSXSTATUS = {}
    FINISHED = False
    seconds = 180
    wait_with_message(seconds)

    while not FINISHED:
        try:
            seconds = 30
            wait_with_message(seconds)
            Log.info(f"checking the status of NSX edges, please wait (CTL+C To Abort)")
            RESULT = SDDC.nsx_status(ticket, raw)
            if RESULT and RESULT != [] and RESULT['status'] != "FAILED":
                FINISHED = True
        except:
            continue

    if RESULT != []:
        if RESULT['status'] != "FAILED":
            Log.info(RESULT['status'])
            PATTERNS = ["edge_ip_address", "edge_name", "status", "transport_node_id", "pnic_status", "mgmt_connection_status", "tunnel_status", "high_availability_status"]
            for I in RESULT['data'].replace(",","\n").split('\n'):
                line = listToStringWithoutBrackets(I).replace('"','').split(',')
                for D in PATTERNS:
                    if D == line[0].strip().split(":")[0].strip():
                        if D == "edge_ip_address":
                            IP = line[0].strip().split(":")[1].strip()
                            NSXSTATUS[IP] = {line[0].strip().split(":")[0].strip(): line[0].strip().split(":")[-1].strip()}
                        else:
                            NSXSTATUS[IP].update({line[0].strip().split(":")[0].strip(): line[0].strip().split(":")[-1].strip()})
        else:
            Log.json(json.dumps(RESULT, indent=2))
            Log.critical(f"nsx status for {SDDC_NAME} FAILED")
    else:
        Log.critical('something went wrong when connecting to the SDDC')

    DATADICT = {}
    DATA = []

    for I in NSXSTATUS:
        DATA.append(NSXSTATUS[I])

    if DATA:
        DATADICT = DATA
        Log.info(f"\n{tabulate(DATADICT, headers='keys', tablefmt='rst')}")
    else:
        Log.warn('there are 0 defined policies for BgpNeighborConfig resource')

    # start maintenance now
    mode = 'enter'
    Log.info(f"{mode}ing maintenance mode on {NSX['ACTIVE']['vm_name']} now, please wait...")
    RESULT = SDDC.nsx_maintenance(NSX['ACTIVE']['node_id'], ticket, mode, raw)
    if RESULT == []:
        Log.critical('something went wrong when connecting to the SDDC')
    else:
        if RESULT['status'] != "FAILED":
            PATTERNS = ["sddc_state", "status"]
            for I in filter_text(RESULT['params']['SCRIPTDATA']['data'].replace(",","\n")).split('\n'):
                line = listToStringWithoutBrackets(I).replace('"','').split(':')
                for D in PATTERNS:
                    if D in line[0]:
                        Log.info(line[0].strip() + " => " + str(line[1:]))
            Log.info(RESULT['status'])
        else:
            Log.json(json.dumps(RESULT, indent=2))
            Log.critical(f"nsx {mode} maintenance for {NSX['ACTIVE']['node_id']} FAILED")

    seconds = 60
    wait_with_message(seconds)

    mode = 'exit'
    Log.info(f"{mode}ing maintenance mode on {NSX['ACTIVE']['vm_name']} now, please wait...")
    RESULT = SDDC.nsx_maintenance(NSX['ACTIVE']['node_id'], ticket, mode, raw)
    if RESULT == []:
        Log.critical('something went wrong when connecting to the SDDC')
    else:
        if RESULT['status'] != "FAILED":
            PATTERNS = ["sddc_state", "status"]
            for I in filter_text(RESULT['params']['SCRIPTDATA']['data'].replace(",","\n")).split('\n'):
                line = listToStringWithoutBrackets(I).replace('"','').split(':')
                for D in PATTERNS:
                    if D in line[0]:
                        Log.info(line[0].strip() + " => " + str(line[1:]))
            Log.info(RESULT['status'])
        else:
            Log.json(json.dumps(RESULT, indent=2))
            Log.critical(f"nsx {mode} maintenance for {NSX['ACTIVE']['node_id']} FAILED")

    seconds = 60
    wait_with_message(seconds)

    Log.info(f"enabling SSH for NSX Edge in {SDDC_NAME}, please wait...")
    RESULT = SDDC.nsx_ssh_toggle('edge', 'start', ticket, raw=False)

    if RESULT == []:
        Log.critical('something went wrong when connecting to the SDDC')
    else:
        if RESULT['status'] != "FAILED":
            Log.info(RESULT['status'])
            for I in RESULT['data'].replace(",","\n").split('\n'):
                line = listToStringWithoutBrackets(I).replace('"','').split(':')
                if line[0] == "output":
                    Log.info(line[1].strip() + " => " + str(line[2:]))
                else:
                    Log.info(line[0].strip() + " => " + str(line[1:]))
        else:
            Log.json(json.dumps(RESULT, indent=2))
            Log.info(f"nsx ssh toggle to start FAILED")

    MSG = 'ACTION: EDGE FAILOVER STARTING'
    print()
    print(misc.MYBLUE + misc.UNDERLINE + MSG + misc.RESET)
    if NSX['ACTIVE']['rebooted'] is False:
        ANS = input(f"\nINFO: would you like to reboot the old active node {NSX['ACTIVE']['vm_name']}? [y/n]: ")
        if ANS == 'Y' or ANS == 'y':
            Log.info(f"rebooting {NSX['ACTIVE']['vm_name']} now, please wait...")
            EDGE = listToStringWithoutBrackets(NSX['ACTIVE']['vm_name'].split('-')[-1:])
            CMD = f"govops-vmc-tools sddc-nsx-ssh --sddc={NSX['ACTIVE']['sddc_id']} --node=edge{EDGE} --ticket={ticket} --root --command='reboot'"
            print()
            Log.info(f"running command: {CMD}")
            print()
            os.system(CMD)
            NSX['ACTIVE'].update({'rebooted': True})
        else:
            Log.info(f"skipping reboot of the old active node {NSX['ACTIVE']['vm_name']}...")
            EDGE = listToStringWithoutBrackets(NSX['ACTIVE']['vm_name'].split('-')[-1:])
            CMD = f"govops-vmc-tools sddc-nsx-ssh --sddc={NSX['ACTIVE']['sddc_id']} --node=edge{EDGE} --ticket={ticket} --root --command='reboot'"
            print()
            Log.info(f"skipping command: {CMD}")
            print()

    FINISHED = False
    seconds = 180
    wait_with_message(seconds)

    while not FINISHED:
        try:
            seconds = 30
            wait_with_message(seconds)
            Log.info(f"checking the status of NSX edges, please wait (CTL+C To Abort)")
            RESULT = SDDC.nsx_status(ticket, raw)
            if RESULT and RESULT != [] and RESULT['status'] != "FAILED":
                FINISHED = True
        except:
            continue

    Log.info("please wait while collecting NSX active edge information post-failover")
    RESULT = SDDC.nsx_show_active_edge(ticket, raw=False)
    FOUND = False
    NSX = {}
    if RESULT == []:
        Log.critical('something went wrong when connecting to the SDDC')
    else:
        NSX['ACTIVE'] = {}
        DICT = {}
        PATTERNS = ["sddc_state", "sddc_version", "org_id", "org_type", "sddc_id", "resource_type", "maintenance_mode", "ip_addresses", "node_display_name", "overall_status", "vm_name", "vm_host", "host_node_deployment_status", "node_id", "rebooted"]
        for I in filter_text(RESULT['data']['params']['SCRIPTDATA']['data'].replace(",","\n")).split('\n'):
            field = [I.replace('"','').split(':')]
            for D in PATTERNS:
                if D == field[0][0]:
                    FOUND = True
                    line = listToStringWithoutBrackets(I).replace('"','').split(':')
                    DICT[line[0].strip()] = line[1].strip()
                    if D == 'ip_addresses' or D == 'sddc_id' or D == 'node_id' or D == 'vm_name':
                        NSX['ACTIVE'].update({D: line[1].strip()})
                    if D == 'overall_status':
                        STATUS = line[1].strip()
                        if 'GREEN' in STATUS:
                            STATUS = misc.GREEN + misc.UNDERLINE + STATUS + misc.RESET
                        else:
                            STATUS = misc.RED + misc.UNDERLINE + STATUS + misc.RESET
                        NSX['ACTIVE'].update({D: STATUS})
        if FOUND is False:
            Log.critical(f'unable to find active NSX edges for {SDDC_NAME}')
        else:
            if raw:
                Log.json(json.dumps(DICT, indent=2))

    Log.info("please wait while collecting NSX standby edge information post-failover")
    RESULT = SDDC.nsx_show_standby_edge(ticket, raw=False)
    FOUND = False
    if RESULT == []:
        Log.critical('something went wrong when connecting to the SDDC')
    else:
        DICT = {}
        NSX['STANDBY'] = {}
        PATTERNS = ["sddc_state", "sddc_version", "org_id", "org_type", "sddc_id", "resource_type", "maintenance_mode", "ip_addresses", "node_display_name", "overall_status", "vm_name", "vm_host", "host_node_deployment_status", "node_id", "rebooted"]
        for I in filter_text(RESULT['data']['params']['SCRIPTDATA']['data'].replace(",","\n")).split('\n'):
            field = [I.replace('"','').split(':')]
            for D in PATTERNS:
                if D == field[0][0]:
                    FOUND = True
                    line = listToStringWithoutBrackets(I).replace('"','').split(':')
                    DICT[line[0].strip()] = line[1].strip()
                    if D == 'ip_addresses' or D == 'sddc_id' or D == 'node_id' or D == 'vm_name':
                        NSX['STANDBY'].update({D: line[1].strip()})
                    if D == 'overall_status':
                        STATUS = line[1].strip()
                        if 'GREEN' in STATUS:
                            STATUS = misc.GREEN + misc.UNDERLINE + STATUS + misc.RESET
                        else:
                            STATUS = misc.RED + misc.UNDERLINE + STATUS + misc.RESET
                        NSX['STANDBY'].update({D: STATUS})
        if FOUND is False:
            Log.critical(f'unable to find active NSX edges for {SDDC_NAME}')
        else:
            if raw:
                Log.json(json.dumps(DICT, indent=2))
 
    Log.info("please wait while collecting vpn-sessions post-failover")
    RESULT = SDDC.nsx_vpn_sessions(raw)
    TOTAL_POST = 0
    if RESULT != []:
        NSX['VPN'] = {}
        DATA = []
        DATADICT = {}
        PATTERNS = [ "resource_type", "tunnel_port_id", "id", "display_name", "local_endpoint_id", "peer_endpoint_id", "enabled" , "ip_addresses"]
        for I in filter_text(str(RESULT['nsx']).replace(",","\n")).split('\n'):
            field = [I.replace('"','').split(':')]
            line = listToStringWithoutBrackets(I).replace('"','').split(':')
            if line[0].strip() == 'results':
                try:
                    IPADDRESS = line[4].strip()
                    DATADICT[IPADDRESS] = {line[3].strip(): line[4].strip()}
                except:
                    break
            for D in PATTERNS:
                if D == field[0][0].strip().replace("'",""):
                    DATADICT[IPADDRESS].update({line[0].strip(): line[1].strip()})
                    if D == 'display_name' and line[1].strip() is not None:
                        TOTAL_POST = TOTAL_POST + 1
        NSX['VPN'].update({'vpn-sessions': DATADICT})
    else:
        Log.critical('something went wrong when connecting to the SDDC')

    print()
    if TOTAL_PRE == TOTAL_POST:
        Log.info("total number of VPN sessions pre-failover:  " + misc.GREEN + str(TOTAL_PRE) + misc.MOVE2 + 'SUCCESS' + misc.RESET)
        Log.info("total number of VPN sessions post-failover: " + misc.GREEN + str(TOTAL_POST) + misc.MOVE2 + 'SUCCESS' + misc.RESET)
    else:
        Log.warn("total number of VPN sessions pre-failover:  " + misc.RED + str(TOTAL_PRE) + misc.MOVE2 + 'FAILURE' + misc.RESET)
        Log.warn("total number of VPN sessions post-failover: " + misc.RED + str(TOTAL_POST) + misc.MOVE2 + 'FAILURE' + misc.RESET)

    # dump information now
    if raw:
        Log.json(json.dumps(NSX, indent=2))
    else:
        print()
        GET = ['ACTIVE', 'STANDBY']
        for D in GET:
            myfile = os.environ['HOME'] + '/' + f'edge_failover_{D}.csv'
            if os.path.isfile(myfile):
                os.remove(myfile)
            with open(myfile, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=NSX[D].keys())
                writer.writeheader()
                writer.writerow(NSX[D])
        for D in GET:
            myfile = os.environ['HOME'] + '/' + f'edge_failover_{D}.csv'
            print(misc.MYBLUE + misc.UNDERLINE + D + misc.RESET)
            CMD = f'cat {myfile} | cut -d, -f 2- | tail -n 1 | tabulate -s, -f rst'
            os.system(CMD)
        print()

    _get_policy_status(SDDC, raw)

@nsx.command('maintenance', help='enter or exit transport maintenance mode for NSX in a specific SDDC', context_settings={'help_option_names':['-h','--help']})
@click.argument('sddc_id', required=False, default=None)
@click.option('-m', '--mode', help="available modes are enter or exit", default=None, type=click.Choice(['enter', 'exit']), required=True)
@click.option('-n', '--node', help="provide the edge trasport node ID", default=None, required=False)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.option('-t', '--ticket', 'ticket', help="CSSD or CSCM ticket asssociated with the RTS task", type=str, required=False, default='CSSD-1234', show_default=True)
@click.pass_context
def nsx_maintenance(ctx, sddc_id, mode, node, raw, ticket):
    AUTH, PROFILE = get_operator_context(ctx)
    aws_ready = False
    version_only = False
    if sddc_id is None:
        DATA = []
        target_org, name = MenuResults(ctx)
        OUTPUT = CSP.org_show_sddcs(target_org, aws_ready, version_only, AUTH, PROFILE, raw)
        for I in OUTPUT:
            ID = I['id']
            NAME = I['name'].rjust(50)
            STRING = ID + '\t' + NAME
            DATA.append(STRING)
        INPUT = 'sddc manager'
        CHOICE = runMenu(DATA, INPUT)
        if CHOICE:
            CHOICE = ''.join(CHOICE)
            SDDC_NAME = CHOICE.split('\t')[1].strip()
            sddc_id = CHOICE.split('\t')[0]
            if SDDC_NAME:
                Log.info(f"gathering sddc information for {sddc_id} now, please wait...")
            else:
                Log.critical("please select an sddc-name to continue...")
        else:
            Log.critical("please select an sddc-name to continue...")

    SDDC = sddc(sddc_id, AUTH, PROFILE, None)
    if node is None:
        Log.info(f"gathering NSX status prior to entering maintenance mode {mode}")
        RESULT = SDDC.nsx_status(ticket, raw)
        NSXSTATUS = {}
        if RESULT != []:
            if RESULT['status'] != "FAILED":
                Log.info(RESULT['status'])
                PATTERNS = ["edge_name", "edge_ip_address", "status", "transport_node_id", "summary"]
                IGNORE = ["system_status"]
                for I in RESULT['data'].replace(",","\n").split('\n'):
                    line = listToStringWithoutBrackets(I).replace('"','').split(',')
                    for D in PATTERNS:
                        if D in line[0].strip() and D not in IGNORE:
                            if 'control_connection_status' in line[0].strip():
                                continue
                            if D == "edge_ip_address":
                                IP = line[0].strip().split(":")[1].strip()
                                NSXSTATUS[IP] = {}
                            else:
                                if D == "summary":
                                    NSXSTATUS['summary'] = {line[0].strip().split(":")[0].strip(): line[0].strip().split(":")[-1].strip()}
                                    continue
                                NSXSTATUS[IP].update({line[0].strip().split(":")[0].strip(): line[0].strip().split(":")[-1].strip()})
            else:
                Log.json(json.dumps(RESULT, indent=2))
                Log.critical(f"nsx status for {SDDC_NAME} FAILED")
        else:
            Log.critical('something went wrong when connecting to the SDDC')
   
        DATA = []
        for IP in NSXSTATUS:
            try:
                NAME = NSXSTATUS[IP]['edge_name']
                NODEID = NSXSTATUS[IP]['transport_node_id']
                DATA.append(NAME + "\t" + NODEID)
            except:
                pass
        INPUT = 'edge manager'
        CHOICE = runMenu(DATA, INPUT)
        if CHOICE:
            CHOICE = ''.join(CHOICE)
            name = CHOICE.split('\t')[0].strip()
            node = CHOICE.split('\t')[1].strip()
            if name:
                Log.info(f"preparing maintenance {mode} mode for {name} now, please wait")
            else:
                Log.critical("please select an edge name to continue...")
        else:
            Log.critical("please select an edge name to continue...")

    RESULT = SDDC.nsx_maintenance(node, ticket, mode, raw)
    if RESULT == []:
        Log.critical('something went wrong when connecting to the SDDC')
    else:
        if RESULT['status'] != "FAILED":
            PATTERNS = ["sddc_state", "status"]
            for I in filter_text(RESULT['params']['SCRIPTDATA']['data'].replace(",","\n")).split('\n'):
                line = listToStringWithoutBrackets(I).replace('"','').split(':')
                for D in PATTERNS:
                    if D in line[0]:
                        Log.info(line[1])
            Log.info(RESULT['status'])
        else:
           Log.json(json.dumps(RESULT, indent=2))
           Log.critical(f"nsx {mode} maintenance for {name} FAILED")

@nsx.command('ssh-toggle', help='enable or disable SSH on NSX in a specific SDDC', context_settings={'help_option_names':['-h','--help']})
@click.argument('nsx_type', required=True, default=None, type=click.Choice(['controller', 'manager', 'edge']))
@click.argument('action', required=True, default=None, type=click.Choice(['start', 'stop', 'restart']))
@click.argument('sddc_id', required=False, default=None)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.option('-t', '--ticket', 'ticket', help="CSSD or CSCM ticket asssociated with the RTS task", type=str, required=False, default='CSSD-1234', show_default=True)
@click.pass_context
def nsx_ssh_toggle(ctx, nsx_type, action, sddc_id, raw, ticket):
    AUTH, PROFILE = get_operator_context(ctx)
    aws_ready = False
    version_only = False
    if sddc_id is None:
        DATA = []
        target_org, name = MenuResults(ctx)
        OUTPUT = CSP.org_show_sddcs(target_org, aws_ready, version_only, AUTH, PROFILE, raw)
        for I in OUTPUT:
            ID = I['id']
            NAME = I['name'].rjust(50)
            STRING = ID + '\t' + NAME
            DATA.append(STRING)
        INPUT = 'sddc manager'
        CHOICE = runMenu(DATA, INPUT)
        if CHOICE:
            CHOICE = ''.join(CHOICE)
            SDDC_NAME = CHOICE.split('\t')[1].strip()
            sddc_id = CHOICE.split('\t')[0]
            if SDDC_NAME:
                Log.info(f"gathering sddc information for {sddc_id} now, please wait...")
            else:
                Log.critical("please select an sddc-name to continue...")
        else:
            Log.critical("please select an sddc-name to continue...")
    SDDC = sddc(sddc_id, AUTH, PROFILE, None)
    RESULT = SDDC.nsx_ssh_toggle(nsx_type, action, ticket, raw)
    if RESULT == []:
        Log.critical('something went wrong when connecting to the SDDC')
    else:
        if RESULT['status'] != "FAILED":
            Log.info(RESULT['status'])
            for I in RESULT['data'].replace(",","\n").split('\n'):
                line = listToStringWithoutBrackets(I).replace('"','').split(':')
                if line[0] == "output":
                    Log.info(line[1].strip() + " => " + str(line[2:]))
                else:
                    Log.info(line[0].strip() + " => " + str(line[1:]))
        else:
            Log.json(json.dumps(RESULT, indent=2))
            Log.critical(f"nsx ssh toggle to {action} for {nsx_type} FAILED")

@nsx.group('show', help='show data about the NSX in a SDDC', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def nsx_show(ctx):
    pass

@nsx_show.command('summary', help='quick summary of NSX related information under a given SDDC', context_settings={'help_option_names':['-h','--help']})
@click.argument('sddc_id', required=False, default=None)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def nsx_show_summary(ctx, sddc_id, raw):
    AUTH, PROFILE = get_operator_context(ctx)
    aws_ready = False
    version_only = False
    if sddc_id is None:
        DATA = []
        target_org, name = MenuResults(ctx)
        OUTPUT = CSP.org_show_sddcs(target_org, aws_ready, version_only, AUTH, PROFILE, raw)
        for I in OUTPUT:
            ID = I['id']
            NAME = I['name'].rjust(50)
            STRING = ID + '\t' + NAME
            DATA.append(STRING)
        INPUT = 'sddc manager'
        CHOICE = runMenu(DATA, INPUT)
        if CHOICE:
            CHOICE = ''.join(CHOICE)
            SDDC_NAME = CHOICE.split('\t')[1].strip()
            sddc_id = CHOICE.split('\t')[0]
            if SDDC_NAME:
                Log.info(f"gathering sddc information for {sddc_id} now, please wait...")
            else:
                Log.critical("please select an sddc-name to continue...")
        else:
            Log.critical("please select an sddc-name to continue...")
 
    SDDC = sddc(sddc_id, AUTH, PROFILE, None)
    RESULT = SDDC.nsx_show_all(raw)
    if RESULT == []:
        Log.critical('something went wrong when connecting to the SDDC')
    else:
        Log.json(json.dumps(RESULT, indent=2))

@nsx_show.command('node-status', help='show the node status for NSX in a specific SDDC', context_settings={'help_option_names':['-h','--help']})
@click.argument('sddc_id', required=False, default=None)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def nsx_node_status(ctx, sddc_id, raw):
    AUTH, PROFILE = get_operator_context(ctx)
    aws_ready = False
    version_only = False
    if sddc_id is None:
        DATA = []
        target_org, name = MenuResults(ctx)
        OUTPUT = CSP.org_show_sddcs(target_org, aws_ready, version_only, AUTH, PROFILE, raw)
        for I in OUTPUT:
            ID = I['id']
            NAME = I['name'].rjust(50)
            STRING = ID + '\t' + NAME
            DATA.append(STRING)
        INPUT = 'sddc manager'
        CHOICE = runMenu(DATA, INPUT)
        if CHOICE:
            CHOICE = ''.join(CHOICE)
            SDDC_NAME = CHOICE.split('\t')[1].strip()
            sddc_id = CHOICE.split('\t')[0]
            if SDDC_NAME:
                Log.info(f"gathering sddc information for {sddc_id} now, please wait...")
            else:
                Log.critical("please select an sddc-name to continue...")
        else:
            Log.critical("please select an sddc-name to continue...")

    SDDC = sddc(sddc_id, AUTH, PROFILE, None)
    RESULT = SDDC.nsx_node_status(raw)
    if RESULT != []:
        Log.json(json.dumps(RESULT, indent=2))
    else:
        Log.critical('something went wrong when connecting to the SDDC')

@nsx_show.command('vpn-sessions', help='show the VPN sessions for NSX in a specific SDDC', context_settings={'help_option_names':['-h','--help']})
@click.argument('sddc_id', required=False, default=None)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def nsx_vpn_sessions(ctx, sddc_id, raw):
    AUTH, PROFILE = get_operator_context(ctx)
    aws_ready = False
    version_only = False
    if sddc_id is None:
        DATA = []
        target_org, name = MenuResults(ctx)
        OUTPUT = CSP.org_show_sddcs(target_org, aws_ready, version_only, AUTH, PROFILE, raw)
        for I in OUTPUT:
            ID = I['id']
            NAME = I['name'].rjust(50)
            STRING = ID + '\t' + NAME
            DATA.append(STRING)
        INPUT = 'sddc manager'
        CHOICE = runMenu(DATA, INPUT)
        if CHOICE:
            CHOICE = ''.join(CHOICE)
            SDDC_NAME = CHOICE.split('\t')[1].strip()
            sddc_id = CHOICE.split('\t')[0]
            if SDDC_NAME:
                Log.info(f"gathering sddc information for {sddc_id} now, please wait...")
            else:
                Log.critical("please select an sddc-name to continue...")
        else:
            Log.critical("please select an sddc-name to continue...")

    SDDC = sddc(sddc_id, AUTH, PROFILE, None)
    RESULT = SDDC.nsx_vpn_sessions(raw)
    TOTAL = 0
    if RESULT != []:
        PATTERNS = [ "resource_type", "tunnel_port_id", "id", "display_name", "local_endpoint_id", "peer_endpoint_id", "enabled" , "ip_addresses"]
        for I in filter_text(str(RESULT['nsx']).replace(",","\n")).split('\n'):
            field = [I.replace('"','').split(':')]
            line = listToStringWithoutBrackets(I).replace('"','').split(':')
            if line[0].strip() == 'results':
                Log.info(line[1].strip() + " => " + str(line[2:]))
            for D in PATTERNS:
                if D == field[0][0].strip().replace("'",""):
                    Log.info(line[0].strip() + " => " + line[1].strip())
                    if D == 'display_name' and line[1].strip():
                        TOTAL = TOTAL + 1
    else:
        Log.critical('something went wrong when connecting to the SDDC')
    Log.info(f"total number of VPN sessions: {TOTAL}")

@nsx_show.command('vpn-endpoints', help='show the VPN local endpoints for NSX in a specific SDDC', context_settings={'help_option_names':['-h','--help']})
@click.argument('sddc_id', required=False, default=None)
@click.option('-t', '--type', help="available types are local or peer", default='local', type=click.Choice(['local', 'peer']), show_default=True)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def nsx_vpn_endpoints(ctx, sddc_id, type, raw):
    AUTH, PROFILE = get_operator_context(ctx)
    aws_ready = False
    version_only = False
    if sddc_id is None:
        DATA = []
        target_org, name = MenuResults(ctx)
        OUTPUT = CSP.org_show_sddcs(target_org, aws_ready, version_only, AUTH, PROFILE, raw)
        for I in OUTPUT:
            ID = I['id']
            NAME = I['name'].rjust(50)
            STRING = ID + '\t' + NAME
            DATA.append(STRING)
        INPUT = 'sddc manager'
        CHOICE = runMenu(DATA, INPUT)
        if CHOICE:
            CHOICE = ''.join(CHOICE)
            SDDC_NAME = CHOICE.split('\t')[1].strip()
            sddc_id = CHOICE.split('\t')[0]
            if SDDC_NAME:
                Log.info(f"gathering sddc information for {sddc_id} now, please wait...")
            else:
                Log.critical("please select an sddc-name to continue...")
        else:
            Log.critical("please select an sddc-name to continue...")

    SDDC = sddc(sddc_id, AUTH, PROFILE, None)
    RESULT = SDDC.nsx_vpn_endpoints(type, raw)
    NSX = {}

    if RESULT != []:
        DATADICT = {}
        PATTERNS = [ "resource_type", f"{type}_address", "id", "display_name" ]
        for I in filter_text(str(RESULT['nsx']).replace(",","\n")).split('\n'):
            field = [I.replace('"','').split(':')]
            line = listToStringWithoutBrackets(I).replace('"','').split(':')
            if line[0].strip() == f'{type}_address':
                IPADDRESS = line[1].strip()
                DATADICT[IPADDRESS] = {line[0].strip(): line[1].strip()}
            for D in PATTERNS:
                if D == field[0][0].strip().replace("'",""):
                    DATADICT[IPADDRESS].update({D: line[1].strip()})
        NSX.update(DATADICT)
    else:
        Log.critical('something went wrong when connecting to the SDDC')

    DATADICT = {}
    DATA = []
    for I in NSX:
        DATA.append(NSX[I])
    if DATA:
        DATADICT = DATA
        Log.info(f"\n{tabulate(DATADICT, headers='keys', tablefmt='rst')}")

@nsx_show.command('edge-status', help='show the edge status for NSX in a specific SDDC', context_settings={'help_option_names':['-h','--help']})
@click.argument('sddc_id', required=False, default=None)
@click.option('-t', '--ticket', 'ticket', help="CSSD or CSCM ticket asssociated with the RTS task", type=str, required=False, default='CSSD-1234', show_default=True)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def nsx_edge_status(ctx, sddc_id, ticket, raw):
    AUTH, PROFILE = get_operator_context(ctx)
    aws_ready = False
    version_only = False
    if sddc_id is None:
        DATA = []
        target_org, name = MenuResults(ctx)
        OUTPUT = CSP.org_show_sddcs(target_org, aws_ready, version_only, AUTH, PROFILE, raw)
        for I in OUTPUT:
            ID = I['id']
            NAME = I['name'].rjust(50)
            STRING = ID + '\t' + NAME
            DATA.append(STRING)
        INPUT = 'sddc manager'
        CHOICE = runMenu(DATA, INPUT)
        if CHOICE:
            CHOICE = ''.join(CHOICE)
            SDDC_NAME = CHOICE.split('\t')[1].strip()
            sddc_id = CHOICE.split('\t')[0]
            if SDDC_NAME:
                Log.info(f"gathering sddc information for {sddc_id} now, please wait...")
            else:
                Log.critical("please select an sddc-name to continue...")
        else:
            Log.critical("please select an sddc-name to continue...")

    SDDC = sddc(sddc_id, AUTH, PROFILE, None)
    _get_edge_status(SDDC, ticket, raw)

def _get_edge_status(SDDC, ticket, raw):

    RESULT = SDDC.nsx_status(ticket, raw)
    NSX = {}
    if RESULT != []:
        if RESULT['status'] != "FAILED":
            Log.info(RESULT['status'])
            PATTERNS = ["edge_ip_address", "edge_name", "status", "transport_node_id", "pnic_status", "mgmt_connection_status", "tunnel_status", "high_availability_status"]
            for I in RESULT['data'].replace(",","\n").split('\n'):
                line = listToStringWithoutBrackets(I).replace('"','').split(',')
                for D in PATTERNS:
                    if D == line[0].strip().split(":")[0].strip():
                        if D == "edge_ip_address":
                            IP = line[0].strip().split(":")[1].strip()
                            NSX[IP] = {line[0].strip().split(":")[0].strip(): line[0].strip().split(":")[-1].strip()}
                        else:
                            NSX[IP].update({line[0].strip().split(":")[0].strip(): line[0].strip().split(":")[-1].strip()})
        else:
            Log.json(json.dumps(RESULT, indent=2))
            Log.critical(f"nsx status for {SDDC_NAME} FAILED")
    else:
        Log.critical('something went wrong when connecting to the SDDC')

    DATADICT = {}
    DATA = []

    for I in NSX:
        DATA.append(NSX[I])

    if DATA:
        DATADICT = DATA
        Log.info(f"\n{tabulate(DATADICT, headers='keys', tablefmt='rst')}")
    else:
        Log.warn('there are 0 defined policies for BgpNeighborConfig resource')
        return None

@nsx_show.command('policy-status', help='show the policy status for NSX in a specific SDDC', context_settings={'help_option_names':['-h','--help']})
@click.argument('sddc_id', required=False, default=None)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def nsx_policy_status(ctx, sddc_id, raw):
    AUTH, PROFILE = get_operator_context(ctx)
    aws_ready = False
    version_only = False
    if sddc_id is None:
        DATA = []
        target_org, name = MenuResults(ctx)
        OUTPUT = CSP.org_show_sddcs(target_org, aws_ready, version_only, AUTH, PROFILE, raw)
        for I in OUTPUT:
            ID = I['id']
            NAME = I['name'].rjust(50)
            STRING = ID + '\t' + NAME
            DATA.append(STRING)
        INPUT = 'sddc manager'
        CHOICE = runMenu(DATA, INPUT)
        if CHOICE:
            CHOICE = ''.join(CHOICE)
            SDDC_NAME = CHOICE.split('\t')[1].strip()
            sddc_id = CHOICE.split('\t')[0]
            if SDDC_NAME:
                Log.info(f"gathering sddc information for {sddc_id} now, please wait...")
            else:
                Log.critical("please select an sddc-name to continue...")
        else:
            Log.critical("please select an sddc-name to continue...")

    SDDC = sddc(sddc_id, AUTH, PROFILE, None)
    _get_policy_status(SDDC, raw)

def _get_policy_status(SDDC, raw):

    RESULT = SDDC.nsx_policy_status(raw)
    NSX = {}
    DATADICT = {}
    if RESULT != []:
        PATTERNS = [ "display_name", "status" ]
        for I in filter_text(str(RESULT['nsx']).replace(",","\n")).split('\n'):
            field = [I.replace('"','').split(':')]
            line = listToStringWithoutBrackets(I).replace('"','').split(':')
            if line[0].strip() == f'display_name':
                DISPLAYNAME = line[1].strip()
                DATADICT[DISPLAYNAME] = {line[0].strip(): line[1].strip()}
            for D in PATTERNS:
                if D == field[0][0].strip().replace("'",""):
                    if D == 'status':
                        DATADICT[DISPLAYNAME].update({D: line[4].strip()})
                    else:
                        DATADICT[DISPLAYNAME].update({D: line[1].split(',')[0].strip()})
        NSX.update(DATADICT)
    else:
        Log.warn('there are 0 defined policies for BgpNeighborConfig resource')
        return None

    DATADICT = {}
    DATA = []

    for I in NSX:
        DATA.append(NSX[I])

    if DATA:
        DATADICT = DATA
        Log.info(f"\n{tabulate(DATADICT, headers='keys', tablefmt='rst')}")
    else:
        Log.warn('there are 0 defined policies for BgpNeighborConfig resource')
        return None
        

@nsx_show.command('cluster-status', help='show the cluster status for NSX in a specific SDDC', context_settings={'help_option_names':['-h','--help']})
@click.argument('sddc_id', required=False, default=None)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def nsx_cluster_status(ctx, sddc_id, raw):
    AUTH, PROFILE = get_operator_context(ctx)
    aws_ready = False
    version_only = False
    if sddc_id is None:
        DATA = []
        target_org, name = MenuResults(ctx)
        OUTPUT = CSP.org_show_sddcs(target_org, aws_ready, version_only, AUTH, PROFILE, raw)
        for I in OUTPUT:
            ID = I['id']
            NAME = I['name'].rjust(50)
            STRING = ID + '\t' + NAME
            DATA.append(STRING)
        INPUT = 'sddc manager'
        CHOICE = runMenu(DATA, INPUT)
        if CHOICE:
            CHOICE = ''.join(CHOICE)
            SDDC_NAME = CHOICE.split('\t')[1].strip()
            sddc_id = CHOICE.split('\t')[0]
            if SDDC_NAME:
                Log.info(f"gathering sddc information for {sddc_id} now, please wait...")
            else:
                Log.critical("please select an sddc-name to continue...")
        else:
            Log.critical("please select an sddc-name to continue...")

    SDDC = sddc(sddc_id, AUTH, PROFILE, None)
    RESULT = SDDC.nsx_cluster_status(raw)
    if RESULT != []:
        Log.json(json.dumps(RESULT, indent=2))
    else:
        Log.critical('something went wrong when connecting to the SDDC')

@nsx_show.command('credentials', help='show login credentials for NSX in a specific SDDC', context_settings={'help_option_names':['-h','--help']})
@click.argument('sddc_id', required=False, default=None)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def nsx_show_credentials(ctx, sddc_id, raw):
    AUTH, PROFILE = get_operator_context(ctx)
    aws_ready = False
    version_only = False
    if sddc_id is None:
        DATA = []
        target_org, name = MenuResults(ctx)
        OUTPUT = CSP.org_show_sddcs(target_org, aws_ready, version_only, AUTH, PROFILE, raw)
        for I in OUTPUT:
            ID = I['id']
            NAME = I['name'].rjust(50)
            STRING = ID + '\t' + NAME
            DATA.append(STRING)
        INPUT = 'sddc manager'
        CHOICE = runMenu(DATA, INPUT)
        if CHOICE:
            CHOICE = ''.join(CHOICE)
            SDDC_NAME = CHOICE.split('\t')[1].strip()
            sddc_id = CHOICE.split('\t')[0]
            if SDDC_NAME:
                Log.info(f"gathering sddc information for {sddc_id} now, please wait...")
            else:
                Log.critical("please select an sddc-name to continue...")
        else:
            Log.critical("please select an sddc-name to continue...")

    SDDC = sddc(sddc_id, AUTH, PROFILE, None)
    RESULT = SDDC.nsx_show_credentials()
    if RESULT == []:
        Log.critical('something went wrong when connecting to the SDDC')
    else:
        Log.json(json.dumps(RESULT, indent=2))

@nsx_show.command('vpn-info', help='show vpn information for the SDDC', context_settings={'help_option_names':['-h','--help']})
@click.argument('sddc_id', required=False, default=None)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.option('-t', '--ticket', 'ticket', help="CSSD or CSCM ticket asssociated with the RTS task", type=str, required=False, default='CSSD-1234', show_default=True)
@click.option('-v', '--vpn', 'vpn', help="available VPN types are L2 or L3", default='L2', type=click.Choice(['L2', 'L3']), show_default=True)
@click.pass_context
def nsx_vpn_info(ctx, sddc_id, raw, ticket, vpn):
    AUTH, PROFILE = get_operator_context(ctx)
    aws_ready = False
    version_only = False
    if sddc_id is None:
        DATA = []
        target_org, target_name = MenuResults(ctx)
        OUTPUT = CSP.org_show_sddcs(target_org, aws_ready, version_only, AUTH, PROFILE, raw)
        for I in OUTPUT:
            ID = I['id']
            NAME = I['name'].rjust(50)
            STRING = ID + '\t' + NAME
            DATA.append(STRING)
        INPUT = 'sddc manager'
        CHOICE = runMenu(DATA, INPUT)
        if CHOICE:
            CHOICE = ''.join(CHOICE)
            SDDC_NAME = CHOICE.split('\t')[1].strip()
            sddc_id = CHOICE.split('\t')[0]
            if SDDC_NAME:
                Log.info(f"gathering sddc information for {sddc_id} now, please wait...")
            else:
                Log.critical("please select an sddc-name to continue...")
        else:
            Log.critical("please select an sddc-name to continue...")

    SDDC = sddc(sddc_id, AUTH, PROFILE, None)
    RESULT = SDDC.nsx_show_vpn_info(ticket, raw=raw, vpn=vpn)
    FOUND = False

    if RESULT == []:
        Log.critical('something went wrong when connecting to the SDDC')
    else:
        Log.info(RESULT['status'])
        for I in RESULT['data'].replace(",","\n").split('\n'):
            line = listToStringWithoutBrackets(I).replace('"','').split(',')
            if line[0] == "result":
                Log.info(line[2].strip())
            else:
                Log.info(line[0].strip())

@nsx_show.command('node-details', help='show standby edge information for the SDDC', context_settings={'help_option_names':['-h','--help']})
@click.argument('sddc_id', required=False, default=None)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.option('-t', '--ticket', 'ticket', help="CSSD or CSCM ticket asssociated with the RTS task", type=str, required=False, default='CSSD-1234', show_default=True)
@click.pass_context
def nsx_node_details(ctx, sddc_id, raw, ticket):
    AUTH, PROFILE = get_operator_context(ctx)
    aws_ready = False
    version_only = False
    if sddc_id is None:
        DATA = []
        target_org, target_name = MenuResults(ctx)
        OUTPUT = CSP.org_show_sddcs(target_org, aws_ready, version_only, AUTH, PROFILE, raw)
        for I in OUTPUT:
            ID = I['id']
            NAME = I['name'].rjust(50)
            STRING = ID + '\t' + NAME
            DATA.append(STRING)
        INPUT = 'sddc manager'
        CHOICE = runMenu(DATA, INPUT)
        if CHOICE:
            CHOICE = ''.join(CHOICE)
            SDDC_NAME = CHOICE.split('\t')[1].strip()
            sddc_id = CHOICE.split('\t')[0]
            if SDDC_NAME:
                Log.info(f"gathering sddc information for {sddc_id} now, please wait...")
            else:
                Log.critical("please select an sddc-name to continue...")
        else:
            Log.critical("please select an sddc-name to continue...")

    SDDC = sddc(sddc_id, AUTH, PROFILE, None)
    RESULT = SDDC.nsx_show_node_details(ticket, raw)
    FOUND = False

    if RESULT == []:
        Log.critical('something went wrong when connecting to the SDDC')
    else:
        for I in filter_text(RESULT['data']['params']['SCRIPTDATA']['data'].replace(",","\n")).split('\n'):
            FOUND = True
            line = listToStringWithoutBrackets(I).replace('"','').split(':')
            Log.info(line[0] + " => " + str(line[1:]))
        if FOUND is False:
            Log.critical(f'unable to find active NSX edges for {SDDC_NAME}')

@nsx_show.command('standby-edge', help='show standby edge information for the SDDC', context_settings={'help_option_names':['-h','--help']})
@click.argument('sddc_id', required=False, default=None)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.option('-t', '--ticket', 'ticket', help="CSSD or CSCM ticket asssociated with the RTS task", type=str, required=False, default='CSSD-1234', show_default=True)
@click.pass_context
def standby_nsx_edges(ctx, sddc_id, raw, ticket):
    AUTH, PROFILE = get_operator_context(ctx)
    aws_ready = False
    version_only = False
    if sddc_id is None:
        DATA = []
        target_org, target_name = MenuResults(ctx)
        OUTPUT = CSP.org_show_sddcs(target_org, aws_ready, version_only, AUTH, PROFILE, raw)
        for I in OUTPUT:
            ID = I['id']
            NAME = I['name'].rjust(50)
            STRING = ID + '\t' + NAME
            DATA.append(STRING)
        INPUT = 'sddc manager'
        CHOICE = runMenu(DATA, INPUT)
        if CHOICE:
            CHOICE = ''.join(CHOICE)
            SDDC_NAME = CHOICE.split('\t')[1].strip()
            sddc_id = CHOICE.split('\t')[0]
            if SDDC_NAME:
                Log.info(f"gathering sddc information for {sddc_id} now, please wait...")
            else:
                Log.critical("please select an sddc-name to continue...")
        else:
            Log.critical("please select an sddc-name to continue...")

    SDDC = sddc(sddc_id, AUTH, PROFILE, None)
    RESULT = SDDC.nsx_show_standby_edge(ticket, raw)
    FOUND = False

    if RESULT == []:
        Log.critical('something went wrong when connecting to the SDDC')
    else:
        PATTERNS = ["sddc_state", "sddc_version", "org_id", "org_type", "sddc_id", "resource_type", "maintenance_mode", "ip_addresses", "node_display_name", "overall_status", "vm_name", "vm_host", "host_node_deployment_status", "node_id"]
        for I in filter_text(RESULT['data']['params']['SCRIPTDATA']['data'].replace(",","\n")).split('\n'):
            field = [I.replace('"','').split(':')]
            for D in PATTERNS:
                if D == field[0][0]:
                    FOUND = True
                    line = listToStringWithoutBrackets(I).replace('"','').split(':')
                    Log.info(line[0] + " => " + line[1])
        if FOUND is False:
            Log.critical(f'unable to find active NSX edges for {SDDC_NAME}')

@nsx_show.command('active-edge', help='show active edge information for the SDDC', context_settings={'help_option_names':['-h','--help']})
@click.argument('sddc_id', required=False, default=None)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.option('-t', '--ticket', 'ticket', help="CSSD or CSCM ticket asssociated with the RTS task", type=str, required=False, default='CSSD-1234', show_default=True)
@click.pass_context
def active_nsx_edges(ctx, sddc_id, raw, ticket):
    AUTH, PROFILE = get_operator_context(ctx)
    aws_ready = False
    version_only = False
    if sddc_id is None:
        DATA = []
        target_org, target_name = MenuResults(ctx)
        OUTPUT = CSP.org_show_sddcs(target_org, aws_ready, version_only, AUTH, PROFILE, raw)
        for I in OUTPUT:
            ID = I['id']
            NAME = I['name'].rjust(50)
            STRING = ID + '\t' + NAME
            DATA.append(STRING)
        INPUT = 'sddc manager'
        CHOICE = runMenu(DATA, INPUT)
        if CHOICE:
            CHOICE = ''.join(CHOICE)
            SDDC_NAME = CHOICE.split('\t')[1].strip()
            sddc_id = CHOICE.split('\t')[0]
            if SDDC_NAME:
                Log.info(f"gathering sddc information for {sddc_id} now, please wait...")
            else:
                Log.critical("please select an sddc-name to continue...")
        else:
            Log.critical("please select an sddc-name to continue...")

    SDDC = sddc(sddc_id, AUTH, PROFILE, None)
    RESULT = SDDC.nsx_show_active_edge(ticket, raw)
    FOUND = False

    if RESULT == []:
        Log.critical('something went wrong when connecting to the SDDC')
    else:
        PATTERNS = ["sddc_state", "sddc_version", "org_id", "org_type", "sddc_id", "resource_type", "maintenance_mode", "ip_addresses", "node_display_name", "overall_status", "vm_name", "vm_host", "host_node_deployment_status", "node_id"]
        for I in filter_text(RESULT['data']['params']['SCRIPTDATA']['data'].replace(",","\n")).split('\n'):
            field = [I.replace('"','').split(':')]
            for D in PATTERNS:
                if D == field[0][0]:
                    FOUND = True
                    line = listToStringWithoutBrackets(I).replace('"','').split(':')
                    Log.info(line[0] + " => " + line[1])
        if FOUND is False:
            Log.critical(f'unable to find active NSX edges for {SDDC_NAME}')

def listToStringWithoutBrackets(list1):
    return str(list1).replace('[','').replace(']','').replace("'", "").replace("{","").replace("}","")

def filter_characters(text):
    # we use this dictionary to match opening/closing tokens
    STATES = {
        '"': '"', "'": "'",
        "{": "}", "[": "]"
    }

    # these two variables represent the current state of the parser
    escaping = False
    state = list()

    # we iterate through each character
    for c in text:
        if escaping:
            # if we are currently escaping, no special treatment
            escaping = False
        else:
            if c == "\\":
                # character is a backslash, set the escaping flag for the next character
                escaping = True
            elif state and c == state[-1]:
                # character is expected closing token, update state
                state.pop()
            elif c in STATES:
                # character is known opening token, update state
                state.append(STATES[c])
            elif c == ';' and state == ['}']:
                # this is the delimiter we want to change
                c = ','
        yield c

    assert not state, "unexpected end of file"

def filter_text(text):
    return ''.join(filter_characters(text))

@nsx_show.command('logical-routers', help='show logical routers in a specific SDDC', context_settings={'help_option_names':['-h','--help']})
@click.argument('sddc_id', required=False, default=None)
@click.option('-t', '--type', help="available types are TIER0, TIER1, or TIER2", default='ALL', type=click.Choice(['TIER0', 'TIER1', 'ALL']), show_default=True)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def nsx_logical_routers(ctx, sddc_id, type, raw):
    AUTH, PROFILE = get_operator_context(ctx)
    aws_ready = False
    version_only = False
    if sddc_id is None:
        DATA = []
        target_org, name = MenuResults(ctx)
        OUTPUT = CSP.org_show_sddcs(target_org, aws_ready, version_only, AUTH, PROFILE, raw)
        for I in OUTPUT:
            ID = I['id']
            NAME = I['name'].rjust(50)
            STRING = ID + '\t' + NAME
            DATA.append(STRING)
        INPUT = 'sddc manager'
        CHOICE = runMenu(DATA, INPUT)
        if CHOICE:
            CHOICE = ''.join(CHOICE)
            SDDC_NAME = CHOICE.split('\t')[1].strip()
            sddc_id = CHOICE.split('\t')[0]
            if SDDC_NAME:
                Log.info(f"gathering sddc information for {sddc_id} now, please wait...")
            else:
                Log.critical("please select an sddc-name to continue...")
        else:
            Log.critical("please select an sddc-name to continue...")

    SDDC = sddc(sddc_id, AUTH, PROFILE, None)
    RESULT = SDDC.nsx_show_logical_routers(type, raw)
    if RESULT == []:
        Log.critical('something went wrong when connecting to the SDDC')
    else:
        Log.json(json.dumps(RESULT, indent=2))

def runMenu(DATA, INPUT):
    COUNT = 0
    FINAL = []
    TITLE = f'VMC Menu: {INPUT}'
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

def wait_with_message(seconds):
    while True:
        Log.info(f"sleeping for {seconds} seconds, please wait...")
        time.sleep(30)
        seconds = seconds - 30
        if seconds <= 0:
            Log.info("FINISHED")
            break
    return True

