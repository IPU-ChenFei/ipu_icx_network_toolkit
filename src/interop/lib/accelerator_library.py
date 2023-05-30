import os
import subprocess
import sys
import six
import time
import re
import threading
import signal

from src.lib import content_exceptions
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_artifactory_utils import ContentArtifactoryUtils
from src.lib.content_configuration import ContentConfiguration
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider

from src.lib import content_exceptions
from src.lib.os_lib import WindowsCommonLib
from src.collaterals.collateral_constants import CollateralConstants
from src.lib.dtaf_content_constants import PTUToolConstants
from src.lib.tools_constants import ArtifactoryName, ArtifactoryTools
from src.provider.sgx_provider import SGXProvider
from src.lib.grub_util import GrubUtil
from src.lib.install_collateral import InstallCollateral
from src.lib.content_base_test_case import ContentBaseTestCase



class AcceleratorLibrary(object):

    INTEL_IOMMU_ON_STR = "intel_iommu=on,sm_on iommu=on"
    REGEX_FOR_INTEL_IOMMU_ON_STR = r"intel_iommu=on,sm_on\siommu=on"
    REGEX_FOR_QAT_WORKLOAD_SUCCESS = r"Sample\scode\scompleted\ssuccessfully."
    REGEX_FOR_DLB_WORKLOAD_SUCCESS = r"Success"
    REGEX_FOR_DEVICE_CONFIG_SUCCESS = r"enabled\s(\d+)\sdevice\(s\)\sout\sof\s(\d+)"
    REGEX_FOR_WQ_CONFIG_SUCCESS = r"enabled\s(\d+)\swq\(s\)\sout\sof\s(\d+)"
    REGEX_FOR_DSA_WORKLOAD_SUCCESS = r"(\d+)\sof\s(\d+)\swork\squeues\slogged\scompletion\srecords"
    REGEX_FOR_IAA_WORKLOAD_SUCCESS = r"(\d+)\sof\s(\d+)\stests\spassed"
    REGEX_FOR_FISHER_TOOL_SUCCESS = r"I: fisher: stats: PASS = "
    CPA_SAMPLE_CODE = "./cpa_sample_code signOfLife=1"
    IAX_CONFIG_FILE_COMMAND = "./Setup_Randomize_IAX_Conf.sh"
    DSA_CONFIG_FILE_COMMAND = "./Setup_Randomize_DSA_Conf.sh"
    SIOV_MULTI_VM_ACCELERATOR_FILE = "./Accelerators_SIOV_Multi_VM.sh"
    SHELL_SCRIPT_PATH = "/root/scripts/"
    REGEX_FOR_VM_WORLOAD = r"Workloads run successfully of (\d+) VMs"
    REGEX_FOR_SGX_WORKLOAD = r"Planed: (\d+)   Success: (\d+)"

    def __init__(self, log, os_obj, cfg_opts):

        self._log = log
        self._os = os_obj
        self.sut_os = self._os.os_type
        self._cfg = cfg_opts
        self._common_content_lib = CommonContentLib(self._log, self._os, self._cfg)
        self._common_content_configuration = ContentConfiguration(self._log)

        self._install_collateral = InstallCollateral(self._log, self._os, cfg_opts)  # ....
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp = ProviderFactory.create(si_dbg_cfg, self._log)  # type: SiliconDebugProvider
        self.sgx = SGXProvider.factory(self._log, cfg_opts, self._os, self.sdp)
        self.run_time = self._common_content_configuration.get_workload_time()  # ..
        self._command_timeout = self._common_content_configuration.get_command_timeout()
        self._os_time_out_in_sec = self._common_content_configuration.os_full_ac_cycle_time_out()
        self._reboot_time_out = self._common_content_configuration.get_reboot_timeout()
        self.sut_ras_tools_path = None
        self.sut_viral_injector_path = None
        self.sut_viral_injector_path = None
        self.dpdk_file_path = self._common_content_configuration.get_dpdk_file()
        self.dpdk_file_name = os.path.split(self.dpdk_file_path)[-1].strip()
        self.dpdk_patch_file_name = self._common_content_configuration.get_dpdk_patch_file()
        self.rdt_file_path = self._common_content_configuration.get_rdt_file()
        self.kernel_rpm_file_name = self._common_content_configuration.get_kernel_rpm_file()
        self.qat_file_path = self._common_content_configuration.get_qat_file()
        self.hqm_file_path = self._common_content_configuration.get_hqm_file()
        self.accel_file_path = self._common_content_configuration.get_idx_file()
        self.spr_file_path = self._common_content_configuration.get_spr_file()
        self._ldb_traffic_data = self._common_content_configuration.get_hqm_ldb_traffic_data()
        self._platform = self._common_content_lib.get_platform_family()
        self._os_lib = WindowsCommonLib(self._log, os_obj)
        self.ROOT = "/root"
        self._artifactory_obj = ContentArtifactoryUtils(self._log, self._os, self._common_content_lib, cfg_opts)
        self._grub_obj = GrubUtil(self._log, self._common_content_configuration, self._common_content_lib)
        self._num_of_cycles = self._common_content_configuration.memory_number_of_cycle()  

    def dsa_workload_on_host(self):
        """
             This function runs DSA workload on host.
             :param : None
             :Runs the dsa workload for given RUN_TIME
             :return: None
        """

        try:
            self._log.info("Running DSA workload...")
            dsa_config = self._common_content_lib.execute_sut_cmd(f"{self.DSA_CONFIG_FILE_COMMAND} -ua",
                                                                  "Configuring DSA devices",
                                                                  self._command_timeout,
                                                                  cmd_path="/root/accel-random-config-and-test/")
            op = re.search(self.REGEX_FOR_WQ_CONFIG_SUCCESS, "".join(dsa_config))
            if op.group(1) == op.group(2):
                self._log.info("DSA work-queues configured Successfully")
            else:
                self._log.error("DSA work-queues configuration Failed")

            cnt = 0
            com_time = time.perf_counter() + self.run_time
            while time.perf_counter() < com_time:
                cnt += 1
                dsa_test = self._common_content_lib.execute_sut_cmd(f"{self.DSA_CONFIG_FILE_COMMAND} -o 0x3",
                                                                    "Running DSA test",
                                                                    self._command_timeout,
                                                                    cmd_path="/root/accel-random-config-and-test/")
                time.sleep(1)
                op = re.search(self.REGEX_FOR_DSA_WORKLOAD_SUCCESS, "".join(dsa_test))
                if op.group(1) == op.group(2):
                    self._log.info("DSA workload run Successfully in loop: {}".format(cnt))
                else:
                    self._log.error("DSA workload Failed in loop: {}".format(cnt))
            self._log.info(f"Ran DSA stress-workload for {self.run_time} seconds ...")
        except Exception as ex:
            log_error = "Error in running DSA Test."
            self._log.error(log_error)
            RuntimeError(ex)

    def iax_workload_on_host(self):
        """
            This function runs IAX workload on host.
            :param : None
            :Runs the IAX workload for given RUN_TIME
            :return: None
        """

        try:
            self._log.info("Running IAA workload...")
            iaa_config = self._common_content_lib.execute_sut_cmd(f"{self.IAX_CONFIG_FILE_COMMAND} -ua",
                                                                  "Configuring IAX devices",
                                                                  self._command_timeout,
                                                                  cmd_path="/root/accel-random-config-and-test/")

            op = re.search(self.REGEX_FOR_WQ_CONFIG_SUCCESS, "".join(iaa_config))
            if op.group(1) == op.group(2):
                self._log.info("IAX work-queues configured Successfully")
            else:
                self._log.error("IAX work-queues configuration Failed")

            cnt = 0
            com_time = time.perf_counter() + self.run_time
            while time.perf_counter() < com_time:
                cnt += 1
                iaa_test = self._common_content_lib.execute_sut_cmd(f"{self.IAX_CONFIG_FILE_COMMAND} -r",
                                                                    "Running IAA test",
                                                                    self._command_timeout,
                                                                    cmd_path="/root/accel-random-config-and-test/")
                time.sleep(1)
                op = re.search(self.REGEX_FOR_IAA_WORKLOAD_SUCCESS, "".join(iaa_test))
                if op.group(1) == op.group(2):
                    self._log.info("IAX workload run Successfully in loop: {}".format(cnt))
                else:
                    self._log.error("IAX workload Failed in loop: {}".format(cnt))
            self._log.info(f"Ran IAX stress-workload for {self.run_time} seconds ...")

        except Exception as ex:
            log_error = "Error in running IAA Test."
            self._log.error(log_error)
            RuntimeError(ex)

    def run_qat_workload_on_host(self):
        """
            This function runs QAT workload on host.
            :param : None
            :Runs the QAT workload for given RUN_TIME
            :Executes cpa sample code present in QAT folder
            :return: None
         """
        try:
            self._log.info("Running QAT workload...")
            cnt = 0
            com_time = time.perf_counter() + self.run_time
            while time.perf_counter() < com_time:
                cnt += 1
                qat_test = self._common_content_lib.execute_sut_cmd(self.CPA_SAMPLE_CODE,
                                                                    "Running QAT test",
                                                                    self._command_timeout,
                                                                    cmd_path="/root/QAT/build/")
                time.sleep(1)
                if re.findall(self.REGEX_FOR_QAT_WORKLOAD_SUCCESS, "".join(qat_test)):
                    self._log.info("QAT workload run Successfully in loop: {}".format(cnt))
                else:
                    self._log.error("QAT workload Failed in loop: {}".format(cnt))
            self._log.info(f"Ran QAT stress-workload for {self.run_time} seconds ...")

        except Exception as ex:
            log_error = "Error in running QAT Test."
            self._log.error(log_error)
            RuntimeError(ex)

    def run_dpdk_workload_on_host(self, common_content_lib=None):
        """
        This function runs dpdk workload on host.
            :param : None
            :Runs the DPDK  workload for given RUN_TIME
            :return: None
        """
        self._log.info("Running DLB workload...")
        try:
            if common_content_lib is None:
                common_content_lib = self._common_content_lib
            dpdk_file_name = os.path.split(self.dpdk_file_path)[-1].strip()
            dpdk_name, version = self._install_collateral.get_name_version(dpdk_file_name)
            dpdk_full_folder_name = dpdk_name + '-' + 'stable' + '-' + version

            config_cmd = "cd /root/HQM/dpdk/{};" \
                         "ninja -C builddir;" \
                         "mkdir -p /mnt/hugepages;" \
                         "mount -t hugetlbfs nodev /mnt/hugepages;" \
                         "echo 2048 > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages".format(
                dpdk_full_folder_name)

            workload_cmd = "cd /root/HQM/dpdk/{}/builddir/app/;" \
                           "./dpdk-test-eventdev --vdev=dlb2_event -- --test=order_queue --plcores=3 --wlcore=4,5,6," \
                           "7,8,9,10,11,12,13,14,15,16,17 --nb_flows=64 --nb_pkts=1000000000".format(
                dpdk_full_folder_name)

            dpdk_config = common_content_lib.execute_sut_cmd_no_exception(config_cmd, "Configuring DPDK workload",
                                                                          self._command_timeout, cmd_path=self.ROOT,
                                                                          ignore_result="ignore")
            cnt = 0
            com_time = time.perf_counter() + self.run_time
            while time.perf_counter() < com_time:
                cnt += 1
                dlb_test = self._common_content_lib.execute_sut_cmd(workload_cmd, "Executing DPDK workload",
                                                                    self._command_timeout, cmd_path=self.ROOT)
                time.sleep(1)
                if re.findall(self.REGEX_FOR_DLB_WORKLOAD_SUCCESS, "".join(dlb_test)):
                    self._log.info("DLB workload run Successfully in loop: {}".format(cnt))
                else:
                    self._log.error("DLB workload Failed in loop: {}".format(cnt))
            self._log.info(f"Ran DPDK stress-workload for {self.run_time} seconds ...")

        except Exception as ex:
            log_error = "Error in running DLB Test."
            self._log.error(log_error)
            RuntimeError(ex)

    def run_fisher_tool_on_host(self, type_of_error, workload, common_content_lib=None):
        """
        This function runs fisher workload on host.
            :param: str type_of_error: whether correctable or uncorrectable error
            :param: str workload: specifies the workload used
            :Run the fisher tool for the given type_of_error
            :return: None
        """
        self._log.info("Running Fisher tool...")
    
        if common_content_lib is None:
            common_content_lib = self._common_content_lib

        if workload == 'DLB':
            dpdk_file_name = os.path.split(self.dpdk_file_path)[-1].strip()
            dpdk_name, version = self._install_collateral.get_name_version(dpdk_file_name)
            dpdk_full_folder_name = dpdk_name + '-' + 'stable' + '-' + version
            print(dpdk_full_folder_name)
            workload_command ="/root/HQM/dpdk/{}/builddir/app/./dpdk-test-eventdev -c 0xf --vdev=dlb2_event -- --test=order_queue --plcores=1 --wlcore=2,3 --nb_flows=64".format(dpdk_full_folder_name)
        elif workload == 'DSA':
            workload_command ="/dsa_test-5.12/dsa_test -v -i 0 -d 0 -l 65536 -f 0x2 -n 100 -w 0 -t 2000 -o 0x3"
        elif workload == 'IAX':
            workload_command ="{} -r".format(self.IAX_CONFIG_FILE_COMMAND)
        elif workload == 'QAT':
            workload_command ="/root/QAT/build/./cpa_sample_code"
        
        self._log.info('Workload command: {}'.format(workload_command))

        if self.run_time < 60:
            fisher_tool_run_time = "{}s".format(int(self.run_time))
        elif self.run_time < 3600:
            fisher_tool_run_time = "{}m".format(int(self.run_time/60))
        else:
            fisher_tool_run_time = "{}h".format(int(self.run_time/3600))
        
        self._log.info('Fisher tool run time: {}'.format(fisher_tool_run_time))

        if type_of_error =="uncorrectable":
            injection_cmd = 'memory-uncorrectable-non-fatal --cycles={}'.format(self._num_of_cycles)
        else:
            injection_cmd = 'memory-correctable --runtime={}'.format(fisher_tool_run_time)
        
        fisher_workload = f"'{workload_command}'"
        fisher_command = r"fisher --workload={} " \
                            "--injection-type={}".format(fisher_workload, injection_cmd)

        self._log.info('Fisher command: {}'.format(fisher_command))
        
        create_shell_script_cmd= "touch test.sh"
    
        insert_workload_cmd='echo "{}" > test.sh'.format(fisher_command)

        delete_file_cmd='rm -rf test.sh'

        bash_cmd="sh test.sh"

        if (workload=='DSA') or (workload=='IAX'):
            self._log.info("Running DSA/IAX workload inside 'accel-random-config-and-test'")
            self._common_content_lib.execute_sut_cmd(create_shell_script_cmd, create_shell_script_cmd,self._command_timeout, "/root/accel-random-config-and-test/")
            self._common_content_lib.execute_sut_cmd(insert_workload_cmd, insert_workload_cmd,self._command_timeout, "/root/accel-random-config-and-test/")
            fisher_test = self._os.execute(bash_cmd,self._command_timeout,cwd="/root/accel-random-config-and-test/")
            self._common_content_lib.execute_sut_cmd(delete_file_cmd, delete_file_cmd,self._command_timeout, "/root/accel-random-config-and-test/")
        else:
            self._log.info("Running DLB/QAT workload in 'root'")
            self._common_content_lib.execute_sut_cmd(create_shell_script_cmd, create_shell_script_cmd,self._command_timeout, self.ROOT)
            self._common_content_lib.execute_sut_cmd(insert_workload_cmd, insert_workload_cmd,self._command_timeout, self.ROOT)
            fisher_test = self._os.execute(bash_cmd,self._command_timeout,cwd=self.ROOT)
            self._common_content_lib.execute_sut_cmd(delete_file_cmd, delete_file_cmd,self._command_timeout, self.ROOT)

        # print(fisher_test.stdout, "Output Stream")
        # print(fisher_test.stderr, "Error stream")

        fisher_result = fisher_test.stderr

        self._log.info(fisher_result)
        
        if type_of_error =="uncorrectable":
            REGEX_FISHER= "{}{} - FAIL = 0".format(self.REGEX_FOR_FISHER_TOOL_SUCCESS, self._num_of_cycles)
        else:
            cur_num_of_cycles= len(re.findall(self.REGEX_FOR_FISHER_TOOL_SUCCESS, fisher_result)) - 1
            REGEX_FISHER= "{}{} - FAIL = 0".format(self.REGEX_FOR_FISHER_TOOL_SUCCESS, cur_num_of_cycles)

        if re.findall(REGEX_FISHER, fisher_result):
            self._log.info("The error injection ran successfully for the given workload.")
        else:
            raise content_exceptions.TestFail("Error injection could not occur through fisher tool.")
            

    def install_sgx_hydra_tool(self):
        """
        This method installs psw and sdk on the sut.
        Copies hydra test tool in SUT and installs

        :return: hydra_test_path: hydra test toll path in SUT
        """
        app_str = "/App"
        # Installation of PSW
        self.sgx.check_psw_installation()
        # Installation of sgx sdk
        self.sgx.install_sdk()
        self._log.info("Copying Hydra tool and unzipping in SUT")
        # Copying sgx hydra tool to sut
        hydra_test_path = self._install_collateral.copy_and_install_hydra_tool() + app_str
        self._log.debug("SGX Hydra tool is installed in location {}".format(hydra_test_path))
        return hydra_test_path

    def run_hydra_test(self, hydra_test_path, test_duration=60, enclave_mb="128", num_enclave_threads="64",
                       num_regular_threads="64"):
        """
        Runs hydra test for given time

        :param hydra_test_path: hydra test path in sut
        :param test_duration: time duration in seconds to run the test, :type: int
        :param enclave_mb: Enclave MB, :type: str
        :param num_enclave_threads: Enclave threads in number, :type: str.
        :param num_regular_threads: Regular Threads in number, :type: str
        :raise: content exception if the sgx hydra test fails to run for specified duration or any error
                found during the test execution.
        """
        cat_cmd = "cat {}".format(self.sgx.HYDRA_FILE)
        error = "error"
        # Executing sgxhydra cmd
        self._os.execute_async(self.sgx.HYDRA_CMD.format(enclave_mb, num_enclave_threads, num_regular_threads,
                                                         test_duration, self.sgx.HYDRA_FILE), hydra_test_path)
        self._log.debug("SGX Hydra test is running for {}s".format(test_duration))
        start_time = time.time()
        while (time.time() - start_time) <= test_duration:
            time.sleep(60)
            grep_hydra_output = self._os.execute(self.sgx.HYDRA_GREP, self._command_timeout)
            hydra_count = grep_hydra_output.stdout.count(self.sgx.SGX_HYDRA)
            if hydra_count <= 1:
                raise content_exceptions.TestFail("SGX Hydra test is not running")
        hydra_res = self._common_content_lib.execute_sut_cmd(cat_cmd, cat_cmd, self._command_timeout,
                                                             hydra_test_path)
        self._log.debug("SGX Hydra test output is {}".format(hydra_res))
        if re.search(error, hydra_res.lower()):
            raise content_exceptions.TestFail("Error found during the test execution of sgx Hydra test")
        self._log.info("SGX Hydra test ran successfully for {}s duration".format(test_duration))
        try:
            log_dir = self._common_content_lib.get_log_file_dir()
            self._os.copy_file_from_sut_to_local(hydra_test_path + "//" + self.sgx.HYDRA_FILE,
                                                 log_dir + "//" + self.sgx.HYDRA_FILE)
        except Exception as e:
            self._log.error("Unable to copy the Sgx Hydra file due to the error {} ".format(e))

    def run_socwatch_tool_on_host(self, common_content_lib=None):
        """
        This function runs socwatch tool on host.
            :param : None
            :Runs the socwatch tool for given RUN_TIME
            :return: None
        """
        self._log.info("Running socwatch tool...")

        if common_content_lib is None:
            common_content_lib = self._common_content_lib
        
        try:
            file_name = self._common_content_configuration.get_socwatch_tool_name_config(self._os.os_type.lower()).replace('.tar.gz','')
            path = "{}/socwatch/{}/".format(self.ROOT,file_name)
            socwatch_cmd="./socwatch -m -f cpu-cstate -f cpu-pstate -t {}".format(self.run_time)
            self._common_content_lib.execute_sut_cmd(socwatch_cmd, socwatch_cmd,self._command_timeout, path)
        except Exception as e:
            self._log.error("Unable to run socwatch tool due to the error {} ".format(e))
            raise content_exceptions.TestFail("Socwatch tool couldn't be executed.")

    def check_mce_on_host(self, common_content_lib=None):
        """
        This function checks whether MCE occured on host or not.
            :param : None
            :Executes "abrt-cli list |grep mce" to check if MCE occured.
            :return: None
        """
        self._log.info("Checking MCE...")

        if common_content_lib is None:
            common_content_lib = self._common_content_lib
        
        try:
            check_log_cmd = "abrt-cli list |grep mce"
            cmd_output=self._os.execute(check_log_cmd, self._command_timeout, cwd=self.ROOT)
            if not (cmd_output.stdout == ''):
                raise content_exceptions.TestFail("There are some MCE errors or dmesg log errors. Hence, test failed.")
        except Exception as e:
            self._log.error("Unable to check MCE log due to the error {} ".format(e))
            raise content_exceptions.TestFail("Cannot check MCE.")
    
    def check_c6_residency_value_on_host(self, cc6_value, pc6_value, common_content_lib=None):
        """
        This function checks the PC6 residency value from socwatch log.
            :param : Value of desired PC6 residency in % that need to be checked 
            :return: None
        """
        self._log.info("Checking socwatch log...")

        if common_content_lib is None:
            common_content_lib = self._common_content_lib
        
        try:
            file_name = self._common_content_configuration.get_socwatch_tool_name_config(self._os.os_type.lower()).replace('.tar.gz','')
            path = "{}/socwatch/{}/".format(self.ROOT,file_name)
            log_dir = self._common_content_lib.get_log_file_dir()
            sut_file_path= os.path.join(path, "SoCWatchOutput.csv")
            host_file_path= os.path.join(log_dir, "SoCWatchOutput.csv")
            self._os.copy_file_from_sut_to_local(sut_file_path,host_file_path)
            file_read = open(host_file_path, "r")
            CC6_text= "CC6"
            PC6_text= "PC6"
            lines = file_read.readlines()
            for line in lines:
                if CC6_text in line:
                    data= line.split()
                    value=float(data[2])
                    self._log.info('cc6')
                    self._log.info(value)
                    if value < cc6_value:
                        # closing file after reading
                        file_read.close()
                        self._log.error("CC6 Residency value is not more than {}".format(cc6_value))
                        raise content_exceptions.TestFail("CC6 Residency value is less than expected.")
                    break
            for line in lines:
                if PC6_text in line:
                    data= line.split()
                    value=float(data[2])
                    self._log.info('pc6')
                    self._log.info(value)
                    if value < pc6_value:
                        # closing file after reading
                        file_read.close()
                        self._log.error("PC6 Residency value is not more than {}".format(pc6_value))
                        raise content_exceptions.TestFail("PC6 Residency value is less than expected.")
                    break
            # closing file after reading
            file_read.close()
        except Exception as e:
            # closing file after reading
            file_read.close()
            self._log.error("Unable to check CC6/PC6 Residency value because of this error : {} ".format(e))
            raise content_exceptions.TestFail("Failed to check CC6/PC6 Residency Value.")
    
    def interrupt_process(self,workload):
        """
        This function runs the interrupt command.
            :param: str workload: specifies the workload used
            :Execute the interrupt command by using the process id of the workload
            :return: None
        """
        # try:
        if workload=='DSA':
            workload_name = "DSA_Conf"
        elif workload=='IAX':
            workload_name = "IAX_Conf"
        elif workload=='QAT':
            workload_name = "cpa_sample_code"
        elif workload=='DLB':
            workload_name = "dpdk-test-eventdev"
        
        time.sleep(60)
        get_pid_cmd= 'ps -aux | grep "{}"'.format(workload_name)
        print(get_pid_cmd)
        pid_cmd_result= self._os.execute(get_pid_cmd,self._command_timeout,cwd=self.ROOT)
        pid= pid_cmd_result.stdout.split()[1]
        cmd='kill -s SIGSTOP {}'.format(pid) 
        self._log.info(cmd)
        cmd_result= self._os.execute(cmd,self._command_timeout,cwd=self.ROOT)

    def run_workload_with_interrupt_on_host(self,workload):
        """
        This function runs workload on host with interrupt.
            :param: str workload: specifies the workload used
            :Run the workload with interrupt
            :return: None
        """
        try:
            if workload=='DSA':
                workload_thread = threading.Thread(target=self.dsa_workload_on_host)
            elif workload=='IAX':
                workload_thread = threading.Thread(target=self.iax_workload_on_host)
            elif workload=='QAT':
                workload_thread = threading.Thread(target=self.run_qat_workload_on_host)
            elif workload=='DLB':
                workload_thread = threading.Thread(target=self.run_dpdk_workload_on_host)
            
            workload_stop_thread = threading.Thread(target=self.interrupt_process,args=(workload,))

            workload_thread.start()
            workload_stop_thread.start()
            
            workload_thread.join()
            workload_stop_thread.join()

            self._log.info("Workload ended")

        except Exception as ex:
            log_error = "Error in interrupting workload."
            self._log.error(log_error)
            raise content_exceptions.TestFail("Failed to run workload with interrupt.")

    def check_mce_log(self):
        clear_log_cmd = "abrt-cli rm /var/spool/abrt/* "
        self._os.execute(clear_log_cmd, self._command_timeout, cwd =self.ROOT)

    def configure_driver_to_enable_siov(self):
        """
        Configure driver to enable SIOV

        :raise: Testfail if configuring SIOV fails
        """
        configure_qat_siov_cmd_list = ["sed -i 's/ServicesEnabled.*/ServicesEnabled = sym/g' /etc/4xxx_dev*",
                                       "sed -i 's/NumberAdis = 0/NumberAdis = 64/g' /etc/4xxx_dev*",
                                       "sed -i 's/NumberCyInstances.*/NumberCyInstances = 0/g' /etc/4xxx_dev*",
                                       "sed -i 's/NumberDcInstances.*/NumberDcInstances = 0/g' /etc/4xxx_dev*",
                                       "service qat_service stop",
                                       "service qat_service start"]
        REGEX_FOR_SYM_SIOV = "Available sym.\s:(.\d+)"
        for cmd in configure_qat_siov_cmd_list:
            output = self._common_content_lib.execute_sut_cmd(cmd, cmd, self._command_timeout)
            self._log.debug("Output of the command {} is {}".format(cmd, output))

        output = self._common_content_lib.execute_sut_cmd("./vqat_ctl show", "verifying SIOV", self._command_timeout,
                                                          "QAT/build")
        self._log.debug("Output of the command {} is {}".format("./vqat_ctl show", output))
        list_siov_sym = re.findall(REGEX_FOR_SYM_SIOV, output)
        if all([int(x) for x in list_siov_sym]):
            self._log.info("SIOV configured successfully")
        else:
            raise content_exceptions.TestFail("SIOV configured is unsuccessful")

    def configure_dsa(self):
        """
        Configure DSA

        :raise: Testfail if configuring DSA fails
        """
        self._log.info("Configure DSA")
        dsa_config = self._common_content_lib.execute_sut_cmd(f"{self.DSA_CONFIG_FILE_COMMAND}  -maD -F1 -w15",
                                                              "Configuring DSA devices",
                                                              self._command_timeout,
                                                              cmd_path="/root/accel-random-config-and-test/")
        self._log.debug(dsa_config)
        op = re.search(self.REGEX_FOR_WQ_CONFIG_SUCCESS, "".join(dsa_config))
        if op.group(1) == op.group(2):
            self._log.info("DSA work-queues configured Successfully")
        else:
            raise content_exceptions.TestFail("DSA work-queues configuration Failed")

    def configure_iax(self):
        """
        Configure IAX

        :raise: Testfail if configuring IAX fails
        """
        self._log.info("Configuring IAA")
        iaa_config = self._common_content_lib.execute_sut_cmd(f"{self.IAX_CONFIG_FILE_COMMAND} -maD -F1 -w15",
                                                              "Configuring IAX devices",
                                                              self._command_timeout,
                                                              cmd_path="/root/accel-random-config-and-test/")
        self._log.debug(iaa_config)
        op = re.search(self.REGEX_FOR_WQ_CONFIG_SUCCESS, "".join(iaa_config))
        if op.group(1) == op.group(2):
            self._log.info("IAX work-queues configured Successfully")
        else:
            raise content_exceptions.TestFail("IAX work-queues configuration Failed")

    def launch_multiple_vm_with_siov(self):
        """
        Launch multiple VMs through shell script

        :return: Total number of VMs created
        :raise: Testfail if multiple VM creation fails
        """
        REGEX_FOR_VM_VERFICATION = r"VM running on port.(\d+)"
        REGEX_TOTAL_VM = r"Total VMs.=.(\d+)"
        self._log.info("Launching multiple VMs")
        launch_vm_output = self._common_content_lib.execute_sut_cmd(
            f"{self.SIOV_MULTI_VM_ACCELERATOR_FILE} -n 1 -a -Q sym -H -S -D 1dwq -I 1dwq -c 8 -i gva",
            "launch multiple vm",
            self._command_timeout,
            cmd_path=self.SHELL_SCRIPT_PATH)
        self._log.debug("Launch multiple VM with SIOV command output {}".format(launch_vm_output))
        # verification
        total_vm = re.findall(REGEX_TOTAL_VM, launch_vm_output)
        list_total_vm = re.findall(REGEX_FOR_VM_VERFICATION, launch_vm_output)
        self._log.debug("Total VM : {}".format(total_vm))
        self._log.debug("Total VM list : {}".format(list_total_vm))

        if int(total_vm[0]) == len(list_total_vm):
            self._log.info("Multiple VM creation is successful, total VM are {}".format(int(total_vm[0])))
        else:
            raise content_exceptions.TestFail("Multiple VM creation failed!!!")
        return int(total_vm[0])

    def run_qat_workload_on_multiple_vm(self, vm_count):
        """
        Run QAT workload on Multiple VMs

        :param: vm_count: Total number of VMs on which workload are running
        :raise: Testfail if QAT workload failed to run on multiple VMs
        """
        self._log.info("Running QAT workload {} for seconds".format(self.run_time))
        qat_workload_multiple_vm_output = self._common_content_lib.execute_sut_cmd(
            f"{self.SIOV_MULTI_VM_ACCELERATOR_FILE} -r '/root/workloads/./qat_workload.sh -t {self.run_time}'",
            "qat workload multiple vm",
            self.run_time + 200,
            cmd_path=self.SHELL_SCRIPT_PATH)
        self._log.debug("QAT workload output on multiple VM with SIOV {}".format(qat_workload_multiple_vm_output))
        # verification
        workload_on_total_vm = re.findall(self.REGEX_FOR_VM_WORLOAD, qat_workload_multiple_vm_output)
        if workload_on_total_vm and int(workload_on_total_vm[0]) == vm_count:
            self._log.info("Workload QAT ran successfully in all {} VMs".format(int(workload_on_total_vm[0])))
        else:
            raise content_exceptions.TestFail("QAT workload failed to run in {} VMs".format(vm_count))

    def run_dlb_workload_on_multiple_vm(self, vm_count):
        """
        Run DLB workload on Multiple VMs

        :param: vm_count: Total number of VMs on which workload are running
        :raise: Testfail if DLB workload failed to run on multiple VMs
        """
        self._log.info("Running DLB workload for {} seconds".format(self.run_time))
        dlb_workload_multiple_vm_output = self._common_content_lib.execute_sut_cmd(
            f"{self.SIOV_MULTI_VM_ACCELERATOR_FILE} -r '/root/workloads/./hqm_workload.sh -o -t {self.run_time}'",
            "dlb workload multiple vm",
            self.run_time + 200,
            cmd_path=self.SHELL_SCRIPT_PATH)
        self._log.debug("DLB workload output on multiple VM with SIOV {}".format(dlb_workload_multiple_vm_output))
        # verification
        workload_on_total_vm = re.findall(self.REGEX_FOR_VM_WORLOAD, dlb_workload_multiple_vm_output)
        if workload_on_total_vm and int(workload_on_total_vm[0]) == vm_count:
            self._log.info("DLB workload ran successfully in all {} VMs".format(int(workload_on_total_vm[0])))
        else:
            raise content_exceptions.TestFail("DLB workload failed to run in {} VMs".format(vm_count))

    def run_dsa_workload_on_multiple_vm(self, vm_count):
        """
        Run DSA workload on Multiple VMs

        :param: vm_count: Total number of VMs on which workload are running
        :raise: Testfail if DSA workload failed to run on multiple VMs
        """
        self._log.info("Running DSA workload for {} seconds".format(self.run_time))
        dsa_workload_multiple_vm_output = self._common_content_lib.execute_sut_cmd(
            f"{self.SIOV_MULTI_VM_ACCELERATOR_FILE} -r '/root/workloads/./dsa_workload.sh -t {self.run_time}'",
            "dsa workload multiple vm",
            self.run_time + 200,
            cmd_path=self.SHELL_SCRIPT_PATH)
        self._log.debug("DSA workload output on multiple VM with SIOV {}".format(dsa_workload_multiple_vm_output))
        # verification
        workload_on_total_vm = re.findall(self.REGEX_FOR_VM_WORLOAD, dsa_workload_multiple_vm_output)
        if workload_on_total_vm and int(workload_on_total_vm[0]) == vm_count:
            self._log.info("Workload DSA ran successfully in all {} VMs".format(int(workload_on_total_vm[0])))
        else:
            raise content_exceptions.TestFail("DSA workload failed to run in {} VMs".format(vm_count))

    def run_iax_workload_on_multiple_vm(self, vm_count):
        """
        Run IAX workload on Multiple VMs

        :param: vm_count: Total number of VMs on which workload are running
        :raise: Testfail if IAX workload failed to run on multiple VMs
        """
        self._log.info("Running IAX workload for {} seconds".format(self.run_time))
        iax_workload_multiple_vm_output = self._common_content_lib.execute_sut_cmd(
            f"{self.SIOV_MULTI_VM_ACCELERATOR_FILE} -r '/root/workloads/./iax_workload.sh  -t {self.run_time}'",
            "iax workload multiple vm",
            self.run_time + 200,
            cmd_path=self.SHELL_SCRIPT_PATH)
        self._log.debug("IAX workload output on multiple VM with SIOV {}".format(iax_workload_multiple_vm_output))
        # verification
        workload_on_total_vm = re.findall(self.REGEX_FOR_VM_WORLOAD, iax_workload_multiple_vm_output)
        if workload_on_total_vm and int(workload_on_total_vm[0]) == vm_count:
            self._log.info("Workload IAX ran successfully in all {} VMs".format(int(workload_on_total_vm[0])))
        else:
            raise content_exceptions.TestFail("IAX workload failed to run in {} VMs".format(vm_count))

    def run_sgx_workload_on_multiple_vm(self, vm_count):
        """
        Run SGX workload on Multiple VM's
        :param: vm_count: Total number of VMs on which workload are running
        :raise: Testfail if SGX workload failed to run on multiple VMs
        """
        self._log.info("Running SGX workload for {} seconds".format(self.run_time))
        sgx_workload_multiple_vm_output = self._common_content_lib.execute_sut_cmd(
            f"{self.SIOV_MULTI_VM_ACCELERATOR_FILE} -r '/root/workloads/./sgx_workload.sh -t {self.run_time}'",
            "sgx workload multiple vm",
            self.run_time + 200,
            cmd_path=self.SHELL_SCRIPT_PATH)
        self._log.debug("SGX workload output on multiple VM with SIOV {}".format(sgx_workload_multiple_vm_output))
        workload_on_total_vm = re.findall(self.REGEX_FOR_SGX_WORKLOAD, sgx_workload_multiple_vm_output)
        if int(workload_on_total_vm[0][0]) == int(workload_on_total_vm[0][1]):
            self._log.info('Workload SGX ran successfully on all {} VMs'.format(vm_count))
        else:
            raise content_exceptions.TestFail("SGX workload failed to run in {} VMs".format(vm_count))
