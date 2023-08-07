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

SlackClient - a CLI client and Python module for interacting with VMware Slack

Current features:
* posting and deleting messages and reactions
* replying and reacting to messages in threads
* creating and archiving channels
* inviting and removing people from channels

NOTE: this project is using `argparse` on purpose to demonstrate backwards-compability

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
* slack_sdk
  ```sh
  pip install slack_sdk
  ```
* argparse
  ```sh
  pip install argparse
  ```

### Installation

1. Clone the repo or download the latest wheel from /dist
2. Install the wheel with pip or add the cloned repo to one of your paths (python3 -c "import sys; print(sys.path)")

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
### CLI Usage

* `slackclient post` - post a message
```sh
slackclient --channel C123456789 --messagetext "Hello" --reply 123456.7890
# send message Hello to C123456789 channel in a threaded reply to message ID 123456.7890
```
* `slackclient react` - react to a message
```sh
slackclient react --channel C123456789 --timestamp 123456.7890 --emoji :+1 --profile beta
# react with a thumbs up (:+1) to a mesage ID 123456.7890 in channel C123456789, using user profile 'beta'
```
* `slackclient unpost` - delete a message
```sh
slackclient unpost --channel C123456789 --timestampp 123456.7890
# delete a message ID 123456.7890 in channel C123456789
```
* `slackclient unreact` - remove a reaction to a message
```sh
slackclient unreact --channel C123456789 --timestamp 123456.7890 --emoji :+1
# remove a thumbs up reaction (:+1) from a message ID 123456.7890 in channel C123456789
```
* `slackclient channel` - manage Slack channels
  * `slackclient channel --action adduser` - add a user to the channel
  ```sh
  slackclient channel --action adduser --user jdoe --channel C1234567890
  # add user jdoe to channel C123456789
  ```
  * `slackclient channel --action deluser` - kick a user from the channel
  ```sh
  slackclient channel --action deluser --user jdoe --channel C123456789
  # remove a user jdoe from channel C123456789
  ```
  * `slackclient channel --action create` - create Slack channel
  ```sh
  slackclient channel --action create --name test_channel --private
  # create a channel named test_channel and mark is as private
  ```
  * `slackclient channel --action archive` - mark channel as archive
  ```sh
  slackclient channel --action archive --channel C123456789
  ```
  * `slackclient channel --action unarchive` - mar channel as active again
  ```sh
  slackclient channale --action unarchive --channel C123456789  
  ```
  * `slackclient channel --action topic` - set a topic for the channel
  ```sh
  slackclient channel --action topic --topic "this is a topic" --channel C123456789
  ```

For help with required and optional parameters, please see the `slackclient <subcommand> --help` 

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
### Dev Usage

* post a message as a reply
```python
from slackclient.post import post_slack_message
JSON_RESPONSE = post_slack_message(channels='C123456789', message_text='Hello there', thread_timestamp='12345.67890')
print(JSON_RESPONSE)
```
* create a slack channel and mark it as private
```python
from slackclient.channel import channel_create
JSON_RESPONSE = channel_create('test_channel', private=True)
print(JSON_RESPONSE)
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ROADMAP -->
## Roadmap

- [ ] profiles - allow to connect to Slack as multiple users
- [ ] further enhance bulk operations

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

Christopher Stacks - stacksc@vmware.com

Project Link: [https://gitlab.eng.vmware.com/govcloud-ops/govops-devops-python](https://gitlab.eng.vmware.com/govcloud-ops/govops-devops-python)

<p align="right">(<a href="#readme-top">back to top</a>)</p>