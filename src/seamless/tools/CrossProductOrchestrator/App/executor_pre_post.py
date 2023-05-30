#!/usr/bin/env python
import json
import os
import platform
import time
from datetime import datetime
from multiprocessing import Process
from importlib import import_module
import logging

from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.lib import log_utils
from dtaf_core.lib.dtaf_constants import Framework
from src.seamless.tools.CrossProductOrchestrator.App.Utils.Process import SeamLessProcess
from src.seamless.tools.CrossProductOrchestrator.App.json_parser import JsonParserHelper, JsonFunction
from src.seamless.tools.CrossProductOrchestrator.App.rununtil_bk import rununtil

process_obj = []
serial_process_obj = []
class_name_list = []


class CrossProduct:

    def __init__(self):
        self.exec_os = platform.system()
        self.arguments = None
        self.config_parameters = None
        self.sut_os_cfg = None
        self.temp_array = []
        self.cpof_log = self.get_logs("Framework log", "Framework_")
        self.rununtil_obj = rununtil()

    def get_logs(self, name, filename):
        """
        Create a logger object
        :param name:log name
        :param filename: log filename
        :return logger object
        """
        # Gets or creates a logger
        logger_cf = logging.getLogger(name)

        # set log level
        logger_cf.setLevel(logging.DEBUG)

        # set dir and file name
        log_dir_name = "C:/framework-logs/"
        log_file_name = log_dir_name + filename + self.__class__.__name__ + datetime.now().strftime(
            "%Y-%m-%d_%H.%M") + ".log"
        if not os.path.exists(log_dir_name):
            os.makedirs(log_dir_name)

        # define file handler and set formatter
        file_handler = logging.FileHandler(log_file_name)
        # Define message format
        ptv_log_fmt = logging.Formatter(
            fmt='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
            datefmt='%m/%d/%Y %I:%M:%S %p')
        file_handler.setFormatter(ptv_log_fmt)

        # add file handler to logger
        logger_cf.addHandler(file_handler)

        return logger_cf

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
        #self.cpof_log.info(str(self.preprocessing.__name__) + 'Called')
        try:
            cfg_file_default = Framework.CFG_FILE_PATH[self.exec_os]
        except KeyError:
            self.cpof_log.info("Error - execution OS " + str(self.exec_os) + " not supported!")
            raise RuntimeError("Error - execution OS " + str(self.exec_os) + " not supported!")

        self.arguments = BaseTestCase.parse_arguments(None, cfg_file_default)
        self.config_parameters = BaseTestCase.parse_config_file(self.arguments)
        self.sut_os_cfg = self.config_parameters.find(SutOsProvider.DEFAULT_CONFIG_PATH)

        test_log = log_utils.create_logger(class_name, False, self.config_parameters)
        print("testlog1111 ", type(test_log))

        import_module(executable_path)
        mod = import_module(executable_path, class_name)
        current_class_name = getattr(mod, class_name)

        ob = current_class_name(test_log, self.arguments, self.config_parameters)
        return ob

    def preexecution(self):
        print("Pre Executable Called")

    '''def executorhelper(self, executable_path, class_name, method_name):
        """
        executorhelper will call the function provided by input paramter using eval

        :param executable_path: executable path from the json file
        :param class_name: class name from json file
        :param method_name: method name from json file
        """

        self.cpof_log.info(str(self.executorhelper.__name__) + "Called\n")
        self.cpof_log.info('Class Name :' + str(class_name))
        self.cpof_log.info('Executable Path :' + str(executable_path))
        self.cpof_log.info('Method Name :' + str(method_name))

        object = self.preprocessing(executable_path, class_name)
        object.prepare()
        print("***************",eval(f"object.{method_name}()"))
        print("8888888888888888888888888888888888888")

    def currentexeuctable(self, user_json_data):
        """-
        b
        current executable will create the object for each entry in the json and it will call current_post_processing

        :param user_json_data : User JSON file
        """
        global process_obj
        self.cpof_log.info("Current Executable Called")
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
                        "force_terminate": False,
                        "loop_counter": 0
                    }
                }

                # Store the Process Object and it's details on a global variable which can be used through the program
                process_obj.append(temp_dict)

        # current_post_processing will start the functions which created above
        self.current_post_processing()'''

    def executorhelper(self, executable_list):
        """
        executorhelper will call the function provided by input parameter using eval

        :param executable_list: input list of executables
        """

        self.cpof_log.info(str(self.executorhelper.__name__) + "Called\n")
        self.cpof_log.info("executor list:")
        self.cpof_log.info(executable_list)
        print("executable list", executable_list)
        class_object = None
        for each in executable_list:
            # print("class name ", each[0]["class_name"])
            # print("method name", each[0]['entry_method_name'])
            # self.cpof_log.info("Inside executor help, iterate over executable list: " + str(each[0]['entry_method_name']))
            # import_object = self.preprocessing(each[0]["executable_path"], each[0]["class_name"])
            # import_object.prepare()
            # eval(f"import_object.{each[0]['entry_method_name']}()")
            print("class name ", each[0]["class_name"])
            print("method name", each[0]['entry_method_name'])
            if len(class_name_list) != 0:
                print("clash name list ", class_name_list)
                for each_class in class_name_list:
                    if each[0]["class_name"] == each_class.get("class_name"):
                        class_object = each_class.get("object")
                    else:
                        class_object = self.preprocessing(each[0]["executable_path"],  each[0]["class_name"])
                        temp_dict = {"class_name":  each[0]["class_name"], "object": class_object}
                        class_name_list.append(temp_dict)
            else:
                class_object = self.preprocessing(each[0]["executable_path"], each[0]["class_name"])
                temp_dict = {"class_name": each[0]["class_name"], "object": class_object}
                class_name_list.append(temp_dict)
            class_object.prepare()
            time.sleep(10)
            eval(f"class_object.{each[0]['entry_method_name']}()")

    def currentexeuctable(self, user_json_data):
        """
        current executable will create the object for each entry in the json and it will call current_post_processing

        :param user_json_data : User JSON file
        """
        global process_obj
        self.cpof_log.info("Current Executable Called")

        # print(user_json_data)
        for step_object in user_json_data:
            executable_list = []
            # print(step_object)
            # if step_object.get("execute_in_background"):
            for key, value in step_object['executable'].items():
                # get required parameters from the user json file
                if "pre_executable" == key and value:
                    executable_list.append(value)
                    pre_executable_path = value[0]["executable_path"]
                    pre_class_name = value[0]["class_name"]
                    pre_entry_method_name = value[0]["entry_method_name"]

                elif "current_executable" == key and value:
                    executable_list.append(value)
                    current_executable_path = value[0].get("executable_path")
                    current_class_name = value[0].get("class_name")
                    current_entry_method_name = value[0].get("entry_method_name")

                elif "post_executable" == key and value:
                    executable_list.append(value)
                    post_executable_path = value[0].get("executable_path")
                    post_class_name = value[0].get("class_name")
                    post_entry_method_name = value[0].get("entry_method_name")

            print("executable list after scanning pre cur pos: ", executable_list)

            # create the process object
            pro_run_obj = Process(target=self.executorhelper, args=(executable_list, ))
            #print("............", step_object['executable']['current_executable'][0]["current_executable_id"])
            temp_dict = {
                        "step_id": {
                            "step_id": step_object['step_id'],
                            "object": pro_run_obj,
                            "param": executable_list,
                            "Start_time": datetime.now(),
                            "force8_terminate": False,
                            "loop_counter": 0
                        }
                    }
            print(temp_dict)
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
        pro_list = []
        # this loop is to run the functions which needed the parallelism
        self.cpof_log.info("Running Parallel Functions")
        for each_process in process_obj:
            process_id = each_process.get("step_id").get("step_id")
            if JsonParserHelper(process_id, JsonFunction.get_execute_in_background_status_new):
                # start parallel process here
                # parallel function should be executed when execute in background is set to True
                self.cpof_log.info('Starting :' + str(each_process.get("step_id").get("object")))
                print(each_process["step_id"]["object"])
                # Update the process starting time
                each_process["step_id"]["Start_time"] = datetime.now()
                each_process["step_id"]["loop_counter"] = 1
                # Start the Process
                each_process.get("step_id").get("object").start()
                pro_list.append(each_process.get("step_id").get("object"))
            else:
                # check for the functions which are not executed yet. when control reaches here, non-parallel functions
                # are left, so check for non-parallel functions and execute them directly
                # get the required parameters from the user json file
                current_executable_path = JsonParserHelper(process_id, JsonFunction.get_current_executable_path)
                current_class_name = JsonParserHelper(process_id, JsonFunction.get_current_class_name)
                current_method_name = JsonParserHelper(process_id, JsonFunction.get_current_method_name)
                print("serial execution", each_process.get("step_id").get("param"))
                print("pro list 11111", pro_list)
                for obj in pro_list:
                    time.sleep(300)
                    print("onjjj", obj)
                    if not obj.is_alive():
                        self.executorhelper(each_process.get("step_id").get("param")) # current_executable_path, current_class_name, current_method_name])

        self.current_rununtil_processing()


    def current_rununtil_processing(self):
        """
        current rununtil processing will check for required run until conditions and if needed it will
        recreate the object and update the global data and rerun the process
        """
        global process_obj
        self.cpof_log.info("current_rununtil_processing Called")
        time_for_each_loop = 10
        status_check = True
        while status_check:
            # iterate through each process which is created
            status_check = False
            for each_process in process_obj:

                self.cpof_log.info(
                    "status_check value at the beginning of for loop: " + str(status_check) + str(each_process.get("step_id").get("current_id")))
                self.cpof_log.info("In for loop")
                process_id = each_process.get("step_id").get("current_id")
                self.cpof_log.info("Process status: " + str(each_process.get("step_id").get("object").is_alive()) + " " + str(each_process.get("step_id").get("current_id")))
                # using the current step id check if that process is parallel process or not.
                # if execute in background is set, then it's parallel process
                if JsonParserHelper(process_id, JsonFunction.get_execute_in_background_status): # and not each_process.get("step_id").get("object").is_alive():
                    self.cpof_log.info("Inside run until")
                    self.cpof_log.info(
                        "Process status: " + str(each_process.get("step_id").get("object").is_alive()) + str(
                            each_process.get("step_id")))

                    # get the current time and calculate how much time the function has executed
                    current_time = datetime.now()
                    start_time = each_process.get("step_id").get("Start_time")
                    difference = ((current_time - start_time).total_seconds()) / 60
                    max_time = JsonParserHelper(each_process.get("step_id").get("current_id"),
                                                JsonFunction.get_max_time_out)



                    # Calling max timeout function
                    status_max_timeout, each_process = self.rununtil_obj.check_rununtil_max_timeout(difference, max_time, each_process, process_obj)
                    self.cpof_log.info(str(each_process.get("step_id").get("current_id")) + ", max time: " + str(
                        max_time) + ", difference: " + str(difference) + " max time status: " + str(status_max_timeout))

                    # Max Time is not yet reached, run till the min timeout
                    min_time_out = JsonParserHelper(each_process.get("step_id").get("current_id"),
                                                    JsonFunction.get_run_until_min_time_out)

                    # Calling min timeout function
                    status_min_timeout = self.rununtil_obj.check_rununtil_min_timeout(difference, min_time_out)
                    self.cpof_log.info(str(each_process.get("step_id").get("current_id")) + ", min time: " + str(
                        min_time_out) + ", difference: " + str(difference) + " status min time: " + str(status_min_timeout))

                    # Calling step_id function
                    run_until_step_id = JsonParserHelper(each_process.get("step_id").get("current_id"),
                                                         JsonFunction.get_run_until_step_id)
                    status_step_id = self.rununtil_obj.check_rununtil_step_id(run_until_step_id, process_obj)
                    self.cpof_log.info(str(each_process.get("step_id").get("current_id")) + " step id status:" + str(status_step_id))

                    # Calling loop function
                    run_until_loop = JsonParserHelper(each_process.get("step_id").get("current_id"),
                                                      JsonFunction.get_run_until_loop)
                    status_loop = self.rununtil_obj.check_rununtil_loop_count(run_until_loop, each_process)
                    self.cpof_log.info(str(each_process.get("step_id").get("current_id")) + " loop_counter: " + str(each_process.get("step_id").get("loop_counter")) + " status loop: " + str(status_loop))

                    # Calling End of Life function
                    end_of_life = JsonParserHelper(each_process.get("step_id").get("current_id"),
                                                   JsonFunction.get_run_until_end_of_life)
                    self.cpof_log.info(str(each_process.get("step_id").get("current_id")) + " end of life status : " + str(end_of_life))

                    if (status_min_timeout or status_step_id or status_loop or end_of_life) and not status_max_timeout:

                        if not each_process.get("step_id").get("object").is_alive():
                            param = each_process.get("step_id").get("param")
                            print("param", param)
                            # Creating the process object
                            '''pro_run_obj = Process(target=self.executorhelper,
                                                  args=(param[0], param[1], param[2]))'''
                            pro_run_obj = Process(target=self.executorhelper,
                                                  args=param)

                            # update the new process object to the global and local variable
                            for global_each1 in process_obj:
                                if each_process.get("step_id").get("current_id") == global_each1.get(
                                        "step_id").get("current_id"):
                                    # update the global and local process object
                                    global_each1["step_id"]["object"] = pro_run_obj
                                    each_process["step_id"]["object"] = pro_run_obj

                            self.cpof_log.info("Re running the process in run until: "+str(each_process.get('step_id').get('current_id')))

                            # Increment loop counter before restarting
                            each_process["step_id"]["loop_counter"] = each_process.get("step_id").get("loop_counter") + 1

                            # Start the newly created process. (rerunning same function with new process)
                            pro_run_obj.start()
                        if not end_of_life:
                            status_check = status_check or True
                        self.cpof_log.info("reset status_check value on passing run until cond: " + str(status_check) + str(each_process.get("step_id").get("current_id")))

                    else:
                        status_check = status_check or False
                        self.cpof_log.info(
                            "reset status_check value on failing run until conf: " + str(status_check) + str(each_process.get("step_id").get("current_id")))



            post_control_status = []
            for each_process_ in process_obj:
                status = each_process_.get("step_id").get("object").is_alive()
                post_control_status.append(not status)

            self.cpof_log.info("Status check: " + str(status_check))
            self.cpof_log.info("post_control_status:" + str(post_control_status))

            time.sleep(time_for_each_loop)

        # Terminate processes with end of life set to true
        self.cpof_log.info("Call end of life terminate")
        for each_process in process_obj:
            end_of_life = JsonParserHelper(each_process.get("step_id").get("current_id"), JsonFunction.get_run_until_end_of_life)
            each_process_obj = each_process_.get("step_id").get("object")
            self.cpof_log.info("")
            if end_of_life and each_process_obj.is_alive():
                each_process_obj.terminate()
                self.cpof_log.info("Terminate process: " + str(each_process.get("step_id").get("current_id")))


def ProcessControlStatus(self):
    """
    Control Status will check for max timeout to which program can identify when it needs to be stopped.
    """
    max_time_out = []
    global process_obj
    for each in process_obj:
        if JsonParserHelper(each.get("step_id").get("current_id"), JsonFunction.get_execute_in_background_status):
            max_time_out.append(
                JsonParserHelper(each.get("step_id").get("current_id"), JsonFunction.get_max_time_out))

    self.cpof_log.info(str(self.ProcessControlStatus.__name__) + "max_time_out :" + str(max_time_out))
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
