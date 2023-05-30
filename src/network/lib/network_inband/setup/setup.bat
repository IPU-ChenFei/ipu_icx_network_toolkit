@echo off

:: PRC Proxy
set http_proxy=http://child-prc.intel.com:913
set https_proxy=http://child-prc.intel.com:913

:: Python Dependencies
pip install paramiko

:: Python Environment Variable
set PYTHONPATH=%PYTHONPATH%;..
