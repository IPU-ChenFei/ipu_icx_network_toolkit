#！/usr/bin/sh
#date:2021-12-22


# set proxy
echo ----------------------------------
echo Provide below proxy for reference
echo ----------------------------------
echo China: child-prc.intel.com:913
echo India: proxy01.iind.intel.com:911
echo America: proxy-us.intel.com:911
echo Common: proxy-chain.intel.com:911
echo ----------------------------------

echo press "Enter" to use default proxy
read -p "set http_proxy:" proxy

if [ "$proxy" == "" ];then
  export http_proxy=child-prc.intel.com:913
  echo use default proxy
else
  export http_proxy=$proxy
fi

pip3 install prettytable
pip3 install frameworks.automation.dtaf.core-production.zip

# set python3 interpretor cmd interface as python
python3_link="/usr/bin/python"
if [ ! -L $python3_link ];then
  ln -s /usr/bin/python3 /usr/bin/python
fi
