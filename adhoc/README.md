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

AdHoc Client - a CLI client for interacting with adhoc modules and/or scripts

Current features:
* using this as a template to setup the adhoc client
* no major features yet

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

For help with required and optional parameters, please see the `adhoc <subcommand> --help` 

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
### Dev Usage

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- ROADMAP -->
## Roadmap

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
6. Rebuild the project and test for accuracy (`./rebuild.sh adhoc`)

After making changes to the source code, please remember to build a new wheel for the project by running `python3 -m build --wheel` in the root of the project (where .toml file is)

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- CONTACT -->
## Contact

Chris Stacks - stacksc@vmware.com
Paul Wilk - wilkp@vmware.com

Project Link: [https://gitlab.eng.vmware.com/govcloud-ops/govops-devops-python](https://gitlab.eng.vmware.com/govcloud-ops/govops-devops-python)

<p align="right">(<a href="#readme-top">back to top</a>)</p>
