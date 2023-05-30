#!/usr/bin/env python
#################################################################################
# INTEL CONFIDENTIAL
# Copyright Intel Corporation All Rights Reserved.
#
# The source code contained or described herein and all documents related to
# the source code ("Material") are owned by Intel Corporation or its suppliers
# or licensors. Title to the Material remains with Intel Corporation or its
# suppliers and licensors. The Material may contain trade secrets and proprietary
# and confidential information of Intel Corporation and its suppliers and
# licensors, and is protected by worldwide copyright and trade secret laws and
# treaty provisions. No part of the Material may be used, copied, reproduced,
# modified, published, uploaded, posted, transmitted, distributed, or disclosed
# in any way without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
#################################################################################

import re
import os
import six
import time
import ntpath
import os.path
import zipfile
import platform
import subprocess
from os import path
from subprocess import Popen, PIPE, STDOUT

from dtaf_core.providers.bios_menu import BiosSetupMenuProvider, BiosBootMenuProvider
from dtaf_core.providers.ac_power import AcPowerControlProvider
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.physical_control import PhysicalControlProvider
from src.lib.content_configuration import ContentConfiguration
from src.environment.os_prerequisites import OsPreRequisitesLib
from dtaf_core.providers.sut_os_provider import SutOsProvider
from src.lib.tools_constants import SysUser


class OsInstallationLib(object):
    """
    This class contains common functions which can be used for os installation.
    """

    def __init__(self, test_log, cfg_opts):
        self._log = test_log
        self._cfg_opts = cfg_opts
        ac_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._ac = ProviderFactory.create(ac_cfg, test_log)
        phy_cfg = cfg_opts.find(PhysicalControlProvider.DEFAULT_CONFIG_PATH)
        self._phy = ProviderFactory.create(phy_cfg, test_log)
        self._os_pre_req_lib = OsPreRequisitesLib(test_log, cfg_opts)
        setupmenu_cfg = cfg_opts.find(BiosSetupMenuProvider.DEFAULT_CONFIG_PATH)
        self.setupmenu = ProviderFactory.create(setupmenu_cfg, test_log)
        bootmenu_cfg = cfg_opts.find(BiosBootMenuProvider.DEFAULT_CONFIG_PATH)
        self.bootmenu = ProviderFactory.create(bootmenu_cfg, test_log)
        self._common_content_configuration = ContentConfiguration(self._log)

        self.inventory_filename = False

        if not self.inventory_filename:
            self.inventory_filename = None

        self.os_params = self._os_pre_req_lib.get_sut_inventory_data("rhel", self.inventory_filename)

        self._os_install = True  # for flashing ifwi image alone

        self._atf_username = SysUser.USER
        self._atf_password = SysUser.PWD

        self._ostype = "RHEL"

        # host machine is linux or Windows
        self._host = "windows_host"
        self._format_pendrive = True
        self._usb_size = self.os_params[1]
        self._curl_server = "bdcspiec010.gar.corp.intel.com"

        # software package
        self._initialize_sft_pkg = True  # True or Flase to initialize software package
        self._direct_sft_pkg_download = None  # whether to download os image given by user #True or False
        self._direct_sft_img_path = None  # full atf software_pkg path along with file name extension
        self._usr_given_local_sft_mode = True  # local drive #True or by default none
        sut_os_cfg = self._cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, self._log)  # type: SutOsProvider
        self._local_drive_sft_pkg = self._common_content_configuration.get_sft_pkg_path(self._os.os_subtype.lower())  # path is from Local location # in hostmachine #full path to be given Also With FileName # where the .zip sft pkg is present in local drive

        # os package
        self._initialize_os_pkg = True  # True  to initialize os package download or further choose reuse
        self._direct_os_download = None  # whether to download os image given by user #True by default none
        self._direct_os_img_path = None  # full atf os location path along with file name extension
        self._usr_given_local_os_mode = True  # local drive #True or by default none
        self._local_drive_os_pkg = self._common_content_configuration.get_os_pkg_path(self._os.os_subtype.lower())  # path in location computer the# hostmachine #full path to be given Also With FileName # where the .zip os img is present in local drive

        # extraction
        self._extract_sft_package = True
        self._extract_os_package = True

        # bios
        self._usb_drive_name = self.os_params[0]  # USB Device Name from Which OS Needed To Be Installed From
        self._hardisk_drive_name = self.os_params[2]  # name of the Hard Disk in Which Os Needs To Be Loaded
        self._bios_path = "Boot Maintenance Manager,Boot Options, Change Boot Order"  # Bios Path To Change Boot-Order "xxxx,xxx,xxx"
        self._boot_select_uefi_path = "Boot Manager Menu,UEFI Internal Shell"  # Select Boot Path For Selecting UEFI Shell "xxxx,xxx,xxx"
        self._save_knob_name = "Commit Changes and Exit"  # Select Boot Path For Selecting USB Drive "xxxx,xxx,xxx"

        ##automation enabler
        self._rhel_cfg_file_name = self._common_content_configuration.get_cfg_file_name(self._os.os_subtype.lower())
        self._fedora_cfg_file_name = "fc31-uefi-ks.cfg"

    def format_usb_drive(self, size, format_usb=None, wim=None):
        """
        :- size Pendrive Size accepted size values are 8,16,32,64
           wim for windwos installation it requires a special format of the pendrive into 2 partion, pass yes or True if os that needs to be copied into pendrive is .wim
        return True
        following the action of True, formats the pendrive assigns letter S and renames the usb_drive to OS
        """
        size = str(size)
        if str(platform.architecture()).find("WindowsPE") != -1:
            try:
                p = Popen(["diskpart"], stdin=PIPE, stdout=PIPE)
                if six.PY2:
                    ret = p.stdin.write(b'rescan \n')
                    ret = p.stdin.write(b'list disk \n')
                    ret = p.stdin.write(b'exit \n')
                    ret = p.stdout.read()
                    a = ret.split(",")
                    a = str(a).strip()
                    a = " ".join(a.split())
                elif six.PY3:
                    ret = p.stdin.write(bytes("rescan \n", encoding='utf-8'))
                    time.sleep(2)
                    ret = p.stdin.write(bytes("list disk \n", encoding='utf-8'))
                    time.sleep(2)
                    ret = p.stdin.write(bytes("exit \n", encoding='utf-8'))
                    ret = p.communicate()
                    a = str(ret).split(",")
                    a = str(a).strip()
                    a = " ".join(a.split())
                try:
                    if (size == "8"):
                        for i in ("7 GB", "7.8 GB", "7.5 GB", "6 GB", "6.5 GB", "6.8 GB"):
                            try:
                                if (a.index(str(i)) != -1):
                                    index = a.index(str(i))
                                    self._log.info(
                                        "Usb Available Size That was Found {0} {1}".format(a[index:index + 2], "GB"))
                                    data = (a[index - 19:index + 2])
                                    break
                            except:
                                continue
                    elif (size == "16"):
                        for i in ("14 GB", "14.5 GB", "13 GB", "12.5 GB", "13.5 GB"):
                            try:
                                if (a.index(str(i)) != -1):
                                    index = a.index(str(i))
                                    self._log.info(
                                        "Usb Available Size That was Found {0} {1}".format(a[index:index + 2], "GB"))
                                    data = (a[index - 20:index + 2])
                                    break
                            except:
                                continue
                    elif (size == "32"):
                        for i in ("27 GB", "27.5 GB", "28 GB", "28.5 GB", "28.8 GB","28.2 GB","28.7 GB","28.9 GB", "29 GB","29.2 GB","29.3 GB","29.5 GB"):
                            try:
                                if (a.index(str(i)) != -1):
                                    index = a.index(str(i))
                                    self._log.info(
                                        "Usb Available Size That was Found {0} {1}".format(a[index:index + 2], "GB"))
                                    data = (a[index - 20:index + 2])
                                    break
                            except:
                                continue
                    elif (size == "64"):
                        for i in ("57 GB", "57.5 GB","56 GB", "56.5 GB", "56.8 GB", "57.8 GB", "58 GB", "58.5 GB", "59.5 GB"):
                            try:
                                if (a.index(str(i)) != -1):
                                    index = a.index(str(i))
                                    self._log.info(
                                        "Usb Available Size That was Found {0} {1}".format(a[index:index + 2], "GB"))
                                    data = (a[index - 20:index])
                                    break
                            except:
                                continue
                    else:
                        self._log.error(
                            "Please Ensure that pendrive size is Correct and Connected To Host-Machine Supported size of USb 8,16,32,64gb {0}".format(
                                ret))
                        return False
                    mb = (int(a[index:index + 2]) * 1000)
                    ntfs = (mb - 4000)
                    fat_size = 3000
                except Exception as ex:
                    self._log.error(
                        "Please Ensure that pendrive size is Correct and Connected To Host-Machine Supported size of USb 8,16,32,64gb {0}".format(
                            ex))
                    return False
                a = ["Disk 1", "Disk 2", "Disk 3", "Disk 4"]
                for i in range(0, 10):
                    if (a[i] in data):
                        pendrive_disk = a[i]
                        self._log.info("This {0} is USB_Device".format(pendrive_disk))
                        break
                if ((str(wim)).lower() in ["true", "yes", "on"]):
                    time.sleep(10)
                    try:
                        if six.PY2:
                            p = Popen([b'diskpart'], stdin=PIPE)
                            res1 = p.stdin.write(b'list vol \n')
                            time.sleep(4)
                            p.stdin.flush()
                            res1 = p.stdin.write(b'rescan \n')
                            time.sleep(4)
                            p.stdin.flush()
                            res1 = p.stdin.write(b'list disk \n')
                            time.sleep(1)
                            p.stdin.flush()
                            res1 = p.stdin.write(b'select ' + str(pendrive_disk) + ' \n')
                            time.sleep(1)
                            p.stdin.flush()
                            try:
                                res4 = p.stdin.write(b'clean \n')
                                time.sleep(5)
                                p.stdin.flush()
                            except:
                                res4 = p.stdin.write(b'clean \n')
                                time.sleep(5)
                                p.stdin.flush()
                            res1 = p.stdin.write(b'rescan \n')
                            time.sleep(5)
                            p.stdin.flush()
                            res1 = p.stdin.write(b'select ' + str(pendrive_disk) + ' \n')
                            time.sleep(2)
                            p.stdin.flush()
                            res5 = p.stdin.write(b"create partition primary SIZE=" + str(ntfs) + " \n")
                            time.sleep(3)
                            p.stdin.flush()
                            res6 = p.stdin.write(b"FORMAT FS=NTFS Label=UsbWIMs QUICK \n")
                            time.sleep(6)
                            p.stdin.flush()
                            res7 = p.stdin.write(b"assign letter=S\n")
                            time.sleep(2)
                            p.stdin.flush()
                            res8 = p.stdin.write(b"active \n")
                            time.sleep(2)
                            p.stdin.flush()
                            res6 = p.stdin.write(b"create partition primary SIZE=" + str(fat_size) + " \n")
                            time.sleep(3)
                            p.stdin.flush()
                            res6 = p.stdin.write(b"FORMAT FS=fat32 Label=WIMAGERUSB QUICK \n")
                            time.sleep(6)
                            p.stdin.flush()
                            res7 = p.stdin.write(b"assign letter=H \n")
                            time.sleep(2)
                            p.stdin.flush()
                            res8 = p.stdin.write(b"active \n")
                            time.sleep(2)
                            p.stdin.flush()
                            res8 = p.stdin.write(b"exit \n")
                            time.sleep(2)
                            p.stdin.flush()
                        elif six.PY3:
                            p = Popen(['diskpart'], stdin=PIPE)
                            res1 = p.stdin.write(bytes('list vol \n', encoding='utf8'))
                            time.sleep(4)
                            p.stdin.flush()
                            res1 = p.stdin.write(bytes('rescan \n', encoding='utf8'))
                            time.sleep(2)
                            p.stdin.flush()
                            res1 = p.stdin.write(bytes('list disk \n', encoding='utf8'))
                            time.sleep(2)
                            p.stdin.flush()
                            res1 = p.stdin.write(bytes('select ' + str(pendrive_disk) + ' \n', encoding='utf8'))
                            time.sleep(2)
                            p.stdin.flush()
                            try:
                                res4 = p.stdin.write(bytes('clean \n', encoding='utf8'))
                                time.sleep(8)
                                p.stdin.flush()
                            except:
                                res1 = p.stdin.write(bytes('rescan \n', encoding='utf8'))
                                time.sleep(3)
                                p.stdin.flush()
                                res1 = p.stdin.write(bytes('select ' + str(pendrive_disk) + ' \n', encoding='utf8'))
                                time.sleep(2)
                                p.stdin.flush()
                                res4 = p.stdin.write(bytes('clean \n', encoding='utf8'))
                                time.sleep(8)
                                p.stdin.flush()

                            res1 = p.stdin.write(bytes('select ' + str(pendrive_disk) + ' \n', encoding='utf8'))
                            time.sleep(2)
                            p.stdin.flush()
                            res5 = p.stdin.write(
                                bytes("create partition primary SIZE=" + str(ntfs) + "\n", encoding='utf8'))
                            time.sleep(3)
                            p.stdin.flush()
                            res6 = p.stdin.write(bytes("FORMAT FS=NTFS Label=UsbWIMs QUICK \n", encoding='utf8'))
                            time.sleep(6)
                            p.stdin.flush()
                            res7 = p.stdin.write(bytes("assign letter=S\n", encoding='utf8'))
                            time.sleep(2)
                            p.stdin.flush()
                            res8 = p.stdin.write(bytes("active \n", encoding='utf8'))
                            time.sleep(2)
                            p.stdin.flush()
                            res6 = p.stdin.write(
                                bytes("create partition primary SIZE=" + str(fat_size) + " \n", encoding='utf8'))
                            time.sleep(3)
                            p.stdin.flush()
                            res6 = p.stdin.write(bytes("FORMAT FS=fat32 Label=WIMAGERUSB QUICK \n", encoding='utf8'))
                            time.sleep(6)
                            p.stdin.flush()
                            res7 = p.stdin.write(bytes("assign letter=H \n", encoding='utf8'))
                            time.sleep(2)
                            p.stdin.flush()
                            res8 = p.stdin.write(bytes("active \n", encoding='utf8'))
                            time.sleep(2)
                            p.stdin.flush()
                            res8 = p.stdin.write(bytes("exit \n", encoding='utf8'))
                            time.sleep(2)
                            p.stdin.flush()
                        # Downloading Wim-imager
                        # cwd = os.getcwd()
                        cwd = r"C:\os_package\wimimager.zip"
                        if (str(platform.architecture()).find("WindowsPE") != -1):
                            if not os.path.exists(cwd):
                                self._log.info("Wim_Imager Tool is Being Downloaded")
                                opt = subprocess.Popen(
                                    "curl -X GET " + str(self._curl_server) + "/files/wimimager.zip --output wimimager.zip",
                                    cwd=r"C:\os_package", stdin=PIPE, stdout=PIPE, stderr=STDOUT, shell=True)
                                opt = opt.stdout.read()
                                if (str(opt).find(r"100") != -1):
                                    self._log.info("Wim_Imager Tool Downloaded")
                                else:
                                    self._log.error("Curl_Server Down DOWNLAOD fAILED")
                            else:
                                self._log.info("Wim_Imager Tool already available in the folder -> '{}".format(cwd))
                        else:
                            print("NOT yet Implemented for Linux")
                        # Extracting Wim-Imager
                        self._log.info("Wim_Imager Tool Extraction To Pendrive In-Progress")
                        #cwd = os.getcwd()
                        cwd = r"C:\os_package"
                        if (str(platform.architecture()).find("WindowsPE") != -1):
                            path_to_zip_file = cwd + str("\wimimager.zip")
                            Target_path = "H:"
                            with zipfile.ZipFile(path_to_zip_file, 'r') as zip_ref:
                                zip_ref.extractall(Target_path)
                            self._log.info("Wim_Imager Tool Extraction To Pendrive Successfull")
                            return True
                        elif (str(platform.architecture()).find(r"ELF") != -1):
                            path_to_zip_file = cwd + str("/wimimager.zip")
                            Target_path = r"/home/pi/Desktop/linuxashost"
                            with zipfile.ZipFile(path_to_zip_file, 'r') as zip_ref:
                                zip_ref.extractall(Target_path)
                            self._log.info("Wim_Imager Tool Extraction To Pendrive Successfull")
                            return True
                    except Exception as ex:
                        self._log.error("Issues Encounterd While Formatting Pendrive: {0}".format(ex))
                        return False
                else:  # non-wimager that is normal usb flashing single drive
                    time.sleep(10)
                    try:
                        if six.PY3:
                            p = Popen(['diskpart'], stdin=PIPE)
                            res1 = p.stdin.write(bytes("list vol \n", encoding='utf8'))
                            time.sleep(4)
                            p.stdin.flush()
                            res1 = p.stdin.write(bytes("rescan \n", encoding='utf8'))
                            time.sleep(1)
                            p.stdin.flush()
                            res1 = p.stdin.write(bytes("list disk \n", encoding='utf8'))
                            time.sleep(1)
                            p.stdin.flush()
                            res1 = p.stdin.write(bytes("select " + str(pendrive_disk) + " \n", encoding='utf8'))
                            time.sleep(1)
                            p.stdin.flush()
                            try:
                                res4 = p.stdin.write(bytes("clean \n", encoding='utf8'))
                                time.sleep(5)
                                p.stdin.flush()
                            except:
                                res1 = p.stdin.write(bytes('rescan \n', encoding='utf8'))
                                time.sleep(3)
                                p.stdin.flush()
                                res1 = p.stdin.write(bytes('select ' + str(pendrive_disk) + ' \n', encoding='utf8'))
                                time.sleep(2)
                                p.stdin.flush()
                                res4 = p.stdin.write(bytes('clean \n', encoding='utf8'))
                                time.sleep(8)
                                p.stdin.flush()

                            res1 = p.stdin.write(bytes('select ' + str(pendrive_disk) + ' \n', encoding='utf8'))
                            time.sleep(2)
                            p.stdin.flush()
                            res5 = p.stdin.write(bytes("create partition primary \n", encoding='utf8'))
                            time.sleep(3)
                            p.stdin.flush()
                            res8 = p.stdin.write(bytes("FORMAT FS=FAT32 Label=OS QUICK \n", encoding='utf8'))
                            time.sleep(10)
                            p.stdin.flush()
                            res7 = p.stdin.write(bytes("assign letter=S \n", encoding='utf8'))
                            time.sleep(2)
                            p.stdin.flush()
                            res8 = p.stdin.write(bytes("active \n", encoding='utf8'))
                            time.sleep(2)
                            p.stdin.flush()
                            res8 = p.stdin.write(bytes("exit \n", encoding='utf8'))
                            time.sleep(2)
                            p.stdin.flush()
                            return True
                        elif six.PY2:
                            p = Popen(['diskpart'], stdin=PIPE)
                            res1 = p.stdin.write(b'list vol \n')
                            time.sleep(4)
                            p.stdin.flush()
                            res1 = p.stdin.write(b'rescan \n')
                            time.sleep(1)
                            p.stdin.flush()
                            res1 = p.stdin.write(b'list disk \n')
                            time.sleep(1)
                            p.stdin.flush()
                            res1 = p.stdin.write(b'select ' + str(pendrive_disk) + ' \n')
                            time.sleep(1)
                            p.stdin.flush()
                            try:
                                res4 = p.stdin.write(b'clean \n')
                                time.sleep(5)
                                p.stdin.flush()
                            except:
                                res4 = p.stdin.write(b'clean \n')
                                time.sleep(5)
                                p.stdin.flush()
                            res1 = p.stdin.write(b'rescan \n')
                            time.sleep(5)
                            p.stdin.flush()
                            res1 = p.stdin.write(b'rescan \n')
                            time.sleep(3)
                            p.stdin.flush()
                            res5 = p.stdin.write(b"create partition primary \n")
                            time.sleep(3)
                            p.stdin.flush()
                            res8 = p.stdin.write(b"FORMAT FS=FAT32 Label=OS QUICK \n")
                            time.sleep(10)
                            p.stdin.flush()
                            res7 = p.stdin.write(b"assign letter=S \n")
                            time.sleep(2)
                            p.stdin.flush()
                            res8 = p.stdin.write(b"active \n")
                            time.sleep(2)
                            p.stdin.flush()
                            res8 = p.stdin.write(b"exit \n")
                            time.sleep(2)
                            p.stdin.flush()
                            return True
                    except Exception as ex:
                        self._log.error("Issues Encounterd While Formatting Pendrive {0}".format(ex))
                        return False
            except Exception as ex:
                self._log.info("Runas Administrator Priveillage Needs To Be Given {0}".format(ex))
                return False
        elif (str(platform.architecture()).find(r"ELF") != -1):
            self._log.error("Not yet Implemented for LINUX Hostmachines")

    def download_extract_os_image(self, Extract=None, Format_usb=None):
        """
        :param Extract:
        :param Format_usb:
        :return True or False with Error
        This Function is to Download and Extract the Base OS IMage Into Pendrive For Os Installation.
         it has 3 methods Direct Artifactory Download, Offline Pre-Downloaded OS Image, OWR IDF Jenkins Trigger Support.
         it can be customized According to User Requirement.
        """
        if (self._initialize_os_pkg == True):
            if (self._direct_os_download == True):
                try:
                    self._log.info(
                        "Method -1 Direct Download Of OS Package From Artifactory Location Given By User{0}".format(
                            self._direct_os_img_path))
                    head, tail = ntpath.split(self._direct_os_img_path)
                    self._base_os_name = tail
                    self._log.info("OS PACKAGE NAME >>> {0} <<<".format(self._base_os_name))
                    subprocess.check_output("curl --silent -u " + str(self._atf_username) + ":" + str(
                        self._atf_password) + " -X GET " + str(self._direct_os_img_path) + " --output " + str(
                        self._base_os_name), shell=True)
                    time.sleep(5)
                except Exception as ex:
                    self._log.error(
                        "{0} Artifactory Path Is Not Given Properly and Please Check ATF Usernme {1} and Password {2}".format(
                            self._direct_os_img_path, self._atf_username, self._atf_password))
                    return False
            elif (self._usr_given_local_os_mode == True):  # for making use of already #pre downlaoded package
                try:
                    self._log.info("Method - 2 Pre-Downloaded OS in Local Machine Path Given By User {0}".format(
                        self._local_drive_os_pkg))
                    head, tail = ntpath.split(self._local_drive_os_pkg)
                    self._base_os_name = tail
                    self._ostype = "Linux"
                    self._log.info("OS PACKAGE NAME >>> {0} <<<".format(self._base_os_name))
                    if (self._ostype == "Linux"):
                        if (zipfile.is_zipfile(self._local_drive_os_pkg) == True):
                            self._log.info("This Is the location of Predownloaded Linux OS Package {0}".format(
                                self._local_drive_os_pkg))
                        elif (str(".wim") in self._base_os_name):
                            self._log.error(
                                "This is Windows Image change the --OSTYPE to windows, Mistached Image Given for OSTYPE")
                            return False
                        else:
                            self._log.error("Improper Download Check File Name Not a valid Format")
                            return False
                    elif (self._ostype == "ESXI"):
                        if (zipfile.is_zipfile(self._local_drive_os_pkg) == True):
                            self._log.info("This Is the location of Predownloaded ESXI OS Package {0}".format(
                                self._local_drive_os_pkg))
                        elif (str(".wim") in self._base_os_name):
                            self._log.error(
                                "This is Windows Image change the --OSTYPE to windows, Mistached Image Given for OSTYPE")
                            return False
                        else:
                            self._log.error("Improper Download Check File Name Not a valid Format")
                            return False
                    elif (self._ostype == "Windows_Wim"):
                        wim_size = os.stat(self._local_drive_os_pkg).st_size
                        if (str(wim_size) >= "3000000000"):
                            if (str(".wim") in self._local_drive_os_pkg):
                                self._log.info("This Is the location of Predownloaded Windows .wim Package {0}".format(
                                    self._local_drive_os_pkg))
                            else:
                                self._log.error("In-approprite Package Set for Different ostype, Change Accordingly")
                                return False
                        else:
                            self._log.error(
                                "In-approprite Package Set for Different ostype, Change Accordingly, This --OS_TYPE is Meant for .wim windows")
                            return False
                    else:
                        self._log.error("--OS_TYPE can Either be Linux or Windows or ESXI , Unknown OS Type Given")
                        return False
                except Exception as ex:
                    self._log.error(
                        "Path needs to given along with package_name eg:- c:\\xxx\\os_pkg.zip or opt//os_pkg.zip {0}".format(
                            ex))
                    return False
            else:  # owr based trigger
                self._log.error("OWR IDF Jenkins Trigger Support is not implemented for download os image")
                return False
            self._log.info("Verifying Downloaded OS Image")
            if (self._usr_given_local_os_mode == True):
                Dnd_img_path = self._local_drive_os_pkg
            else:
                cwd = os.getcwd()
                if (self._host == "windows_host"):
                    Dnd_img_path = cwd + "\\" + str(self._base_os_name)
                else:
                    Dnd_img_path = cwd + "//" + str(self._base_os_name)

            if (path.exists(Dnd_img_path) == True):
                if (self._ostype == "Linux"):
                    if (zipfile.is_zipfile(Dnd_img_path) == True):
                        self._log.info("Downloaded Image {0} Verified Successfull".format(Dnd_img_path))
                    else:
                        self._log.error(
                            "Downloaded File Is Not A ZIP Image File,Artifactory Path Is Not Given Properly and Please Check ATF Usernme and Password")
                        return False
                elif (self._ostype == "ESXI"):
                    if (zipfile.is_zipfile(Dnd_img_path) == True):
                        self._log.info("Downloaded Image {0} Verified Successfull".format(Dnd_img_path))
                    else:
                        self._log.error(
                            "Downloaded File Is Not A ZIP Image File,Artifactory Path Is Not Given Properly and Please Check ATF Usernme and Password")
                        return False
                elif (self._ostype == "Windows_Wim"):
                    wim_size = os.stat(Dnd_img_path).st_size
                    if (str(wim_size) >= "3000000000"):
                        if (str(".wim") in Dnd_img_path):
                            self._log.info(
                                "Downloaded Windows .wim Image {0} Verified Successfull ".format(Dnd_img_path))
                        else:
                            self._log.error(
                                "Failed, Downloaded Windows .wim Image {0} Failed To Verify ".format(Dnd_img_path))
                            return False
                    else:
                        self._log.error(
                            "Failed, Windows .wim Image Size is Below Expected Broken Image {0} Failed To Verify ".format(
                                Dnd_img_path))
                        return False
                else:
                    self._log.error("Unspecified OS Type")
                    return False
                if (Extract == True):
                    if (Format_usb == True):
                        if (self._ostype == "Windows_Wim"):
                            for i in range(0, 10):
                                ret_windows = self.format_usb_drive(self._usb_size, wim=True)
                                if (ret_windows == True):
                                    self._log.info(
                                        "USB Disk Partitioned Into two Partition Disk WITH FAT32 and NTFS format")
                                    self._log.info("USB Disk Partitioning Verification of S and H Drive")
                                    # create a file in S and H drive
                                    drive_file = [r"S:\s_drive.txt", r"H:\h_drive.txt"]
                                    usb_formatted_correct = []
                                    try:
                                        for drive_path in drive_file:
                                            with open(drive_path, "x") as fh:
                                                fh.write(drive_path)
                                                self._log.info("File has been created under {}..".format(drive_path))

                                            if os.path.exists(drive_path):
                                                usb_formatted_correct.append(True)
                                                os.remove(drive_path)
                                            else:
                                                usb_formatted_correct.append(False)
                                        if all(usb_formatted_correct):
                                            self._log.info(
                                                "Successfully verified USB Disk Partitioning of S and H Drive.. "
                                                "Proceeding further")
                                            break
                                    except:
                                        continue
                                elif(i>=2):
                                    return False
                                else:
                                    continue
                        elif (self._ostype == "Linux" or "ESXI"):
                            for i in range(0, 10):
                                ret_linux = self.format_usb_drive(self._usb_size)
                                if (ret_linux == True):
                                    self._log.info(
                                        "USB Disk Partioned Into One Single Partition Disk WITH FAT32 format")
                                    self._log.info("USB Disk Partitioning Verification of S Drive")
                                    # create a file in S drive
                                    drive_file = r"S:\s_drive.txt"
                                    try:
                                        with open(drive_file, "x") as fh:
                                            fh.write(drive_file)
                                            self._log.info("File has been created under {}..".format(drive_file))

                                        if os.path.exists(drive_file):
                                            os.remove(drive_file)
                                            self._log.info(
                                                "Successfully verified USB Disk Partitioning of S Drive.. "
                                                "Proceeding further")
                                            break
                                    except:
                                        continue
                                elif (i >= 2):
                                    return False
                                else:
                                    continue

                    self._log.info("OS Packages are about To Be Extracted and Copied To USB")
                    try:
                        if (self._ostype == "Linux"):
                            start = time.time()
                            print("start to extract {}".format(Dnd_img_path))
                            with zipfile.ZipFile(Dnd_img_path, 'r') as zip_ref:
                                zip_ref.extractall("S:")
                            end = time.time()
                            zip_extract = (abs(start - end))
                            zip_extract = ("{:05.2f}".format(zip_extract))
                            self._log.info(
                                "Base OS Image {0} Packages Extract To USB Successfull Time Taken >> {1} Seconds".format(
                                    self._base_os_name, zip_extract))
                            return True
                        elif (self._ostype == "ESXI"):
                            start = time.time()
                            print("start to extract {}".format(Dnd_img_path))
                            with zipfile.ZipFile(Dnd_img_path, 'r') as zip_ref:
                                zip_ref.extractall("S:")
                            end = time.time()
                            zip_extract = (abs(start - end))
                            zip_extract = ("{:05.2f}".format(zip_extract))
                            self._log.info(
                                "Base ESXI OS Image {0} Packages Extract To USB Successfull Time Taken >> {1} Seconds".format(
                                    self._base_os_name, zip_extract))
                            return True
                        elif (self._ostype == "Windows_Wim"):
                            if (self._host == "windows_host"):
                                start = time.time()
                                subprocess.check_output("echo Y|copy " + str(Dnd_img_path) + " S:", shell=True)
                                end = time.time()
                                wim_copy = (abs(start - end))
                                wim_copy = ("{:05.2f}".format(wim_copy))
                                #  Fix if more than one HDD connected, assigned drive letter accordingly.
                                no_of_ssds = self._os_pre_req_lib.get_ssd_names_config()

                                dict_ssds = {1: 'E', 2: 'F', 3: 'G', 4: 'H'}
                                if no_of_ssds == 0 or no_of_ssds is None:
                                    self._log.error("Failed to get the SSD information, reasons could be are listed "
                                                    "below, \n 1. Seems there are no SSDs connected to the SUT. \n "
                                                    "2. If Manual - SUT Inventory config file is not updated correctly"
                                                    "with all the connected information..\n "
                                                    "3. If Auto - ITP has failed to get the correct SSD information,"
                                                    "please check the ITP connection")
                                    raise RuntimeError

                                with open("H:\WimagerUsbCommands.xml", "r+") as f:
                                    text = f.read()
                                    try:
                                        text = re.sub("sample.wim",
                                                      r"{}:\\".format(dict_ssds[no_of_ssds]) + str(self._base_os_name),
                                                      text)
                                    except Exception as ex:
                                        self._log.error("Either there are no hard disk found or more than 4 hard disks"
                                                        "are connected, please connect only 4 or less and try again..")
                                        raise ex
                                    f.seek(0)
                                    f.write(text)
                                    f.truncate()
                                self._log.debug("Wim Name Change Confirmed In USB, For Auto-Install")
                                self._log.info(
                                    "OS Image-Kit {0} Packages Copy To USB Successfull Time Taken >> {1} Seconds".format(
                                        self._base_os_name, wim_copy))
                                return True
                            else:
                                self._log.debug("Not Yet Implemented for Linux HostMachine")
                    except  Exception as ex:
                        self._log.error("Error In OS Packages Extraction {0}".format(ex))
                        return False
                else:
                    self._log.info("Extract To USB and Format USB is Given False")
                    return True
            else:
                self._log.error("OS Image File is Not Getting Downloaded, Check Given Path Properly")
                return False
        else:
            self._log.info("Download OS Package Parameter is Given as False, OS Package Download Will not Happen")
            return True

    def automation_post_installation_enabler(self):
        if (os.path.isfile("S:\\" + str(self._rhel_cfg_file_name)) == True):
            print("This is RHEL OS")

            with open("S:\\" + str(self._rhel_cfg_file_name), 'r') as file:
                filedata = file.read()
                time.sleep(4)

            filedata = filedata.replace('firewall --disabled',
                                        'firewall --disabled' + "\n" + (
                                            "network  --bootproto=dhcp --device=enp1s0 --onboot=on --ipv6=auto") + "\n" + (
                                            "network  --bootproto=dhcp --device=enp2s0 --onboot=on --ipv6=auto") + "\n" + (
                                            "network  --bootproto=dhcp --device=enp3s0 --onboot=on --ipv6=auto") + "\n" + (
                                            "network  --bootproto=dhcp --device=enp4s0 --onboot=on --ipv6=auto")
                                        )
            filedata = filedata.replace("touch /etc/rc.d/postinstall.sh", "touch /etc/rc.d/postinstall.sh" + "\n" + (
                "ln -s /usr/bin/python3.6 /usr/bin/python"))
            with open("S:\\" + str(self._rhel_cfg_file_name), 'w', encoding="utf-8") as file1:
                file1.write(filedata)

            # replacement strings
            WINDOWS_LINE_ENDING = b'\r\n'
            UNIX_LINE_ENDING = b'\n'

            file_path = "S:\\" + str(self._rhel_cfg_file_name)

            with open(file_path, 'rb') as open_file:
                content = open_file.read()

            content = content.replace(WINDOWS_LINE_ENDING, UNIX_LINE_ENDING)

            with open(file_path, 'wb') as open_file:
                open_file.write(content)

        else:
            self._log.error("This Is Not Rhel8.2 OS")

        if (os.path.isfile("S:\\" + str(self._fedora_cfg_file_name)) == True):
            self._log.info("This is Fedora OS")
            opt = subprocess.Popen("curl -X GET " + str(self._curl_server) + "/files/" + str(
                self._fedora_cfg_file_name) + " --output " + str(self._fedora_cfg_file_name), stdin=PIPE, stdout=PIPE,
                                   stderr=STDOUT, shell=True)
            opt = opt.stdout.read()
            if (str(opt).find(r"100") != -1):
                self._log.info("Fedora Configuration File Downloaded")
            else:
                self._log.error("Failed To Download Fedora {0} From Curl {1} Server".format(self._fedora_cfg_file_name,
                                                                                            self._curl_server))
                return False
            cwd = os.getcwd()
            if (self._host == "windows_host"):
                subprocess.check_output(
                    "echo y | xcopy " + str(cwd) + "\\" + str(self._fedora_cfg_file_name) + " S:\\" + " /e", shell=True)
            else:
                subprocess.check_output("sudo mv " + str(cwd) + "//" + str(self._fedora_cfg_file_name) + " S://",
                                        shell=True)

        else:
            self._log.error("This Is Not Fedora OS")
        cwd = os.getcwd()
        if (self._ostype == "Linux"):
            try:
                opt = subprocess.Popen(
                    "curl -X GET " + str(self._curl_server) + "/files/xmlcli.zip --output xmlcli.zip",
                    stdin=PIPE, stdout=PIPE, stderr=STDOUT, shell=True)
                opt = opt.stdout.read()
                if (str(opt).find(r"100") != -1):
                    self._log.info("XMLCLI Tool Downloaded")
                else:
                    self._log.error("Failed To Download From Curl Server")
                    return False
                if (str(platform.architecture()).find("WindowsPE") != -1):
                    path_to_zip_file = cwd + str("\\xmlcli.zip")
                    Target_path = "S:\APP"
                    with zipfile.ZipFile(path_to_zip_file, 'r') as zip_ref:
                        zip_ref.extractall(Target_path)
                    self._log.info("XMLCLI Tool Extraction To Pendrive Successfull")
                    return True
                else:
                    self._log.error("Need To Code For lINUX Hostmachine Environment")
            except Exception as ex:
                self._log.error("Xmlcli Tool Failed To Download {0}".format(ex))
                return False
        elif (self._ostype == "ESXI"):
            self._log.error("Xmlcli Tool Can't Get Copied since It's An ESIX Image")
            return "Integrated_wim_image"
        else:
            self._log.error("Xmlcli Tool Can't Get Copied since It's An Integrated Image")
            return "Integrated_wim_image"

    def download_extract_sft_package(self, Extract=None, Format_usb=None):
        ##linux sft package download
        if (self._initialize_sft_pkg == True):
            self._log.info("Extracting_Package TO USB IS {0}".format(Extract))
            if (self._direct_sft_pkg_download == True):
                try:
                    self._log.info("Method-1 Direct Download Of Software Package From Artifactory {0}".format(
                        self._direct_sft_pkg_download))
                    self._log.info("This Is the location of Software Package Artifactory Location {0}".format(
                        self._direct_sft_img_path))
                    head, tail = ntpath.split(self._direct_sft_img_path)
                    self._stf_pkg_name = tail
                    self._log.info("SOFTWARE-KIT PACKAGE NAME >>> {0} <<<".format(self._stf_pkg_name))
                    subprocess.check_output(
                        "curl -u " + str(self._atf_username) + ":" + str(self._atf_password) + " -X GET " + str(
                            self._direct_sft_img_path) + " --output " + str(self._stf_pkg_name), shell=True)
                    self._log.info("Direct Download Of Software Package From Artifactory Successfull")
                except Exception as ex:
                    self._log.error(
                        "{0} Artifactory Path Is Not Given Properly and Please Check ATF Usernme {1} and Password {2} {3}".format(
                            self._direct_sft_img_path, self._atf_username, self._atf_password, ex))
                    return False
            elif (self._usr_given_local_sft_mode == True):  # for making usee of already #pre downloaded package
                try:
                    self._log.info("Method-2 Pre-Downloaded Software Package in Local Machine {0}".format(
                        self._local_drive_sft_pkg))
                    head, tail = ntpath.split(self._local_drive_sft_pkg)
                    self._stf_pkg_name = tail
                    self._log.info("SOFTWARE-KIT PACKAGE NAME >>> {0} <<<".format(self._stf_pkg_name))
                    if (zipfile.is_zipfile(self._local_drive_sft_pkg) == True):
                        self._log.info("This Is the location of Predownloaded Software Package {0}".format(
                            self._local_drive_sft_pkg))
                    else:
                        self._log.error("File Name IS Not Correct")
                        return False
                except Exception as ex:
                    self._log.error(
                        "Path needs to given along with package_name eg:- c:\\xxx\\sft_pkg.zip or opt//sft_pkg.zip {0}".format(
                            ex))
                    return False
            else:
                self._log.error("Method -3 OWR Triggerd and Downloaded Software Package FROM Artifactory is not "
                               "implemented")
                return False
            if (self._usr_given_local_sft_mode == True):
                Dnd_sft_path = self._local_drive_sft_pkg
            else:
                cwd = os.getcwd()
                if (self._host == "windows_host"):
                    Dnd_sft_path = cwd + "\\" + str(self._stf_pkg_name)
                else:  # linus host
                    Dnd_sft_path = cwd + "//" + str(self._stf_pkg_name)
            head, tail = ntpath.split(Dnd_sft_path)
            pkg_name = tail
            self._log.info("Path Of Software Package {0}".format(Dnd_sft_path))
            if (path.exists(Dnd_sft_path) == True):
                if (zipfile.is_zipfile(Dnd_sft_path) == True):
                    self._log.info("Verified Software Package {0} Verification Successfull".format(pkg_name))
                else:
                    self._log.error(
                        "{0} File Is Not A Proper ZIP Image File,Package {1} Artifactory Path Is Not Given Properly and Please Check ATF Usernme {2} and Password {3}".format(
                            pkg_name, Dnd_sft_path, self._atf_username, self._atf_password))
                    return False
                if (Extract == True):
                    self._log.info("Software Packages are about To Be Extracted and Copied To USB")
                    try:
                        self._log.info("Software Package {0}".format(Dnd_sft_path))
                        with zipfile.ZipFile(Dnd_sft_path, 'r') as zip_ref:
                            zip_ref.extractall("S:")
                        self._log.info("Software {0} Packages Extraction To USB Successfull".format(Dnd_sft_path))
                        ret = self.automation_post_installation_enabler()
                        if (ret in [True, "Integrated_wim_image"]):
                            return True
                        else:
                            return False
                    except  Exception as ex:
                        self._log.error("Error In Software Packages Extraction {0}".format(ex))
                        return False
                else:
                    self._log.info(
                        "Software Package Extract To USB is set has False Only Downloaded The Software Package")
            else:
                self._log.error("Software Package is Not Getting Downloaded check, Given Path Properly")
                return False
        else:
            self._log.info(
                "Download Software Package Parameter is Given as False, Software Package Download Will not Happen")
            return True

    def platform_ac_power_off(self):

        if self._ac.ac_power_off() == True:
            self._log.info("Platform(SUT) AC-power TURNED OFF")
        else:
            self._log.error("Failed TO Do AC-power OFF")
            return False
        # Making Sure Platform AC-Power is Turned OFF
        if self._ac.get_ac_power_state() == False:
            self._log.info("Platform(SUT) AC-power TURNED-OFF Confirmed")
            time.sleep(3)
            return True
        else:
            self._log.error("Platform(SUT) AC-power TURNED-Off Confirmation failed")
            return False

    def platform_ac_power_on(self):
        if self._ac.ac_power_on() == True:
            self._log.info("Platfor(SUT) AC-power TURNED ON")
        else:
            self._log.error("Failed TO Do AC-power ON")
            return False
        time.sleep(4)
        if self._ac.get_ac_power_state() == True:
            self._log.info("Platform(SUT) AC-power TURNED-ON Confirmed")
            # time.sleep(2)
            return True
        else:
            self._log.error("Failed To Platform(SUT) AC-power TURNED-Off Confirmation")
            return False

    def switch_usb_to_target(self):  # changed
        if (self._phy.connect_usb_to_sut() != True):
            self._log.error("USB Switching To SUT Failed")
            return False
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
                ret = self.setupmenu.select(str(path[i]), None, 60, True)
                print(self.setupmenu.get_selected_item().return_code)
                self.setupmenu.enter_selected_item(10, False)
                self._log.info("Entered into {0} ".format(path[i]))
            return True
        except Exception as ex:
            self._log.error("{0} Issues Observed".format(ex))
            return False

    def enter_into_bios(self):
        if self.setupmenu.wait_for_entry_menu(1000):
            for i in range(0, 3):
                f2_state = self.setupmenu.press(r'F2')
                time.sleep(0.3)
                if f2_state:
                    self._log.info("Entry Menu Detected")
                    break
            ret = self.setupmenu.wait_for_bios_setup_menu(30)
            self._log.info("Entered Into Bios Menu")
            return True
        else:
            self._log.error("Failed To Enter Into Bios Menu Page,Close COM Port if opened in Putty")
            return False

    @property
    def extract_os_package(self):
        return self._extract_os_package

    @property
    def format_pendrive(self):
        return self._format_pendrive

    @property
    def os_install(self):
        return self._os_install

    @property
    def extract_sft_package(self):
        return self._extract_sft_package

    @property
    def usb_drive_name(self):
        return self._usb_drive_name

    @property
    def bios_path(self):
        return self._bios_path

    @property
    def hardisk_drive_name(self):
        return self._hardisk_drive_name

    @property
    def save_knob_name(self):
        return self._save_knob_name

    @property
    def boot_select_uefi_path(self):
        return self._boot_select_uefi_path
