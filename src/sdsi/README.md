# SDSi Validation
## Configuration Requirements
#### To run SDSi validation scripts, the following basic configuration must be satisfied:
* Python version must be >=3.8.
  >Python 3.8.10 is the latest version with installer: https://www.python.org/downloads/release/python-3810/
  
* Python2 must be installed for rsc2 support.
  >Python 2.7.13 is recommended: https://www.python.org/downloads/release/python-2713/

* Required Python modules must be installed.
  >The modules are listed at requirements.txt in the sdsi directory. <br>
  A single command can be run to install all required modules in a single pip command. <br>
  You may be prompted for credentials for intel internal modules: <br>
  `pip install -r requirements.txt --proxy http://proxy-chain.intel.com:911`
  
* Xmlcli must be configured on the SUT. The last tested version was xmlcli-1.6.3.
  Python Must also be installed on the SUT to execute xmlcli commands.
  >Place the Xmlcli package in the appropriate directory on the SUT as defined in the Automation config folder. <br>
  Ex: \<sutospath>**/opt/APP/xmlcli/**\</sutospath>

* Dtaf environment variables must be defined.
  >An environment variable must be added to PYTHONPATH for the dtaf_content root folder. Ex: `C:\dtaf\dtaf_content` <br>
  An environment variable must be added to PYTHONPATH for the site-packages folder. Ex: `C:\Python38\Lib\site-packages`
  
* Dtaf configuration files must be created on host at C:\Automation
  >A system configuration file. Ex: `C:\Automation\system_configuration.xml` <br>
  A python variable configuration file. Ex: `C:\Automation\JF53SPV0005A.cfg` <br>

* The SDSi-Agent must be installed on the SUT.
    > Verify the installation with `sdsi-agent -h`

* Feature LACs and Erase LAC must be placed in the root/sdsi_licenses directory.
  > Use the standard naming for feature LACs, Ex: `2272C3CAFAEA6754_key_id_1_rev_97_DSA4_IAA4.json` <br>
  Use the standard name for erase key: `MASTER_ERASE_LAC-EagleStream-00000000-FOR_PREPRODUCTION_CPUS_ONLY.json` <br> <br>
  (optional) For automatic LAC requesting, obtain an API-key: https://api-portal.intelondemand-prx.intel.com/ <br>
  This API key must be saved as an environment variable named sdsi_api_key. The test scripts will automatically
  attempt LAC requesting if the required LAC is missing.

## Directory Structure:
    sdsi: SDSi test domain root
    ├── deployment: Contains scripts used to create a deployable framework to sprinter/command center.
    ├── lib: Contains all common libraries/tools to provide test functionality.
    │   ├── license: Contains automatic license requesting tools.
    │   └── tools: Contains modular type-specific tools which can be imported by test scripts.
    └── tests: Contains all of the scripts for sdsi validation.
        ├── agent: Contains the test scripts implemented using the sdsi-agent.
        └── provisioning: Contains the test scripts implemented using the sdsi-installer/parser. (Soon to be deprecated)
