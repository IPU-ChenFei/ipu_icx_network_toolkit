<h1>E2E Provisioning One Liner</h1>

<h2>Modes:</h2>
The modes are applicable for both offline and online OS installation methods.

1. Auto (by Default)
   
2. Manual

<h3>Auto:</h3>
The user will just run the Testcase script and it will take care of everything for you.

For your information, in this auto mode, the script will choose the **first** <mark>ssd/hdd/nvme </mark> as per the boot order list that was already set on the BIOS. 

<h3>Manual:</h3>
The user will create a folder under C: drive called <mark>Inventory </mark> under that create a config file name <mark>sut_inventory.cfg </mark> and should add the following things.

<h4>Creation of sut_inventory.cfg:</h4>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;User should add all the SSD/HDD/NVME names that are connected on the system the .cfg file mandatory, then the user should trigger the script for OS installation.

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;For your information, you can add ssd or hdd or nvme device names against the option name "yyyy_ssd_name_xxxx", the <mark>yyyy</mark> should be replaced with "sata" or "nvme" based on the device connected and 
the <mark>xxxx</mark> should be anyone of the OS name, which is mentioned in the below example as we are fetching it based on the os name string, if the drive does not have any OS, please provide the option name as <mark>ssd_name_blank</mark>.

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; In case if you have same OS installed on different SSDs or more number of empty SSDs, please append "_1" at the 
end of the naming, below is the example that illustrates the same.

**_<h1>***Please make sure the naming conventions are same as below***</h1>_**

<mark>[sut_information] </mark>

<mark>mode = manual </mark>

<mark>usb_name_1 = xxxxxxxxxx </mark> (eg : UEFI hp x303w BC2B109BB177819C19)

<mark>usb_size = xx  </mark>(eg : 32)

<mark>sata_ssd_name_rhel = xxxxxxxxx </mark> (eg: UEFI KINGSTON SA400S37240G 50026B738073D860)

<mark>nvme_ssd_name_rhel_1 = xxxxxxxxx </mark> (eg: UEFI KINGSTON SA400S37240G 50026B738073D860)

<mark>sata_ssd_name_windows = xxxxxxxxx </mark>(eg: UEFI KINGSTON SA400S37240G 50026B738073D744)

<mark>nvme_ssd_name_windows_1 = xxxxxxxxx </mark>(eg: UEFI KINGSTON SA400S37240G 50026B738073D744)

<mark>sata_ssd_name_centos = xxxxxxxxx  </mark>(eg: UEFI KINGSTON SA400S37240G 50026B738073D789)

<mark>nvme_ssd_name_centos_1 = xxxxxxxxx  </mark>(eg: UEFI KINGSTON SA400S37240G 50026B738073D789)

<mark>sata_ssd_name_esxi = xxxxxxxxx </mark> (eg: UEFI KINGSTON SA400S37240G 50026B738073D254)

<mark>nvme_ssd_name_esxi_1 = xxxxxxxxx </mark> (eg: UEFI KINGSTON SA400S37240G 50026B738073D254)

<mark>sata_ssd_name_blank = xxxxxxxxx </mark> (eg: UEFI KINGSTON SA400S37240G 50026B738073D254)

<mark>nvme_ssd_name_blank_1 = xxxxxxxxx </mark> (eg: UEFI KINGSTON SA400S37240G 50026B738073D254)

|<mark>Example for Manual mode </mark>|
|-------------------------|
|<span style="color:green;font-weight:bold">[sut_information]</span>|
|<span style="color:#28D6C0">mode = manual</span>|
|<span style="color:#28D6C0">usb_name_1 = UEFI HP x740w 6E009930E417B555</span>|
|<span style="color:#28D6C0">usb_size = 32</span>|
|<span style="color:#28D6C0">sata_ssd_name_rhel = UEFI CT480BX500SSD1 2003E3E36486</span>|
|<span style="color:#28D6C0">nvme_ssd_name_rhel_1 = UEFI CT480BX500SSD1 2003E3E36486</span>|
|<span style="color:#28D6C0">sata_ssd_name_windows = UEFI KINGSTON SA400S37240G 50026B738073D860</span>|
|<span style="color:#28D6C0">nvme_ssd_name_windows_1 = UEFI KINGSTON SA400S37240G 50026B738073D860</span>|
|<span style="color:#28D6C0">sata_ssd_name_centos = UEFI KINGSTON SA400S37240G 50026B738073D744</span>|
|<span style="color:#28D6C0">nvme_ssd_name_centos_1 = UEFI KINGSTON SA400S37240G 50026B738073D744</span>|
|<span style="color:#28D6C0">sata_ssd_name_esxi = UEFI KINGSTON SA400S37240G 50026B738073D745</span>|
|<span style="color:#28D6C0">nvme_ssd_name_esxi_1 = UEFI KINGSTON SA400S37240G 50026B738073D745</span>|
|<span style="color:#28D6C0">sata_ssd_name_blank = UEFI KINGSTON SA400S37240G 50026B738073D765</span>|
|<span style="color:#28D6C0">nvme_ssd_name_blank_1 = UEFI KINGSTON SA400S37240G 50026B738073D765</span>|

<h3><span style="color:red;font-weight:bold">**** </span> All the below commands should run from HOST machine Command Prompt <span style="color:red;font-weight:bold">****</span></h3>

**_<h1>Pre-Downloaded OS, Software and IFWI & BMC & CPLD Package: (Offline)</h1>_**

In this method user have already downloaded the base operating system, software and IFWI packages in host machine and wants to make use of it.

Path of the below python files resides in DTAF Content Framework under "dtaf_content\src\environment\"

For RHEL - the path you should be in "dtaf_content\src\environment\linux_rhel"

For CentOS - the path you should be in "dtaf_content\src\environment\linux_centos"

For ESXI - the path you should be in "dtaf_content\src\environment\esxi"

For Windows - the path you should be in "dtaf_content\src\environment\windows"

For BMC Flashing -the path you should be in "dtaf_content\src\environment\bmc_flashing"

For IFWI Flashing -the path you should be in "dtaf_content\src\environment\ifwi_flashing"

For CPLD Flashing -the path you should be in "dtaf_content\src\environment\cpld_flashing"

<mark>Highlighted </mark> paths can be edited, as they are local drive paths where user keeps the files that they want to pass in. 

**_Linux:- RHEL:_**

**Syntax:** python paiv_rhel_os_offline_installation.py --LOCAL_OS_PACKAGE_LOCATION <mark>C:\xxx_OSpackage.zip </mark> --LOCAL_SOFTWARE_PACKAGE_LOCATION <mark>C:\xxxx_SWpackage.zip </mark>

**Example:** python paiv_rhel_os_offline_installation.py --LOCAL_OS_PACKAGE_LOCATION <mark>C:\os_package\8.2.0-x86_64-dvd_FRE_IA-64_EGS-SRV-RHEL-20.36.1.19873.zip </mark>

--LOCAL_SOFTWARE_PACKAGE_LOCATION <mark>C:\os_package\EGS-SRV-RHEL-20.36.1.19873_SWpackage.zip </mark>

_**Linux:- CentOS:-**_

**Syntax:** python paiv_cent_os_offline_installation.py --LOCAL_OS_PACKAGE_LOCATION <mark>C:\xxx_OSpackage.zip </mark> --LOCAL_SOFTWARE_PACKAGE_LOCATION <mark>C:\xxxx_SWpackage.zip </mark>

**Example:** python paiv_cent_os_offline_installation.py --LOCAL_OS_PACKAGE_LOCATION <mark>C:\os_package\centos-8.2.202009110048_FRE_IA-64_EGS-SRV-CENTOS-20.50.3.28670.zip </mark>

--LOCAL_SOFTWARE_PACKAGE_LOCATION <mark>C:\os_package\EGS-SRV-CENTOS-20.50.3.28670_SWpackage.zip </mark>

**_Windows:-wim_**

**Syntax:** python paiv_win_os_offline_installation.py --LOCAL_OS_PACKAGE_LOCATION <mark>C:\xxx_OSpackage.wim </mark>

**Example:** python paiv_win_os_offline_installation.py --LOCAL_OS_PACKAGE_LOCATION <mark>C:\dump_os_pack\17763Win2019_RS5_OEMRET_FRE_IA-64_EGS-SRV-WS2019-20.37.4.20820.wim </mark>

**_Esxi:_**

**Syntax:** python paiv_esxi_os_offline_installation.py --LOCAL_OS_PACKAGE_LOCATION <mark>C:\xxx_OSpackage.zip </mark> --LOCAL_SOFTWARE_PACKAGE_LOCATION <mark>C:\xxxx_SWpackage.zip </mark>

**Example:** python paiv_esxi_os_offline_installation.py --LOCAL_OS_PACKAGE_LOCATION <mark>C:\os_package\vmvisor-installer-with-test-certs-7.0.1-16358407.x86_64-v2_FRE_IA-64_EGS-SRV-ESXI-20.35.2.19153.zip --LOCAL_SOFTWARE_PACKAGE_LOCATION C:\os_package\EGS-SRV-ESXI-20.35.2.19153_SWpackage.zip </mark>

**_IFWI flashing:_**

**Syntax:** python paiv_ifwi_flashing_offline.py --LOCAL_IFWI_IMG_PATH <mark>C:\xxx_IFWIpackage.zip </mark>

**Example:** python paiv_ifwi_flashing_offline.py --LOCAL_IFWI_IMG_PATH <mark>C:\IFWI_Image\EGSDCRB1.SYS.OR.64.2020.39.7.18.1136_SPR_EBG_SPS.zip </mark>

**_BMC Flashing:- Banino_**

**Syntax:** python paiv_bmc_flashing_banino_offline.py --LOCAL_IFWI_IMG_PATH <mark>C:\xxx_BMCpackage.zip </mark>

**Example:** (.ROM file for Flashing in 2 types)

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**_Directly Giving Predownloaded BMC image from Local: (.zip format)_**

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;python paiv_bmc_flashing_banino_offline.py --LOCAL_BMC_IMG_PATH <mark>C:\IFWI_Image\OBMC-egs-0.16-0-g6cb381-e37eb79.zip </mark>

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**_Directly Giving Predownloaded BMC image from Local: (.ROM format directly)_**

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;python paiv_bmc_flashing_banino_offline.py --LOCAL_BMC_IMG_PATH <mark>C:\IFWI_Image\OBMC-egs-0.16-0-g6cb381-e37eb79-pfr-full.ROM </mark>

**_BMC Flashing:- Redfish_**

**Syntax:** python paiv_bmc_flashing_redfish_offline.py --LOCAL_BMC_IMG_PATH <mark>C:\xxxbmc.zip </mark>

**Example:** (.bin file for Flashing in 3 types)

&nbsp;&nbsp;&nbsp;&nbsp;**_Directly Giving Predownloaded BMC image from Local: (.zip format)_**

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;python paiv_bmc_flashing_redfish_offline.py --LOCAL_BMC_IMG_PATH <mark>C:\BMC_IFWI_Image\OBMC-egs-0.16-0-g6cb381-e37eb79.zip </mark>

&nbsp;&nbsp;&nbsp;&nbsp;**_Directly Giving Predownloaded BMC image from Local: (.7z format)_**

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;python paiv_bmc_flashing_redfish_offline.py --LOCAL_BMC_IMG_PATH <mark>C:\BMC_IFWI_Image\OBMC-egs-0.15-0-g7beaf7-e37eb79.7z </mark>

&nbsp;&nbsp;&nbsp;&nbsp;**_Directly Giving Predownloaded BMC image from Local: (.bin format directly)_**

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;python paiv_bmc_flashing_redfish_offline.py --LOCAL_BMC_IMG_PATH <mark>C:\BMC_IFWI_Image\OBMC-egs-0.16-0-g6cb381-e37eb79-pfr-oob.bin </mark>

**_CPLD Flashing:_**

**Syntax:** python paiv_cpld_flashing_offline.py --LOCAL_CPLD_MAIN_IMG_PATH <mark>C:\XXX.zip </mark> --LOCAL_CPLD_SECONDARY_IMG_PATH <mark>C:\XXX.zip </mark>

**Examples:** (.pof file for Flashing in 2 types)

&nbsp;&nbsp;&nbsp;&nbsp;**_Directly Giving Predownloaded Main and Secondary CPLD images from Local: (.zip format)_** 

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;python paiv_cpld_flashing_offline.py --LOCAL_CPLD_MAIN_IMG_PATH <mark>C:\cpld_frimware\MainFpga_2vA.zip </mark> --LOCAL_CPLD_SECONDARY_IMG_PATH <mark>C:\cpld_frimware\ac_rp_fab3_SecondaryFpga_0v7.zip </mark>

&nbsp;&nbsp;&nbsp;&nbsp;**_Directly Giving Predownloaded Main and Secondary CPLD images from Local: (.pof format directly)_**

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;python paiv_cpld_flashing_offline.py --LOCAL_CPLD_MAIN_IMG_PATH <mark>C:\cpld_frimware\ac_rp_fab3_MainFpga_2vA.pof </mark> --LOCAL_CPLD_SECONDARY_IMG_PATH <mark>C:\cpld_frimware\ac_rp_fab3_SecondaryFpga_0v7.pof </mark>

**_<h1>Direct Download of Software PKG, Base OS and IFWI & CPLD and BMC PKG from Artifactory (Online)_**</h1>

In this method user have the Artifactory link of base operating system and Software package for Linux, Cent os, esxi, windows (.wim), IFWI, CPLD and BMC package artifactory URL.

Path of the below python files resides in DTAF Content Framework under "dtaf_content\src\environment\"

For RHEL - the path you should be in "dtaf_content\src\environment\linux_rhel"

For CentOS -  the path you should be in "dtaf_content\src\environment\linux_centos"

For ESXI -  the path you should be in "dtaf_content\src\environment\esxi"

For Windows -  the path you should be in "dtaf_content\src\environment\windows"

For BMC Flashing - the path you should be in "dtaf_content\src\environment\bmc_flashing"

For IFWI Flashing - the path you should be in "dtaf_content\src\environment\ifwi_flashing"

For CPLD Flashing - the path you should be in "dtaf_content\src\environment\cpld_flashing"

<mark>Highlighted </mark> paths can be edited, as per your requirement based on what artifactory link you want to pass in. 

**_Linux:-RHEL_**

**Syntax:** python paiv_rhel_os_online_installation.py --ATF_PATH_SFT_PKG <mark>https://xxx_SoftwarePackage.zip  </mark> --ATF_PATH_OS_PKG <mark>https://xxx_OSPackage.zip  </mark>

**Example:** python paiv_rhel_os_online_installation.py --ATF_PATH_SFT_PKG <mark>https://ubit-artifactoryba.intel.com/artifactory/dcg-dea-srvplat-local/Kits/EGS-SRV-RHEL/EGS-SRV-RHEL-20.36.1.19873/Images/EGSSRV-RHEL-20.36.1.19873_SWpackage.zip </mark> --ATF_PATH_OS_PKG <mark>https://ubit-artifactoryba.intel.com/artifactory/dcg-dea-srvplat-local/Kits/EGS-SRV-RHEL/EGS-SRV-RHEL-20.36.1.19873/Images/8.2.0-x86_64-dvd_FRE_IA-64_EGS-SRV-RHEL-20.36.1.19873.zip </mark>

**_Linux:-CentOS_**

**Syntax:** python paiv_cent_os_online_installation.py --ATF_PATH_SFT_PKG <mark>https://xxx_SoftwarePackage.zip </mark> --ATF_PATH_OS_PKG <mark>https://xxx_OSPackage.zip </mark>

**Example:** python paiv_cent_os_online_installation.py --ATF_PATH_SFT_PKG <mark>https://ubit-artifactoryba.intel.com/artifactory/dcg-dea-srvplat-local/Kits/EGS-SRV-CentOS/EGS-SRV-CENTOS-
20.44.3.25132/Images/EGS-SRV-CENTOS-20.44.3.25132_SWpackage.zip </mark> --ATF_PATH_OS_PKG <mark>https://ubitartifactory-ba.intel.com/artifactory/dcg-dea-srvplat-local/Kits/EGS-SRV-RHEL/EGS-SRV-RHEL-
20.36.1.19873/Images/8.2.0-x86_64-dvd_FRE_IA-64_EGS-SRV-RHEL-20.36.1.19873.zip </mark>

**_Windows:-_**

**Syntax:** python paiv_win_os_online_installation.py --ATF_PATH_OS_PKG <mark>https://xxx_OSPackage.wim </mark>

**Example:** python paiv_win_os_online_installation.py --ATF_PATH_OS_PKG <mark>https://ubit-artifactoryba.intel.com/artifactory/dcg-dea-srvplat-local/Kits/EGS-SRV-WS2019/EGS-SRV-WS2019-
20.37.4.20820/Images/17763Win2019_RS5_OEMRET_FRE_IA-64_EGS-SRV-WS2019-20.37.4.20820.wim </mark>

**_Esxi:_**

**Syntax:** python paiv_esxi_os_online_installation.py --ATF_PATH_SFT_PKG <mark>https://xxx_SoftwarePackage.zip </mark> --ATF_PATH_OS_PKG <mark>https://xxx_OSPackage.zip </mark>

**Example:** python paiv_esxi_os_online_installation.py --ATF_PATH_SFT_PKG <mark>https://ubit-artifactoryba.intel.com/artifactory/dcg-dea-srvplat-local/Kits/EGS-SRV-ESXI/EGS-SRV-ESXI-20.35.2.19153/Images/EGSSRV-ESXI-20.35.2.19153_SWpackage.zip </mark> --ATF_PATH_OS_PKG <mark>https://ubit-artifactoryba.intel.com/artifactory/dcg-dea-srvplat-local/Kits/EGS-SRV-ESXI/EGS-SRV-ESXI-
20.35.2.19153/Images/vmvisor-installer-with-test-certs-7.0.1-16358407.x86_64-v2_FRE_IA-64_EGS-SRV-ESXI-20.35.2.19153.zip </mark>

**_IFWI flashing:_**

**Syntax:** python paiv_ifwi_flashing_online.py --ATF_PATH_IFWI_PKG <mark>https://xxx_IFWIpackage.zip </mark>

**Example:** python paiv_ifwi_flashing_online.py --ATF_PATH_IFWI_PKG <mark>https://ubit-artifactorysh.intel.com/artifactory/dcg-dea-srvplat-local/Kits/ICX-SRV-RHEL/ICX-SRV-RHEL-
20.40.5.23102/Packages/IFWI/2020.29.2.02.0415_0017.d92/IFWI_2020.29.2.02.0415_0017.D92.zip </mark>

**_BMC Flashing:- Banino_**

**Syntax:** python paiv_bmc_flashing_banino_online.py --ATF_PATH_BMC_PKG <mark>https://package.zip </mark>

**Example:** python paiv_bmc_flashing_banino_online.py --ATF_PATH_BMC_PKG <mark>https://ubit-artifactoryba.intel.com/artifactory/DEG-PSS-local/EagleStream_SapphireRapids_Post_Si/Firmwares/BMC/OBMC-egs-
0.16-0-g6cb381-e37eb79.zip </mark>

**_BMC Flashing:- Redfish_**

**Syntax:** python paiv_bmc_flashing_redfish_online.py --ATF_PATH_BMC_RED_PKG <mark>https://ATFBMC.zip </mark>

**Example:** 

&nbsp;&nbsp;&nbsp;&nbsp;**_Artifactory link with BMC image: (.zip format)_**

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;python paiv_bmc_flashing_redfish_online.py --ATF_PATH_BMC_RED_PKG <mark>https://ubit-artifactoryba.intel.com/artifactory/DEG-PSS-local/EagleStream_SapphireRapids_Post_Si/Firmwares/BMC/OBMC-egs-0.16-0-g6cb381-e37eb79.zip </mark>

&nbsp;&nbsp;&nbsp;&nbsp;**_Artifactory link with BMC image: (.7z format)_**

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;python paiv_bmc_flashing_redfish_online.py --ATF_PATH_BMC_RED_PKG <mark>https://ubit-artifactoryba.intel.com/artifactory/DEG-PSS-local/EagleStream_SapphireRapids_Post_Si/Firmwares/BMC/OBMC-egs-0.15-0-g7beaf7-e37eb79.7z </mark>

**_CPLD Flashing:-_**

**Syntax:** python paiv_cpld_flashing_online.py --ATF_PATH_CPLD_MAIN_PKG <mark>https://atf.zip </mark> --ATF_PATH_CPLD_SECONDARY_PKG <mark>https://atf.zip </mark>

**Example:** python paiv_cpld_flashing_online.py --ATF_PATH_CPLD_MAIN_PKG <mark>https://ubit-artifactoryba.intel.com/artifactory/dcg-dea-srvplat-local/Kits/EGS-SRV-RHEL/EGS-SRV-RHEL-
20.45.2.25578/Packages/PLD_Main/pld_main_2va/MainFpga_2vA.zip </mark> --ATF_PATH_CPLD_SECONDARY_PKG <mark>https://ubit-artifactory-ba.intel.com/artifactory/dcg-dea-srvplat-local/Kits/EGS-SRV-RHEL/EGS-SRV-RHEL-20.45.2.25578/Packages/PLD_Modular/pld_modular_ac_rp_fab3_secondaryfpga_0v7/ac_rp_fab3_SecondaryFpga_0v7.zip </mark>
                                        
                                                            ------------ > END OF FILE < ----------