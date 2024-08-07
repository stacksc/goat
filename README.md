<img width="200" height="200" alt="image" src="https://github.com/stacksc/goat/assets/116677370/36bb12c0-e491-40fe-8cd5-171329d10653">
<img alt="gif" border=1 width=900 height=500 src="https://github.com/stacksc/goat/assets/116677370/7f4842a4-d028-4761-b032-4d6377f372e2">

<h1>Feedback Appreciation</h1>
In order to make this application as user-friendly as possible, please provide any feedback to help the user expierience and logic.<br>
Please open an issue, leave comments, or even a thumbs up on the project goes a long way with continued development.

<a name="readme-top"></a>
<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li><a href="#hlo">HLO</a></li>
    <li><a href="#showcase">Gallery</a></li>
    <li><a href="#about-the-project">About The Project</a>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#contacts">Contacts</a></li>
    <li><a href="#goatshell">GoatShell</a></li>
    <li><a href="#cache-data">Cache</a></li>
    <li><a href="#current-usage">Usage</a></li>
    <li><a href="#versions">Versions</a></li>
    <li><a href="#jira-authentication">JIRA authentication</a></li>
    <li><a href="#user-manuals">User Manuals</a></li>
  </ol>
</details>

<h1>GOAAT CLI & GOATSHELL</h1>

<h2>7 CLOUDS & 1 SHELL</h2>

<!-- HLO -->
## HLO

The presented project is currently undergoing significant development efforts.

This initiative revolves around establishing seamless communication with a diverse array of APIs, including prominent platforms such as Slack, JIRA, and Jenkins. It doesn't stop there – the project extends its reach to encompass major public cloud providers such as GCP, OCI, AWS, and Azure. The primary goal is to simplify by streamlining credential and configuration management.

<!-- SHOWCASE -->
## Showcase

https://www.centerupt.com
<br>
https://vimeo.com/showcase/10685985

<!-- ABOUT THE PROJECT -->
## About The Project

GOAAT ("goat") - a front-end application for Python modules to communicate with most Public Cloud Platforms (GCP, OCI, AWS, Azure, IBM, Alibaba). Source code of this app can also be used as an example of how to write code using our internal modules and how to integrate multiple modules together in a single app/package.<br>
<br>
GOAAT and GOATSHELL can work together or independently. When launching <b>goatshell</b>, you can interact with any major cloud provider and <u>not</u> depend on goat credential management. GOAT is useful when setting up APIs such as JIRA, SLACK, Jenkins, etc. GOATSHELL is primarily useful as a cloud wrapper.<br>

<!-- GETTING STARTED -->
## Getting Started

### Installation
1. Stable release is available on PyPi
2. A manual installation is provided with a shell script to build all modules

#### <b>Manual Installation</b>

1. Create a virtual environment. We will call it `prod`:
   ```sh
   python3 -m venv ~/prod
   ```
2. Activate virtual environment:
   ```sh
   cd ~/prod && source bin/activate
   ```
3. Clone the repo:
   ```sh
   git clone https://github.com/stacksc/goat.git
   ```
4. Install all required packages with 1 script from the main repository: 
   ```sh
   cd ~/prod/goat && ./bulk.sh --action rebuild --target all
   ```
#### <b>PIP INSTALLATION</b>

1. Install the following packages from pypi:
   ```
   pip install goatshell goaat
   ```
2. If there are <b><u>dependency issues</u></b> please use this command to re-fetch everything. 
   ```
   pip install goatshell goaat --force-reinstall
   ```
   
<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- GOATSHELL -->
## GOATSHELL
For more details, check out the [manual](./goat-shell/README.md)

<!-- CACHE DATA -->
## cache data
1. The cache is used to store credentials and configuration data per module.
2. The .cfg files are encrypted with Fernet and only GOAT can access the keys.
3. to recreate your cache, you can remove the configs and keys from this directory: `~/goat`
4. files will look like those listed below.
5. if these files are removed, you will need to reauthenticate/setup each module.

```
$ find ~/goat -type f -name "*.key" -o -name "*.cfg"
./.awstools.key
./.slacktools.cfg
./.slacktools.key
./.awstools.cfg
./.ocitools.cfg
./.ocitools.key
./.jiratools.key
./.jiratools.cfg
./.jenkinstools.cfg
./.gitools.cfg
./.gitools.key
./.jenkinstools.key
```

<!-- CURRENT USAGE -->
## Current Usage
```
$ goat -h
Usage: goat [OPTIONS] COMMAND [ARGS]...

  goat => GCP, OCI, & AWS TK

Options:
  -v, --version       print version of goat and all its submodules
  -m, --manuals TEXT  print all defined manuals matching pattern(s)
  -h, --help          Show this message and exit.

Commands:
  aws      AWS CLI Client         Current Profile: CENTERUPT Region: AP-SOUTHEAST-1
  configs  Config Client          Current Profile: N/A
  jenkins  Jenkins Client         Current Profile: HTTP://LOCALHOST:8080
  jira     JIRA CLI Client        Current Profile: HTTPS://GOAAT.ATLASSIAN.NET
  oci      OCI CLI Client         Current Profile: CENTERUPT Region: US-ASHBURN-1
  slack    Slack CLI Client       Current Profile: DEFAULT
```
## Versions
```
$ goat -v
GOAT:			2023.8.17.1901
- awstools:		2023.8.17.1901
- configstore:		2023.8.17.1901
- jenkinstools:		2023.8.17.1903
- jiratools:		2023.8.17.1901
- ocitools:		2023.8.17.1901
- slacktools:		2023.8.17.1901
- toolbox:		2023.8.17.1901

        (_(
        /_/'_____/)
        "  |      |
           |""""""|
```

<!-- CONTACTS -->
## Contacts
Christopher Stacks - <centerupt@gmail.com>

<!-- JIRA AUTHENTICATION -->
## JIRA Authentication
1. The following example demonstrates JIRA authentication for the first time:
```
$ goat jira -p stage auth -u https://goaat.atlassian.net -m pass
Enter username [stacksc] :
Enter password: **************
INFO: Caching some system info now to save time later... please wait
INFO: Caching facts complete
```

<!-- USER MANUALS -->
## User Manuals
1. The following example demonstrates how to search the user manuals for a command using the `-m` switch:
```
$ goat -m jira -m search
```

## AWS Authentication
1. The following example demonstrates AWS authentication for the first time:
```
goat aws -p centerupt iam authenticate -r us-east-1 -o json
Please enter AWS_KEY_ID: AKIAUMD5PPM4KSDFGOLR
Please enter AWS_SECRET_ACCESS_KEY: ****************************************
INFO: credentials saved successfully
INFO: aws profile caching initialized
INFO: caching s3 data...
INFO: caching ec2 data...
INFO: caching rds data...
INFO: you can now use your new profile with 'aws --profile centerupt
```
2. Override the default region with: `goat aws -r {regionName}`; i.e. `goat aws -r us-west-1`

## Jenkins Tasks
```
$ goat jenkins -h
Usage: goat jenkins [OPTIONS] COMMAND [ARGS]...

  Jenkins Client                       Current Profile: DEFAULT

Options:
  -p, --profile TEXT  user profile for Jenkins operations
  -h, --help          Show this message and exit.

Commands:
  auth  perform authentication operations against Jenkins
  show  retrieve information from Jenkins
```

## jenkins auth setup
```
$ goat jenkins auth setup
WARN: Encryption key not detected. Generating a new one
Enter jenkins username [stacksc] : stacksc
Enter jenkins password: *********
Paste jenkins full URL here: **********************
INFO: access token expired or not found. Generating a new one
INFO: jenkins settings saved succesfully
```

## post auth cache
```
$ goat configs show jenkinstools
{
    "default": {
        "config": {
            "username": "stacksc",
            "password": "******************",
            "access_token": {
                "token": "******************",
                "timestamp": 1691719300.347849
            },
            "crumb_token": {
                "crumb": "Jenkins-Crumb:7c9f5fecf82a11ff98ab8f5c158ab5a52098e83c6e9cb4408b2ddfc1ffcdfe23",
                "timestamp": 1691719300.532575
            }
        },
        "metadata": {
            "name": "default",
            "created_by": "stacksc",
            "created_at": "1691719288.30942",
            "JENKINS_URL": "http://localhost:8080"
        }
    },
    "latest": {
        "config": {
            "role": "default"
        },
        "metadata": {
            "name": "latest",
            "created_by": "stacksc",
            "created_at": "1691719300.539011"
        }
    }
}
```

## Jenkins Show
```
$ goat jenkins show -h
Usage: goat jenkins show [OPTIONS] COMMAND [ARGS]...

  retrieve information from Jenkins

Options:
  -d, --debug [0|1|2]  0 = no output, 1 = default, 2 = debug on
  -m, --menu           launch a menu driven interface for common Jenkins user actions
  -h, --help           Show this message and exit.

Commands:
  access-token      API token for accessing the Jenins functionality
  access-token-age  how long the current access token will remain active
  config            retrieve the entire content of jenkinstool's configstore instance
  credentials       display system credentials available for jobs
  crumb-token       API crumb for accessing the Jenins functionality
  crumb-token-age   how long the current crumb token will remain active
  jobs              display information about Jenkins job names
  user              display information about Jenkins users
```

### jenkins examples
```
$ goat jenkins show -h
Usage: goat jenkins show [OPTIONS] COMMAND [ARGS]...

  retrieve information from Jenkins

Options:
  -d, --debug [0|1|2]  0 = no output, 1 = default, 2 = debug on
  -m, --menu           launch a menu driven interface for common Jenkins user actions
  -h, --help           Show this message and exit.

Commands:
  access-token      API token for accessing the Jenins functionality
  access-token-age  how long the current access token will remain active
  config            retrieve the entire content of jenkinstool's configstore instance
  credentials       display system credentials available for jobs
  crumb-token       API crumb for accessing the Jenins functionality
  crumb-token-age   how long the current crumb token will remain active
  jobs              display information about Jenkins job names
  user              display information about Jenkins users
```

```
$ goat jenkins show jobs last-failed
INFO: checking last failed job name capacity-reporter build now, please wait...
{
  "_class": "hudson.model.FreeStyleBuild",
  "number": 12,
  "url": "http://localhost:8080/goaat/job/capacity-reporter/12/"
}
```

## SLACK communication
```
$ goat slack -h
Usage: goat slack [OPTIONS] COMMAND [ARGS]...

  Slack CLI Client                     Current Profile: DEFAULT

Options:
  -p, --profile TEXT  User profile to use for connecting to Slack
  -h, --help          Show this message and exit.

Commands:
  channel  manage Slack channels; create, archive, invite users etc
  config   retrieve the entire content of slacktools's configstore
  post     post a meessage to a given channel(s)
  react    post a reaction to a given message in specific channel
  unpost   delete a meessage in a given channel
  unreact  remove a reaction to a given message in a specific channel

```

### init slacktools
* pre-requisites:
   - slack bot / application:
      - users are responsible for getting the right privileges and access token for their respective workspace.
      - slack permissions are out of scope for this document.
   - bot tokens start with: `xoxb-`
   - app tokens start with: `xapp-`

1. Users will be prompted for a slack bot token the first time the module is launched,<br>
   and this is stored in the configstore.
```
$ goat slack post -m "Hello - this is a test from stacks" C05LXFYUNNM
WARN: Encryption key not detected. Generating a new one
INFO: Please enter the API token for Slack profile 'default'
Paste Slack token here: *********************************************************
INFO: Message sent at 1691849015.552989
```

### post a message
```
$ goat slack post -m "Hello - this is a test from stacks" C05LXFYUNNM
INFO: Message sent at 1691706809.465009
```

### react to a message
```
$ goat slack react -t 1691706809.465009 -e wavy_dash C05LXFYUNNM
INFO: Reaction posted
```

## JIRA Module Demonstration
```
$ goat jira -h
Usage: goat jira [OPTIONS] COMMAND [ARGS]...

  JIRA CLI Client                      Current Profile: HTTPS://GOAAT.ATLASSIAN.NET

Options:
  -p, --profile TEXT  profile name to use when working with the jiraclient  [default: default]
  -h, --help          Show this message and exit.

Commands:
  auth     setup or change authentication settings for JIRA
  config   manage configuration details for the Jira server on this profile
  issue    manage JIRA issues
  project  manage JIRA projects
  search   search for issues in Jira
```
## Authentication setup
```
$ goat jira -p default auth -u https://goaat.atlassian.net -m pass
WARN: Encryption key not detected. Generating a new one
Is this going to be your default profile (Y/N)? : Y
Enter username [stacksc] :
Enter password: ******************
INFO: Caching some system info now to save time later... please wait
INFO: Caching facts complete
```
## Configuration / Cached Data
```
$ goat jira config
{
    "config": {
        "mode": "pass",
        "url": "https://goaat.atlassian.net",
        "default": "Y",
        "user": "stacksc",
        "pass": "******************"
    },
    "metadata": {
        "name": "default",
        "created_by": "centerupt.stacks@gmail.com",
        "created_at": "1676180080.897811",
        "projects": {
            "CSCM": {},
            "CSSD": {},
            "GUAR": {},
            "ITEX": {},
            "TEMP": {},
            "UCP": {},
            "UCPS": {},
            "VLOPS": {},
            "GD": {}
         }
    }
}
```
## Project Search
```
$ goat jira project search -h
Usage: goat jira project search [OPTIONS] [PROJECTS]...

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
$ goat jira project search CSCM -a stacksc -l 10
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
<br>

## OCI examples
### The following pre-requisites are needed:
1. Tenant OCID
2. User OCID
3. Public key fingerprint
4. Profile name

```
$ goat oci iam authenticate -r us-ashburn-1 -t ocid1.tenancy.oc1..aaaaaaaajkxcejo4fjvjwfceouocuzxgmbexy7cqy423kjchmyywtpoigb5a -u ocid1.user.oc1..aaaaaaaaizly2w5xebvjn7rhty63aaq3ydavo45yueirf7ncv7s7hstpdi4a -f 1f:ce:1a:08:94:93:b7:a9:56:29:38:71:20:a0:63:4e -p centerupt
WARN: Encryption key not detected. Generating a new one
INFO: credentials saved successfully
INFO: you can now use your new profile with 'oci --profile centerupt
INFO: oci profile caching initialized
INFO: caching oss data...
INFO: caching OCI object storage buckets...
INFO: caching OCI object storage buckets...
INFO: caching compute data...
INFO: caching compute instances...
INFO: caching compute instances...
INFO: caching dbs data...
INFO: automatic refresh of dbs instance cache initiated
INFO: caching DBS instances...
INFO: caching DBS instances across all compartments...
INFO: automatic refresh of dbs instance cache initiated
INFO: caching DBS instances...
INFO: caching DBS instances across all compartments...
INFO: caching DBS instances...
INFO: caching DBS instances across all compartments...
INFO: caching regions data...
INFO: caching regions...
INFO: caching region subscriptions...
INFO: caching vault data...
INFO: caching vaults...
INFO: caching vault data across all compartments...
INFO: caching secrets data...
INFO: caching secrets...
INFO: caching secrets across all compartments...
INFO: caching compartment data...
INFO: caching compartments...
INFO: caching compartment data across all levels...
INFO: caching keys data...
INFO: caching keys...
INFO: caching vault keys across all compartments...
```

### post authentication cache 
1. the following information is cached automatically and stored in the configstore
2. the caching mechanism works for all modules (jira, aws, oci, etc)

```
$ goat configs show ocitools
{
    "centerupt": {
        "config": {},
        "metadata": {
            "name": "centerupt",
            "created_by": "stacksc",
            "created_at": "1692487004.961252",
            "fingerprint": "1f:ce:1a:08:94:93:b7:a9:56:29:38:71:20:a0:63:4e",
            "key_file": "~/.oci/oci_api_key.pem",
            "tenancy": "ocid1.tenancy.oc1..aaaaaaaajkxcejo4fjvjwfceouocuzxgmbexy7cqy423kjchmyywtpoigb5a",
            "region": "us-ashburn-1",
            "user": "ocid1.user.oc1..aaaaaaaaizly2w5xebvjn7rhty63aaq3ydavo45yueirf7ncv7s7hstpdi4a",
            "cached_buckets": {
                "us-ashburn-1": {
                    "test-goat-2": {
                        "name": "test-goat-2",
                        "namespace": "idqa8rzudg50",
                        "compartment": "test",
                        "ocid": "ocid1.compartment.oc1..aaaaaaaaxdgwsdrg47aattjmpu5ue3i5o5wuq4bmmpbdxzrhzrbi2iejr52a"
                    },
                    "test-goat": {
                        "name": "test-goat",
                        "namespace": "idqa8rzudg50",
                        "compartment": "centerupt",
                        "ocid": "ocid1.tenancy.oc1..aaaaaaaajkxcejo4fjvjwfceouocuzxgmbexy7cqy423kjchmyywtpoigb5a"
                    },
                    "last_cache_update": "1692495797.869417"
                }
            },
            "cached_instances": {
                "us-ashburn-1": {
                    "instance-20230807-1711": {
                        "display_name": "instance-20230807-1711",
                        "lifecycle_state": "RUNNING",
                        "instance_type": "Compute",
                        "shape": "VM.Standard.E2.1.Micro",
                        "compartment_name": "root",
                        "public_ips": "129.213.121.59 ",
                        "private_ips": "10.0.0.202 ",
                        "AD": "US-ASHBURN-AD-1"
                    },
                    "last_cache_update": "1692487014.350064"
                }
            },
            "cached_dbs_instances": {
                "us-ashburn-1": {
                    "LLE8SPADCEIQ1DW9": {
                        "display_name": "LLE8SPADCEIQ1DW9",
                        "lifecycle_state": "STOPPED",
                        "ocpu": 1,
                        "memory": "n/a",
                        "shape": "ATP",
                        "compartment_name": "root",
                        "type": "ATP",
                        "public_ips": "n/a",
                        "private_ips": "n/a",
                        "OS": "n/a",
                        "AD": "US-ASHBURN-1"
                    },
                    "last_cache_update": "1692487029.967132",
                    "MTI4ETRAK6CBSN0C": {
                        "display_name": "MTI4ETRAK6CBSN0C",
                        "lifecycle_state": "AVAILABLE",
                        "ocpu": 0,
                        "memory": "n/a",
                        "shape": "ATP",
                        "compartment_name": "root",
                        "type": "ATP",
                        "public_ips": "n/a",
                        "private_ips": "n/a",
                        "OS": "n/a",
                        "AD": "US-ASHBURN-1"
                    }
                }
            },
            "cached_regions": {
                "us-ashburn-1": {
                    "region_key": "IAD",
                    "region_name": "us-ashburn-1",
                    "status": "READY",
                    "is_home_region": true
                }
            },
            "cached_vaults": {
                "us-ashburn-1": {
                    "ocid1.vault.oc1.iad.dvsn55nkaac7q.abuwcljtdnbc3y52gknda4m323mwghkxba6rwg6qius7ceib5zmcripeynfq": {
                        "display_name": "JAZZYJAM",
                        "compartment": "primary",
                        "crypto_endpoint": "https://dvsn55nkaac7q-crypto.kms.us-ashburn-1.oraclecloud.com",
                        "management_endpoint": "https://dvsn55nkaac7q-management.kms.us-ashburn-1.oraclecloud.com",
                        "lifecycle_state": "ACTIVE"
                    },
                    "ocid1.vault.oc1.iad.dvsn4n5daabia.abuwcljtwuleevaxighwb2a57dmmevvvp3l3djd4ermm3q4h2faq566pbbnq": {
                        "display_name": "blah",
                        "compartment": "test",
                        "crypto_endpoint": "https://dvsn4n5daabia-crypto.kms.us-ashburn-1.oraclecloud.com",
                        "management_endpoint": "https://dvsn4n5daabia-management.kms.us-ashburn-1.oraclecloud.com",
                        "lifecycle_state": "PENDING_DELETION"
                    },
                    "ocid1.vault.oc1.iad.dvsn4flyaadx4.abuwcljt3gopkgiyq3l73mv5w3stwiyjdbwthmvmuz4htxumouvriavrbwla": {
                        "display_name": "PRIMARY-GOAT",
                        "compartment": "test",
                        "crypto_endpoint": "https://dvsn4flyaadx4-crypto.kms.us-ashburn-1.oraclecloud.com",
                        "management_endpoint": "https://dvsn4flyaadx4-management.kms.us-ashburn-1.oraclecloud.com",
                        "lifecycle_state": "PENDING_DELETION"
                    },
                    "ocid1.vault.oc1.iad.dvsn5p7qaabwc.abuwcljrdrdiz2g3qsxts2gjfp7d735lpnowd5db2xq5dd25wpdyooyiolwq": {
                        "display_name": "PRIMARYGOAT",
                        "compartment": "centerupt",
                        "crypto_endpoint": "https://dvsn5p7qaabwc-crypto.kms.us-ashburn-1.oraclecloud.com",
                        "management_endpoint": "https://dvsn5p7qaabwc-management.kms.us-ashburn-1.oraclecloud.com",
                        "lifecycle_state": "ACTIVE"
                    },
                    "ocid1.vault.oc1.iad.dvsn4ncuaad2i.abuwcljrjxxf3gopfwqxylxzrr3bqxmgeicbad4l62bvfsi2z6f2b4chl7cq": {
                        "display_name": "GOAT",
                        "compartment": "centerupt",
                        "crypto_endpoint": "https://dvsn4ncuaad2i-crypto.kms.us-ashburn-1.oraclecloud.com",
                        "management_endpoint": "https://dvsn4ncuaad2i-management.kms.us-ashburn-1.oraclecloud.com",
                        "lifecycle_state": "PENDING_DELETION"
                    },
                    "ocid1.vault.oc1.iad.dvsn4mrwaafxg.abuwcljtkqqwxjul7vjdbnlmxukqxhpoy2hkkkrccwdykuvzhngb6hnevd4q": {
                        "display_name": "PRIMARY-G",
                        "compartment": "centerupt",
                        "crypto_endpoint": "https://dvsn4mrwaafxg-crypto.kms.us-ashburn-1.oraclecloud.com",
                        "management_endpoint": "https://dvsn4mrwaafxg-management.kms.us-ashburn-1.oraclecloud.com",
                        "lifecycle_state": "PENDING_DELETION"
                    },
                    "ocid1.vault.oc1.iad.dvsn4ileaaaey.abuwcljrr2e7g7vc5j3vj5pgh3en7xq4hrqtzebny7uohdt7y57nnuk5cx6q": {
                        "display_name": "PRIMARY",
                        "compartment": "centerupt",
                        "crypto_endpoint": "https://dvsn4ileaaaey-crypto.kms.us-ashburn-1.oraclecloud.com",
                        "management_endpoint": "https://dvsn4ileaaaey-management.kms.us-ashburn-1.oraclecloud.com",
                        "lifecycle_state": "PENDING_DELETION"
                    },
                    "ocid1.vault.oc1.iad.dvsn4fe2aaayo.abuwcljsuipzfgyaucpbrnjdwssgvn6pwk32wduqjjxjcoritnlvx73ulkva": {
                        "display_name": "TESTING-GOAT",
                        "compartment": "centerupt",
                        "crypto_endpoint": "https://dvsn4fe2aaayo-crypto.kms.us-ashburn-1.oraclecloud.com",
                        "management_endpoint": "https://dvsn4fe2aaayo-management.kms.us-ashburn-1.oraclecloud.com",
                        "lifecycle_state": "PENDING_DELETION"
                    },
                    "ocid1.vault.oc1.iad.dvsnudxiaaa4e.abuwcljt4brhm6u4xhwsucrdolyxf3nuys65rn2u6k5s7crlxhkhltpqh53q": {
                        "display_name": "TEST",
                        "compartment": "centerupt",
                        "crypto_endpoint": "https://dvsnudxiaaa4e-crypto.kms.us-ashburn-1.oraclecloud.com",
                        "management_endpoint": "https://dvsnudxiaaa4e-management.kms.us-ashburn-1.oraclecloud.com",
                        "lifecycle_state": "PENDING_DELETION"
                    },
                    "ocid1.vault.oc1.iad.b5q42kbmaagui.abuwcljtm4664hztspkzk25tjrslamlk37ra4mdfvgg44ttnnw45tmkk2qoq": {
                        "display_name": "Centerupt",
                        "compartment": "centerupt",
                        "crypto_endpoint": "https://b5q42kbmaagui-crypto.kms.us-ashburn-1.oraclecloud.com",
                        "management_endpoint": "https://b5q42kbmaagui-management.kms.us-ashburn-1.oraclecloud.com",
                        "lifecycle_state": "PENDING_DELETION"
                    },
                    "last_cache_update": "1692487034.060408"
                }
            },
            "cached_secrets": {
                "us-ashburn-1": {
                    "ocid1.vaultsecret.oc1.iad.amaaaaaajwdohpyarnqkvteyutgrrtlozsgc2sphawozpuvsxucbo42rhzla": {
                        "secret_name": "thisIsTest",
                        "content": "WndleEpkb1JuMzdNY0Zs",
                        "type": "BASE64",
                        "description": "thisIsTest",
                        "compartment": "centerupt",
                        "lifecycle_state": "ACTIVE"
                    },
                    "last_cache_update": "1692487038.140763"
                }
            },
            "cached_compartments": {
                "us-ashburn-1": {
                    "ocid1.compartment.oc1..aaaaaaaa3isbxyb7h3k4a5lsfrcegchfzdcyl3at7tupo2agsf66255wbz6a": {
                        "name": "jazz.1a2AmUCn",
                        "id": "ocid1.compartment.oc1..aaaaaaaa3isbxyb7h3k4a5lsfrcegchfzdcyl3at7tupo2agsf66255wbz6a",
                        "lifecycle_state": "DELETED",
                        "description": "jazz"
                    },
                    "ocid1.compartment.oc1..aaaaaaaa6lru6dwzpeldmemduvycx3sw6kovxzig6miumhxc3znsx4r2wdhq": {
                        "name": "jazzyjeff.3A9fZVcg",
                        "id": "ocid1.compartment.oc1..aaaaaaaa6lru6dwzpeldmemduvycx3sw6kovxzig6miumhxc3znsx4r2wdhq",
                        "lifecycle_state": "DELETED",
                        "description": "jazzyjeff"
                    },
                    "ocid1.compartment.oc1..aaaaaaaacqvk5lihdtkzp6svy3dmtrk5rwpjseycuigndjki3vtcu7ytbenq": {
                        "name": "ManagedCompartmentForPaaS",
                        "id": "ocid1.compartment.oc1..aaaaaaaacqvk5lihdtkzp6svy3dmtrk5rwpjseycuigndjki3vtcu7ytbenq",
                        "lifecycle_state": "ACTIVE",
                        "description": "idcs-53f91ffa8629421090151dedc15f7c93|24092907|centerupt@gmail.com-Oracle-732170"
                    },
                    "ocid1.compartment.oc1..aaaaaaaarx7w6xroehgvclzbe4jt34cyhyg6hzfquuyftpppkbqjcusqmilq": {
                        "name": "primary",
                        "id": "ocid1.compartment.oc1..aaaaaaaarx7w6xroehgvclzbe4jt34cyhyg6hzfquuyftpppkbqjcusqmilq",
                        "lifecycle_state": "ACTIVE",
                        "description": "primary"
                    },
                    "ocid1.compartment.oc1..aaaaaaaavl24h3k3ibe5w4ph57zsy7c7ja7twah4637jfdktq5vhm4xdepla": {
                        "name": "shep",
                        "id": "ocid1.compartment.oc1..aaaaaaaavl24h3k3ibe5w4ph57zsy7c7ja7twah4637jfdktq5vhm4xdepla",
                        "lifecycle_state": "ACTIVE",
                        "description": "Testing compartments holding instances"
                    },
                    "ocid1.compartment.oc1..aaaaaaaaxdgwsdrg47aattjmpu5ue3i5o5wuq4bmmpbdxzrhzrbi2iejr52a": {
                        "name": "test",
                        "id": "ocid1.compartment.oc1..aaaaaaaaxdgwsdrg47aattjmpu5ue3i5o5wuq4bmmpbdxzrhzrbi2iejr52a",
                        "lifecycle_state": "ACTIVE",
                        "description": "This is a test compartment to hold compute instances"
                    },
                    "ocid1.compartment.oc1..aaaaaaaa2iatkwmfk42qdqtgnno2y2isjm55eylmw3y26aevawthlh3tvkoa": {
                        "name": "test-goat.A9nJDzlX",
                        "id": "ocid1.compartment.oc1..aaaaaaaa2iatkwmfk42qdqtgnno2y2isjm55eylmw3y26aevawthlh3tvkoa",
                        "lifecycle_state": "DELETED",
                        "description": "test-goat"
                    },
                    "ocid1.tenancy.oc1..aaaaaaaajkxcejo4fjvjwfceouocuzxgmbexy7cqy423kjchmyywtpoigb5a": {
                        "name": "centerupt",
                        "id": "ocid1.tenancy.oc1..aaaaaaaajkxcejo4fjvjwfceouocuzxgmbexy7cqy423kjchmyywtpoigb5a",
                        "lifecycle_state": "ACTIVE",
                        "description": "centerupt"
                    },
                    "last_cache_update": "1692487041.320159"
                }
            },
            "cached_keys": {
                "us-ashburn-1": {
                    "ocid1.key.oc1.iad.dvsn5p7qaabwc.abuwcljr43otebl6lj7mkqmyocnnvyhxm5i5k2opkkjopza4rsldwucrnd3a": {
                        "display_name": "keyName",
                        "lifecycle_state": "ENABLED",
                        "protection_mode": "HSM",
                        "algorithm": "AES"
                    },
                    "ocid1.key.oc1.iad.dvsn5p7qaabwc.abuwcljtyw7fa5cxyyoo5g7wdg4hthrrfpwxbxh7xl4bu5lpdgj54qop2csq": {
                        "display_name": "thisIsTest",
                        "lifecycle_state": "ENABLED",
                        "protection_mode": "HSM",
                        "algorithm": "AES"
                    },
                    "last_cache_update": "1692487043.272804"
                }
            }
        }
    },
    "latest": {
        "config": {
            "name": "centerupt"
        },
        "metadata": {
            "name": "latest",
            "created_by": "stacksc",
            "created_at": "1692487046.984028"
        }
    }
}

-------------------- oci config for all profiles --------------------

    [centerupt]
    region=us-ashburn-1
    tenancy=ocid1.tenancy.oc1..aaaaaaaajkxcejo4fjvjwfceouocuzxgmbexy7cqy423kjchmyywtpoigb5a
    user=ocid1.user.oc1..aaaaaaaaizly2w5xebvjn7rhty63aaq3ydavo45yueirf7ncv7s7hstpdi4a
    fingerprint=1f:ce:1a:08:94:93:b7:a9:56:29:38:71:20:a0:63:4e
    key_file=~/.oci/oci_api_key.pem
```

1. Override the default region with: `goat oci -r {regionName}`; i.e. `goat oci -r us-phoenix-1`

### OCI usage
```
$ goat oci -h
Usage: goat oci [OPTIONS] COMMAND [ARGS]...

  OCI CLI Client                       Current Profile: DEFAULT

Options:
  -p, --profile TEXT  profile name to use when working with ocitools
  -h, --help          Show this message and exit.

Commands:
  cli   run any ocicli (oci) command while leveraging ocitools profile functionality
  iam   manage and switch between OCI profiles for all realms
  oss   object storage functions to sync buckets and filesystems
  show  display configuration data for ocitools and ocicli
```

#### OCI object storage
```
$ goat oci oss -h
Usage: goat oci oss [OPTIONS] COMMAND [ARGS]...

  object storage functions to sync buckets and filesystems

Options:
  -m, --menu  use the menu to perform OCI OSS actions
  -h, --help  Show this message and exit.

Commands:
  create    create a new bucket
  delete    delete a specified bucket
  download  download from OSS to local storage
  refresh   manually refresh OSS cached data
  show      show the data stored in OSS cache
  upload    upload from local storage to OSS bucket
```

#### Improved Cloud Wrapper ####

<img width="1703" alt="image" src="https://github.com/stacksc/goat/assets/116677370/39b87c3c-49d0-4576-b452-f1e3bdb31015">
<br>
<br>
<img width="1703" alt="image" src="https://github.com/stacksc/goat/assets/116677370/4e9f678b-9cae-462a-89a1-5494d2468aca">
<br>
