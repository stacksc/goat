<img width="150" height="150" alt="image" src="https://github.com/stacksc/goat/assets/116677370/1c49320a-f116-4a7e-bb36-0bdbaf3934ac">
<video width="600" height="300" src="https://github.com/stacksc/goat/assets/116677370/58e27064-3e4a-4e90-a8ba-229b1ae6258c"></video>

<h1>GOATSHELL</h1>
<h2>7 Clouds & 1 Shell</h2>

## Getting Started

### Prerequisites
### Installation

#### Manual Installation

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

#### PIP installation (stable)

1. Install the following packages from pypi:
   ```
   pip install goatshell goaat
   ```
   
<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Contacts
Christopher Stacks - <centerupt@gmail.com>

## Mechanics
The project is built with dependecies such as aws2, oci-cli, az-cli, and gcloud. <br>However, other cloud providers are configured to work but not packaged with the project such as ibmcloud and Alibaba cloud.
<br><br>
If the command isn't available, such as ibmcloud or aliyun, suggestions will not be provided. Otherwise syntax completion works as normal.
<br><br>
The following cloud providers are currently supported:
<br>
<img width="1008" alt="image" src="https://github.com/stacksc/goat/assets/116677370/e2dfca65-a741-43e4-a2d7-19fac3f7f54a">

### toolbar
The toolbar will refresh after hitting the ENTER key or with specific hotkeys.
<br><br>
The toolbar is updated appropriately based on what command you ran. Once you run a command, the toolbar is refreshed with your <u>current</u> cloud.
<br><br>
The profile is updated <u>dynamically</u> based on your <u>current</u> cloud and you have the ability to toggle profiles for any cloud.

```
goat>
Current Cloud: AWS  F8 Usage F10 Toggle Profile: CENTERUPT F12 Quit
```

### toggle
The only toggle currently supported is profile switching. Everything else is dynamic based on first token.
<br>
