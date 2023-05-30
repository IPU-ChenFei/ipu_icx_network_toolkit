# Accelerator Interop and Concurrency Test Cases

## 1 - For all RAS Memory Uncorrectable and Correctable Stress Tests

- Make sure "FISH" tool is installed in the SUT and VM as per the test case.
    - Follow these steps for the installation :
        - Check the version of python installed.
            - Use "python --version" or "python3 --version" to check the python version.
            - Link python and python3 "ln -s /usr/bin/python3.6 /usr/bin/python".
            - Install python devel "yum install python36-devel".
        - Run below commands for download and installation fisher tool.
            - export no_proxy=*.intel.com
            - export PYTHONHTTPSVERIFY=0
            - export PIP_TRUSTED_HOST=intelpypi.pdx.intel.com
            - pip3 install pysvtools.fish-automation -i https://intelpypi.pdx.intel.com/pythonsv/production

## 2 - For all RAS Memory Correctable Tests in VM using FISHER Tool

- On Host/NUC, Go to C:\Python36\Lib\site-packages\pysvtools\fish_automation and open command prompt.
- Run "python remote_injector.py --platform=EagleStream --server-port=1900" command for remote injection.