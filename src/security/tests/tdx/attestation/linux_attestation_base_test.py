#!/usr/bin/env python
##########################################################################
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
##########################################################################
"""
    :TDX Attestation Base Test:

    Launch a TD guest and successfully run a quote.
"""
import sys
import os

from dtaf_core.lib.dtaf_constants import Framework
from src.lib import content_exceptions
from src.security.tests.tdx.tdx_common_linux import LinuxTdxBaseTest
from src.security.tests.sgx.sgx_registration.sgx_registration_common import SgxRegistrationCommon


class TdAttestation(LinuxTdxBaseTest):
    """
           This is a base test for workload testing with TD guests as part of the TDX feature.

           The following parameters in the content_configuration.xml file should be populated before running a test.

            Change <TDX><num_of_vms> to control the number of TD guests that will be run in parallel.
            Each test will have its own parameter to adjust for run time; this should be explained in the individual
            test case.

            :Scenario: Launch the number of TD guests prescribed, initiate the workload on each TD guest, run for the
            necessary time to complete the tests, then verify the SUT and the TD guests have not crashed.

            :Phoenix IDs:

            :Test steps:

                :1: Launch a TD guest.

                :2: On TD guest, launch a stress suite or workload.

                :3: Repeat steps 1 and 2 for the prescribed number of TD guests.

                :4: Run until workload tests complete.

            :Expected results: Each TD guest should boot and the workload suite should run to completion with no
            errors on the SUT or any of the TD guests.

            :Reported and fixed bugs:

            :Test functions:

        """

    def __init__(self, test_log, arguments, cfg_opts):
        """Create an instance of test case.

        :param cfg_opts: Configuration Object of provider
        :type cfg_opts: str
        :param test_log: Log object
        :type arguments: Namespace
        :param arguments: None
        :type cfg_opts: Namespace
        :return: None
        """
        super(TdAttestation, self).__init__(test_log, arguments, cfg_opts)
        self.attestation_path = ""
        self.expect_install_pccs_script = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                       "../collateral/expect_pccs_install.sh")
        self.working_directory = "/tmp/attestation/"
        self.mp_bios_knob = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../collateral/mp_bios_knob.cfg")
        self.ATTESTATION_SERVER = arguments.ATTESTATION_SERVER.upper()

    @classmethod
    def add_arguments(cls, parser):
        """
        :param parser: argument parser
        :return: None
        """
        super(TdAttestation, cls).add_arguments(parser)
        parser.add_argument("--server", "--s", action="store", dest="ATTESTATION_SERVER", default="SBX")

    def prepare(self):
        self.os_preparation()
        self.tdx_properties[self.tdx_consts.DAM_ENABLE] = False  # DAM must be disabled to test attestation
        bios_knobs = list()
        bios_knobs.append(self.mp_bios_knob)
        self._log.debug(f"Configuring BIOS knobs for registration server {self.ATTESTATION_SERVER.upper()}.")
        server_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   f"../collateral/{self.ATTESTATION_SERVER.lower()}_attestation_server.cfg")

        bios_knobs.append(server_file)
        bios_knob_file = self.bios_file_builder(bios_knobs)
        self.check_knobs(knob_file=bios_knob_file, set_on_fail=True, reboot_on_knob_set=True)
        if not self.production_ucode():
            raise content_exceptions.TestSetupError("IFWI on platform does not contain production signed ucode.")
        self.install_collateral.yum_install("yum-utils")
        self.execute_os_cmd(f"mkdir -p {self.working_directory}")
        self.install_dcap()
        self.install_pccs()
        self.install_attestation_script()
        super(TdAttestation, self).prepare()

    def execute(self):
        return self.run_attestation_check()

    def production_ucode(self) -> bool:
        """Check if ucode in programmed IFWI is production signed.
        :return: True if ucode is production signed, False if ucode is not production signed."""
        ucode_register = self.msr_read(self.tdx_consts.RegisterConstants.UCODE_SIGNING)
        return not self.bit_util.is_bit_set(ucode_register, self.tdx_consts.UcodeSigningMsrBit.UCODE_PROD_BIT)

    def install_pccs(self):
        """Install pccs."""
        self.execute_os_cmd("dnf install -y --setopt=install_weak_deps=False --nogpgcheck sgx-dcap-pccs.x86_64")
        temp_file = "pccs_install.sh"
        with open(self.expect_install_pccs_script) as in_file:
            with open(temp_file, "w") as out_file:
                data = in_file.read()
                data = data.format(self.command_timeout,
                                   "sudo -u pccs /opt/intel/sgx-dcap-pccs/install.sh",
                                   self.tdx_properties[self.tdx_consts.SBX_API_KEY],
                                   self.tdx_properties[self.tdx_consts.PCCS_PWD],
                                   self.tdx_properties[self.tdx_consts.PCCS_PWD],
                                   self.tdx_properties[self.tdx_consts.PCCS_PWD],
                                   self.tdx_properties[self.tdx_consts.PCCS_PWD])
                out_file.write(data)
        self.os.copy_local_file_to_sut(temp_file, self.working_directory)
        script_path = self.working_directory + temp_file
        os.remove(temp_file)
        self.os.execute("dos2unix {}".format(script_path), self.command_timeout)
        self.os.execute("chmod +x {}".format(script_path), self.command_timeout)
        self.execute_os_cmd(script_path)  # run expect script to install PCCS
        if self.ATTESTATION_SERVER == self.tdx_consts.AttestationServers.SBX:
            self.execute_os_cmd("sed -i 's|/api|/sbx.api|g' /opt/intel/sgx-dcap-pccs/config/default.json")
        self.execute_os_cmd("systemctl start pccs")
        if self.execute_os_cmd("systemctl status pccs | grep \"active (running)\"") == "":
            raise content_exceptions.TestSetupError("PCCS service failed to start.")
        if "Started Provisioning Certificate Caching Service (PCCS)" in self.execute_os_cmd("journalctl -u pccs | cat"):
            self._log.debug("PCCS service appears to have no errors.")
        else:
            content_exceptions.TestSetupError("PCCS service doesn't appear to have started.")

    def install_dcap(self):
        """Install dcap package."""
        attestation_file = self.tdx_properties[self.tdx_consts.ATTESTATION_STACK].split("/")[-1]
        self.os.copy_local_file_to_sut(self.tdx_properties[self.tdx_consts.ATTESTATION_STACK], self.working_directory +
                                       attestation_file)
        attestation_file_path = self.working_directory + attestation_file
        self.attestation_path = attestation_file_path.rsplit(".", 1)[0]  # get rid of file extension
        self.execute_os_cmd(f"unzip -o {attestation_file_path} -d {self.attestation_path}")  # decompress attestation stack, overwrite old files
        if not self.os.check_if_path_exists(self.attestation_path, directory=True):
            raise content_exceptions.TestFail(f"Could not find downloaded attestation stack at expected location.  "
                                              f"Verify {self.tdx_consts.ATTESTATION_STACK} in content_configuration.xml"
                                              f" file exists.")
        self.execute_os_cmd(f"tar -xzf {self.attestation_path}/Installer/sgx_rpm_local_repo.tgz --directory "
                            f"{self.attestation_path}/Installer")
        self.execute_os_cmd(f"yum-config-manager --add-repo "
                            f"file://{self.attestation_path}/Installer/sgx_rpm_local_repo/")

    def install_attestation_script(self) -> str:
        """Install attestation e2e verification script.
        :return: file path on SUT for e2e verification script."""
        file_name = self.tdx_properties[self.tdx_consts.E2E_SCRIPT_LOCATION].rsplit("/", 1)[1]
        self.os.copy_local_file_to_sut(self.tdx_properties[self.tdx_consts.E2E_SCRIPT_LOCATION], self.working_directory)
        if not self.os.check_if_path_exists(self.working_directory + file_name):
            raise content_exceptions.TestSetupError(f"Failed to copy e2e script to SUT.  Looked in "
                                                    f"{self.working_directory + file_name}.")
        self.execute_os_cmd(f"cd {self.working_directory}; tar -xvf {file_name}")
        path_to_attestation_script = self.execute_os_cmd(f"find {self.working_directory} -name "
                                                         f"\'{file_name.rsplit('.', 2)[0]}\'")
        return path_to_attestation_script

    def run_attestation_check(self, log_file_name: str = None) -> bool:
        """Run attestation e2e script.
        :param log_file_name: name of log file for attestation verification.
        :return: True if attestation passes verification checks."""
        if log_file_name is None:
            log_file_name = "attestation_log.log"
        path = self.execute_os_cmd(f"find {self.working_directory} -name \'e2e-test.sh\'")
        self.execute_os_cmd(
            f"sed -i 's/123intel/{self.tdx_properties[self.tdx_consts.PCCS_PWD]}/g' "
            f"{path}")  # replace default weak password with pccs password
        output = self.execute_os_cmd(f"cd {path.rsplit('/', 1)[0]}; {path} 2>&1 | tee {log_file_name}")
        errors = True if "No errors were found" in output else False
        self._log.debug(f"Output of attestation script:\n{output}")
        if not errors:  # need to find this string to know attestation passed
            raise content_exceptions.TestFail("Attestation log file indicates an error has been found.  Please refer "
                                              "to log file.")
        self._log.debug("Attestation check has passed.")
        log_path = self.execute_os_cmd(f"find {self.working_directory} -name \'{log_file_name}\'")
        self.os.copy_file_from_sut_to_local(log_path, f"{self.log_dir}/{log_file_name}")
        self.execute_os_cmd(f"rm -f {log_path}")
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TdAttestation.main() else Framework.TEST_RESULT_FAIL)
