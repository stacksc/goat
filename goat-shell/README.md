<img width="150" height="150" alt="image" src="https://github.com/stacksc/goat/assets/116677370/1c49320a-f116-4a7e-bb36-0bdbaf3934ac">
<video width="600" height="300" src="https://github.com/stacksc/goat/assets/116677370/58e27064-3e4a-4e90-a8ba-229b1ae6258c"></video>

<h1>GOATSHELL</h1>
<h2>7 Clouds & 1 Shell</h2>

## Installation

### Manual Installation

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
   git clone git@github.com:stacksc/goat.git
   ```
4. Install all required packages with 1 script from the main repository: 
   ```sh
   cd ~/prod/goat && ./bulk.sh --action rebuild --target all
   ```

### PIP installation (stable)

1. Install the following packages from pypi:
   ```
   pip install goatshell goaat --force-reinstall
   ```
2. Type the following command to launch goatshell:
   ```
   goatshell
   ```

```
┌───────────────────────────────────────────────────────────────────────────────────────────────────────| GOAT INTERFACE |───────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                     Purpose: Cloud Wrapper                                                                                                     │
│                                                                                             TIP: resource completion coming soon!                                                                                              │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
┌────────| Hotkeys |─────────┐┌─────────────| Advanced |─────────────┐┌────────| Commands |────────┐
│[F9]  Toggle VI mode        ││history   : shell history             ││e|exit    : exit shell      │
│[F10] Toggle Profile        ││!<cmd>    : run OS command            ││c|clear   : clear screen    │
│[TAB] Fuzzy Complete        ││cloud     : view cloud details        ││h|help    : display usage   │
└────────────────────────────┘└──────────────────────────────────────┘└────────────────────────────┘

    Auto-Completion Instructions:
    ----------------------------
    1. To trigger auto-completion, start with TAB or type the beginning of a command or option and press Tab.
    2. Auto-completion will suggest available commands, options, and arguments based on your input.
    3. Use the arrow keys or Tab to navigate through the suggestions.
    4. Press Enter to accept a suggestion or Esc to cancel.
    5. If an option requires a value, use --option=value instead of --option value.
    6. The prompt will change dynamically based on cloud provider interaction.

[oci:DEFAULT]>
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Contacts
Christopher Stacks - <centerupt@gmail.com>

## Mechanics
The project is built with dependecies such as aws2, oci-cli, az-cli. <br>However, other cloud providers are configured to work but <u>NOT</u> packaged with the project such as ibmcloud, gcloud, and Alibaba cloud.
<br><br>
Each time the first token is passed (i.e. cloud provider) a function will verify if the command is avialable.
<br>
This keeps the command line clean with the cloud providers you only work with.
<br><br>
The following cloud providers are currently supported:
<br>
<img width="777" alt="image" src="https://github.com/stacksc/goat/assets/116677370/faea14fd-0aba-42ec-93d2-9325614cffcd">

## Toolbar
The toolbar will refresh after hitting the ENTER key or with specific hotkeys.
<br><br>
The toolbar is updated appropriately based on what command you ran. Once you run a command, the toolbar is refreshed with your <u>current</u> cloud.
<br><br>
The profile is updated <u>dynamically</u> based on your <u>current</u> cloud and you have the ability to toggle profiles for any cloud.

```
goat>
Current Cloud: AWS  F8 Usage F10 Toggle Profile: CENTERUPT F12 Quit
```

## Toggle
The only toggle currently supported is profile switching. Everything else is dynamic based on first token.
<br>

<!DOCTYPE html>
<html>
<body>

<h2>Cloud CLI Options</h2>

<table border="1">
    <thead>
        <tr>
            <th>#</th>
            <th>Name</th>
            <th>Status</th>
            <th>Additional Info</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>1</td>
            <td>OCI-CLI</td>
            <td>Default / Supported</td>
            <td></td>
        </tr>
        <tr>
            <td>2</td>
            <td>AWS</td>
            <td>Default / Supported</td>
            <td></td>
        </tr>
        <tr>
            <td>3</td>
            <td>AZ</td>
            <td>Default / Supported</td>
            <td></td>
        </tr>
        <tr>
            <td>4</td>
            <td>GCLOUD</td>
            <td>Supported / Manual Installation</td>
            <td><a href="https://cloud.google.com/sdk/docs/install">Installation Guide</a></td>
        </tr>
        <tr>
            <td>5</td>
            <td>ALIYUN</td>
            <td>Supported / Manual Installation</td>
            <td><a href="https://www.alibabacloud.com/help/en/alibaba-cloud-cli/latest/install">Installation Guide</a></td>
        </tr>
        <tr>
            <td>6</td>
            <td>IBMCLOUD</td>
            <td>Supported / Manual Installation</td>
            <td><a href="https://cloud.ibm.com/docs/cli?topic=cli-install-ibmcloud-cli">Installation Guide</a></td>
        </tr>
    </tbody>
</table>

</body>
</html>


Once the relative CLI is installed, the goatshell application will recognize that it is available & syntax completion will be provided.<br>
The project is packaged with cloud provider JSON files which get refreshed automatically per major release with dynamic CLI scrapers.<br><br>
As the first token is passed (i.e. cloud provider) it directs the goatshell application to the correct JSON file.

