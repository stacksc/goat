# ==============================================================================
# Copyright (c) 2020, Oracle and/or its affiliates. All rights reserved.
# ==============================================================================
# common variables and functions for python can be imported from this file

from contextlib import contextmanager
from contextlib import closing
from subprocess import Popen, PIPE

import socket
import color

import sys, os, pickle, re, socket, subprocess

RESET = '\033[0m'
CYAN = '\033[0;36m'
RED = '\033[1;31m'
YELLOW = '\033[0;33m'
GREEN = '\033[0;32m'
MAGENTA = '\033[0;35m'
BLUE = '\033[38;5;69m'
ORANGE = '\033[38;5;172m'
UNDERLINE = '\033[4m'
BOLD = '\033[1m'
SCREEN_WIDTH = 95
MOVE1 = '\033[70G'
MOVE2 = '\033[100G'
myhost = socket.gethostname().lower()
site = myhost.split("-")[0].strip().upper()
#gatewayfile = '/opt/ORCLemaas/omcdevops/omccli/scratch/gateways.csv'
#gateways = [line.split(',')[1].strip().lower() for line in open(gatewayfile)]
#secondary_gw = [line.split(',')[2].strip().lower() for line in open(gatewayfile)]
#draw_layout = '/opt/ORCLemaas/omcdevops/omccli/modules/omcshell/lib/OmcUi.py'
#draw_usage = '/opt/ORCLemaas/omcdevops/omccli/modules/omcshell/lib/Usage.py'

def printBanner():

    if 'US2Z24' in site or 'NL1Z15' in site:
        color.printTitle()
    else:
        os.system(draw_layout)

def check_socket(host, port):
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        if sock.connect_ex((host, port)) == 0:
            return 0
        else:
            return -1

def getGateway():
    for s in gateways:
        if site.lower() in s:
            gateway = str(s)
            gateway = ''.join(gateway)
            break
    return gateway

def getSecondary():
    for s in secondary_gw:
        if site.lower() in s:
            secondary = str(s)
            secondary = ''.join(secondary)
            break
    return secondary

def get_username():
    from os import environ, getcwd
    user = (lambda: environ["USERNAME"] if "C:" in getcwd() else environ["USER"])()
    return user

def printInfo(message):

    mydate = os.popen("date +'%A %Y-%m-%d %R %Z'").read().strip()
    message = GREEN + "[ MESSAGE ]" + RESET + " [ %s ] [ %s ]" %(mydate, message)
    print(message)

def printWarn(message):

    mydate = os.popen("date +'%A %Y-%m-%d %R %Z'").read().strip()
    message = YELLOW + "[ WARNING ]" + RESET + " [ %s ] [ %s ]" %(mydate, message)
    print(message)

def printFail(message):

    mydate = os.popen("date +'%A %Y-%m-%d %R %Z'").read().strip()
    message = RED + "[ FAILURE ]" + RESET + " [ %s ] [ %s ]" %(mydate, message)
    print(message)

def info(string,a=''):
    if a != '':
        print(YELLOW + "INFO: " + RESET + string%a)
    else:
        print(YELLOW + "INFO: " + RESET + string)

def error(string,a=''):
    if a != '':
        print(RED + "ERROR:" + RESET + string%a)
    else:
        print(RED + "ERROR:" + RESET + string)

def warn(string,a=''):
    if a != '':
        print(YELLOW + "WARN: " + RESET + string%a)
    else:
        print(YELLOW + "WARN: " + RESET + string)

def getTier():
    if any(re.findall(r'agt-1|agt-2|gwaytier-service-mgr|serviceregistrynode-1', myhost, re.IGNORECASE)):
        tier = 'GW'
    elif any(re.findall(r'ctr-1|service-manager-and-provisioning1|service-mgr-prov1|smandprovisioningnode', myhost, re.IGNORECASE)):
        tier = 'CT'
    else:
        tier = 'UNKNOWN'
    return tier

def startTunnel(gateway):

    # run a connection to gateway node in the background, make things faster for future runs on this node
    # tear it down later
    cmd = 'ssh -F /opt/ORCLemaas/omcdevops/omccli/.ssh/config -o ConnectTimeout=30 -tt -N %s >/dev/null 2>&1 &' %(str(gateway))
    os.system(cmd)
    return

def connectGateway(gateway, start_shell):

    if start_shell is True:
        cmd = "ssh -q -t " + str(gateway) + " \"omc\"" + " -o ""ProxyCommand=nc -x localhost:54021 %h %p"""
    else:
        cmd = "ssh -q %s" %(gateway)
    os.system(cmd)
    return

def sshStatus(gateway):

    cmd = 'ps -ef | grep ssh| grep %s | grep -v grep | awk "{print \$2}"' %(gateway)
    proc = subprocess.Popen([cmd], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()

    return out, err

def stopTunnel(pid):

    cmd = 'kill -9 %s >/dev/null 2>&1' %(pid)
    os.system(cmd)

def tunnelTasks(action):

    sockit = {}
    number = 0

    # start up our tunnel immediately
    gateway = getGateway()
    secondary = getSecondary()
    h = '127.0.0.1'
    port1 = 54021
    res = check_socket(h, port1)
    port2 = 54022
    ret = check_socket(h, port2)

    if res != 0:
        # start tunnel in background
        if action == 'start':
            startTunnel(gateway)
    else:
        # get pid
        pid = sshStatus(gateway)[0].strip()
        if action == 'start':
            if not pid:
                startTunnel(gateway)
        elif action == 'stop':
            if pid:
                stopTunnel(pid)
        sockit[gateway] = [number]
        sockit[gateway].append(pid)
        sockit[gateway].append(port1)
        number = number + 1

    if ret != 0:
        # start tunnel in background
        if action == 'start':
            startTunnel(secondary)
    else:
        # get pid
        pid = sshStatus(secondary)[0].strip()
        if action == 'start':
            if not pid:
                startTunnel(secondary)
        elif action == 'stop':
            if pid:
                stopTunnel(pid)
        sockit[secondary] = [number]
        sockit[secondary].append(pid)
        sockit[secondary].append(port2)
        number = number + 1

    return sockit
