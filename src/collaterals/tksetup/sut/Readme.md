# SUT Environment Setup Guide

#### Method to setup sut environment
    * Windows Command: os_initial_win.bat
    * Linux Command: dos2unix os_initial_linux.sh & sh os_initial_linux.sh
    * Esxi Command:  dos2unix os_initial_esxi.sh & sh os_initial_esxi.sh
Note: For windows OS, copy env_ini.ps1 and os_initial_win.bat to the same folder.
      For linux OS, copy init_yum_repos.sh and os_initial_linux.sh to the same folder.

#### Method to running inband mode
    * Preparation: Download dtaf_core production zip file and put it in tksetup/sut/(linux/windows)
    
    * Windows Command: env_ini_inband.bat
    * Linux Command: dos2unix env_ini_inband.sh & sh env_ini_inband.sh

#### Windows Function
1. Download tools from artifactory(https://ubit-artifactory-sh.intel.com/artifactory/validationtools-sh-local/env/sut/windows) to C:\\BKCPkg\tools
2. modify powreshell execution policy as bypass
3. install xmlcli
4. disable firewall
5. copy devchk dir to C:\BKCPkg
6. copy devchk python packages to py36 sit-packages
7. stop powershell server service
8. install openssh and start servicer
9. install CCBSDK_Internal.exe
10. install python3 interpreter
11. print promption info

#### Linux Function
1. Download tools from artifactory(https://ubit-artifactory-sh.intel.com/artifactory/validationtools-sh-local/env/sut/linux) to /home/BKCPkg/tools
2. install python36 interpreter
3. install xmlcli
4. install uefi tools
5. install screen for async cmd execution
6. disable firewall and selinux
7. reboot when selinux config is changed
8. print promption info

#### Esxi Function
1. disable firewall
2. print promption info
