<img width="150" height="150" alt="image" src="https://github.com/stacksc/goat/assets/116677370/1c49320a-f116-4a7e-bb36-0bdbaf3934ac">
<video width="600" height="300" src="https://github.com/stacksc/goat/assets/116677370/2d306e98-defe-4c9f-8c2d-0368fbd297f0">

<a name="readme-top"></a>
<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#hlo">HLO</a></li>
      <li><a href="#about-the-project">About The Project</a>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contacts">Contacts</a></li>
    <li><a href="#cache-data">Cache</a></li>
    <li><a href="#current-usage">Usage</a></li>
    <li><a href="#versions">Versions</a></li>
    <li><a href="#jira-authentication">JIRA authentication</a></li>
    <li><a href="#user-manuals">User Manuals</a></li>
  </ol>
</details>

<p align="right">(<a href="#readme-top">back to top</a>)</p>
<!-- GETTING STARTED -->
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
5. Install oci-cli using the latest version:<br>
   a. Mac
      ```sh
      brew install oci-cli
      ```
   b. Linux
      ```sh
      bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"
      ```

#### OR with PIP

1. Install the following packages from pypi:
   ```
   pip install goatshell goaat
   ```
   
<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTACTS -->
## Contacts
Christopher Stacks - <centerupt@gmail.com>

#### OCI / GCLOUD / AWS / AZ Shell Interface ####
<img width="2555" alt="image" src="https://github.com/stacksc/goat/assets/116677370/1dbf12c3-2d1f-4508-82a6-bd1ca794a1d8">
<br>
