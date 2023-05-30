#!/usr/bin/env python
import os
import platform
import time
from multiprocessing import Process

from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.lib import log_utils
from dtaf_core.lib.dtaf_constants import Framework
from src.seamless.tools.CrossProductOrchestrator.App.RunCrosses import RunCrosess
from src.seamless.lib.seamless_common import SeamlessBaseTest
from src.seamless.lib.pm_common import SocwatchCommon
from src.seamless.tools.CrossProductOrchestrator.App.Utils.Process import SeamLessProcess


class seamless_abstract(SocwatchCommon):

    def __init__(self, test_log, arguments, cfg_opts):
        super(seamless_abstract, self).__init__(test_log, arguments, cfg_opts)
        self.warm_reset = False

    def check_capsule_pre_conditions(self):
        pass

    def get_current_version(self, echo_version=True):
        fw_inv = self._bmc_redfish.get_firmwareinventory()
        for each in fw_inv:
            if each['Id'] == 'bmc_active':
                version = each['Version']
                print(each)
        return version

    def examine_post_update_conditions(self):
        pass

    def evaluate_workload_output(self, output):
        pass

    def block_until_complete(self, pre_version):
        pass

def create_object(class_name, method_name, package):
    print("Class name --> ", class_name, "Method name -->", method_name)
    exec_os = platform.system()

    try:
        cfg_file_default = Framework.CFG_FILE_PATH[exec_os]
    except KeyError:
        print("Error - execution OS " + str(exec_os) + " not supported!")
        raise RuntimeError("Error - execution OS " + str(exec_os) + " not supported!")
    arguments = BaseTestCase.parse_arguments(None, cfg_file_default)

    # Add user-specified arguments
    # BaseTestCase.add_arguments()

    print(arguments.cfg_file)
    config_parameters = BaseTestCase.parse_config_file(arguments)

    test_log = log_utils.create_logger(class_name, False, config_parameters)

    sut_os_cfg = config_parameters.find(SutOsProvider.DEFAULT_CONFIG_PATH)
    os_obj = ProviderFactory.create(sut_os_cfg, test_log)

    run_function(class_name, method_name, test_log, arguments, os_obj, config_parameters, package)


def run_function(class_name1, method_name, test_log, arguments, os_obj, config_parameters, path):
    """

    """
    from importlib import import_module
    print("path ", path)
    import_module(path)
    mod = import_module(path, class_name1)
    class_name = getattr(mod, class_name1)
    # print("Y"*50)
    ob = class_name(test_log, os_obj, config_parameters)

    #ob.prepare()
    #ob.execute()
    eval(f"ob.{method_name}()")
    quit()

    # eval(f"ob.{method_name}()")




if __name__ == "__main__":

    #process class object
    process_obj = SeamLessProcess()

    JsonFile = os.path.join(os.getcwd(), "Seamless_new.json")
    obj = RunCrosess(JsonFile)
    json_data = obj.parse_input()


    process_info = {
        "step_id": "",
        "process_object": ""

    }

    def run_in_sequence(step_object):
        pass


    def run_until(run_until_obj, pid, p_name):
        if run_until_obj.get("step_ids"):
            status = process_obj.check_process_status_by_id(p_name)
            if status:
                return True
            else:
                #spawn_process(step_object)
                return True
        elif run_until_obj.get("min_time_out"):
            time.sleep(run_until_obj.get("min_time_out"))
            spawn_process(step_object)
            return False
        elif run_until_obj.get("time_out"):
            time.sleep(run_until_obj.get("time_out"))
            process_obj.kill_process_by_id(pid)
            return False
        # elif run_until_obj.get("end_of_life"):
        #
        #     process_obj.kill_process_by_id()
        #     return False



    def spawn_process(step_object):
        # create process
        # while run_until(step_object.get("run_object")) :
        step_id = obj.get_step_id(json_data)
        current_block_data = obj.get_current_block(json_data, step_id)
        #block_values = obj.execute_current_block(current_block_data)
        # print("-----------------------------------------")
        # print("block values ", block_values)
        # print("-------------------------------------------")7
        for each_block in current_block_data:
            for key, val in each_block.items():
                if key == "executable_path":
                    print("executable path ", val)
                    path = val
                if key == "class_name":
                    print("class name ", val)
                    classname = val
                if key == "entry_method_name":
                    print("entry method name ", val)
                    fun1_name = val
                    break
            break
        #fun1_name = current_block_data.get("entry_method_name")
        #print("entry function name", fun1_name)
        #package = current_block_data.get("executable_path")
        #print("package", package)
        pro_run_obj = Process(target=create_object, args=(classname, fun1_name, path))
        pro_run_obj.start()
        pid, p_name = process_obj.set_process_data(pro_run_obj)

        while (1):
            if run_until(step_object.get("run_until"), pid, p_name):
                print(pro_run_obj.pid)
            else:
                break

    for step_object in json_data:
        print("===============================================")
        # print(type(step_object.get("execute_in_background")))
        # print(step_object.get("execute_in_background"))
        # val = step_object.get("execute_in_background")
        val = "False"
        print("val================", val)
        if False == "True": #step_object.get("execute_in_background"):
            print("step objjjjjjjjjjjjjjj", step_object)
            #spawn_process(step_object)
        else:
            run_in_sequence(step_object)
            print("entered else")



        # step_running_status = verify_if_step_is_running(run_until_obj.get("step_ids"))
        # min_time_.out_status = verify_min_time_achieved(run_until_obj.get("min_time_out"))
        # if all(step_running_status,min_time_out_status):
        # return True
        # return False





    # class_name_fun1 = block_values[1].strip()
    # fun1_name = block_values[2].strip()
    # package = block_values[0].strip()
    # # process = Process(target=create_object, args=(class_name_fun1, fun1_name, package))
    # # process.start()
    # # print(process.pid)
    # package1 = "src.seamless.tests.bmc.functional.pm_script"
    # package2 = "src.seamless.tests.bmc.functional.SEAM_BMC_0004_send_bios_update_capsule"
    # class_name2 = block_values[7]
    # fun2_name = block_values[8]
    # process = Process(target=create_object, args=("PmScript", "execute", package1))
    # #time.sleep(10)
    # process1 = Process(target=create_object, args=("SEAM_BMC_0004_send_bios_update_capsule", "execute", package2))
    # process1.start()
    # time.sleep(15)
    # process.start()
    # # print(process1.pid)
    # # process.join()


