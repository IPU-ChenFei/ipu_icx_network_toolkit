import sys
import platform

from dtaf_core.lib.dtaf_constants import Framework
from src.processor.processor_cpuinfo.processor_cpuinfo_common import ProcessorCPUInfoBase


class EventContentConfiguration(ProcessorCPUInfoBase):

    _EIST_DISABLE_BIOS_CONFIG_FILE = "disable_eist_bios_knob.cfg"
    _EIST_ENABLE_BIOS_CONFIG_FILE = "enable_eist_bios_knob.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new  VerifyProcessorCPUInfo object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(EventContentConfiguration, self).__init__(test_log, arguments, cfg_opts, self._EIST_ENABLE_BIOS_CONFIG_FILE,
                                                     self._EIST_DISABLE_BIOS_CONFIG_FILE)

    def prepare(self):
        """
        Setup actions for this test case. Executed before the test logic in execute is called.
        """
        super(EventContentConfiguration, self).prepare()

    def execute(self):
        """
        Execute Main test case.

        :return: True if test completed successfully, False otherwise.
        """
        cpuinfo_dict = self.get_cpu_info()

        exec_os = platform.system()
        try:
            cfg_file_default = Framework.CFG_BASE
        except KeyError:
            err_log = "Error - execution OS " + str(exec_os) + " not supported!"
            self._log.error(err_log)
            raise err_log

        # Get the Automation folder config file path based on OS.
        cfg_file_automation_path = cfg_file_default[exec_os] + "content_configuration.xml"

        try:
            from lxml import etree
            tree = etree.parse(cfg_file_automation_path)
            root = tree.getroot()
            for key,value in cpuinfo_dict.items():
                code = root.xpath('//content/processor/CPU_INFO/SPR/XXXX/{0}'.format(key))
                if code:
                    code[0].text = str(value)
            etree.ElementTree(root).write(cfg_file_automation_path, pretty_print=True)
            return True
        except Exception as ex:
            self._log.error(
                "Failure msg = {0}".format(
                    ex))
            return False


if __name__ == '__main__':
    test_result = EventContentConfiguration.main()
    sys.exit(Framework.TEST_RESULT_PASS if test_result else Framework.TEST_RESULT_FAIL)
