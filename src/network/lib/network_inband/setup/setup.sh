#!/bin/bash

# PRC Proxy
export http_proxy=http://child-prc.intel.com:913
export https_proxy=http://child-prc.intel.com:913

# Python Dependencies
pip3 install paramiko --proxy=http_proxy=http://child-prc.intel.com:913

# Python Environment Variable
export PYTHONPATH=$PYTHONPATH:..
