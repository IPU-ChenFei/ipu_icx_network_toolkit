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
import time
from src.lib.common_content_lib import CommonContentLib
from src.ras.lib.ras_einj_common import RasEinjCommon


class RasNvmeUtils(RasEinjCommon):
    """
    Common NVMe functions useful for eDPC and general tests
    """
    OS_DISK_CMD_EXECUTE_TIMEOUT_IN_SEC = 30
    _POST_UCE_RETRY_DELAY_IN_SEC = 600

    def __init__(self, log, os, cfg_opts, common_content_configuration):
        self._common_content_lib = CommonContentLib(log, os, cfg_opts)
        super(RasNvmeUtils, self).__init__(log, os, self._common_content_lib, common_content_configuration)
        self._log = log
        self._os = os

    def run_bonnie_disk_traffic(self, numa_node, count, partition):
        """
        Start a Bonnie++ session to the nvme
        :param numa_node: The numa node to membind bonnie++ to
        :param count: the number of iterations of the bonnie++ test to run, in general, pass in same parameter as einj
        method is using
        :param partition: The NVMe partition to target with Bonnie++
        """
        self._log.info('Execute the Bonnie++ command')
        linux_bonnie_cmd = 'bonnie++ -u root -d /mnt/{}/ -n 1024 -r 8192 -x {}'.format(partition, count)
        self._os.execute_async("numactl --membind={} {}".format(numa_node, linux_bonnie_cmd), cwd='', ps_name='Bonnie')

    def check_nvme_traffic_is_running(self, partition, uncorrectable=False):
        """
        Check after injection to see if the NVMe mount point is still being r/w to.
        :param partition: OS nvme device partition name to check for traffic
        :param uncorrectable: Flags whether the injection type is uncorrectable, default set to false.
        :return: void
        """

        device = partition[:-2]  # device name for sar is partition name minus the last 2 partition ID characters

        packsec_aggregate = 1
        self._log.info("Aggregating traffic measurements over the next 60 seconds")
        for pack in range(10):
            packsec_value = self.get_nvme_traffic(device)
            packsec_aggregate += packsec_value
            time.sleep(6)  # wait time between checks
            print("Checks left ", (10 - pack), "Current aggregate total ", packsec_aggregate)

        expected_min_pac_sec = 100
        if float(packsec_aggregate) < expected_min_pac_sec:
            self._log.error("Traffic may have failed, waiting 60 seconds and re-checking")
            time.sleep(60)  # wait 60 seconds before retying
            packsec_value = self.get_nvme_traffic(device)
            self._log.info("This is the re-check packets per second value {}".format(packsec_value))

        if float(packsec_aggregate) < expected_min_pac_sec:
            self._log.error("Traffic has failed")
            if uncorrectable:
                self._log.info("Pausing {} minutes after uncorrectable non-fatal error".format
                               (float(self._POST_UCE_RETRY_DELAY_IN_SEC / 60)))
                time.sleep(float(self._POST_UCE_RETRY_DELAY_IN_SEC))
                if float(packsec_aggregate) < expected_min_pac_sec:
                    self._log.error("Traffic has failed")
                    return False
            return False
        else:
            self._log.info("Traffic appears to have continued after EINJ")
            return True

    def get_nvme_traffic(self, device):
        """
        Get traffic r/w status for the NVMe device using sar and prepare several variables used
        Helper for check_nvme_traffic_is_running method which calls this method multiple times
        :param device: device name as it appears in sar
        :param sartype: a string supplied by the check_sar_type function used to determines whether to use -p with sar
        :return:
        """

        if not self.check_sar_type_old():
            traffic_status = self._os.execute("sar -d 1 1 | grep {}".format(device),
                                              self.OS_DISK_CMD_EXECUTE_TIMEOUT_IN_SEC)
        else:
            traffic_status = self._os.execute("sar -d -p 1 1 | grep {}".format(device),
                                              self.OS_DISK_CMD_EXECUTE_TIMEOUT_IN_SEC)

        packets_sec = traffic_status.stdout.split()
        dev_index = packets_sec.index('{}'.format(device))
        packsec_value = float(packets_sec[(int(dev_index + 1))])
        self._log.info("these are the packets/sec {}".format(packsec_value))
        return packsec_value

    def run_ptu(self, ptu_runtime_in_sec):
        """
        Send an OS command to start the PTU program
        :param self:
        :param ptu_runtime_in_sec: Time in seconds to run PTU
        :return: none
        """
        self._os.execute_async(cmd="/ptu/ptu -y -ct 3 -t {}".format(ptu_runtime_in_sec), cwd='', ps_name='PTU')

    def check_running_stress(self):
        """
        Check to see if the requested stress programs are running before the test methods start.
        :param self: self
        :return: Bool.
        """
        stress_status = self._os.execute("screen -ls", self.OS_DISK_CMD_EXECUTE_TIMEOUT_IN_SEC)

        stress_list = stress_status.stdout
        status_bonnie = stress_list.find('.Bonnie')
        status_ptu = stress_list.find('.PTU')
        self._log.info("These are the running stress programs: {}".format(stress_status.stdout))
        if status_bonnie == -1 or status_ptu == -1:
            self._log.info("One or more stress programs failed to start")
            return False
        return True

    def inject_pcie_uncorrectable_errors(self, count, partition, post_uce_inj_wait_secs, edpc_en=True):
        """
        Call the functions of the ras_einj_obj object to perform <count> PCIE uncorrectable error injections
        :param self: self
        :param count: The number of requested error injections
        :param partition: the name of the diskdev representing the partition mounted at /mnt
        :param post_uce_inj_wait_secs: How long to wait in seconds after a UCE-NF error injection
        :param edpc_en: boolean for whether eDPC is set in the BIOS, Needed for cases where signalling changes
        :return: Boolean indicating successful error(s) injection and verification(s)
        """

        for i in range(int(count)):
            if edpc_en:
                inject_and_check_success = self.einj_inject_and_check(
                        error_type=self.EINJ_PCIE_UNCORRECTABLE_NONFATAL, edpc_en=True)
            else:
                inject_and_check_success = self.einj_inject_and_check(
                        error_type=self.EINJ_PCIE_UNCORRECTABLE_NONFATAL, edpc_en=False)
            if not inject_and_check_success:
                return False

            # call a program to verify traffic still running, which is why einj is looped here instead of using the
            # einj_inject_and_check object's "loops count" parameter.
            self.check_nvme_traffic_is_running(partition, uncorrectable=True)
            self._log.info(
                "Pausing {} secs after injection # {} of {}".format(post_uce_inj_wait_secs, i + 1, count))
            time.sleep(float(post_uce_inj_wait_secs))
        return True

    def inject_pcie_correctable_errors(self, count, partition,  post_ce_inj_wait_secs):
        """
        Call the functions of the ras_einj_obj object to perform <count> PCIE correctable error injections

        :param self: self
        :param count: The number of requested error injections
        :param partition: the name of the diskdev representing the partition mounted at /mnt
        :param post_ce_inj_wait_secs: How long to wait in seconds after a CE error injection
        :return: Boolean indicating successful error(s) injection and verification(s)
        """
        for i in range(int(count)):
            if not self.einj_inject_and_check(error_type=self.EINJ_PCIE_CORRECTABLE):
                return False
            # call a program to verify traffic still running, which is why einj is looped here instead of using the
            # einj_inject_and_check object's "loops count" parameter.
            if not self.check_nvme_traffic_is_running(partition):
                return False
            self._log.info(
                "Pausing {} secs after injection # {} of {}".format(post_ce_inj_wait_secs, i + 1, count))
            time.sleep(float(post_ce_inj_wait_secs))

        return True

    def prepare_os_for_nvme_test(self, disk_dev, mount_point):
        """
        Create a mount point for bonnie++ and set auditctl logging to off to keep test logs compact.
        :param disk_dev: The device partition in /dev to mount for testing
        :param mount_point: The filesystem point to mount disk_dev e.g. /dev/nvm0n1p1
        :param self: self
        :return: void
        """
        self._os.execute('auditctl -e 0', self.OS_DISK_CMD_EXECUTE_TIMEOUT_IN_SEC)
        if not self.check_test_dir_exist(mount_point):
            self._os.execute('mkdir /mnt/{}'.format(mount_point), self.OS_DISK_CMD_EXECUTE_TIMEOUT_IN_SEC)
            self._log.info('no mount dir')

        self._os.execute('mount /dev/{} /mnt/{}'.format(disk_dev, mount_point),
                         self.OS_DISK_CMD_EXECUTE_TIMEOUT_IN_SEC)

    def check_test_dir_exist(self, mount_point):
        """
        Check to see if the working dir for bonnie++ is created
        :param mount_point: The desired directory to mount
        """
        self._os.execute('ls /mnt/ | grep {}'.format(mount_point), self.OS_DISK_CMD_EXECUTE_TIMEOUT_IN_SEC)

    def check_sar_type_old(self):
        """
        Check for old sar which needs the -p switch or new sar which changes the position of the "DEV" column with -p
        :return: string type with value 'oldsar' or 'newsar' as appropriate
        """
        sar_ver = self._os.execute("sar -d -p 1 1 | grep -i DEV", self.OS_DISK_CMD_EXECUTE_TIMEOUT_IN_SEC)
        dev = 'DEV'
        position = sar_ver.stdout.split().index(dev)
        return position == 2  # Old version of SAR

    def verify_test_req_progs_installed_on_sut(self):
        """
        Check system for required programs
        :param self: self
        :return: Bool
        """

        self._log.info("checking for required programs")
        bonnie_installed = self._os.execute('which bonnie++', self.OS_DISK_CMD_EXECUTE_TIMEOUT_IN_SEC)
        ptu_installed = self._os.execute('ls / | grep ptu', self.OS_DISK_CMD_EXECUTE_TIMEOUT_IN_SEC)
        numactl_installed = self._os.execute('which numastat', self.OS_DISK_CMD_EXECUTE_TIMEOUT_IN_SEC)
        sysstat_installed = self._os.execute('which sar', self.OS_DISK_CMD_EXECUTE_TIMEOUT_IN_SEC)

        if not bonnie_installed.stdout:
            self._log.error("bonnie++ is required for this test")
            return False  # sys.exit(Framework.TEST_RESULT_FAIL)

        if not ptu_installed.stdout:
            self._log.error("ptu is required for this test and expected to be installed at /ptu")
            return False  # sys.exit(Framework.TEST_RESULT_FAIL)

        if not numactl_installed.stdout:
            self._log.error("numactl which provides numastat is required for this test")
            return False  # sys.exit(Framework.TEST_RESULT_FAIL)

        if not sysstat_installed.stdout:
            self._log.error("sysstat, which provides sar, is required for this test")
            return False  # sys.exit(Framework.TEST_RESULT_FAIL)

        return True

    def cleanup_nvme_test_specific_items(self, mount_point):
        """
        Clean up items specific to test that are not cleaned by the main DTAF cleanup. Also pre-cleans the system before
        a test is run.
        :param self:
        :param mount_point: The filesystem mount point used for disk R/W checks. All files will be deleted so be careful
        :return: none
        """
        self._log.info("Cleaning test configuration")
        self._os.execute("killall screen", self.OS_DISK_CMD_EXECUTE_TIMEOUT_IN_SEC)
        self._os.execute("killall bonnie++", self.OS_DISK_CMD_EXECUTE_TIMEOUT_IN_SEC)
        mount_check = self._os.execute("ls /mnt/{}".format(mount_point), self.OS_DISK_CMD_EXECUTE_TIMEOUT_IN_SEC)
        if mount_check:
            self._log.info("Deleting Bonnie++ files in /mnt/{}".format(mount_point))
            self._os.execute("rm -r -f /mnt/{}/Bonnie*".format(mount_point),
                             (self.OS_DISK_CMD_EXECUTE_TIMEOUT_IN_SEC * 10))
        else:
            self._log.info("NVMe Partition not mounted, skipping file deletion")
        self._log.info("Finished cleanup")
