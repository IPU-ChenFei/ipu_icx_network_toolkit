For the Test case : 1308855057 SATASSD- FW upgrade check in AHCI Mode
1) Need to connect the SUT with 8 SATA SSDs and one M.2 in pch slot.

2) Download the intelmastool from below website and keep it under C:\Automation\BKC\Tools folder in the host.
website address : https://www.intel.com/content/www/us/en/download/19520/intel-memory-and-storage-tool-cli-command-line-interface.html

3) We need to update the content_configuration.xml with below details.
<intelmastool_path>C:\Automation\BKC\Tools\Intel_MAS_CLI_Tool_Linux_1.12.zip</intelmastool_path>


