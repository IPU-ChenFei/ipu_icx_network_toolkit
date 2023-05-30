# Host Environment Setup Guide

#### Method to Use
    ```
    Preparation: Make sure your host have installed git and have access to clone repo code from git webset
    
    Default Command: host_setup.exe -p child-prc.intel.com:913
    Option : host_setup.exe -i -p proxy-us.intel.com:911[，proxy-us.intel.com:912] -v v1.38.0rc0
         -i: Skip download steps only install local tools
         -p: Set http_proxy and https_proxy, if use different proxy, refer to the format < -p http_proxy,https_proxy>
         -v: Install the specific dtaf_core version you provided, default to install v1.38.0rc2
             Release Link: https://github.com/intel-innersource/frameworks.automation.dtaf.core/releases
    ```

#### Description
1. Check dtaf-core install version
2. Install tkconfig and set env path
3. Download tools from artifactory(https://ubit-artifactory-sh.intel.com/artifactory/validationtools-sh-local/env/host) to local
4. Disable firewall and powercfg
5. Install host tools

#### Build a new executable file (For tool developer)
1. modify source code in tksetup\host\host_setup.py
2. install python lib __pyinstaller__
    ```
    pip install pyinstaller --proxy=child-prc.intel.com:913
    ```
3. running .bat file
    ```
    tksetup\host\build.bat
    ```
