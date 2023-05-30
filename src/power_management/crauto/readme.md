### All CRAutomation ISS and Non ISS Test Cases
Pre-requisites:
	pre-installed RHEL/CentOS
	 try below commands in SUT
	/usr/bin/mkdir -p /mnt/apps_source 
	/usr/bin/mount -t cifs -o username=sys_crse,password=Intel@1234Intel@1234,ro,cache=none -v //Vmspfsfsbg06.gar.corp.intel.com/SPR_Share/apps /mnt/apps_source && echo "Mount Successful!" echo "Syncing all apps to Target/DUT local storage"
	then copy required folders (Ex: PM,mlc)

	1  DPC memory configuration(Ex: 8+0,16+0)
	get latest Modules from PythonSV and update tools(Sapphire rapids, Crowvalley, Emmitsburg,Components)
	get latest pmutils and install in SUT( /root/apps/PM/pmutils-master)
	get latest PTU tool and install Manually (root/apps/ptu)
		--(Try running PTU manually, if it works fine please proceed with next step)
		
	Configure BMC
	
Update the Platform Configuration sheet "C:\PythonSV\crowvalley\crautomation\configs\Platform_Configs_OTHER.xlsx"
Update the configuration file "C:\PythonSV\crowvalley\crautomation\release\conf\defaults-other.cfg"
Update the System_configuration file "C:\PythonSV\sapphirerapids\users\cr_tools\release\xpiv_iss\lib\system_configuration.ini"

Now run the test cases.	
##########################################################################################
#######   For Test Case:      PI_Powermanagement_PECI_L   ################################
##########################################################################################
Update the peci_config.ini file with OS ip, OS credential and BMC ip, BMC console credential.
Path: C:\PythonSV\sapphirerapids\users\cr_tools\release\peci

Now run the Test case.


		
	
	
	
	
