::date:2021-12-23

echo --------------------------------------
echo ^| Provide below proxy for reference  ^|
echo --------------------------------------
echo ^|  China: child-prc.intel.com:913    ^|
echo ^|  India: proxy01.iind.intel.com:911 ^|
echo ^|  American: proxy-us.intel.com:911  ^|
echo ^|  Common: proxy-chain.intel.com:911 ^|
echo --------------------------------------

echo press "Enter" to use default proxy
set /p ver="input proxy:"
if %ver%=="" (set ver=child-prc.intel.com:913)

pip install frameworks.automation.dtaf.core-production.zip --proxy %ver%
pip install prettytable --proxy %ver%
