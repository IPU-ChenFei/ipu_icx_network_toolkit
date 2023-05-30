#!/bin/bash
# Run this only once to get baseline config

if [ ! -d /var/log/cycling ]
then
	mkdir /var/log/cycling
fi

# clean up any previous run data
rm -r -f /var/log/cycling/linkstates
rm -r -f /var/log/cycling/cxl_capabilities
mkdir /var/log/cycling/linkstates
mkdir /var/log/cycling/cxl_capabilities
echo 0 > /var/log/cycling/CycleCount
echo 0 > /var/log/cycling/LinkErrorCount
echo 0 > /var/log/cycling/CxlCapErrorCount
echo "Capturing baseline PCIe Link status...." 
# collect the linkstatus information from lspci
lspci -vv | grep -e "LnkSta:" -e "^[[:xdigit:]][[:xdigit:]]:[[:xdigit:]][[:xdigit:]].[[:xdigit:]]" | sed "s/^.*\(LnkSta:.*\),.*$/\1/" > /var/log/cycling/linkstates/InitialLinkState
echo "Baseline PCIe link status stored in /var/log/cycling/linkstates/InitialLinkState"

echo "Capturing baseline Cxl Capabilities data..."
lspci -vv | grep -e "CXLCap" -e "CXLCtl" > /var/log/cycling/cxl_capabilities/Initial_Cxl_Capabilities
echo "Baseline CXL Capabilities stored in /var/log/cycling/cxl_capabilities/Initial_Cxl_Capabilities"
