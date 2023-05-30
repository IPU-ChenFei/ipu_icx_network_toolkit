# AUTO INSTALLER APP – BKM

<span style="color: red;">***Note: Generate system configuration file and then go to setups one after another, follow the steps below!!!***</span>

1. Download the latest kit from the below artifactory path to any directory on your NUC,
2. <https://ubit-artifactory-ba.intel.com/artifactory/dcg-dea-srvplat-local/Automation_Tools/SPR/Auto_Installer_Kit> Unzip it and you will see a folder like this,

![](Images/document.002.png)

3. Inside the “auto\_installer\_vxxx” directory, you will see an .exe file with the same name as shown below,

![](Images/document.003.png)

4. Just double click it, it will open a GUI along with a console, like below,

![](Images/document.004.png)

5. First generate a system configuration either by clicking “<mark>Generate 2S/4S System Configuration</mark>” or “<mark>Generate 8S System Configuration</mark>”, after clicking, you will see the screen below,

![](Images/document.005.png)

6. Fill out the form as per your system information and click submit.
   1. <span style="color: red;">Note - > all the fields are mandatory.</span>

![](Images/document.006.png)

7. If any field(s) are missing, you will see a pop up like below, like OK and continue to fill out all the fields appropriately. 

![](Images/document.007.png)

8. Once all the fields are entered, you can Submit the form, then you will see a pop up to show the form submitted successfully.

![](Images/document.008.png)

9. Once the form is submitted, the system configuration file will be generated in the <mark>**C:\Automation**</mark> folder.
10. The system configuration form will disappear, and you will see the main window to start the “Python Installation” followed by “GIT Bash installation” then we should proceed with “NUC Setup”.
11. Once “NUC Setup” Button clicked, the main window will disappear as well and the NUC provisioning will start in the background, <span style="color: red;">**do not close the console**</span>. It will be auto closed once the installation is done.
12. You can see the progress in the console which will be running along with the installation, find the random snap of the console screen,

![](Images/document.009.png)

13. You can also see the progress in the log file located in the “<mark>**C:\Auto\_Installer\_logs**</mark>”, the naming will be “<hostname>\_auto\_installer\_%YYYY\_%MM\_%DD\_%HH\_%MM\_%SS\_%P (AM or PM)”

![](Images/document.010.png)

14. What the log file has, here is the sneak peak of the same.

```
*03/22/2022 01:50:29 AM,435 INFO     [auto\_installer\_app.py:328]  C:\tools directory exists.. deleting*

*03/22/2022 01:50:29 AM,435 INFO     [auto\_installer\_app.py:330]  C:\tools directory has been deleted.. creating new one..*

*03/22/2022 01:52:40 AM,569 INFO     [auto\_installer\_app.py:452] {'platform\_type': 'Reference'}*

*03/22/2022 01:52:40 AM,569 INFO     [auto\_installer\_app.py:452] {'platform\_type': 'Reference', 'board\_name': 'ArcherCity'}*

*03/22/2022 01:52:40 AM,569 INFO     [auto\_installer\_app.py:452] {'platform\_type': 'Reference', 'board\_name': 'ArcherCity', 'platform\_name': 'SappahireRapids'}*

*03/22/2022 01:52:40 AM,569 INFO     [auto\_installer\_app.py:452] {'platform\_type': 'Reference', 'board\_name': 'ArcherCity', 'platform\_name': 'SappahireRapids', 'cpu\_family': 'SPR'}*

*03/22/2022 01:52:40 AM,569 INFO     [auto\_installer\_app.py:452] {'platform\_type': 'Reference', 'board\_name': 'ArcherCity', 'platform\_name': 'SappahireRapids', 'cpu\_family': 'SPR', 'cpu\_stepping': 'D0'}*

*03/22/2022 01:52:40 AM,569 INFO     [auto\_installer\_app.py:452] {'platform\_type': 'Reference', 'board\_name': 'ArcherCity', 'platform\_name': 'SappahireRapids', 'cpu\_family': 'SPR', 'cpu\_stepping': 'D0', 'pch\_family': 'EBG'}*

*03/22/2022 01:52:40 AM,569 INFO     [auto\_installer\_app.py:452] {'platform\_type': 'Reference', 'board\_name': 'ArcherCity', 'platform\_name': 'SappahireRapids', 'cpu\_family': 'SPR', 'cpu\_stepping': 'D0', 'pch\_family': 'EBG', 'sut\_os\_kernel': '5.15'}*

*03/22/2022 01:52:40 AM,569 INFO     [auto\_installer\_app.py:452] {'platform\_type': 'Reference', 'board\_name': 'ArcherCity', 'platform\_name': 'SappahireRapids', 'cpu\_family': 'SPR', 'cpu\_stepping': 'D0', 'pch\_family': 'EBG', 'sut\_os\_kernel': '5.15', 'sut\_os\_name': 'centos'}*

*03/22/2022 01:52:40 AM,569 INFO     [auto\_installer\_app.py:452] {'platform\_type': 'Reference', 'board\_name': 'ArcherCity', 'platform\_name': 'SappahireRapids', 'cpu\_family': 'SPR', 'cpu\_stepping': 'D0', 'pch\_family': 'EBG', 'sut\_os\_kernel': '5.15', 'sut\_os\_name': 'centos', 'sut\_os\_version': '8'}*

*03/22/2022 01:52:40 AM,569 INFO     [auto\_installer\_app.py:452] {'platform\_type': 'Reference', 'board\_name': 'ArcherCity', 'platform\_name': 'SappahireRapids', 'cpu\_family': 'SPR', 'cpu\_stepping': 'D0', 'pch\_family': 'EBG', 'sut\_os\_kernel': '5.15', 'sut\_os\_name': 'centos', 'sut\_os\_version': '8', 'proxy\_link': 'http://proxy01.iind.intel.com:912'}*

*03/22/2022 01:52:40 AM,584 INFO     [auto\_installer\_app.py:452] {'platform\_type': 'Reference', 'board\_name': 'ArcherCity', 'platform\_name': 'SappahireRapids', 'cpu\_family': 'SPR', 'cpu\_stepping': 'D0', 'pch\_family': 'EBG', 'sut\_os\_kernel': '5.15', 'sut\_os\_name': 'centos', 'sut\_os\_version': '8', 'proxy\_link': 'http://proxy01.iind.intel.com:912', 'git\_hub\_username': 'raj-navee'}*

*03/22/2022 01:52:40 AM,584 INFO     [auto\_installer\_app.py:452] {'platform\_type': 'Reference', 'board\_name': 'ArcherCity', 'platform\_name': 'SappahireRapids', 'cpu\_family': 'SPR', 'cpu\_stepping': 'D0', 'pch\_family': 'EBG', 'sut\_os\_kernel': '5.15', 'sut\_os\_name': 'centos', 'sut\_os\_version': '8', 'proxy\_link': 'http://proxy01.iind.intel.com:912', 'git\_hub\_username': 'raj-navee', 'git\_hub\_personal\_token': 'ghp\_YT9PllTVoMjQVPgV6j57rXC2pJgli94On2xq'}*

*03/22/2022 01:52:40 AM,584 INFO     [auto\_installer\_app.py:452] {'platform\_type': 'Reference', 'board\_name': 'ArcherCity', 'platform\_name': 'SappahireRapids', 'cpu\_family': 'SPR', 'cpu\_stepping': 'D0', 'pch\_family': 'EBG', 'sut\_os\_kernel': '5.15', 'sut\_os\_name': 'centos', 'sut\_os\_version': '8', 'proxy\_link': 'http://proxy01.iind.intel.com:912', 'git\_hub\_username': 'raj-navee', 'git\_hub\_personal\_token': 'ghp\_YT9PllTVoMjQVPgV6j57rXC2pJgli94On2xq', 'sut\_ip\_address': '10.45.131.232'}*

*03/22/2022 01:52:40 AM,584 INFO     [auto\_installer\_app.py:452] {'platform\_type': 'Reference', 'board\_name': 'ArcherCity', 'platform\_name': 'SappahireRapids', 'cpu\_family': 'SPR', 'cpu\_stepping': 'D0', 'pch\_family': 'EBG', 'sut\_os\_kernel': '5.15', 'sut\_os\_name': 'centos', 'sut\_os\_version': '8', 'proxy\_link': 'http://proxy01.iind.intel.com:912', 'git\_hub\_username': 'raj-navee', 'git\_hub\_personal\_token': 'ghp\_YT9PllTVoMjQVPgV6j57rXC2pJgli94On2xq', 'sut\_ip\_address': '10.45.131.232', 'sut\_login\_username': 'root'}*

*03/22/2022 01:52:40 AM,584 INFO     [auto\_installer\_app.py:452] {'platform\_type': 'Reference', 'board\_name': 'ArcherCity', 'platform\_name': 'SappahireRapids', 'cpu\_family': 'SPR', 'cpu\_stepping': 'D0', 'pch\_family': 'EBG', 'sut\_os\_kernel': '5.15', 'sut\_os\_name': 'centos', 'sut\_os\_version': '8', 'proxy\_link': 'http://proxy01.iind.intel.com:912', 'git\_hub\_username': 'raj-navee', 'git\_hub\_personal\_token': 'ghp\_YT9PllTVoMjQVPgV6j57rXC2pJgli94On2xq', 'sut\_ip\_address': '10.45.131.232', 'sut\_login\_username': 'root', 'sut\_login\_password': 'Password123!23'}*

*03/22/2022 01:52:40 AM,584 INFO     [auto\_installer\_app.py:452] {'platform\_type': 'Reference', 'board\_name': 'ArcherCity', 'platform\_name': 'SappahireRapids', 'cpu\_family': 'SPR', 'cpu\_stepping': 'D0', 'pch\_family': 'EBG', 'sut\_os\_kernel': '5.15', 'sut\_os\_name': 'centos', 'sut\_os\_version': '8', 'proxy\_link': 'http://proxy01.iind.intel.com:912', 'git\_hub\_username': 'raj-navee', 'git\_hub\_personal\_token': 'ghp\_YT9PllTVoMjQVPgV6j57rXC2pJgli94On2xq', 'sut\_ip\_address': '10.45.131.232', 'sut\_login\_username': 'root', 'sut\_login\_password': 'Password123!23', 'bmc\_ip\_address': '10.45.131.239'}*

*03/22/2022 01:52:40 AM,584 INFO     [auto\_installer\_app.py:452] {'platform\_type': 'Reference', 'board\_name': 'ArcherCity', 'platform\_name': 'SappahireRapids', 'cpu\_family': 'SPR', 'cpu\_stepping': 'D0', 'pch\_family': 'EBG', 'sut\_os\_kernel': '5.15', 'sut\_os\_name': 'centos', 'sut\_os\_version': '8', 'proxy\_link': 'http://proxy01.iind.intel.com:912', 'git\_hub\_username': 'raj-navee', 'git\_hub\_personal\_token': 'ghp\_YT9PllTVoMjQVPgV6j57rXC2pJgli94On2xq', 'sut\_ip\_address': '10.45.131.232', 'sut\_login\_username': 'root', 'sut\_login\_password': 'Password123!23', 'bmc\_ip\_address': '10.45.131.239', 'bios\_com\_port\_number': 'com52'}*

*03/22/2022 01:52:40 AM,584 INFO     [auto\_installer\_app.py:452] {'platform\_type': 'Reference', 'board\_name': 'ArcherCity', 'platform\_name': 'SappahireRapids', 'cpu\_family': 'SPR', 'cpu\_stepping': 'D0', 'pch\_family': 'EBG', 'sut\_os\_kernel': '5.15', 'sut\_os\_name': 'centos', 'sut\_os\_version': '8', 'proxy\_link': 'http://proxy01.iind.intel.com:912', 'git\_hub\_username': 'raj-navee', 'git\_hub\_personal\_token': 'ghp\_YT9PllTVoMjQVPgV6j57rXC2pJgli94On2xq', 'sut\_ip\_address': '10.45.131.232', 'sut\_login\_username': 'root', 'sut\_login\_password': 'Password123!23', 'bmc\_ip\_address': '10.45.131.239', 'bios\_com\_port\_number': 'com52', 'bmc\_com\_port\_number': 'com53'}*

*03/22/2022 01:52:40 AM,584 INFO     [auto\_installer\_app.py:452] {'platform\_type': 'Reference', 'board\_name': 'ArcherCity', 'platform\_name': 'SappahireRapids', 'cpu\_family': 'SPR', 'cpu\_stepping': 'D0', 'pch\_family': 'EBG', 'sut\_os\_kernel': '5.15', 'sut\_os\_name': 'centos', 'sut\_os\_version': '8', 'proxy\_link': 'http://proxy01.iind.intel.com:912', 'git\_hub\_username': 'raj-navee', 'git\_hub\_personal\_token': 'ghp\_YT9PllTVoMjQVPgV6j57rXC2pJgli94On2xq', 'sut\_ip\_address': '10.45.131.232', 'sut\_login\_username': 'root', 'sut\_login\_password': 'Password123!23', 'bmc\_ip\_address': '10.45.131.239', 'bios\_com\_port\_number': 'com52', 'bmc\_com\_port\_number': 'com53', 'ladybird\_driver\_serial\_number': '271650049'}*

*03/22/2022 01:52:40 AM,584 INFO     [auto\_installer\_app.py:452] {'platform\_type': 'Reference', 'board\_name': 'ArcherCity', 'platform\_name': 'SappahireRapids', 'cpu\_family': 'SPR', 'cpu\_stepping': 'D0', 'pch\_family': 'EBG', 'sut\_os\_kernel': '5.15', 'sut\_os\_name': 'centos', 'sut\_os\_version': '8', 'proxy\_link': 'http://proxy01.iind.intel.com:912', 'git\_hub\_username': 'raj-navee', 'git\_hub\_personal\_token': 'ghp\_YT9PllTVoMjQVPgV6j57rXC2pJgli94On2xq', 'sut\_ip\_address': '10.45.131.232', 'sut\_login\_username': 'root', 'sut\_login\_password': 'Password123!23', 'bmc\_ip\_address': '10.45.131.239', 'bios\_com\_port\_number': 'com52', 'bmc\_com\_port\_number': 'com53', 'ladybird\_driver\_serial\_number': '271650049', 'is\_this\_rasp\_system': 'true'}*

*03/22/2022 01:52:40 AM,584 INFO     [auto\_installer\_app.py:452] {'platform\_type': 'Reference', 'board\_name': 'ArcherCity', 'platform\_name': 'SappahireRapids', 'cpu\_family': 'SPR', 'cpu\_stepping': 'D0', 'pch\_family': 'EBG', 'sut\_os\_kernel': '5.15', 'sut\_os\_name': 'centos', 'sut\_os\_version': '8', 'proxy\_link': 'http://proxy01.iind.intel.com:912', 'git\_hub\_username': 'raj-navee', 'git\_hub\_personal\_token': 'ghp\_YT9PllTVoMjQVPgV6j57rXC2pJgli94On2xq', 'sut\_ip\_address': '10.45.131.232', 'sut\_login\_username': 'root', 'sut\_login\_password': 'Password123!23', 'bmc\_ip\_address': '10.45.131.239', 'bios\_com\_port\_number': 'com52', 'bmc\_com\_port\_number': 'com53', 'ladybird\_driver\_serial\_number': '271650049', 'is\_this\_rasp\_system': 'true', 'raritan\_pdu\_ip\_address\_or\_name': '10.45.252.58'}*

*03/22/2022 01:52:40 AM,584 INFO     [auto\_installer\_app.py:452] {'platform\_type': 'Reference', 'board\_name': 'ArcherCity', 'platform\_name': 'SappahireRapids', 'cpu\_family': 'SPR', 'cpu\_stepping': 'D0', 'pch\_family': 'EBG', 'sut\_os\_kernel': '5.15', 'sut\_os\_name': 'centos', 'sut\_os\_version': '8', 'proxy\_link': 'http://proxy01.iind.intel.com:912', 'git\_hub\_username': 'raj-navee', 'git\_hub\_personal\_token': 'ghp\_YT9PllTVoMjQVPgV6j57rXC2pJgli94On2xq', 'sut\_ip\_address': '10.45.131.232', 'sut\_login\_username': 'root', 'sut\_login\_password': 'Password123!23', 'bmc\_ip\_address': '10.45.131.239', 'bios\_com\_port\_number': 'com52', 'bmc\_com\_port\_number': 'com53', 'ladybird\_driver\_serial\_number': '271650049', 'is\_this\_rasp\_system': 'true', 'raritan\_pdu\_ip\_address\_or\_name': '10.45.252.58', 'raritan\_pdu\_username': 'EMR-PVST'}*

*03/22/2022 01:52:40 AM,584 INFO     [auto\_installer\_app.py:452] {'platform\_type': 'Reference', 'board\_name': 'ArcherCity', 'platform\_name': 'SappahireRapids', 'cpu\_family': 'SPR', 'cpu\_stepping': 'D0', 'pch\_family': 'EBG', 'sut\_os\_kernel': '5.15', 'sut\_os\_name': 'centos', 'sut\_os\_version': '8', 'proxy\_link': 'http://proxy01.iind.intel.com:912', 'git\_hub\_username': 'raj-navee', 'git\_hub\_personal\_token': 'ghp\_YT9PllTVoMjQVPgV6j57rXC2pJgli94On2xq', 'sut\_ip\_address': '10.45.131.232', 'sut\_login\_username': 'root', 'sut\_login\_password': 'Password123!23', 'bmc\_ip\_address': '10.45.131.239', 'bios\_com\_port\_number': 'com52', 'bmc\_com\_port\_number': 'com53', 'ladybird\_driver\_serial\_number': '271650049', 'is\_this\_rasp\_system': 'true', 'raritan\_pdu\_ip\_address\_or\_name': '10.45.252.58', 'raritan\_pdu\_username': 'EMR-PVST', 'raritan\_pdu\_password': 'P@ssword1234!234'}*

*03/22/2022 01:52:40 AM,584 INFO     [auto\_installer\_app.py:452] {'platform\_type': 'Reference', 'board\_name': 'ArcherCity', 'platform\_name': 'SappahireRapids', 'cpu\_family': 'SPR', 'cpu\_stepping': 'D0', 'pch\_family': 'EBG', 'sut\_os\_kernel': '5.15', 'sut\_os\_name': 'centos', 'sut\_os\_version': '8', 'proxy\_link': 'http://proxy01.iind.intel.com:912', 'git\_hub\_username': 'raj-navee', 'git\_hub\_personal\_token': 'ghp\_YT9PllTVoMjQVPgV6j57rXC2pJgli94On2xq', 'sut\_ip\_address': '10.45.131.232', 'sut\_login\_username': 'root', 'sut\_login\_password': 'Password123!23', 'bmc\_ip\_address': '10.45.131.239', 'bios\_com\_port\_number': 'com52', 'bmc\_com\_port\_number': 'com53', 'ladybird\_driver\_serial\_number': '271650049', 'is\_this\_rasp\_system': 'true', 'raritan\_pdu\_ip\_address\_or\_name': '10.45.252.58', 'raritan\_pdu\_username': 'EMR-PVST', 'raritan\_pdu\_password': 'P@ssword1234!234', 'raritan\_pdu\_first\_outlet': '1'}*

*03/22/2022 01:52:40 AM,584 INFO     [auto\_installer\_app.py:452] {'platform\_type': 'Reference', 'board\_name': 'ArcherCity', 'platform\_name': 'SappahireRapids', 'cpu\_family': 'SPR', 'cpu\_stepping': 'D0', 'pch\_family': 'EBG', 'sut\_os\_kernel': '5.15', 'sut\_os\_name': 'centos', 'sut\_os\_version': '8', 'proxy\_link': 'http://proxy01.iind.intel.com:912', 'git\_hub\_username': 'raj-navee', 'git\_hub\_personal\_token': 'ghp\_YT9PllTVoMjQVPgV6j57rXC2pJgli94On2xq', 'sut\_ip\_address': '10.45.131.232', 'sut\_login\_username': 'root', 'sut\_login\_password': 'Password123!23', 'bmc\_ip\_address': '10.45.131.239', 'bios\_com\_port\_number': 'com52', 'bmc\_com\_port\_number': 'com53', 'ladybird\_driver\_serial\_number': '271650049', 'is\_this\_rasp\_system': 'true', 'raritan\_pdu\_ip\_address\_or\_name': '10.45.252.58', 'raritan\_pdu\_username': 'EMR-PVST', 'raritan\_pdu\_password': 'P@ssword1234!234', 'raritan\_pdu\_first\_outlet': '1', 'raritan\_pdu\_second\_outlet': 'na'}*

*03/22/2022 01:52:40 AM,584 INFO     [auto\_installer\_app.py:452] {'platform\_type': 'Reference', 'board\_name': 'ArcherCity', 'platform\_name': 'SappahireRapids', 'cpu\_family': 'SPR', 'cpu\_stepping': 'D0', 'pch\_family': 'EBG', 'sut\_os\_kernel': '5.15', 'sut\_os\_name': 'centos', 'sut\_os\_version': '8', 'proxy\_link': 'http://proxy01.iind.intel.com:912', 'git\_hub\_username': 'raj-navee', 'git\_hub\_personal\_token': 'ghp\_YT9PllTVoMjQVPgV6j57rXC2pJgli94On2xq', 'sut\_ip\_address': '10.45.131.232', 'sut\_login\_username': 'root', 'sut\_login\_password': 'Password123!23', 'bmc\_ip\_address': '10.45.131.239', 'bios\_com\_port\_number': 'com52', 'bmc\_com\_port\_number': 'com53', 'ladybird\_driver\_serial\_number': '271650049', 'is\_this\_rasp\_system': 'true', 'raritan\_pdu\_ip\_address\_or\_name': '10.45.252.58', 'raritan\_pdu\_username': 'EMR-PVST', 'raritan\_pdu\_password': 'P@ssword1234!234', 'raritan\_pdu\_first\_outlet': '1', 'raritan\_pdu\_second\_outlet': 'na', 'quartus\_application\_exe\_path': 'caa'}*

*03/22/2022 01:52:44 AM,368 INFO     [auto\_installer\_app.py:2427] Python Version Check has started...*

*03/22/2022 01:52:44 AM,555 INFO     [auto\_installer\_app.py:2431] Python 3 is installed . Version that is installed is b'Python 3.6.8\r\n':* 

*03/22/2022 01:52:58 AM,157 INFO     [auto\_installer\_app.py:1322] ['Python 3.6.8 Development Libraries (64-bit)', 'Python 3.6.8 Executables (64-bit symbols)', 'Python 3.6.8 Tcl/Tk Support (64-bit)', 'Python 3.6.8 pip Bootstrap (64-bit)', 'Python 3.6.8 Executables (64-bit)', 'Python 3.6.8 Core Interpreter (64-bit)', 'Python 3.6.8 Tcl/Tk Support (64-bit symbols)', 'Python 3.6.8 Utility Scripts (64-bit)', 'Python 3.6.8 Standard Library (64-bit)', 'Python 3.6.8 Core Interpreter (64-bit symbols)', 'Python 3.6.8 Documentation (64-bit)', 'Python 3.6.8 Standard Library (64-bit symbols)']*

*03/22/2022 01:52:58 AM,157 INFO     [auto\_installer\_app.py:1326] Command executed successfully to fetch the python installation suite..*

*03/22/2022 01:53:10 AM,492 INFO     [auto\_installer\_app.py:1342] Executing (\\E00807FL30SE001\ROOT\CIMV2:Win32\_Product.IdentifyingNumber="{A43B98B0-5A92-4EBA-929D-FE0A840CD97A}",Name="Python 3.6.8 Development Libraries (64-bit)",Vendor="Python Software Foundation",Version="3.6.8150.0")->Uninstall()*

*Method execution successful.*

*Out Parameters:*

*instance of \_\_PARAMETERS*

*{*

`	`*ReturnValue = 0;*

*};*

*03/22/2022 01:53:10 AM,492 INFO     [auto\_installer\_app.py:1343] Command executed successfully to uninstall : Python 3.6.8 Development Libraries (64-bit)*

*03/22/2022 01:53:22 AM,295 INFO     [auto\_installer\_app.py:1342] Executing (\\E00807FL30SE001\ROOT\CIMV2:Win32\_Product.IdentifyingNumber="{549F47E0-165E-4FE7-BF1F-BFAA3CCDE062}",Name="Python 3.6.8 Executables (64-bit symbols)",Vendor="Python Software Foundation",Version="3.6.8150.0")->Uninstall()*

*Method execution successful.*

*Out Parameters:*

*instance of \_\_PARAMETERS*

*{*

`	`*ReturnValue = 0;*

*};*

*03/22/2022 01:53:22 AM,295 INFO     [auto\_installer\_app.py:1343] Command executed successfully to uninstall : Python 3.6.8 Executables (64-bit symbols)*

*03/22/2022 01:53:46 AM,154 INFO     [auto\_installer\_app.py:1342] Executing (\\E00807FL30SE001\ROOT\CIMV2:Win32\_Product.IdentifyingNumber="{EBD78311-1837-4432-94EE-5A5E5E206888}",Name="Python 3.6.8 Tcl/Tk Support (64-bit)",Vendor="Python Software Foundation",Version="3.6.8150.0")->Uninstall()*

*Method execution successful.*

*Out Parameters:*

*instance of \_\_PARAMETERS*

*{*

`	`*ReturnValue = 0;*

*};*

*03/22/2022 01:53:46 AM,154 INFO     [auto\_installer\_app.py:1343] Command executed successfully to uninstall : Python 3.6.8 Tcl/Tk Support (64-bit)*

*03/22/2022 01:53:58 AM,545 INFO     [auto\_installer\_app.py:1342] Executing (\\E00807FL30SE001\ROOT\CIMV2:Win32\_Product.IdentifyingNumber="{C48DD541-2669-499A-B7AB-EC0504307601}",Name="Python 3.6.8 pip Bootstrap (64-bit)",Vendor="Python Software Foundation",Version="3.6.8150.0")->Uninstall()*

*Method execution successful.*

*Out Parameters:*

*instance of \_\_PARAMETERS*

*{*

`	`*ReturnValue = 0;*

*};*

*03/22/2022 01:53:58 AM,545 INFO     [auto\_installer\_app.py:1343] Command executed successfully to uninstall : Python 3.6.8 pip Bootstrap (64-bit)*

*03/22/2022 01:54:10 AM,215 INFO     [auto\_installer\_app.py:1342] Executing (\\E00807FL30SE001\ROOT\CIMV2:Win32\_Product.IdentifyingNumber="{E1155302-B578-4D8C-8431-FAE677FBC58C}",Name="Python 3.6.8 Executables (64-bit)",Vendor="Python Software Foundation",Version="3.6.8150.0")->Uninstall()*

*Method execution successful.*

*Out Parameters:*

*instance of \_\_PARAMETERS*

*{*

`	`*ReturnValue = 0;*

*};*

*03/22/2022 01:54:10 AM,215 INFO     [auto\_installer\_app.py:1343] Command executed successfully to uninstall : Python 3.6.8 Executables (64-bit)*

*03/22/2022 01:54:21 AM,816 INFO     [auto\_installer\_app.py:1342] Executing (\\E00807FL30SE001\ROOT\CIMV2:Win32\_Product.IdentifyingNumber="{290348F2-D9D3-470E-9858-22F0F74E3623}",Name="Python 3.6.8 Core Interpreter (64-bit)",Vendor="Python Software Foundation",Version="3.6.8150.0")->Uninstall()*

*Method execution successful.*

*Out Parameters:*

*instance of \_\_PARAMETERS*

*{*

`	`*ReturnValue = 0;*

*};*

*03/22/2022 01:54:21 AM,816 INFO     [auto\_installer\_app.py:1343] Command executed successfully to uninstall : Python 3.6.8 Core Interpreter (64-bit)*

*03/22/2022 01:54:33 AM,376 INFO     [auto\_installer\_app.py:1342] Executing (\\E00807FL30SE001\ROOT\CIMV2:Win32\_Product.IdentifyingNumber="{C2004103-BC19-4296-972D-CC2217B3A8AF}",Name="Python 3.6.8 Tcl/Tk Support (64-bit symbols)",Vendor="Python Software Foundation",Version="3.6.8150.0")->Uninstall()*

*Method execution successful.*

*Out Parameters:*

*instance of \_\_PARAMETERS*

*{*

`	`*ReturnValue = 0;*

*};*

*03/22/2022 01:54:33 AM,376 INFO     [auto\_installer\_app.py:1343] Command executed successfully to uninstall : Python 3.6.8 Tcl/Tk Support (64-bit symbols)*

*03/22/2022 01:54:45 AM,717 INFO     [auto\_installer\_app.py:1342] Executing (\\E00807FL30SE001\ROOT\CIMV2:Win32\_Product.IdentifyingNumber="{1F5F06E6-A6C0-482E-8FEB-681DE2059228}",Name="Python 3.6.8 Utility Scripts (64-bit)",Vendor="Python Software Foundation",Version="3.6.8150.0")->Uninstall()*

*Method execution successful.*

*Out Parameters:*

*instance of \_\_PARAMETERS*

*{*

`	`*ReturnValue = 0;*

*};*

*03/22/2022 01:54:45 AM,732 INFO     [auto\_installer\_app.py:1343] Command executed successfully to uninstall : Python 3.6.8 Utility Scripts (64-bit)*

*03/22/2022 01:55:12 AM,820 INFO     [auto\_installer\_app.py:1342] Executing (\\E00807FL30SE001\ROOT\CIMV2:Win32\_Product.IdentifyingNumber="{4BFF1147-97F2-432E-AD26-2224B609957C}",Name="Python 3.6.8 Standard Library (64-bit)",Vendor="Python Software Foundation",Version="3.6.8150.0")->Uninstall()*

*Method execution successful.*

*Out Parameters:*

*instance of \_\_PARAMETERS*

*{*

`	`*ReturnValue = 0;*

*};*

*03/22/2022 01:55:12 AM,820 INFO     [auto\_installer\_app.py:1343] Command executed successfully to uninstall : Python 3.6.8 Standard Library (64-bit)*

*03/22/2022 01:55:24 AM,176 INFO     [auto\_installer\_app.py:1342] Executing (\\E00807FL30SE001\ROOT\CIMV2:Win32\_Product.IdentifyingNumber="{EB5B19E8-6325-44BA-9F49-AC78EC7AF8FB}",Name="Python 3.6.8 Core Interpreter (64-bit symbols)",Vendor="Python Software Foundation",Version="3.6.8150.0")->Uninstall()*

*Method execution successful.*

*Out Parameters:*

*instance of \_\_PARAMETERS*

*{*

`	`*ReturnValue = 0;*

*};*

*03/22/2022 01:55:24 AM,176 INFO     [auto\_installer\_app.py:1343] Command executed successfully to uninstall : Python 3.6.8 Core Interpreter (64-bit symbols)*

*03/22/2022 01:55:35 AM,627 INFO     [auto\_installer\_app.py:1342] Executing (\\E00807FL30SE001\ROOT\CIMV2:Win32\_Product.IdentifyingNumber="{73EE519A-D901-4844-8E8F-C635705A2414}",Name="Python 3.6.8 Documentation (64-bit)",Vendor="Python Software Foundation",Version="3.6.8150.0")->Uninstall()*

*Method execution successful.*

*Out Parameters:*

*instance of \_\_PARAMETERS*

*{*

`	`*ReturnValue = 0;*

*};*

*03/22/2022 01:55:35 AM,627 INFO     [auto\_installer\_app.py:1343] Command executed successfully to uninstall : Python 3.6.8 Documentation (64-bit)*

*03/22/2022 01:55:47 AM,235 INFO     [auto\_installer\_app.py:1342] Executing (\\E00807FL30SE001\ROOT\CIMV2:Win32\_Product.IdentifyingNumber="{A0D6BD8E-8573-4A52-A087-37D8016BF512}",Name="Python 3.6.8 Standard Library (64-bit symbols)",Vendor="Python Software Foundation",Version="3.6.8150.0")->Uninstall()*

*Method execution successful.*

*Out Parameters:*

*instance of \_\_PARAMETERS*

*{*

`	`*ReturnValue = 0;*

*};*

*03/22/2022 01:55:47 AM,235 INFO     [auto\_installer\_app.py:1343] Command executed successfully to uninstall : Python 3.6.8 Standard Library (64-bit symbols)*

*03/22/2022 01:55:47 AM,704 INFO     [auto\_installer\_app.py:1367] D0 stepping has been selected.*

*03/22/2022 01:55:47 AM,704 INFO     [auto\_installer\_app.py:1368] Proceeding with fresh python-3.6.8-amd64.exe installation..*

*03/22/2022 01:55:47 AM,720 INFO     [auto\_installer\_app.py:1369] Downloading python-3.6.8-amd64.exe ..*

*03/22/2022 01:55:53 AM,468 INFO     [auto\_installer\_app.py:1374] python-3.6.8-amd64.exe successfully downloaded from artifactory..*

*03/22/2022 01:55:53 AM,468 INFO     [auto\_installer\_app.py:1385] python-3.6.8-amd64.exe installation has started..*

*03/22/2022 01:56:25 AM,23 INFO     [auto\_installer\_app.py:1389] 0*

*03/22/2022 01:56:25 AM,23 INFO     [auto\_installer\_app.py:1394] python-3.6.8-amd64.exe installed successfully*

**This document was truncated here because it was created in the Evaluation Mode.**
**Created with an evaluation copy of Aspose.Words. To discover the full versions of our APIs please visit: https://products.aspose.com/words/**
```