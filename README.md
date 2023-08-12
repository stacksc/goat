<img src="./images/Goat_icon.svg.png" alt="GOAT" width="200"/>
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
    <li><a href="#cache-data">Cache</a></li>
    <li><a href="#current-usage">Usage</a></li>
    <li><a href="#versions">Versions</a></li>
    <li><a href="#jira-authentication">JIRA authentication</a></li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->
## About The Project

GOAT ("goat") - a front-end application for the Python modules to communicate with most Public Cloud Platforms (GCP, OCI, AWS, & Azure). Source code of this app can also be used as an example of how to write code using our internal modules and how to integrate multiple modules together in a single app/package.<br>

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
./.refresh.key
./.refresh.cfg
```

<!-- CURRENT USAGE -->
## Current Usage
```
goat -h
Usage: goat [OPTIONS] COMMAND [ARGS]...

  goat => GCP, OCI, & AWS TK

Options:
  -v, --version       print version of goat and all its submodules
  -m, --manuals TEXT  print all defined manuals matching pattern(s)
  -h, --help          Show this message and exit.

Commands:
  aws      AWS CLI Client              Current Profile: DEFAULT
  configs  Config Client               Current Profile: N/A
  jenkins  Jenkins Client              Current Profile: DEFAULT
  jira     JIRA CLI Client             Current Profile: HTTPS://GOAAT.ATLASSIAN.NET
  oci      OCI CLI Client              Current Profile: CENTERUPT
  slack    Slack CLI Client            Current Profile: DEFAULT
```
## Versions
```
$ goat -v
GOAT:			1.0.0
- awstools:		1.0.3
- configstore:		1.0.0
- jenkinstools:		0.0.7
- jiratools:		1.0.0
- ocitools:		0.0.3
- slacktools:		1.0.0
- toolbox:		1.0.0

        (_(
        /_/'_____/)
        "  |      |
           |""""""|
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- GETTING STARTED -->
## Getting Started

### Prerequisites
### Installation

1. Clone the repo:
   ```sh
   git clone git@github.com:stacksc/goat.git
   ```
2. Install all required packages with 1 script from the main repository: 
   ```sh
   ./bulk.sh --action rebuild --target all
   ```
<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- ROADMAP -->
## Roadmap

- [ ] TBD - roadmap not yet available or determined.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTRIBUTING -->
## Contributing
Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".

1. Fork the Project (optional)
2. Create your Feature Branch: `git checkout -b feature/AmazingFeature`
3. Commit your Changes: `git commit -m 'Add some AmazingFeature'`
4. Push to the Branch: `git push origin feature/AmazingFeature`
5. Open a Pull Request

After making changes to the source code, please remember to build a new wheel for the project by running `python3 -m build --wheel` in the root of the project (where .toml file is)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

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

## AWS Authentication
1. The following example demonstrates AWS authentication for the first time:
```
$ goat aws -p default iam authenticate --region us-gov-west-1 --output json
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
$ goat aws iam assume-role atlcs
INFO: successfully assumed the role
INFO: aws profile caching initialized
INFO: caching s3 data...
INFO: caching ec2 data...
INFO: caching rds data...
INFO: run source ~/goatrole.sh
```

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
### TUI for job selections
* [ENTER] per job will launch tasks on that object
<img src="./images/jenkins.png" alt="Jenkins" width="1200"/>
<br>
<img src="./images/jenkins2.png" alt="Jenkins" width="1200"/>
<br>

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
## Text User Interface
* [ENTER] per ticket will launch the URL in your browser using click
<img src="./images/jira_menu.png" alt="JIRA" width="1200"/>
<br>

## OCI examples
### The following pre-requisites are needed:
1. Tenant OCID
2. User OCID
3. Public key fingerprint
4. Profile name

```
$ goat oci iam authenticate -r us-ashburn-1 -t {tenantOcid} -u {userOcid} -f {fingerprint} -p {profile}
WARN: Encryption key not detected. Generating a new one
INFO: credentials saved successfully
INFO: you can now use your new profile with 'oci --profile centerupt
INFO: oci profile caching initialized
INFO: caching oss data...
INFO: connecting to OSS as centerupt via us-ashburn-1...
INFO: connecting to OSS as centerupt via us-ashburn-1...
INFO: caching OCI object storage buckets...
INFO: compartment name: test holds object storage buckets in region us-ashburn-1
INFO: caching compute data...
INFO: connecting to OCI compute as centerupt via us-ashburn-1...
INFO: caching compute instances...
INFO: processing compartment:  root
INFO:
======================  =================  ===============  ======================  ==================  ==============  =============  ===============
display_name            lifecycle_state    instance_type    shape                   compartment_name    public_ips      private_ips    AD
======================  =================  ===============  ======================  ==================  ==============  =============  ===============
instance-20230807-1711  RUNNING            Compute          VM.Standard.E2.1.Micro  root                129.213.121.59  10.0.0.202     US-ASHBURN-AD-1
======================  =================  ===============  ======================  ==================  ==============  =============  ===============

INFO: processing compartment:  ManagedCompartmentForPaaS
INFO: processing compartment:  shep
INFO: processing compartment:  test
INFO: caching dbs data...
INFO: connecting to OCI DBS as centerupt via us-ashburn-1...
INFO: caching DBS instances...
INFO: connecting to OCI DBS as centerupt via us-ashburn-1...
INFO: caching DBS instances...
INFO: processing compartment:  root
INFO:
================  =================  ======  ========  =======  ==================  ======  ============  =============  ====  ============
display_name      lifecycle_state      ocpu  memory    shape    compartment_name    type    public_ips    private_ips    OS    AD
================  =================  ======  ========  =======  ==================  ======  ============  =============  ====  ============
LLE8SPADCEIQ1DW9  AVAILABLE               1  n/a       ATP      root                ATP     n/a           n/a            n/a   US-ASHBURN-1
================  =================  ======  ========  =======  ==================  ======  ============  =============  ====  ============

INFO: processing compartment:  ManagedCompartmentForPaaS
INFO: processing compartment:  shep
INFO: processing compartment:  test
INFO: caching regions data...
INFO: connecting to OCI as centerupt via us-ashburn-1...
INFO: caching regions...
INFO: connecting to OCI as centerupt via us-ashburn-1...
INFO: caching region subscriptions...
INFO:
============  =============  ========  ================
region_key    region_name    status    is_home_region
============  =============  ========  ================
IAD           us-ashburn-1   READY     True
============  =============  ========  ================
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
            "created_at": "1691710189.381707",
            "fingerprint": "1f:ce:1a:08:94:93:b7:a9:56:29:38:71:20:a0:63:4e",
            "key_file": "~/.oci/oci_api_key.pem",
            "tenancy": "ocid1.tenancy.oc1..aaaaaaaajkxcejo4fjvjwfceouocuzxgmbexy7cqy423kjchmyywtpoigb5a",
            "region": "us-ashburn-1",
            "user": "ocid1.user.oc1..aaaaaaaaizly2w5xebvjn7rhty63aaq3ydavo45yueirf7ncv7s7hstpdi4a",
            "cached_buckets": {
                "bucketeer": {
                    "name": "bucketeer",
                    "namespace": "idqa8rzudg50",
                    "compartment": "test",
                    "ocid": "ocid1.compartment.oc1..aaaaaaaaxdgwsdrg47aattjmpu5ue3i5o5wuq4bmmpbdxzrhzrbi2iejr52a"
                },
                "goat-stacks": {
                    "name": "goat-stacks",
                    "namespace": "idqa8rzudg50",
                    "compartment": "test",
                    "ocid": "ocid1.compartment.oc1..aaaaaaaaxdgwsdrg47aattjmpu5ue3i5o5wuq4bmmpbdxzrhzrbi2iejr52a"
                },
                "test-bucket": {
                    "name": "test-bucket",
                    "namespace": "idqa8rzudg50",
                    "compartment": "test",
                    "ocid": "ocid1.compartment.oc1..aaaaaaaaxdgwsdrg47aattjmpu5ue3i5o5wuq4bmmpbdxzrhzrbi2iejr52a"
                },
                "last_cache_update": "1691710190.993007"
            },
            "cached_instances": {
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
                "last_cache_update": "1691710193.441092"
            },
            "cached_dbs_instances": {
                "LLE8SPADCEIQ1DW9": {
                    "display_name": "LLE8SPADCEIQ1DW9",
                    "lifecycle_state": "AVAILABLE",
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
                "last_cache_update": "1691710200.217792"
            },
            "cached_regions": {
                "IAD": {
                    "region_key": "IAD",
                    "region_name": "us-ashburn-1",
                    "status": "READY",
                    "is_home_region": true
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
            "created_at": "1691710203.898848"
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

#### OSS Interface
* [ENTER] per bucket or object will initiate task
<img src="./images/downloads.png" alt="OCI Downloads" width="1200"/>
<br>
<img src="./images/download_1.png" alt="OCI Downloads" width="1200"/>
<br>

#### Native Notifications
* native notifications are included on more critical tasks as in the following example:
<img src="./images/native_notifications.png" alt="notifications" width="600"/>
<br>
