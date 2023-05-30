#!/usr/bin/env python
import json
import os
import platform
import time
from datetime import datetime
from multiprocessing import Process
import logging
from importlib import import_module
import threading
import enum
import random

from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.lib import log_utils
from dtaf_core.lib.dtaf_constants import Framework
from src.seamless.tools.JsonParserValidator.json_parser import JsonParser
from src.seamless.tools.CrossProductOrchestrator.App.RunCrosses import RunCrosess
from src.seamless.lib.seamless_common import SeamlessBaseTest
from src.seamless.tools.CrossProductOrchestrator.App.Utils.Process import SeamLessProcess

process_obj = []


# creating enumerations class for user JSON parser
class JsonFunction(enum.Enum):
    get_run_until_step_id = 1
    get_run_until_min_time_out = 2
    get_run_until_loop = 3
    get_run_until_time_out = 4
    get_run_until_end_of_life = 5
    get_max_time_out = 6
    get_main_id_from_current_id = 7
    get_execute_in_background_status = 8
    get_current_executable_path = 9
    get_current_class_name = 10
    get_current_method_name = 11


def JsonParserHelper(current_step_id, request_data):
    """
    return the required data based on enum provided by the user

    :param current_step_id : current execution step_id
    :param request_data : data which API need's to return based on the ENUM

    :return: User Json data based on the request_data
    """
    file_path = os.path.join(os.getcwd(), "Seamless_new.json")
    json_file = open(file_path, 'r')
    user_json_data = json.load(json_file)

    if request_data == JsonFunction.get_run_until_step_id:
        for step_object in user_json_data:
            current_executable = step_object.get("executable").get("current_executable")
            for each in current_executable:
                if current_step_id == each.get("current_executable_id"):
                    return step_object.get("run_until").get("step_id")

    elif request_data == JsonFunction.get_run_until_min_time_out:
        for step_object in user_json_data:
            current_executable = step_object.get("executable").get("current_executable")
            for each in current_executable:
                if current_step_id == each.get("current_executable_id"):
                    return float(step_object.get("run_until").get("min_time_out"))

    elif request_data == JsonFunction.get_run_until_loop:
        for step_object in user_json_data:
            current_executable = step_object.get("executable").get("current_executable")
            for each in current_executable:
                if current_step_id == each.get("current_executable_id"):
                    return step_object.get("run_until").get("loop")

    elif request_data == JsonFunction.get_run_until_end_of_life:
        for step_object in user_json_data:
            current_executable = step_object.get("executable").get("current_executable")
            for each in current_executable:
                if current_step_id == each.get("current_executable_id"):
                    return eval(step_object.get("run_until").get("end_of_life"))

    elif request_data == JsonFunction.get_max_time_out:
        for step_object in user_json_data:
            current_executable = step_object.get("executable").get("current_executable")
            for each in current_executable:
                if current_step_id == each.get("current_executable_id"):
                    return float(step_object.get("max_time_out"))

    elif request_data == JsonFunction.get_main_id_from_current_id:
        for step_object in user_json_data:
            current_executable = step_object.get("executable").get("current_executable")
            for each in current_executable:
                if current_step_id == each.get("current_executable_id"):
                    return step_object.get("step_id")

    elif request_data == JsonFunction.get_execute_in_background_status:
        for step_object in user_json_data:
            current_executable = step_object.get("executable").get("current_executable")
            for each in current_executable:
                if current_step_id == each.get("current_executable_id"):
                    return bool(step_object.get("execute_in_background"))

    elif request_data == JsonFunction.get_current_executable_path:
        for step_object in user_json_data:
            current_executable = step_object.get("executable").get("current_executable")
            for each in current_executable:
                if current_step_id == each.get("current_executable_id"):
                    return each.get("executable_path")

    elif request_data == JsonFunction.get_current_class_name:
        for step_object in user_json_data:
            current_executable = step_object.get("executable").get("current_executable")
            for each in current_executable:
                if current_step_id == each.get("current_executable_id"):
                    return each.get("class_name")

    elif request_data == JsonFunction.get_current_method_name:
        for step_object in user_json_data:
            current_executable = step_object.get("executable").get("current_executable")
            for each in current_executable:
                if current_step_id == each.get("current_executable_id"):
                    return each.get("entry_method_name")

    print("Invalid Data Requested")
    return None


class CrossProduct:

    def __init__(self):
        self.exec_os = platform.system()
        self.arguments = None
        self.config_parameters = None
        self.sut_os_cfg = None
        self.temp_array = []

    def validator(self):
        """
        Schema Validator to validate user input json data is in right format or not.
        """
        return True

    def preprocessing(self, executable_path, class_name):
        """
        preprocessing will import the reqired modules and it will return the absolute class name

        :param executable_path: executable path from the json file
        :param class_name: class name from json file

        :return: absolute class name path
        """
        print(f'{self.preprocessing.__name__} Called')
        try:
            cfg_file_default = Framework.CFG_FILE_PATH[self.exec_os]
        except KeyError:
            print("Error - execution OS " + str(self.exec_os) + " not supported!")
            raise RuntimeError("Error - execution OS " + str(self.exec_os) + " not supported!")

        self.arguments = BaseTestCase.parse_arguments(None, cfg_file_default)
        self.config_parameters = BaseTestCase.parse_config_file(self.arguments)
        self.sut_os_cfg = self.config_parameters.find(SutOsProvider.DEFAULT_CONFIG_PATH)

        test_log = log_utils.create_logger(class_name, False, self.config_parameters)

        import_module(executable_path)
        mod = import_module(executable_path, class_name)
        current_class_name = getattr(mod, class_name)

        ob = current_class_name(test_log, self.arguments, self.config_parameters)
        return ob

    def preexecution(self):
        print("Pre Executable Called")

    def executorhelper(self, executable_path, class_name, method_name):
        """
        executorhelper will call the function provided by input paramter using eval

        :param executable_path: executable path from the json file
        :param class_name: class name from json file
        :param method_name: method name from json file
        """
        pro_obj = SeamLessProcess()
        print(f"{self.executorhelper.__name__} Called\n")
        print(f'Class Name :  {class_name}')
        print(f'Executable Path :  {executable_path}')
        print(f'Method Name :  {method_name}')
        # to verification only Start
        # for i in range(random.randint(5, 15)):
        #     pass
        # to verification only End

        object = self.preprocessing(executable_path, class_name)
        object.prepare()
        eval(f"object.{method_name}()")

    def currentexeuctable(self, user_json_data):
        """
        current executable will create the object for each entry in the json and it will call current_post_processing

        :param user_json_data : User JSON file
        """
        global process_obj
        print("Current Executable Called")
        for step_object in user_json_data:
            # if step_object.get("execute_in_background"):
            current_executable = step_object.get("executable").get("current_executable")
            current_executable_count = len(current_executable)
            for each in range(current_executable_count):
                # get required parameters from the user json file
                executable_path = current_executable[each].get("executable_path")
                class_name = current_executable[each].get("class_name")
                entry_method_name = current_executable[each].get("entry_method_name")

                # create the process object
                pro_run_obj = Process(target=self.executorhelper,
                                      args=(executable_path, class_name, entry_method_name))
                temp_dict = {
                    "step_id": {
                        "current_id": current_executable[each].get("current_executable_id"),
                        "object": pro_run_obj,
                        "param": [executable_path, class_name, entry_method_name],
                        "Start_time": datetime.now(),
                        "force_terminate": False
                    }
                }

                # Store the Process Object and it's details on a global variable which can be used through the program
                process_obj.append(temp_dict)

        # current_post_processing will start the functions which created above
        self.current_post_processing()

    def postexecutable(self):
        """
        post executable if any
        """
        pass

    def current_post_processing(self):
        """
        current post processing will run the processes which is created by currentexeuctable and it will call for current_rununtil_processing,
        at the end it will run the serial functions provided by the user.
        """
        global process_obj

        # this loop is to run the functions which needed the parallelism
        print("Running Parallel Functions")
        for each_process in process_obj:
            process_id = each_process.get("step_id").get("current_id")
            if JsonParserHelper(process_id, JsonFunction.get_execute_in_background_status):
                # start parallel process here
                # parallel function should be executed when execute in background is set to True
                print(f'Starting : {each_process.get("step_id").get("object")}')
                # Update the process starting time
                each_process["step_id"]["Start_time"] = datetime.now()
                # Start the Process
                each_process.get("step_id").get("object").start()
            else:
                # check for the functions which are not executed yet. when control reaches here, non-parallel functions
                # are left, so check for non-parallel functions and execute them directly
                # get the required parameters from the user json file
                current_executable_path = JsonParserHelper(process_id, JsonFunction.get_current_executable_path)
                current_class_name = JsonParserHelper(process_id, JsonFunction.get_current_class_name)
                current_method_name = JsonParserHelper(process_id, JsonFunction.get_current_method_name)
                print(f"Running : {current_method_name}")
                # Start executing the functions directly
                self.executorhelper(current_executable_path, current_class_name, current_method_name)

        self.current_rununtil_processing()


    def check_rununtil_step_id(self):
        pass



    def check_rununtil_min_tmieout(self):
        pass




    def check_rununtil_max_timeout(self, difference, max_time, each_process):
        status = True
        # if it's reached to MAX time, then kill the process
        if difference >= float(max_time):  # or difference >= float(min_time):
            # update force_terminate so that it will not conflict with RunUntil
            for global_each in process_obj:
                if each_process.get("step_id").get("current_id") == \
                        global_each.get("step_id").get("current_id"):
                    # update both global and local process since currently within this function we are using local
                    global_each["step_id"]["force_terminate"] = True
                    each_process["step_id"]["force_terminate"] = True

            each_process_obj = each_process.get("step_id").get("object")
            # if the process is still alive force terminate it.
            if each_process_obj.is_alive():
                print(f'{each_process.get("step_id").get("current_id")} exceeds the Max Time')
                # Terminate the process since it reaches to its maximum limit if its alive
                each_process_obj.terminate()
                status = True
        else:
            status = False
        return status

    def check_rununtil_end_of_life(self):
        pass


    def check_rununtil_loop_count(self):
        pass





    def current_rununtil_processing(self):
        """
        current rununtil processing will check for required run until conditions and if needed it will
        recreate the object and update the global data and rerun the process
        """
        global process_obj
        print(f'{self.current_rununtil_processing.__name__} Called')
        time_for_each_loop = 10
        status_check = True
        while status_check:
            # iterate through each process which it created
            for each_process in process_obj:
                process_id = each_process.get("step_id").get("current_id")
                # using the current step id check if that process is parallel process or not.
                # if execute in background is set, then it's parallel process
                if JsonParserHelper(process_id, JsonFunction.get_execute_in_background_status):
                    print(f'Checking for process_id : {process_id}')
                    print(f'process_obj : {process_obj}')

                    # get the current time and calculate how much time the function has executed
                    current_time = datetime.now()
                    start_time = each_process.get("step_id").get("Start_time")
                    difference = ((current_time - start_time).total_seconds()) / 60
                    max_time = JsonParserHelper(each_process.get("step_id").get("current_id"),
                                                JsonFunction.get_max_time_out)

                    print(f'{each_process.get("step_id").get("current_id")} start : '
                          f'{start_time} max : {max_time} Diff : {difference}')

                    # Calling max timeout function
                    status = self.check_rununtil_max_timeout(difference, max_time, each_process)

                    # Max Time is not yet reached, run till the min timeout
                    min_time_out = JsonParserHelper(each_process.get("step_id").get("current_id"),
                                                    JsonFunction.get_run_until_min_time_out)

                    print(f'difference : {difference} min_time_out : {min_time_out}')
                    if difference <= min_time_out:
                        print(f'force_terminate : {each_process.get("step_id").get("force_terminate")}')
                        if not each_process.get("step_id").get("force_terminate"):
                            each_process_obj = each_process.get("step_id").get("object")
                            print(each_process_obj)
                            if not each_process_obj.is_alive():
                                # get the rununtil step id's to check for dependency to run again
                                if len(JsonParserHelper(each_process.get("step_id").get("current_id"),
                                                        JsonFunction.get_run_until_step_id)) > 0:
                                    # currently, assuming only 1 rununtil step id given
                                    run_until_process_step_id = \
                                        JsonParserHelper(each_process.get("step_id").get("current_id"),
                                                         JsonFunction.get_run_until_step_id)[0]
                                    for each in process_obj:
                                        if run_until_process_step_id == each.get("step_id").get("current_id"):
                                            run_until_process_obj = each.get("step_id").get("object")

                                            # if rununtil step id is still running, due to dependency, rerun the process again, since it's under min_time_ot check
                                            if run_until_process_obj.is_alive():
                                                param = each_process.get("step_id").get("param")
                                                print(f'calling executorhelper Param : '
                                                      f'{param[0]}, {param[1]}, {param[2]}')

                                                # Creating the process object
                                                pro_run_obj = Process(target=self.executorhelper,
                                                                      args=(param[0], param[1], param[2]))

                                                # update the new process object to the global and local variable
                                                for global_each1 in process_obj:
                                                    if each.get("step_id").get("current_id") == global_each1.get(
                                                            "step_id").get("current_id"):
                                                        # update the global and local process object
                                                        global_each1["step_id"]["object"] = pro_run_obj
                                                        each["step_id"]["object"] = pro_run_obj

                                                print(f"Re-Running the Process since it's not reached to min "
                                                      f"time {each_process.get('step_id').get('current_id')}")

                                                # Start the newly created process. (rerunning same function with new process)
                                                pro_run_obj.start()
                                # if the function doesn't have any rununtil step it
                                else:
                                    # if the process is finished, then rerun the process
                                    if not each_process_obj.is_alive():
                                        param = each_process.get("step_id").get("param")
                                        print(f'calling executorhelper Param : {param[0]}, {param[1]}, {param[2]}')
                                        pro_run_obj = Process(target=self.executorhelper,
                                                              args=(param[0], param[1], param[2]))

                                        for global_each1 in process_obj:
                                            if each_process.get("step_id").get("current_id") == \
                                                    global_each1.get("step_id").get("current_id"):

                                                # update the global and local process object
                                                global_each1["step_id"]["object"] = pro_run_obj
                                                each_process["step_id"]["object"] = pro_run_obj

                                        print(f"Re-Running the Process since it's not reached to min "
                                              f"time {each_process.get('step_id').get('current_id')}")
                                        # start the new process
                                        pro_run_obj.start()

                    # main process is running more than min timeout
                    else:
                        if not each_process.get("step_id").get("force_terminate"):
                            each_process_obj = each_process.get("step_id").get("object")
                            if not each_process_obj.is_alive():
                                # get the rununtil step id's to check for dependency to run again

                                if len(JsonParserHelper(each_process.get("step_id").get("current_id"),
                                                        JsonFunction.get_run_until_step_id)) > 0:
                                    # currently, assuming only 1 rununtil step id given
                                    run_until_process_step_id = \
                                        JsonParserHelper(each_process.get("step_id").get("current_id"),
                                                         JsonFunction.get_run_until_step_id)[0]
                                    for each in process_obj:
                                        if run_until_process_step_id == each.get("step_id").get("current_id"):
                                            run_until_process_obj = each.get("step_id").get("object")

                                            # if rununtil step id is still running, due to dependency, rerun the process again, since it's under min_time_ot check
                                            if not run_until_process_obj.is_alive():
                                                param = each_process.get("step_id").get("param")
                                                print(
                                                    f'calling executorhelper Param : {param[0]}, {param[1]}, {param[2]}')
                                                pro_run_obj = Process(target=self.executorhelper,
                                                                      args=(param[0], param[1], param[2]))

                                                for global_each1 in process_obj:
                                                    if each.get("step_id").get("current_id") == global_each1.get(
                                                            "step_id").get("current_id"):
                                                        # update the global and local process object
                                                        global_each1["step_id"]["object"] = pro_run_obj
                                                        each["step_id"]["object"] = pro_run_obj

                                                print(
                                                    f"Re-Running the Process since it's not reached to min time {each_process.get('step_id').get('current_id')}")
                                                pro_run_obj.start()

                            post_control_status = []
                            for each_process_ in process_obj:
                                status = each_process_.get("step_id").get("object").is_alive()
                                post_control_status.append(status)
                            
                            print(f'post_control_status : {post_control_status}')
                            if not all(post_control_status):
                                status_check = False

                    time.sleep(time_for_each_loop)

    def ProcessControlStatus(self):
        """
        Control Status will check for max timeout to which program can identify when it needs to be stopped.
        """
        global process_obj
        max_time_out = []
        for each in process_obj:
            if JsonParserHelper(each.get("step_id").get("current_id"), JsonFunction.get_execute_in_background_status):
                max_time_out.append(
                    JsonParserHelper(each.get("step_id").get("current_id"), JsonFunction.get_max_time_out))

        print(f"{self.ProcessControlStatus.__name__} max_time_out : {max_time_out}")
        return max(max_time_out)


if __name__ == "__main__":

    obj = CrossProduct()

    if not obj.validator():
        print("Schema Validator Failed")
    userjsonfile = os.path.join(os.getcwd(), "Seamless_new.json")
    file = open(userjsonfile, 'r')
    userjsondata = json.load(file)

    # obj.preprocessing()
    # obj.preexecution()
    obj.currentexeuctable(userjsondata)
