#!/bin/bash
# TOOLSET CHECK
# name: mlc
# domain: bkc
# version: 3.9a
# md5sum: 744FB9476DBE24712B8B743B205BBDA4

INSTALL_PATH=$HOME/mlc

test -d $INSTALL_PATH

if [ $? -ne 0 ]; then
	echo "$INSTALL_PATH not exists"
	exit -1
fi


chmod +x $INSTALL_PATH/Linux/mlc

if [ $? -ne 0 ]; then
	echo "$INSTALL_PATH/Linux/mlc not executable"
	exit -3
fi

echo 5926de9cdf93435c975c36b10f4da8b3  /root/mlc/mlc_tool_license.txt > mlc.md5
echo 4d2d1bb84ad81a6cadc90482fdc1c6fc  /root/mlc/readme_mlc_v3.9a.pdf >>mlc.md5
echo 423c6beb6a0ade5bd239a3b129062979  /root/mlc/Required_libraries.txt >>mlc.md5
echo cf883b46be2e127500319d1d3a409495  /root/mlc/Linux/mlc >>mlc.md5
echo c1715dfd71f3679b81227ad8eaad3b70  /root/mlc/Linux/redist.txt >>mlc.md5
echo 52371bec01d91b9840ed895f4a4cfc8c  /root/mlc/Windows/mlcdrv.sys >>mlc.md5
echo b7f124eb2a012d9f93a4a40380671ba8  /root/mlc/Windows/mlc.exe >>mlc.md5
echo 2baf836bd30f73e1b6d2ae97b519c1b1  /root/mlc/Windows/redist.txt >>mlc.md5

md5sum -c mlc.md5
if [ $? -ne 0 ]; then
	echo "Installed version not match"
	exit -4
fi

echo "Check Linux MLC Install at $INSTALL_PATH"
echo "Passed!"
exit 0
