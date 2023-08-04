import os, time
from .vmcclient import vmc
from kubetools.kubeclients import vdpclient
from kubetools.kubeclients import k8sclient
from toolbox.results import rv, rnv
from toolbox.logger import Log

class popclient():
    
    def __init__(self, auth, user_profile):
        self.VMC = vmc(auth, user_profile)
        self.VDP = vdpclient()
        self.K8S = k8sclient()
        self.USER_PROFILE = user_profile
        self.AUTH_ORG = auth_org

    def start_vdp_pod(self):
        NAMESPACE = self.VMC.CONFIG.get_var('vmc_namespace', 'config', 'VMC_NAMESPACE', self.USER_PROFILE)
        WAIT_TIME = 10
        ELAPSED_TIME = 0
        POD = f"{os.getenv('USER').split('@')[1]}-pop"
        if not self.VDP.set_cluster('res02').ok:
            return rv(False, 'failed to switch context to res02')
        Log.info(f'making sure that user pod is running in {NAMESPACE} namespace')
        RESULT = self.K8S.run(f'-n {NAMESPACE} get pods 2> /dev/null | grep {POD}')
        if 'Completed' in RESULT.msg:
            Log.debug(self.K8S.run(f'delete pod -n {NAMESPACE} {POD}').msg)
        if not self.K8S.run(f'-n {NAMESPACE} get pod {POD}').ok:
            RESULT = self.K8S.run(f'-n {NAMESPACE} run --restart=Never --attach=false -it {POD} --image=nexus.delta.govcloud.pdx.vmwarefed.com:8084/govcloud-ops/govops-util:latest --overrides="{{"metadata" : {{ "annotations" : {{ "seccomp.security.alpha.kubernetes.io/pod" : "docker/default"}}}},"apiVersion": "v1", "spec": {{"imagePullSecrets":[{{"name": "vmware-nexus-secret"}}],"containers":[{{"name": "{POD}","image": "nexus.delta.govcloud.pdx.vmwarefed.com:8084/govcloud-ops/govops-util:latest","securityContext": {{"allowPrivilegeEscalation": false, "runAsUser": 1001}}}}]}}}}"')
            Log.debug(RESULT.msg)
        while True:
            if self.K8S.run(f'-n {NAMESPACE} get pod {POD} | grep -q Running').msg == "":
                return rnv(True, ['msg', f'{POD} started in {NAMESPACE}'], ['pod', POD])
            print('.')
            time.sleep(1)
            ELAPSED_TIME = ELAPSED_TIME + 1
            if ELAPSED_TIME > WAIT_TIME:
                return rv(False, f'failed to start {POD} pod after {WAIT_TIME}s')
