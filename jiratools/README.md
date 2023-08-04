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
    <li><a href="#cliusage">CLI Usage</a></li>
    <li><a href="#devusage">Dev Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

JiraClient - a CLI client and Python module for interacting with VMware JIRA

Current features:
* creating and updating issues
* searching for issues based on JQL (jira query language)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting Started

### Prerequisites

Internal packages:
* toolbox
  ```sh
  https://gitlab.eng.vmware.com/wilkp/pssrex/-/tree/main/toolbox
  ```
External packages:
* click
  ```sh
  pip install click
  ```
* jira
  ```sh
  pip install jira
  ```
* tabulate
  ```sh
  pip install tabulate
  ```

### Installation

1. Clone the repo or download the latest wheel from /dist
2. Install the wheel with pip or add the cloned repo to one of your paths (python3 -c "import sys; print(sys.path)")
3. To use the jiraclient in CLI mode (ie as a bash command), run `jiraclient auth -u JIRA_URL_HERE -m (pass/token)` to setup your user profile

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CLI USAGE EXAMPLES -->
### CLI Usage

* `jiraclient auth` - setup user authentication to JIRA server
  ```sh
  jiraclient auth --url https://jira.example.com --mode pass # authenticate with username and password (saved to default profile)
  jiraclient auth --url https://jira.example.com --mode token # authenticate with user API token
  jiraclient auth --url https://jira.example.com --mode pass --profile beta # authenticate with user API token and create a new profile 'beta'
  ```
* `jiraclient issue` - manage and search for issues (tickets)
  * `jiraclient issue comment` - post a comment on a given issue
    ```sh
    jiraclient issue comment PUBSECSRE-123 --commente "this is a comment"
    ```
  * `jiraclient issue create` - create a new issue on a project
    ```sh
    jiraclient issue crete --project PUBSECSRE --summary "test ticket" --description "this is a test ticket"
    ```
  * `jiraclient issue transition` - transition the issue to a new status
    ```sh
    jiraclient issue transition PUBSECSRE-123 --name Closed --profile jira
    # transition the issue PUBSECSRE-123 to status 'Closed' using credentials stored on profile "jira"
    jiraclient issue transition PUBSECSRE-123 --showavailable 
    # display available transitions for PUBSECSRE-123 and required updates to the ticket fields (if any)
    jiraclient issue transition PUBSECSRE-123 --id 211 --payload '{"resolution": {"id": "10000"}}'
    # transition PUBSECSRE-123 to status id 211 (Closed) and update the "resolution" field with an allowed value of an id = 10000 (Done)
    jiraclient issue transition PUBSECSRE-123 --id 11 --payload '{"status": {"id": "1234"}, "assignee": {"user": "wilkp"}}'
    # transition PUBSECSRE-123 to status id 11 (in progress) and update the "assignee" to user "wilkp" and set the status to "investigation" (id 1234)
    ```
  * `jiraclient issue update` - updates a given field on an issue
    ```sh
    jiraclient issue update PUBSECSRE-123 -field assignee --value jdoe
    ```
  * `jiraclient issue extract` - extracts value for a dataset in issue description (i.e. worker: John)
    ```sh
    jiraclient issue exctract PUBSECSRE-123 --data_key worker
    # will return a value for the first found key containing the string 'worker' in its name
    jiraclient issue exctract PUBSECSRE-123 --data_key 'shift worker' --exact
    # will return a value for the key with name 'shift worker' if found
    jiraclient issue exctract PUBSECSRE-123 --data_key exworker --exact --multiple
    # will return an array of values for the keys named 'exworker'
    ```
  * `jiraclient issue search` - show summary for an issue or a list issues
    ```sh
    jiraclient issue search PUBSECSRE-301
    # show issues details for issues PUBSECSRE-301
    jiraclient issue search PUBSECSRE-301 PUBSECSRE-302 --json
    # show issues details for issues PUBSECSRE-301 and PUBSECSRE-302 and display result as json
    jiraclient issue search PUBSECSRE-301 PUBSECSRE-302 --csv
    # show issues details for issues PUBSECSRE-301 and PUBSECSRE-302 anbd save the result to csv file
    ```
* `jiraclient project` - manage and search for projects
  * `jiraclient project search` - search for projects based on entered parameters (supports autocomplete)
  ```sh
  jiraclient project search PUBSECSRE --status closed --orderby group --limit 3 --descending 
  # show issues in specific project and on specific status; display 3 results in descending order sorting by assigned group
  jiraclient project search PUBSECSRE --project CSSD --csv jdoe_tickets --reporter jdoe
  # show issues on PUBSECSRE or CSSD projects assigned to jdoes and export the results to a csv file named jdoe_tickets.csv
  jiraclient project search PUBSECSRE CSSD --reporter jdoe --reported jsmith --profile beta
  # show issues assigned to PUBSECSRE or CSSD and assigned to either jdoe or jsmith user; use profile 'beta' for authentication
  ```
* `jiraclient search` - search for issues in Jira
```sh
jiraclient search --project PUBSECSRE --project VMWGOV --status 'closed' --orderby group --limit 3 --descending 
# show issues in specific projects and on specific status; display 3 results in descending order sorting by assigned group
jiraclient search --status 'closed' --status 'done' --csv jdoe_tickets --reporter 'jdoe'
# show issues assigned to jdoe and with status closed or done and export the results to a csv file named jdoe_tickets.csv
jiraclient search --reporter 'jdoe' --reported 'jsmith' --profile beta
# show issues assigned to either jdoe or jsmith user; use profile 'beta' for authentication
```

For help with required and optional parameters, please see the `jiracleint <subcommand> --help` 

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- DEV USAGE EXAMPLES -->
### Dev Usage

* create a JIRA issue
```python
from jiraclient.issue import create_issue
JSON_RESPONSE = create_issue(target_project='PUBSECSRE', issue_summary="Someone's testing the jiraclient module...", issue_description="...and that someone is me.")
print(json.dumps(JSON_RESPONSE))
```
* search for issue and save the result as csv; also accepts raw jql
```python
from jiraclient.show import run_jql_query
FOUND_ISSUES, GENERATED_JQL = run_jql_query(project='PUBSECSRE', assignee='wilkp', csv=True)
FOUND_ISSUES, GENERATED_JQL = run_jql_query(jql='PROJECT = PUBSECSRE AND ASSIGNEE = wilkp', csv=True)
print(f"Found issues {FOUND_ISSUES}\nby running '{GENERATED_JQL}' JQL query")
```
* fetch a JIRA session using credentials stored in configstore profile
```python
from jiraclient.auth import get_jira_session
JIRA_SESSION = get_jira_session('myProfile')
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ROADMAP -->
## Roadmap

- [X] add instancing (multiple user profiles/sessions per config)
- [ ] add bash autocomplete 
- [ ] polish transitioning issues

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