#!/bin/bash
dmidecode -t 17 > dimm_info_get.txt
diff dimm_info_get.txt dimm_info_golden.txt > /dev/null
if [ $? != 0 ];then
	echo "TEST FAIL"
	exit 1
else
	echo "TEST PASS"
fi
