#!/bin/bash
# Run this only once to get baseline config

if [ ! -e /var/log/cycling ]
then
	mkdir /var/log/cycling
fi

# clean up any previous run data
rm -r -f /var/log/cycling/linkstates
mkdir /var/log/cycling/linkstates
echo 0 > /var/log/cycling/CycleCount
echo "Capturing baseline PCIe Link status...." 
# collect the linkstatus information from lspci
lspci -vv | grep -e "LnkSta:" -e "^[[:xdigit:]][[:xdigit:]]:[[:xdigit:]][[:xdigit:]].[[:xdigit:]]" | sed "s/^.*\(LnkSta:.*\),.*$/\1/" > /var/log/cycling/linkstates/InitialLinkState
echo "Baseline PCIe link status stored in /var/log/cycling/linkstates/InitialLinkState" 

