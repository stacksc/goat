<img src="./images/PYPS-Icon1.png" alt="PYPS" width="200"/>
<a name="readme-top"></a>
<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#contacts">Contacts</a></li>
    <li><a href="#mp4-and-image-collections">MP4 & Image Collections</a></li>
    <li><a href="#docker-example">Docker Example</a></li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->
## About The Project

PYPS ("pipes") - PYthon tools by PSsre team - a front-end application for most Python modules created by the Public Sector SRE team. Source code of this app can also be used as an example of how to write code using our internal modules and how to integrate multiple modules together in a single app/package.<br><br>
The PYPS repository and code is for demonstration purposes; this is only to showcase a basic application to common APIs.

## Current Usage
```
pyps -h
Usage: pyps [OPTIONS] COMMAND [ARGS]...

  pyps - PYthon tools by PSsre team - pronounced as 'pipes'

Options:
  -d, --debug [0|1|2]  0 = no output, 1 = default, 2 = debug on
  -v, --version        print version of pyps and all its submodules
  -a, --aliases        print all defined aliases and shortcuts
  -m, --manuals TEXT   print all defined manuals matching pattern(s)
  -s, --setup          setup client(s) for pyps interaction
  -h, --help           Show this message and exit.

Commands:
  aws         VMware AWS CLI Client    -> Current Profile: VMCDELTA
  configs     VMware Config Client     -> Current Profile: N/A
  confluence  VMware Confluence CLI    -> Current Profile: DEFAULT
  fly         VMware Concourse CLI     -> Current Profile: DEFAULT
  git         VMware GIT CLI Client    -> Current Profile: DEFAULT
  jc          VMware JC CLI Client     -> Current Profile: N/A
  jenkins     VMware Jenkins Client    -> Current Profile: DEFAULT
  jfrog       VMware JFROG CLI Client  -> Current Profile: DEFAULT
  jira        VMware JIRA CLI Client   -> Current Profile: https://servicedesk.eng.vmware.com
  report      VMware Report Module     -> Current Profile: N/A
  slack       VMware Slack CLI Client  -> Current Profile: DEFAULT
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- GETTING STARTED -->
## Getting Started

### Prerequisites
### Installation

1. Clone the repo:
   ```sh
   git clone git@github.com:stacksc/pyps.git
   ```
2. Install all required packages with 1 script from the main repository: 
   ```sh
   ./bulk.sh --action rebuild --target all
   ```
<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- ROADMAP -->
## Roadmap

- [ ] TBD - roadmap not yet available

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTRIBUTING -->
## Contributing
Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".

1. Fork the Project (optional)
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

After making changes to the source code, please remember to build a new wheel for the project by running `python3 -m build --wheel` in the root of the project (where .toml file is)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTACTS -->
## Contacts
Christopher Stacks - <stacksc@vmware.com>

<!-- MP4_Collections -->
## MP4 and Image Collections

Native notifications included to direct users to the README document for critical failures:
<br><br>
<img src="./images/notify.jpg" alt="Native Notifications" width="600"/>
<br><br>
The following image is demonstrated out-of-bounds where specific modules are loaded.
<br><br>
PYPS is fine-tuned to behave differently based on the environment.
<br><br>
<img src="./images/pyps-usage.jpg" alt="PYPS Usage" width="600"/>
<br><br>

<!-- DOCKER_EXAMPLE -->
## Docker Example
<details><summary>Docker Example</summary>

```
$ ./prep_env.sh
INFO: preparing to build our docker container
      using multiple tools, scripts and utilities to make the magic happen. Enjoy!

INFO: AWS ACCESS KEY ID & SECRET KEY can be retrieved from: https://sks-gov-ctrl.signin.amazonaws-us-gov.com
INFO: generate new keys if they are inactive, lost, etc...

[0] would you like to use /Users/stacksc/.env for docker preparation? [y/n] y
[1] Enter SSO PASSWORD: **************

===================================================================================
INFO: verify the following information is accurate:
===================================================================================

INFO: GUID User ID:                  stacksc
INFO: AWS_ACCESS_KEY_ID:             ********************
INFO: AWS_SECRET_ACCESS_KEY:         *********************************
INFO: SLACK_BOT_TOKEN:               xoxb-2154537752-4006410458018-2ksepJwq1D21SRY75jI3bfg7
INFO: GIT:                           /home/stacksc/git
INFO: REGION:                        us-gov-west-1

INFO: starting the docker build process, which will stop any running PYPS containers, & prune prior to starting

WARNING! This will remove:
  - all stopped containers
  - all networks not used by at least one container
  - all dangling images
  - all dangling build cache

Are you sure you want to continue? [y/N] Deleted Containers:
b37c7ffa0071627befc0b8b54115edf60b5a88e1e5b6c62c215fca61513d86cf
2c846706a46a3cad72cef1d8ee9f4362db953971bb9f5d013325b51d89aa7c54

Deleted Images:
deleted: sha256:5b6dd0cb7e97b2d1fab2d74a407afc1b1eee03ce6988478a3778cdd8843c1c4d

Deleted build cache objects:
qd67x2au3xf6brr6cjpwvmwh4
2wpusx7ucmrp2edl02lcf7sd5
aqsfo8vs5v5skv6mthrle4r6z
w4gqsg25sm6hgmtjinjdmeus2
ynipegnjgpcz657oy1ci87i5w
ytvi0c4h1c3s0uf8o3c7tnf2m
igoa04qaw7uzu2790bk0z89b3
8hsnwlmvxg2mzl3fsiu1sgzey
rn53li7h1xi8n0isfwh5y1xkl
p3l2j3hsg3g3mio5qx3zf3nnr
rd4wjldmril0aj97j53nd2cnc
6wewwix0y5s9hfytnajp7tjlm
uywzzq3n8yo2du31rl765lezs
pb6drc62embfahaorwbzobf0j
uizqb6hb0tnecuj8n2y5k97zr
992999iaxrfjo5hjvodwqyzla
dpvmkt8zuyhept06ca4rntygr
c01bx8vp6gvlkip1zprqgakrf
apcbjyqemohukxslfa6rm29d9
1ycgp691ygesqdzih6meq3khy
szd99mt1c2hvf52uknru5u94e
wprqg4h54ugqq17fv7rvdko66
mr8pqxo264soyit2b1lkbaxf2
vjk954fpe2mfs63ry8ma6802u
7ucy70bl9rkowbw3e3ni6zzjz
0vy3a12gz90rk0kiwsgitvimn
m4reyneza1i2o7m9v1iidj4r2
izysx9q540l1vaukn7xaqm96n
qrh1lxe3khxvobbzyc8lykg4h
yo9zyoqwci74qxpffddhh9p3p
1b82fn70c29xqolq1o6s0m7zw
nkl1e7l9rqdjr1v2c3gnp9s5s
sr5cshjibrja38ljp0jjaevcq

Total reclaimed space: 1.317GB

[+] Building 76.8s (35/52)
[+] Building 157.1s (53/53) FINISHED
 => [internal] load build definition from Dockerfile                                                                                                                            0.0s
 => => transferring dockerfile: 5.90kB                                                                                                                                          0.0s
 => [internal] load .dockerignore                                                                                                                                               0.0s
 => => transferring context: 2B                                                                                                                                                 0.0s
 => [internal] load metadata for docker.io/library/centos:latest                                                                                                                1.3s
 => [internal] load build context                                                                                                                                               7.3s
 => => transferring context: 319.16MB                                                                                                                                           7.2s
 => [ 1/48] FROM docker.io/library/centos@sha256:a27fd8080b517143cbbbab9dfb7c8571c40d67d534bbdee55bd6c473f432b177                                                               0.0s
 => CACHED [ 2/48] RUN dnf --disablerepo '*' --enablerepo=extras swap centos-linux-repos centos-stream-repos -y # buildkit                                                      0.0s
 => CACHED [ 3/48] RUN yum -y update # buildkit                                                                                                                                 0.0s
 => CACHED [ 4/48] RUN yum install man git gcc openssl-devel bzip2-devel libffi-devel zlib-devel zlib-devel sqlite-devel wget vim sudo net-tools yum-utils vim sudo net-tools   0.0s
 => CACHED [ 5/48] RUN curl https://www.python.org/ftp/python/3.9.15/Python-3.9.15.tgz --output /tmp/Python-3.9.15.tgz # buildkit                                               0.0s
 => CACHED [ 6/48] WORKDIR /tmp                                                                                                                                                 0.0s
 => CACHED [ 7/48] RUN tar xzf Python-3.9.15.tgz # buildkit                                                                                                                     0.0s
 => CACHED [ 8/48] WORKDIR /tmp/Python-3.9.15                                                                                                                                   0.0s
 => CACHED [ 9/48] RUN ./configure --enable-optimizations # buildkit                                                                                                            0.0s
 => CACHED [10/48] RUN yum install make -y # buildkit                                                                                                                           0.0s
 => CACHED [11/48] RUN make altinstall # buildkit                                                                                                                               0.0s
 => CACHED [12/48] RUN yum install sudo which -y # buildkit                                                                                                                     0.0s
 => CACHED [13/48] WORKDIR /tmp                                                                                                                                                 0.0s9 => CACHED [14/48] RUN rm -r Python-3.9.15.tgz # buildkit                                                                                                                       0.0s
 => CACHED [15/48] RUN yum -y install epel-release coreutils python3-argcomplete --allowerasing # buildkit                                                                      0.0s
 => CACHED [16/48] RUN curl https://bootstrap.pypa.io/get-pip.py --output get-pip.py # buildkit                                                                                 0.0s
 => CACHED [17/48] RUN python3.9 get-pip.py # buildkit                                                                                                                          0.0s
 => CACHED [18/48] RUN python3.9 -m pip install --upgrade pip # buildkit                                                                                                        0.0s
 => CACHED [19/48] WORKDIR /var/tmp                                                                                                                                             0.0s
 => [20/48] COPY . /var/tmp/                                                                                                                                                    0.7s
 => [21/48] RUN yum -y install openssh-server openssh-clients sudo pinentry # buildkit                                                                                         25.4s
 => [22/48] RUN --mount=type=secret,id=my_env source /run/secrets/my_env && adduser -m stacksc --shell /bin/bash --comment "pyps user" &&     usermod -aG wheel stacksc &&      1.4s
 => [23/48] RUN --mount=type=secret,id=my_env source /run/secrets/my_env && echo "$SSH_PRV_KEY" > /home/stacksc/.ssh/id_rsa &&     echo "$SSH_PUB_KEY" > /home/stacksc/.ssh/id  0.2s
 => [24/48] RUN yum -y install python3-boto3 jq awscli gnupg2 npm python3-tabulate # buildkit                                                                                   9.6s
 => [25/48] RUN systemctl enable sshd.service # buildkit                                                                                                                        0.2s
 => [26/48] RUN unlink /usr/bin/python3                                                                                                                                         0.2s
 => [27/48] RUN ln -s /usr/local/bin/python3.9 /usr/bin/python3                                                                                                                 0.2s
 => [28/48] RUN --mount=type=secret,id=my_env source /run/secrets/my_env && touch /home/stacksc/.gnupg/gpg-agent.conf &&     chmod 700 -R /home/stacksc/.gnupg &&     chown -R  0.2s
 => [29/48] RUN --mount=type=secret,id=my_env source /run/secrets/my_env && sudo su - stacksc -c "/usr/bin/python3 -m pip install click-man bs4 importlib_resources gnureadlin  5.7s
 => [30/48] RUN --mount=type=secret,id=my_env source /run/secrets/my_env && sudo su - stacksc -c "git config --global user.email stacksc@vmware.com"                            0.2s
 => [31/48] RUN --mount=type=secret,id=my_env source /run/secrets/my_env && sudo su - stacksc -c "git config --global user.name stacksc"                                        0.2s
 => [32/48] RUN --mount=type=secret,id=my_env source /run/secrets/my_env && sudo su - stacksc -c "cd /home/stacksc/git && git clone git@gitlab.eng.vmware.com:govcloud-ops/go  24.9s
 => [33/48] RUN --mount=type=secret,id=my_env source /run/secrets/my_env && sudo su - stacksc -c "cd /home/stacksc/git/govcloud-devops-python && bash ./bulk.sh --action rebu  68.4s
 => [34/48] RUN cp /var/tmp/legacy/vmcgov/load_prompt.sh /home/stacksc/                                                                                                         0.2s
 => [35/48] RUN cp /var/tmp/legacy/.bashrc /home/stacksc/                                                                                                                       0.3s
 => [36/48] RUN cp /var/tmp/legacy/.bash_profile /home/stacksc/                                                                                                                 0.2s
 => [37/48] RUN chown stacksc:stacksc /home/stacksc/.bashrc                                                                                                                     0.2s
 => [38/48] RUN chown stacksc:stacksc /home/stacksc/.bash_profile                                                                                                               0.2s
 => [39/48] RUN chown stacksc:stacksc /home/stacksc/load_prompt.sh                                                                                                              0.2s
 => [40/48] RUN chmod 777 /usr/share/man/man1                                                                                                                                   0.3s
 => [41/48] RUN --mount=type=secret,id=my_env source /run/secrets/my_env && sudo su - stacksc -c "export JIRA_API_TOKEN=${SSO_PASS}; export LOGNAME=stacksc; /home/stacksc/.lo  2.1s
 => [42/48] RUN --mount=type=secret,id=my_env source /run/secrets/my_env && sudo su - stacksc -c "export JIRA_API_TOKEN=${SSO_PASS}; export LOGNAME=stacksc; /home/stacksc/.lo  2.8s
 => [43/48] RUN --mount=type=secret,id=my_env source /run/secrets/my_env && sudo su - stacksc -c "export SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN}; export LOGNAME=stacksc; pyps slac  1.0s
 => [44/48] RUN --mount=type=secret,id=my_env source /run/secrets/my_env && sudo su - stacksc -c "click-man pyps -t /usr/share/man/man1"                                        1.2s
 => [45/48] RUN python3.9 -m pip install --upgrade pip # buildkit                                                                                                               0.7s
 => [46/48] RUN sudo activate-global-python-argcomplete # buildkit                                                                                                              0.3s
 => [47/48] RUN sudo chmod 755 /usr/share/man/man1                                                                                                                              0.2s
 => [48/48] WORKDIR /home/stacksc                                                                                                                                               0.0s
 => exporting to image                                                                                                                                                          1.1s
 => => exporting layers                                                                                                                                                         1.1s
 => => writing image sha256:38eb56084fead8cd123bfc7c30655ded108fed4866abdf3ab21f3fd773e36223                                                                                    0.0s
 => => naming to docker.io/library/pyps                                                                                                                                         0.0s

fb073a69d77a5b851e24e93564392711e063d617214dceb64035819c892b8f47

CONTAINER ID   IMAGE     COMMAND       CREATED                  STATUS                  PORTS     NAMES
fb073a69d77a   pyps      "/bin/bash"   Less than a second ago   Up Less than a second             affectionate_lederberg

INFO: login to pyps now with: docker exec -it $(docker ps -a| grep pyps | awk '{print $1}') bash -l
INFO: copying .env to /Users/stacksc and out of the main repository
INFO: pyps docker build is complete!
```

</details>

## JIRA Authentication
1. The following example demonstrates JIRA authentication for the first time:
```
pyps jira -p stage auth -u https://servicedesk-stage.eng.vmware.com -m pass
Enter username [stacksc] :
Enter password: **************
INFO: Caching some system info now to save time later... please wait
INFO: Caching facts complete
```

## AWS Authentication
1. The following example demonstrates AWS authentication for the first time:
```
$ pyps aws -p default iam authenticate --region us-gov-west-1 --output json
Please enter AWS_KEY_ID: AKIARO3EFWTTEEIKKCFH
Please enter AWS_SECRET_ACCESS_KEY: ****************************************
INFO: credentials saved successfully
INFO: aws profile caching initialized
INFO: caching s3 data...
INFO: caching ec2 data...
INFO: caching rds data...
INFO: you can now use your new profile with 'aws --profile default
```
2. The following example shows how to assume a role after authentication:
```
$ pyps aws iam assume-role atlcs
INFO: successfully assumed the role
INFO: aws profile caching initialized
INFO: caching s3 data...
INFO: caching ec2 data...
INFO: caching rds data...
INFO: run source ~/pypsrole.sh
```
## JIRA Module Demonstration
```
$ pyps jira -h
Usage: pyps jira [OPTIONS] COMMAND [ARGS]...

  VMware JIRA CLI Client               Current Profile: https://servicedesk.eng.vmware.com

Options:
  -d, --debug [0|1|2]  0 = no output, 1 = default, 2 = debug on
  -p, --profile TEXT   profile name to use when working with the jiraclient  [default: default]
  -h, --help           Show this message and exit.

Commands:
  auth     setup or change authentication settings for JIRA
  config   manage configuration details for the Jira server on this profile
  issue    manage JIRA issues
  project  manage JIRA projects
  search   search for issues in Jira
```
## Authentication setup
```
$ pyps jira -p default auth -u https://servicedesk.vmwarefed.com -m pass
WARN: Encryption key not detected. Generating a new one
Is this going to be your default profile (Y/N)? : Y
Enter username [stacksc] :
Enter password: ******************
INFO: Caching some system info now to save time later... please wait
INFO: Caching facts complete
```
## Configuration / Cached Data
```
$ pyps jira config
{
    "config": {
        "mode": "pass",
        "url": "https://servicedesk.vmwarefed.com",
        "default": "Y",
        "user": "stacksc",
        "pass": "******************"
    },
    "metadata": {
        "name": "default",
        "created_by": "stacksc@admins.vmwarefed.com",
        "created_at": "1676180080.897811",
        "projects": {
            "CSCM": {},
            "CSSD": {},
            "GUAR": {},
            "ITEX": {},
            "TEMP": {},
            "UCP": {},
            "UCPS": {},
            "VLOPS": {}
         }
    }
}
```
## Project Search
```
$ pyps jira project search -h
Usage: pyps jira project search [OPTIONS] [PROJECTS]...

  show a summary of projects matching the specified filter

Options:
  -a, --assignee TEXT  i.e. jdoe
  -g, --group TEXT     i.e. devops
  -r, --reporter TEXT  i.e. smithj
  -s, --status TEXT    i.e. closed
  --summary TEXT       text to search for in the summary field
  --description TEXT   text to search for in the description field
  -l, --limit INTEGER  max amount of issues to show
  -o, --orderby TEXT   choose which field to use for sorting
  -A, --ascending      show issues in ascending order
  -D, --descending     show issues in descending order
  -c, --csv TEXT       name of the csv file to save the results to
  -J, --json           output results in JSON format
  -w, --wizard         output results in wizard format for transitioning
  -t, --tui            use the native TUI to launch tickets in the browser
  -h, --help           Show this message and exit.

```
## Example Search
```
pyps jira project search CSCM -a stacksc -l 10
INFO: project = "CSCM" AND assignee = "stacksc"
INFO: scanned 10 tickets in 2.9686810970306396 seconds

INFO:
==========  ========  ============  ===================  ===========================================================================================================  ==========
key         status    assignee      reporter             summary                                                                                                      launcher
==========  ========  ============  ===================  ===========================================================================================================  ==========
CSCM-42185  Closed    Chris Stacks  Archana B S          Govcloud-Atlas SaaS Service Production Push - atlas-vmc-sidecar-log-forwarder                                CSCM-42185
CSCM-42150  Closed    Chris Stacks  Andrey Karadzha (c)  Govcloud-Atlas Atlas Base Image Production Promotion - atlas-atlas-base-image - 2.0.59-20230515-165-9e0611b  CSCM-42150
CSCM-42125  Closed    Chris Stacks  Archana B S          Govcloud-Atlas SaaS Service Production Push - vmc-vmc-fluentd                                                CSCM-42125
CSCM-42124  Closed    Chris Stacks  Archana B S          Govcloud SaaS Service Production Push - vmc-vmc-fluentd                                                      CSCM-42124
CSCM-42108  Closed    Chris Stacks  Yue Chen             Govcloud LINT upgrade for May 2023 adding Nginx                                                              CSCM-42108
CSCM-42103  Closed    Chris Stacks  Abhishek Gupta       Govcloud SaaS Service Production Push - vmc-vmcmon-api-gateway                                               CSCM-42103
CSCM-42088  Closed    Chris Stacks  Sukhmeet Chhabra     Govcloud SaaS Service Production Push - vmc-fm-release-engine-ui                                             CSCM-42088
CSCM-42084  Closed    Chris Stacks  Andrey Karadzha (c)  Govcloud-Atlas Atlas Base Image Production Promotion - atlas-atlas-base-image - 2.0.58-20230512-164-2e26d20  CSCM-42084
CSCM-41058  Closed    Chris Stacks  Saipriya Gavini (c)  Govcloud SaaS Service Production Push - vmc-vmc-reverseproxy                                                 CSCM-41058
CSCM-40945  Closed    Chris Stacks  Andrey Karadzha (c)  Govcloud-Atlas Atlas Base Image Production Promotion - atlas-atlas-base-image - 2.0.54-20230420-159-14ecbe6  CSCM-40945
==========  ========  ============  ===================  ===========================================================================================================  ==========
```
## Text User Interface
* [ENTER] per ticket will launch the URL in your browser using click
<img width="2529" alt="image" src="https://github.com/stacksc/pyps/assets/116677370/84c7aa43-e093-4b60-925e-53fcbcad3de8">

