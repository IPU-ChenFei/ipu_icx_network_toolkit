import sys
import time

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from src.seamless.lib.seamless_common import SeamlessBaseTest


class iperfclass(SeamlessBaseTest):

    def __init__(self, test_log, arguments, cfg_opts):
        super().__init__(test_log, arguments, cfg_opts)
        self.expected_ver = None
        self.warm_reset = None
        self.update_type = None

    def get_current_version(self, echo_version=True):
        fw_inv = self._bmc_redfish.get_firmwareinventory()
        for each in fw_inv:
            if each['Id'] == 'bmc_active':
                version = each['Version']
                print(each)
        return version

    def evaluate_workload_output(self, output):
        pass

    def check_capsule_pre_conditions(self):
        # To-Do add capsule pre condition checks
        return True

    def prepare(self):
        super().prepare()

    def execute(self):
        self.install_Iperf_server()
        self.running_server()
        time.sleep(10)
        return self.install_iperf_win()


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if iperfclass.main() else Framework.TEST_RESULT_FAIL)
