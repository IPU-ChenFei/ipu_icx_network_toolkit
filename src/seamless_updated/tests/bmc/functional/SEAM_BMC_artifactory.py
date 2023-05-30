import sys
import subprocess
from os import path
import zipfile
import ntpath
import shutil
import py7zr

from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.lib.dtaf_constants import Framework
from src.seamless.lib.seamless_common import SeamlessBaseTest
from xml.etree import ElementTree as ET
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider
from src.lib.common_content_lib import CommonContentLib


class SeamlessArtifactory(BaseTestCase):
    PLATFORM_CPU_FAMILY = r"suts/sut/silicon/cpu"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Command example:
        for seamless:
        python3 src\seamless\tests\bmc\functional\artifactory.py
        --stf_pkg_path BIOSCapsule/ProductionBIOSUpdateCapsule/OOB_ProductionBIOSUpdateCapsule_20P06_20P09.zip
        --stf_pkg_path2 IBUcodeCapsule/Production%20Microcode%20Capsule/IB_ProductionUcodeUpdateCapsule_0x170_0x1b2_0x1e0.zip
        --stf_pkg_path3 SPSCapsule/OOB_SPSUpdateCapsule_03.263_03.278.zip
        --stf_pkg_path4 UcodeCapsule/Production%20Microcode%20Capsule/OOB_ProductionUcodeUpdateCapsule_0x170_0x1b2_0x1e0.zip

        For EGS:
        python3 src\seamless\tests\bmc\functional\artifactory.py
        --stf_pkg_path 2021.25.2.04/IFWI/2021.25.2.04(5833_A13)_OOB_Update_Capsule.7z
        """
        super(SeamlessArtifactory, self).__init__(test_log, arguments, cfg_opts)
        self.stf_pkg_path = arguments.stf_pkg_path
        self.stf_pkg_path2 = arguments.stf_pkg_path2
        self.stf_pkg_path3 = arguments.stf_pkg_path3
        self.stf_pkg_path4 = arguments.stf_pkg_path4
        self.domain = arguments.domain
        self.stf_pkg_name = self.stf_pkg_path.split("/")[-1]
        self.stf_pkg_name2 = self.stf_pkg_path2.split("/")[-1]
        self.stf_pkg_name3 = self.stf_pkg_path3.split("/")[-1]
        self.stf_pkg_name4 = self.stf_pkg_path4.split("/")[-1]
        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self.os = ProviderFactory.create(sut_os_cfg, test_log)
        self._common_content_lib = CommonContentLib(self._log, self.os, cfg_opts)
        default_system_config_file = self._common_content_lib.get_system_configuration_file()
        self._log.info("default_system_config_file {}".format(default_system_config_file))
        root = ET.parse(default_system_config_file).getroot()
        product_root = root.find(self.PLATFORM_CPU_FAMILY)
        self._product = product_root.find(r"family").text.strip()


        if self._product == "WHT":
            self.ARTIFACTORY_PATH = "https://ubit-artifactory-sh.intel.com/artifactory/DEG-IFWI-LOCAL/" \
                               "SiEn-Whitley-SeamlessUpdate/CapsuleFile/"
        elif self._product == "EGS":
            self.ARTIFACTORY_PATH = "https://ubit-artifactory-sh.intel.com/artifactory/DEG-IFWI-LOCAL/" \
                                    "SiEn-EagleStream_Sapphire_Rapids/IFWI/Orange/"

        self.LOCAL_HOST_PATH = "C:\\artifactory\\"

    @classmethod
    def add_arguments(cls, parser):
        super(SeamlessArtifactory, cls).add_arguments(parser)
        parser.add_argument('--domain', action='store', help="name of the seamless domain", default="")
        parser.add_argument('--stf_pkg_path', action='store', help="Path of the capsule package with extension", default="")
        parser.add_argument('--stf_pkg_path2', action='store', help="Path of the capsule package2 with extension", default="")
        parser.add_argument('--stf_pkg_path3', action='store', help="Path of the capsule3 package3 with extension", default="")
        parser.add_argument('--stf_pkg_path4', action='store', help="Path of the capsule4 package4 with extension", default="")

    def download(self, local_path, sft_full_path):
        try:
            self._log.info("curl -X GET " + str(
                sft_full_path) + " --output " + str(local_path))
            subprocess.check_output(
                "curl -X GET " + str(
                    sft_full_path) + " --output " + str(local_path), shell=True)
        except Exception as e:
            self._log.error("Download Failed from the location {0} {1}".format(self.sft_full_path, e))
            return False
        return True

    def file_unzip(self, local_path, pkg_name):
        try:
            head, tail = ntpath.split(local_path)
            self._log.info("head {} tail {}".format(head, tail))
            if(".zip" in pkg_name):
                with zipfile.ZipFile(local_path, 'r') as zip_ref:
                    zip_ref.extractall(self.LOCAL_HOST_PATH)
                    self._log.info("Unzipping is Successfull")
            elif(".7z" in pkg_name):
                with py7zr.SevenZipFile(local_path, 'r') as zip_ref:
                    zip_ref.extractall(self.LOCAL_HOST_PATH)
                    self._log.info("Unzipping is Successfull")
        except Exception as e:
            self._log.error("Unzipping of the file {0} Failed {1}".format(self.local_path, e))
            return False
        return True

    def execute(self):
        if path.exists(self.LOCAL_HOST_PATH):
            shutil.rmtree(self.LOCAL_HOST_PATH)
            subprocess.check_output("mkdir " + self.LOCAL_HOST_PATH, shell=True)
        else:
            subprocess.check_output("mkdir " + self.LOCAL_HOST_PATH, shell=True)
        result = False

        try:
            if self._product == "EGS":
                self.local_path = self.LOCAL_HOST_PATH + self.stf_pkg_name
                self.sft_full_path = self.ARTIFACTORY_PATH + self.stf_pkg_path
                pkg1 = self.download(self.local_path, self.sft_full_path)
                if pkg1:
                    res1 = self.file_unzip(self.local_path, self.stf_pkg_name)
                else:
                    self._log.error("Downloading of the file {} is Failed".format(self.stf_pkg_name))
                    return False

                if res1:
                    result = True
                if pkg1:
                    resut = True
                else:
                    result = False
            elif self._product == "WHT":
                self.local_path = self.LOCAL_HOST_PATH + self.stf_pkg_name
                self.sft_full_path = self.ARTIFACTORY_PATH + self.stf_pkg_path
                print(self.stf_pkg_name)
                pkg1 = self.download(self.local_path, self.sft_full_path)
                if pkg1:
                    res1 = self.file_unzip(self.local_path,self.stf_pkg_name)
                else:
                    self._log.error("Downloading of the file {} is Failed".format(self.stf_pkg_name))
                    return False
                self.local_path = self.LOCAL_HOST_PATH + self.stf_pkg_name2
                self.sft_full_path = self.ARTIFACTORY_PATH + self.stf_pkg_path2
                pkg2 = self.download(self.local_path, self.sft_full_path)
                if pkg2:
                    res2 = self.file_unzip(self.local_path,self.stf_pkg_name2)
                else:
                    self._log.error("Downloading of the file {} is Failed".format(self.stf_pkg_name2))
                    return False
                self.local_path = self.LOCAL_HOST_PATH + self.stf_pkg_name3
                self.sft_full_path = self.ARTIFACTORY_PATH + self.stf_pkg_path3
                pkg3 = self.download(self.local_path, self.sft_full_path)
                if pkg3:
                    res3 = self.file_unzip(self.local_path,self.stf_pkg_name3)
                else:
                    self._log.error("Downloading of the file {} is Failed".format(self.stf_pkg_name3))
                    return False
                self.local_path = self.LOCAL_HOST_PATH + self.stf_pkg_name4
                self.sft_full_path = self.ARTIFACTORY_PATH + self.stf_pkg_path4
                pkg4 = self.download(self.local_path, self.sft_full_path)
                if pkg4:
                    res4 = self.file_unzip(self.local_path,self.stf_pkg_name4)
                else:
                    self._log.error("Downloading of the file {} is Failed".format(self.stf_pkg_name4))
                    return False

                if res1 and res2 and res3 and res4:
                    result = True
                else:
                    result = False
        except Exception as ex:
            self._log.error("Downloading of the capsule Failed {0}".format(ex))
            return False

        return result


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SeamlessArtifactory.main() else Framework.TEST_RESULT_FAIL)
