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
The toolbar will refresh after hitting the ENTER key or with specific hotkeys. If you run an aws command, you will be in AWS mode and have the ability to toggle profiles.
<br><br>
If the cloud prefix changes, the toolbar will update to that cloud provider. The profiles change based upon the cloud prefix.
<br>
   1. oci iam user list <enter>
   2. the command runs, processes and you are now in OCI mode.
   3. aws account regions list, rinse and repeat [cycle through whatever cloud provider is needed for the moment]
<br>

And the toolbar is updated appropriately to AWS mode:

```
goat>
Current Cloud: AWS  F8 Usage F10 Toggle Profile: CENTERUPT F12 Quit
```

### toggle
The only toggle currently supported is profile switching. Everything else is dynamic based on first token.
<br>
