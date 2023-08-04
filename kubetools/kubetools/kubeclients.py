import os, subprocess, tempfile, importlib_resources
from toolbox.misc import detect_environment
from configstore.configstore import Config
from toolbox.results import rv

class k8sclient():
    def __init__(self):
        pass

    def run(self, cmd):
        RESULT = run_command('kubectl ' + cmd)
        return RESULT

class vdpclient():
    def __init__(self):
        self.CONFIG = Config('kubetools') # no support for multiple profiles at the moment
        if 'default' not in self.CONFIG.PROFILES:
            self.CONFIG.create_profile()
        self.ENDPOINT = self.CONFIG.get_config('vdp_endpoint', 'default')
        if self.ENDPOINT is None:
            self.CONFIG.get_var('vdp_endpoint', 'config', 'VDP_ENDPOINT', 'default')
        self.CLUSTERS = self.CONFIG.get_config('vdp_clusters', 'default')
        if self.CLUSTERS is None:
            CLUSTERS = get_vdp_clusters()
            self.CLUSTERS = CLUSTERS
            self.CONFIG.update_config(CLUSTERS, 'vdp_clusters', 'default')

    def run(self, cmd):
        RESULT = run_command('vdp ' + cmd)
        return RESULT

    def set_cluster(self, cluster_short_name):
        K8S = k8sclient()
        KNOWN_CLUSTERS = self.CLUSTERS
        KNOWN_CLUSTER_NAMES = []
        FOUND = False
        for CLUSTER in KNOWN_CLUSTERS:
            if cluster_short_name == CLUSTER['short_name']:
                FOUND = True
                CLUSTER_LONG_NAME = f"{CLUSTER['name']}"
            else:
                KNOWN_CLUSTER_NAMES.append(CLUSTER['short_name'])
        if not FOUND:
            return rv(False, f'incorrect cluster specified - {cluster_short_name}\nknown VDP clusters: {KNOWN_CLUSTER_NAMES}')
        else:
            CONTEXT = f"{os.environ['USER']}-{CLUSTER_LONG_NAME}"
            RESULT = K8S.run(f"config use-context {CONTEXT}")
            if RESULT['status'] is False:
                return rv(False, f"failed to set context {CONTEXT}\nmsg: {RESULT['output']}")
            else:
                return rv(True, f'context {CONTEXT} set successfully\n')

def get_vdp_clusters():
    C = 0
    RESULT = detect_environment()
    CLUSTERS = {}
    MY_RESOURCES = importlib_resources.files("toolbox")
    DATA = (MY_RESOURCES / "vdp_clusters.cfg")
    if RESULT == 'gc-prod':
        with open(DATA) as f:
            CONTENTS = f.read()
            for line in CONTENTS.split('\n'):
                C = C + 1
                D = C - 1
                if C == 1:
                    continue
                if line:
                    ORG_ID = line.split(",")[0]
                    CLUSTER_NAME = line.split(",")[1]
                    CLUSTER_SHORT_NAME = CLUSTER_NAME.split('-')[0]
                    CLUSTERS[D] = { 'org': ORG_ID, 'name': CLUSTER_NAME, 'short_name': CLUSTER_SHORT_NAME}
    return CLUSTERS

def run_command(command):
    OUT_1 = tempfile.NamedTemporaryFile(delete=False)
    OUT_2 = tempfile.NamedTemporaryFile(delete=False)
    CMD = command + " 1> " + OUT_1.name + " 2>" + OUT_2.name
    PROC = subprocess.run(CMD, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    with open(OUT_2.name, 'r') as FILE:
        ERROR = FILE.read()
        ERROR = ERROR.split('\n')[0] # vdp has some bizzare way of showing errors 
    if ERROR == "" or ERROR is None:
        with open(OUT_1.name, 'r') as FILE:
            OUTPUT = FILE.read()
            STATUS = True
    else:
        OUTPUT = ERROR
        STATUS = False
    os.remove(OUT_1.name)
    os.remove(OUT_2.name)
    return rv(STATUS, OUTPUT)
