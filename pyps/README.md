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
    <li><a href="#usage">Usage</a></li>
    <li><a href="#how-to-add-a-new-command">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

PYPS ("pipes") - PYthon tools by PSsre team - a front-end application for most Python modules created by the Public Sector SRE team. Source code of this app can also be used as an example of how to write code using our internal modules and how to integrate multiple modules together in a single app/package.

Current features:
* adhoc - run a quick-and-dirty bash command in python
* aws - easily access data from aws and manage profiles for awscli (+ awscli wrapper which makes switching profiles instant)
* jira - manage, comment and transition jira issues plus search for tickets with easy to use parameters or plain old JQL
* slack - post and delete messages and reactions, manage channels, add and remove users etc
* comms - send maintenance and incident notifications to Slack and Jira at the same time
* vmc - manage access & refresh tokens for VMC, users and organizations, deploy and delete SDDCs, connect to ESXi hosts and much, much more
* configs - manage all configstore instances (settings for modules such as jiraclient) and records stored within them

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting Started

### Prerequisites

Internal packages:
* jiraclient
  ```sh
  https://gitlab.eng.vmware.com/wilkp/pssrex/-/tree/main/jiraclient
  ```
* slackclient
  ```sh
  https://gitlab.eng.vmware.com/wilkp/pssrex/-/tree/main/slackclient
  ```
* toolbox
  ```sh
  https://gitlab.eng.vmware.com/wilkp/pssrex/-/tree/main/toolbox
  ```
* csptools
  ```sh
  https://gitlab.eng.vmware.com/wilkp/pssrex/-/tree/main/csptools
  ```
* configstore
  ```sh
  https://gitlab.eng.vmware.com/wilkp/pssrex/-/tree/main/configstore
  ```
External packages:
* click
  ```sh
  pip install click
  ```

### Installation

1. Clone the repo or download the latest wheel from /dist
2. Install the wheel with pip or add the cloned repo to one of your paths (python3 -c "import sys; print(sys.path)")

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
### Usage

* `pyps init` - load all built-in settings; run this before starting to use pyps or other modules
* `pyps jira auth` - setup user authentication to JIRA server
  ```sh
  pyps jira auth --url https://jira.example.com --mode pass # authenticate with username and password
  pyps jira auth --url https://jira.example.com --mode token # authenticate with user API token
  jiraclient auth --url https://jira.example.com --mode pass --profile beta # authenticate with user API token and create a new profile 'beta'
  ```
* `pyps jira issue` - create, comment, update and transition issues (tickets)
  * `pyps jira issue comment` - post a comment on a given issue
    ```sh
    pyps jira issue comment PUBSECSRE-123 --commente "this is a comment"
    ```
  * `pyps jira issue create` - create a new issue on a project
    ```sh
    pyps jira issue crete --project PUBSECSRE --summary "test ticket" --description "this is a test ticket"
    ```
  * `pyps jira issue transition` - transition the issue to a new status
    ```sh
    pyps jira issue transition PUBSECSRE-123 --name Closed --profile jira
    # transition the issue PUBSECSRE-123 to status 'Closed' using credentials stored on profile "jira"
    pyps jira issue transition PUBSECSRE-123 --showavailable 
    # display available transitions for PUBSECSRE-123 and required updates to the ticket fields (if any)
    pyps jira issue transition PUBSECSRE-123 --id 211 --payload '{"resolution": {"id": "10000"}}'
    # transition PUBSECSRE-123 to status id 211 (Closed) and update the "resolution" field with an allowed value of an id = 10000 (Done)
    pyps jira issue transition PUBSECSRE-123 --id 11 --payload '{"status": {"id": "1234"}, "assignee": {"user": "wilkp"}}'
    # transition PUBSECSRE-123 to status id 11 (in progress) and update the "assignee" to user "wilkp" and set the status to "investigation" (id 1234)
    ```
  * `pyps jira issue update` - updates a given field on an issue
    ```sh
    pyps jira issue update PUBSECSRE-123 -field assignee --value jdoe
    ```
  * `pyps jira issue search` - show summary for an issue or a list issues
    ```sh
    pyps jira issue search PUBSECSRE-301
    # show issues details for issues PUBSECSRE-301 
    pyps jira issue search PUBSECSRE-301 PUBSECSRE-302 --json
    # show issues details for issues PUBSECSRE-301 and PUBSECSRE-302 and display result as json
    pyps jira issue search PUBSECSRE-301 PUBSECSRE-302 --csv
    # show issues details for issues PUBSECSRE-301 and PUBSECSRE-302 anbd save the result to csv file
    ```
* `pyps jira project` - manage and search for projects
  * `pyps jira project search` - search for projects based on entered parameters (supports autocomplete)
  ```sh
  pyps jira project search PUBSECSRE --status closed --orderby group --limit 3 --descending 
  # show issues in specific project and on specific status; display 3 results in descending order sorting by assigned group
  pyps jira project search PUBSECSRE --project CSSD --csv jdoe_tickets --reporter jdoe
  # show issues on PUBSECSRE or CSSD projects assigned to jdoes and export the results to a csv file named jdoe_tickets.csv
  pyps jira project search PUBSECSRE CSSD --reporter jdoe --reported jsmith --profile beta
  # show issues assigned to PUBSECSRE or CSSD and assigned to either jdoe or jsmith user; use profile 'beta' for authentication
  ```
* `pyps jira search` - search for issues in Jira
```sh
pyps jira search --project PUBSECSRE --project VMWGOV --status 'closed' --orderby group --limit 3 --descending 
# show issues in specific projects and on specific status; display 3 results in descending order sorting by assigned group
pyps jira search --status 'closed' --status 'done' --csv jdoe_tickets --reporter 'jdoe'
# show issues assigned to jdoe and with status closed or done and export the results to a csv file named jdoe_tickets.csv
pyps jira search --reporter 'jdoe' --reported 'jsmith' --profile beta
# show issues assigned to either jdoe or jsmith user; use profile 'beta' for authentication
```
* `pyps slack post` - post a message
  ```sh
  pyps slack --channels C123456789,C987654321 --messagetext "Hello" --reply 123456.7890
  # send message Hello to C123456789 and C987654321 channels in a threaded reply to message ID 123456.7890
  # NOTE: reply option SHOULD NOT be used with multiple target channels
  ```
* `pyps slack react` - react to a message
  ```sh
  pyps slack react --channel C123456789 --timestamp 123456.7890 --emoji :+1 --profile 'beta'
  # react with a thumbs up (:+1) to a mesage ID 123456.7890 in channels C123456789 and C987654321, using user profile 'beta'
  ```
* `pyps slack unpost` - delete a message
  ```sh
  pyps slack unpost --channel C123456789 --timestampp 123456.7890
  # delete a message ID 123456.7890 in channel C123456789
  ```
* `pyps slack unreact` - remove a reaction to a message
  ```sh
  pyps slack unreact --channel C123456789 --timestamp 123456.7890 --emoji :+1
  # remove a thumbs up reaction (:+1) from a message ID 123456.7890 in channel C123456789
  ```
* `pyps slack channel` - manage Slack channels
  * `pyps slack channel adduser` - add a user to the channel
  ```sh
  pyps slack channel adduser --user jdoe --channel C1234567890
  # add user jdoe to channel C123456789
  ```
  * `pyps slack channel deluser` - kick a user from the channel
  ```sh
  pyps slack channel deluser --user jdoe --channel C123456789
  # remove a user jdoe from channel C123456789
  ```
  * `pyps slack channel create` - create Slack channel
  ```sh
  pyps slack channel create --name test_channel --private
  # create a channel named test_channel and mark is as private
  ```
  * `pyps slack channel archive` - mark channel as archive
  ```sh
  pyps slack channel archive --channel C123456789
  ```
  * `pyps slack channel unarchive` - mar channel as active again
  ```sh
  pyps slack channale unarchive --channel C123456789  
  ```
  * `pyps slack channel topic` - set a topic for the channel
  ```sh
  pyps slack channel topic --topic "this is a topic" --channel C123456789
  ```
* `pyps comms` - create, comment, update and transition issues (tickets)
  * `pyps comms start` - send a notification about a starting maintenance using one of the available templates
  ```sh
  pyps comms start --key PUBSECSRE-123 --change CRQ-1234 --ids C123456789,C987654321
  ```
  * `pyps comms stop` - send a notification about a maintenance window closing using one of the available templates
  ```sh
  pyps comms stop --key PUBSECSRE-123 --change CRQ-1234 ids C123456789,987654321 --result ok
  # send a notification to Jira and Slack about a change completed succesfully 
  ```
  * `pyps comms custom` - send a custom notification to Jira and Slack
  ```sh
  pyps comms custom --key PUBSECSRE-123 --comment "Custom comment" --ids C123456789,C987654321 --message "Cutsom message"
  ```
  * `pyps comms code-red` - send a notification about a P0 incident and follow a code-red procedure (create channel, invite crisis response squad etc)
  ```sh
  pyps comms code-red --summary "aliens attacked Nandos"
  ```
* `pyps configs show` - setup user authentication to JIRA server
  ```sh
  pyps configs show jiraclient 
  # show all records saved for jiraclient
  confpyps configs show slackclient test
  # show all records saved under profile 'test' for slackclient
  pyps configs show cspclient prod operator
  # show all a record 'operator' saved under 'prod' profile for csptools
  ```
* `pyps configs add` - search for issues based on given parameters or pure JQL (and export to csv if needed)
  ```sh
  pyps configs add profile slackclient test
  # add a new profile 'test' to slackclient
  pyps configs add record csptools prod operator --value 123
  # add a new record 'operator' with a value of '123' to 'prod' profile for csptools
  ```
  * `pyps configs delete` - search for issues based on given parameters or pure JQL (and export to csv if needed)
  ```sh
  pyps configs delete profile slackclient test
  # delete profile 'test' from slackclient configstore
  pyps configs delete record csptools prod operator
  # delete record 'operator' from 'prod' profile for csptools configstore
  ```
* `pyps vmc auth` - setup and manage authentication details for CSP and its orgs
  * `pyps vmc auth setup` - setup your API access to a CSP org
  * `pyps vmc auth convert_token` - create an ad-hoc access token using your refresh token (no options/arguments required)
  * `pyps vmc auth get` - use to show authentication-related data pulled from CSP
* `pyps vmc show`
  * `pyps vmc show config` - display the contents of the entire configstore used by csptools (no options/arguments required)
  * `pyps vmc show org`
    * `pyps vmc show org refresh_token` - CSP refresh token
    * `pyps vmc show org access_token` - CSP access token
    * `pyps vmc show org access_token_age` - time until current access token expires
    * `pyps vmc show org org_id` - lookup a CSP org ID by org name
    * `pyps vmc show org org_name` - lookup a CSP org name by org ID
    * `pyps vmc show org org_config` - display the contents of the entire org config stored by csptools
    * `pyps vmc show org all` - show all orgs
    * `pyps vmc show org features` - show all features enabled for an org
    * `pyps vmc show org details` - show all details about an org
    * `pyps vmc show org tasks` - show all tasks for an org
    * `pyps vmc show org task` - show details about a specific task
    * `pyps vmc show org sddcs` - show SDDCs deployed in a given org
  * `pyps vmc show user`
    * `pyps vmc user show details` - show all details about an user
    * `pyps vmc user show orgs` - show orgs associated with the user
    * `pyps vmc user show roles` - show roles assigned to the user
    * `pyps vmc user show service-roles` - show admin role assigned to the user
* `pyps vmc org` - create and manage vmc orgs
  * `pyps vmc org create` - create a new org
  * `pyps vmc org delete` - delete an org
  * `pyps vmc org rename` - rename an existing org
  * `pyps vmc org type` - change org type
  * `pyps vmc org property` - manage org properties
    * `pyps vmc org property default` - apply default set of properties to an org
    * `pyps vmc org property set` - set a sepcific property on an org
    * `pyps vmc org property delete` - delete a property set on an org
    * `pyps vmc org property show` - show all properties on an org
  * `pyps vmc org show` - same as `pyps vmc show org`
  * `pyps vmc org user` - same as `pyps vmc user`
* `pyps vmc user` - manage vmc users
  * `pyps vmc user add` - invite a user to an org
  * `pyps vmc user remove` - remove a user from an org
  * `pyps vmc user role` - change role of a user within an org
    * `pyps vmc user role admin` - make a user an admin for an org
    * `pyps vmc user role change` - change the assigned role of the user
  * `pyps vmc user show` - same as `pyps vmc show user`
* `pyps preset` - manage built-in presets
  * `pyps preset load <file_name>` - load a new preset from a file
  ```sh
  pyps preset load pyps vmc new_preset
  # update csptools module with preset data from new_preset file
  ```
  * `pyps preset add <type> <module> <key:value> <key:value>...` - add new key:value pairs to a preset for a given module
  ```sh
  pyps preset add config csptools user:test id:1234
  pyps preset add metadata csptools url:test.com
  ```  
  * `pyps preset delete <type> <module> <key> <key>...` - delete keys from the preset for a given module
  ```sh
  pyps preset delete config csptools user
  pyps preset delete metadata csptools url name
  ```
  * `pyps preset clear <module>` - completely remove a preset from a given module
  `pyps preset clear csptools`
* `pyps aws iam` - create profiles and retrieve tokens
  * `pyps aws iam authenticate` - create a profile with access key ID and access key secret OR via LDAP log-in (inB only)
  ```bash
  pyps aws iam authenticate --profile test
  # populate /.aws/config and /.aws/credentials with login details for a profile "test"
  # this command will also save aws to data to local cache for future use
  ```
  * `pyps aws iam assume-role` - retrieve session token for a role in federated account AND add the federated account to pyps aws 
  ```bash
  pyps aws iam assume-role delta 1234567890
  # retrieve access details for account 1234567890 and save it under delta profile
  # note: this only has to be run once for other modules to work; 
  # you only need to re-run this if you intend to use the access details with awscli - the tokens generated will last for 30min
  # this command will also save aws to data to local cache for future use
  ```
* `pyps aws s3` - manage S3 buckets
  * `pyps aws s3 create` - create S3 bucket
  ```bash
  pyps aws s3 create test --profile delta
  # create a bucket test under the account saved under "delta" profile
  ```
  * `pyps aws s3 delete` - delete S3 bucket
  ```bash
  pyps aws s3 delete test
  # delete a bucket test under the account saved under "default" profile
  ```
  * `pyps aws s3 upload` - upload a local file/folder to S3
  ```bash
  pyps aws s3 upload ./folder-local test-bucket --profile test
  # upload the "folder-local" folder to "test" bucket under the account saved in test profile
  ```
  * `pyps aws s3 download` - download files from a bucket to local storage
  ```bash
  pyps aws s3 download test-bucket ./folder-local
  # download the contents of test-bucket located in an account saved under the "default" profile and save it to ./folder-local path on your local system
  ```
  * `pyps aws s3 refresh` - refresh the cached data about s3 objects - note: this kicks-in automatically each week
  * `pyps aws s3 show` - show all buckets on the account or files within a bucket
  ```bash
  pyps aws s3 show buckets --profile delta
  # show all S3 buckets on an account saved under the default profile
  pyps aws s3 show test-bucket --profile delta
  # show all files saved in the 'test-bucket' bucket in delta profile
  ```
* `pyps aws ec2` - manage EC2 resources
  * `pyps aws ec2 refresh` - refresh the cached data about EC2 objects - note: this kicks-in automatically each week
  * `pyps aws ec2 show` - show a table view of EC2 objects of a given type
  ```bash
  pyps aws ec2 show instances --profile delta
  # show all EC2 instances on an account saved under the default profile
  ```
* `pyps aws rds` - manage RDS resources
  * `pyps aws rds refresh` - refresh the cached data about RDS objects - note: this kicks-in automatically each week
  * `pyps aws rds show` - show RDS instances on a given account
* `pyps aws cli` - run any awscli commands leveraging pyps aws profile management
```bash
pyps aws cli --profile delta s3 ls
# this will run "aws s3 ls" while sourcing the login details for delta profile
# remember to run 'authenticate --profile delta' or 'assume-role delta 12344564564' at least once before using the cli module
```

For help with required and optional parameters, please see the `pyps <subcommand> --help` 

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- HOW TO ADD A NEW COMMAND -->
## How to add a new Commenad

If your module/utility was writted with click and follows the click layout used in all other modules, you should be able to add it to PYPS with just a simple modification to pyps.py. Let's say we're adding a new module called `pinger` to PYPS. 
In the example below, we assume that `pinger` module's entry-point is a `cli()` function in it's `pinger.py` file and all its functionality is mapped to commands with `click`.
```python
### pyps.py 
import click
(...)
from pinger.pinger improt cli as pinger_cli
(...)
cli.add_command(pinger_cli, name='pinger') # do NOT use generic names such as 'cli' in here; this can BREAK PYPS
```
The code above will import pinger into pyps whenever the user issues a `pyps pinger` command and use the `click` config you already added to `pinger.py` file and any other source files.

If however your module does not use `click` for command parsing or doesn't have command parsing implemented at all, please refer to `pyps/pyps/cmd_slack.py` and `pyps/pyps/cmd_comms.py` for examples on how to intergrate modules utilising other command parsers or no parsers at all respectively.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ROADMAP -->
## Roadmap

- [ ] TBD - roadmap not yet available

See the [open issues](https://gitlab.eng.vmware.com/govcloud-ops/govcloud-devops-python/issues) for a full list of proposed features (and known issues).

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


<!-- CONTACT -->
## Contact

Paul Wilk - wilkp@vmware.com

Project Link: [https://gitlab.eng.vmware.com/govcloud-ops/govops-devops-python](https://gitlab.eng.vmware.com/govcloud-ops/govops-devops-python)

<p align="right">(<a href="#readme-top">back to top</a>)</p>