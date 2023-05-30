FOR SGX SETUP PLEASE DO BELOW CONFIGURATION IN SYSTEM
-----------------------------------------------------
Hardware : 
DIMM : 1 DDR5 DIMMs for each socket @IMC0/CH0/S0
S7E2--ON, ON
S7E1-OFF, OFF
S3F1--OFF, ON
S3F2--ON, ON 

Jumper  J5D4 is closed [kept in 1-2] 
J5E1 [It should be open [position -1]
J5B1 to 2-3 position to enable LT_Downgrade

Please install latest OS from BKC through win imager to get the SGX pacakge


FOR TC ID - H81540 - PI_SGX_TEM_BasicTest_W
----------------------------------------------------
Please do above mentioned configuration and run this TC on windows machine.

For SGX TCs please download the SGX driver pkg and SGXFVT_tool from the BKC mail and copy it under
the below path C:\Automation\Tools\SPR\Linux\ on HOST.
In the content_configuration.xml please update the complete path with the package names
under this tag of PSW_ZIP and SGX_FVT_ZIP.
For more info follow the screenshot under the path readme_support_docs/SGX_Config_edit.JPG
