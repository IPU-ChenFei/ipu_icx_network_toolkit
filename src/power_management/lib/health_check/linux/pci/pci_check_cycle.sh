#!/bin/bash
# Compare the link status with baseline linkstatus and update the status
echo ""

if [ ! -e /var/log/cycling ]
then
	echo "Cycling scripts have no been properly setup"
	exit
fi

timestamp=`date`
let count=`cat /var/log/cycling/CycleCount`+1
echo $count > /var/log/cycling/CycleCount
echo "Cycle number $count at: $timestamp" >> /var/log/cycling/CycleLog
echo "Cycle number $count at: $timestamp" 


echo ""
echo "checking pcie link status..."
lspci -vv | grep -e "LnkSta:" -e "^[[:xdigit:]][[:xdigit:]]:[[:xdigit:]][[:xdigit:]].[[:xdigit:]]" | sed "s/^.*\(LnkSta:.*\),.*$/\1/" > "/var/log/cycling/linkstates/cycle$count.$timestamp"
if diff -q /var/log/cycling/linkstates/InitialLinkState "/var/log/cycling/linkstates/cycle$count.$timestamp" > /dev/null
then
	echo "Link states correct"
else
	echo "Link failure"
	let lnkerr=`cat /var/log/cycling/LinkErrorCount`+1
	echo $lnkerr > /var/log/cycling/LinkErrorCount
	echo "  --ERROR-LNK- Link failure! see /var/log/cycling/linkstates/cycle$count.$timestamp for more information" >> /var/log/cycling/CycleLog
	echo "  --$lnkerr link failures so far--" >> /var/log/cycling/CycleLog
	echo "$lnkerr link failures so far"
fi
echo "...done"

