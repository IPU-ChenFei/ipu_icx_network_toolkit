"""
#Author Suresh Sakthi

version 1.0 23-August-2021 :- Created RHEL BMC VMM Os Installation Script

"""
import re
import os
import six
import sys
import time
import glob
import ntpath
import os.path
from xml.etree import ElementTree as eTree
from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.providers.flash_provider import FlashProvider
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.bios_menu import BiosBootMenuProvider
from dtaf_core.providers.ac_power import AcPowerControlProvider
from dtaf_core.providers.bios_menu import BiosSetupMenuProvider
from dtaf_core.providers.provider_factory import ProviderFactory
from src.environment.os_prerequisites import OsPreRequisitesLib
from dtaf_core.lib.configuration import ConfigurationHelper
from src.lib.tools_constants import SysUser

class Os_Installation(BaseTestCase):
    def __init__(self, test_log, arguments, cfg_opts):
        super(Os_Installation, self).__init__(test_log, arguments, cfg_opts)
        flash_cfg = cfg_opts.find(FlashProvider.DEFAULT_CONFIG_PATH)
        self._flash = ProviderFactory.create(flash_cfg, test_log)
        ac_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._ac = ProviderFactory.create(ac_cfg, test_log)
        tree = eTree.ElementTree()
        if sys.platform == 'win32':
            tree.parse(r'C:\Automation\system_configuration.xml')
        else:
            tree.parse('/opt/Automation/consolelog_configuration.xml')
        root = tree.getroot()
        sut = ConfigurationHelper.get_sut_config(root)
        redfish_flash_cfg = ConfigurationHelper.filter_provider_config(sut=sut, provider_name=r"physical_control",
                                                                       attrib=dict(id="VIRTUAL_MEDIA"))
        redfish_flash_cfg = redfish_flash_cfg[0]
        self._phy = ProviderFactory.create(redfish_flash_cfg, test_log)
        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)
        self._os_pre_req_lib = OsPreRequisitesLib(test_log, cfg_opts)
        setupmenu_cfg = cfg_opts.find(BiosSetupMenuProvider.DEFAULT_CONFIG_PATH)
        self.setupmenu = ProviderFactory.create(setupmenu_cfg, test_log)
        bootmenu_cfg = cfg_opts.find(BiosBootMenuProvider.DEFAULT_CONFIG_PATH)
        self.bootmenu = ProviderFactory.create(bootmenu_cfg, test_log)
        self.os_params = self._os_pre_req_lib.get_sut_inventory_data("rhel")
        self._atf_username = arguments.atf_user
        self._atf_password = arguments.atf_password
        self._atf_iso = arguments.atf_iso_path
        self._log.info("old ISO path = {0}".format(self._atf_iso))
        self._atf_iso = self._atf_iso.replace("artifactory-ba.intel.com/artifactory/dcg-dea-srvplat-local",
                                              "artifactory.intel.com/artifactory/dcg-dea-srvplat-repos")
        self._log.info("new ISO path = {0}".format(self._atf_iso))
        self._usb_drive_name = "UEFI OpenBMC Virtual Media Device"
        if arguments.hardisk_drive_name is None:
            self._hardisk_drive_name = self.os_params[2]  # name of the Hard Disk in Which Os Needs To Be Loaded
        else:
            self._hardisk_drive_name = arguments.hardisk_drive_name
        self._bios_path = arguments.boot_order_change_path  # Bios Path To Change Boot-Order "xxxx,xxx,xxx"
        self._boot_select_path = arguments.boot_select_path  # Select Boot Path For Selecting USB Drive "xxxx,xxx,xxx"
        self._save_knob_name = arguments.save_knob_path  # Select Boot Path For Selecting USB Drive "xxxx,xxx,xxx"
        self._boot_select_path += "," + str(self._usb_drive_name)
        

    def prepare(self):
        pass

    @classmethod
    def add_arguments(cls, parser):
        super(Os_Installation, cls).add_arguments(parser)
        # caf based throw and fetch approach
        ostype = os.environ.get("OSTYPE")
        ifwipath = os.environ.get("IFWIPATH")
        ifwifile = os.environ.get("IFWIFILE")
        imagetype = os.environ.get("IMAGETYPE")
        driverpkgpath = os.environ.get("DRIVERPKGPATH")
        driverfile = os.environ.get("DRIVERFILE")
        imagepath = os.environ.get("IMAGEPATH")
        imagefile = os.environ.get("IMAGEFILE")
        enableflashing = os.environ.get("ENABLEFLASHING")
        basepath = os.environ.get("BASEPATH")
        # host path Fixed or parameter can change them
        parser.add_argument('--ATF_USERNAME', action="store", dest="atf_user", default=SysUser.USER,
                            help="Inorder To Download From Other Artifactory Location give correct username")
        parser.add_argument('--ATF_PASSWORD', action="store", dest="atf_password", default=SysUser.PWD,
                            help="Inorder To Download From Other Artifactory Location give correct password")
        parser.add_argument('--ATF_ISO_PATH', action="store", dest="atf_iso_path", default="https://ubit-artifactory-ba.intel.com/artifactory/list/dcg-dea-srvplat-local/Automation_Tools/SPR/RHEL_bronze.iso",
                            help="Inorder To Mount os image Given In Iso Path")


        # BIOS Selection and Change
        parser.add_argument('--USB_DEVICE_NAME', action="store", dest="usb_drive_name", default="UEFI OpenBMC Virtual Media Device",
                            help="Name of the USB Drive How it Appears in BIOS")
        parser.add_argument('--HARDISK_DEVICE_NAME', action="store", dest="hardisk_drive_name", default=None,
                            help="Name of the Hard Drive How it Appears in BIOS")
        parser.add_argument('--BIOS_BOOT_ORDER_PATH', action="store", dest="boot_order_change_path",
                            default="Boot Maintenance Manager,Boot Options, Change Boot Order",
                            help="Provide Bios Path To Change Boot-Order \"xxxx,xxx,xxx\" by Default Boot Maintenance Manager,Boot Options,Change Boot Order,Commit Changes and Exit")
        parser.add_argument('--BIOS_BOOT_SELECT_PATH', action="store", dest="boot_select_path",
                            default="Boot Manager Menu",
                            help="Provide USB Boot Path \"xxxx,xxx\" For Selecting USB Drive For Os Installation by Default Boot Manager Menu")
        parser.add_argument('--SAVE_KNOB_NAME', action="store", dest="save_knob_path",
                            default="Commit Changes and Exit",
                            help="Save Knob Name by Default This is the Knob Commit Changes and Exit")
        # --IFWIFILE Name of the IFWI Image with .bin Extension
        # For Direct Parameter passing no need of Artifactory usage  --IFWI_IMG_PATH xxxxx --IFWIFILE xxxxx --Dnd_Extract False
        
        #unwanted
        ##SOFTWARE PACKAGE
        # --------------------- Whether To Download and Use ALready Existing SOFTWARE Package
        parser.add_argument('--INITIALIZE_SOFTWARE_PACKAGE', action="store", dest="initialize_sft_pkg", default=None,
                            help="Inorder To Download From ARTIFACTORY or Reuse Software-Package Available in Hostmachine Local Drive, by Default is False")
        # --------------------- FOR DIRECT Download of SOFTWARE PACKAGE
        parser.add_argument('--DIRECT_SOFTWARE_PACKAGE_DOWNLOAD_MODE', action="store", dest="direct_sft_download",
                            default=None,
                            help="InOrder TO Downloaded Software-Package From Artifactory Directly Make It True,by Default False")
        parser.add_argument('--ATF_PATH_SFT_PKG', action="store", dest="atf_sft_pkg_path", default=None,
                            help="Full path along with file name of Software_pkg in Arifactory has To be Given including")  # full path for the base sft_pkg to be given
        # --------------------- FOR Custom RE-Use of SOFTWARE PACKAGE In Local Machine
        parser.add_argument('--LOCAL_SOFTWARE_PACKAGE_MODE', action="store", dest="pre_downloaded_sft_pkg_mode",
                            default=None,
                            help="Inorde TO Make Use Of Already Existing Predownloaded Sfotware Packe From Local Hostmachine, Make It True, By Default it will be False")  # true will fetch the image location along sft img_name passed by user
        parser.add_argument('--LOCAL_SOFTWARE_PACKAGE_LOCATION', action="store",
                            dest="pre_downloaded_sft_local_location", default=None,
                            help="Software Pre-Downlaoded Local Package Path eg: c:\path\sft_pkg.zip")  # c:\path\sft_pkg.zip

        ##BASE OR WIM KIT DOWNLOAD
        # --------------------- Whether To Download or Use ALready Existing OS Package
        parser.add_argument('--INITIALIZE_OS_PACKAGE', action="store", dest="initialize_os_pkg", default=None,
                            help="Inorder To Download or Reuse OS-Package, by Default is False")
        # --------------------- FOR DIRECT Download of OS PACKAGE
        parser.add_argument('--DIRECT_OS_PACKAGE_DOWNLOAD_MODE', action="store", dest="direct_os_download",
                            default=None,
                            help="InOrder TO Make Use Of Direct Artifactory Download Of OS-Package From Local HostMachine Make It True,by Default False")
        parser.add_argument('--ATF_PATH_OS_PKG', action="store", dest="atf_baseos_path", default=None,
                            help="Provide Artifactory URL Link For Os Image Path With File Extension")
        # --------------------- FOR Custom RE-Use of OS PACKAGE In Local Machine
        parser.add_argument('--LOCAL_OS_PACKAGE_MODE', action="store", dest="pre_downloaded_os_pkg_mode", default=False,
                            help="InOrder TO Make Use Of Pre-Downloaded OS-Package From Local HostMachine Make It True,by Default False")
        parser.add_argument('--LOCAL_OS_PACKAGE_LOCATION', action="store", dest="pre_downloaded_os_pkg_location",
                            default=None,
                            help="Incase Already Downloaded OS Image Is Available then Give Full Path With Os Package Filename Extension needs to be given")

        # EXTRACTION
        parser.add_argument('--EXTRACT_SOFTWARE_TO_USB', action="store", dest="extract_sft_package_to_usb",
                            default=True,
                            help="For Avoiding Extraction of Downloaded Software Package To USB, Incase Already Software Package Content Is Available No Need To Extract Again Give False by Default It Will Be True")
        parser.add_argument('--EXTRACT_OS_TO_USB', action="store", dest="extract_os_package_to_usb", default=True,
                            help="For Avoiding Extraction of Downloaded OS Image To USB, Incase Already OS Content Is Available No Need To Extract Again Give False by Default It Will Be True")




    def platform_ac_power_off(self):

        if self._ac.ac_power_off() == True:
            self._log.info("Platfor(SUT) AC-power TURNED OFF")
        else:
            self._log.error("Failed TO Do AC-power OFF")
            return False
        # Making Sure Platform AC-Power is Turned OFF
        if self._ac.get_ac_power_state() == False:
            self._log.info("Platform(SUT) AC-power TURNED-OFF Confrimed")
            time.sleep(3)
            return True
        else:
            self._log.error("Platform(SUT) AC-power TURNED-Off Confrimation failed")
            return False

    def platform_ac_power_on(self):
        if self._ac.ac_power_on() == True:
            self._log.info("Platfor(SUT) AC-power TURNED ON")
        else:
            self._log.error("Failed TO Do AC-power ON")
            return False
        time.sleep(4)
        if self._ac.get_ac_power_state() == True:
            self._log.info("Platform(SUT) AC-power TURNED-ON Confrimed")
            time.sleep(5)
            return True
        else:
            self._log.error("Failed To Platform(SUT) AC-power TURNED-Off Confrimation")
            return False

    def switch_usb_to_target(self):  # changed
        if (self._phy.connect_usb_to_sut(image=self._atf_iso,username=self._atf_username,password=self._atf_password) != True):
            self._log.error("Mounting Failed check BMC IP configured in Physical control provider in Config File")
            return False
        else:
            return True

    def switch_usb_to_host(self):  # changed
        if (self._phy.connect_usb_to_host() != True):
            self._log.error("USB Switching To Host Failed")
            return False
        return True

    def bios_path_navigation(self, path):
        path = path.split(',')
        try:
            for i in range(len(path)):
                time.sleep(10)
                ret = self.setupmenu.get_page_information()
                ret = self.setupmenu.select(str(path[i]), None, True, 60)
                print(self.setupmenu.get_selected_item().return_code)
                self.setupmenu.enter_selected_item(ignore=False, timeout=10)
                self._log.info("Entered into {0} ".format(path[i]))
            return True
        except Exception as ex:
            self._log.error("{0} Issues Observed".format(ex))
            return False

    def bios_path_navigation1(self, path):
        path = path.split(',')
        try:
            time.sleep(60)
            for i in range(len(path)):
                ret = self.setupmenu.get_page_information()
                ret = self.setupmenu.select(str(path[i]), None, True, 60)
                print(self.setupmenu.get_selected_item().return_code)
                self.setupmenu.enter_selected_item(ignore=False, timeout=10)
                self._log.info("Entered into {0} ".format(path[i]))
            self._log.info("Entered Auto install rhel")
            self.setupmenu.enter_selected_item(ignore=False, timeout=10)
            return True
        except Exception as ex:
            self._log.error("{0} Issues Observed".format(ex))
            return False

    def enter_into_bios(self):
        ret=self.setupmenu.wait_for_entry_menu(10000)
        for i in range(0, 10):
            f2_state = self.setupmenu.press(r'F2')
            time.sleep(0.3)
            if f2_state:
                self._log.info("F2 keystroke Pressed")
                break
        ret = self.setupmenu.wait_for_bios_setup_menu(30)
        if(str(ret) == "SUCCESS"):
            self._log.info("Entered Into Bios Menu")
            return True
        else:
            self._log.error("Failed To Enter Into Bios Menu Page,Close COM Port if opened in Putty Check")
            return False

    def execute(self):
        self._log.info("Given ATF location from Product Build {0}".format(self._atf_iso))
        if (self.prepare() != False):
            # Flashing IFWI Image
            if (self.platform_ac_power_off() != True):
                self._log.error("Failed To Platform Ac-Power OFF")
                return False

            if (self.platform_ac_power_on() != True):
                self._log.error("Failed To Platform Ac-Power ON")
                return False

            # Enter Into bios and change boot order and select USB for Installation
            self._log.info("Entering Into Bios SETUP Page of Target Platform")
            if (self.enter_into_bios() != True):
                self._log.error("Didn't Enter Into Bios_Setup Page")
                return False

            if (self.switch_usb_to_target() != True):
                self._log.error("USB_DRIVE Is Not Connected To Platform(SUT)")
                return False

            self._log.info(
                "Entering Into Bios SETUP Page To Change BIOS BOOTORDER AND Select USB For OS-Installation")
            if (self.bios_path_navigation(path=self._bios_path) == True):
                self.setupmenu.change_order([str(self._usb_drive_name)])
                time.sleep(5)
                self.setupmenu.change_order([str(self._hardisk_drive_name)])
                self._log.info("BOOT Order Change Done {0} First Boot Order".format(self._hardisk_drive_name))
                if (self.bios_path_navigation(path=self._save_knob_name) == True):
                    self._log.info("Changing and Saving Boot-Order Successful")
                    self.setupmenu.back_to_root(10, False)
                else:
                    self._log.error("Unable To Change or Find BootOrder")
                    return False
                if (self.bios_path_navigation(path=self._boot_select_path) == True):
                    self._log.info("Selecting USB To Proceed with Boot Successful")
                else:
                    self._log.error("Unable To Enter Into Bios SETUP Page")
                    False
            else:
                self._log.error("Unable To Change Boot-Order and FAILED To Proceed With OS Installation")
                return False

            self._log.info("OS-Installation In Progress Will Taken Some Time")
            # verifying OS installation
            for i in range(0, 80):
                try:
                    time.sleep(60)
                    if (self._os.is_alive() == True):
                        self._log.info("INSTALLED And Entered Into RHEL OS Successfully")
                        self._phy.disconnect_usb()
                        return True
                    elif (i == 50):
                        self._log.info("Os Installation Had Issues Waited For 50 Mins")
                        return False
                    else:
                        self._log.debug("OS Installation Is IN-Progress")
                except:
                    continue

        else:
            self._log.error("Preparing OS-Installation and Wrong-Parameter-Input Given")
            return False
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if Os_Installation.main() else Framework.TEST_RESULT_FAIL)
