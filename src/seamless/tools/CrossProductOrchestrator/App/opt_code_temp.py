#!/usr/bin/env python
import json
import os
import platform
import time
from datetime import datetime
from multiprocessing import Process
from importlib import import_module
import logging
import random
import sys
from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.lib import log_utils
from dtaf_core.lib.dtaf_constants import Framework
from src.seamless.tools.CrossProductOrchestrator.App.Utils.Process import SeamLessProcess
from src.seamless.tools.CrossProductOrchestrator.App.json_parser import JsonParserHelper, JsonFunction
from src.seamless.tools.CrossProductOrchestrator.App.rununtil import rununtil
from concurrent.futures import ProcessPoolExecutor
import shutil
# from dtaf_core.providers.provider_factory import ProviderFactory


process_obj = []
class_name_list = []


def get_function_exceptions():
    if not os.path.isdir(os.path.join(os.getcwd(), "temp_failures")):
        print("temp_failures is not exists")
        return []
    file_paths = []
    exception_data = []

    for root, directories, files in os.walk(os.path.join(os.getcwd(), "temp_failures")):
        for filename in files:
            if '.json' in filename:
                filepath = os.path.join(root, filename)
                file_paths.append(filepath)

    for each_file in file_paths:
        each_file_data = open(each_file, "r")
        try:
            data = json.load(each_file_data)
        except Exception as e:
            print(f"Error while opening the exception file : {each_file} Exception : {e}")
            continue
        needed = True
        for each_entry in exception_data:
            if data["class_name"] in each_entry["class_name"] and data["method_name"] in each_entry["method_name"]:
                needed = False

        if needed:
            exception_data.append(data)

    return exception_data


def store_function_exception(int_dict):
    """
    Since it's running in the process, writing to global variable will not be available outside the process.
    to avoid this issue, write the exceptions to a file in a specific directory, later we can read those and rerun it
    """
    path = os.path.join(os.getcwd(), "temp_failures", str(time.time()).replace(".", "_") + str(random.randint(1000, 9999)) + ".json")
    print("path : ", path)
    f = open(path, "a+")
    f.write(json.dumps(int_dict))
    f.close()
    time.sleep(5)


def executorhelper1(executable_path, class_name, method_name):
    global class_name_list
    # print('Class Name outside111111111111111:' + str(class_name))
    # print('Executable Path :' + str(executable_path))
    # print('Method Name :' + str(method_name))
    class_object = None
    if len(class_name_list) != 0:
        # print("class name list outside class", class_name_list)
        for each_class in class_name_list:
            if class_name == each_class.get("class_name"):
                class_object = each_class.get("object")
            else:
                obj = CrossProduct()
                class_object = obj.preprocessing(executable_path, class_name)
                temp_dict = {"class_name": class_name, "object": class_object}
                class_name_list.append(temp_dict)
    else:
        obj = CrossProduct()
        class_object = obj.preprocessing(executable_path, class_name)
        temp_dict = {"class_name": class_name, "object": class_object}
        class_name_list.append(temp_dict)
    class_object.prepare()
    eval(f"class_object.{method_name}()")


class CrossProduct:

    def __init__(self):
        self.exec_os = platform.system()
        self.arguments = None
        self.config_parameters = None
        self.sut_os_cfg = None
        self.temp_array = []
        self.cpof_log = self.get_logs("Framework log", "Framework_")
        self.rununtil_obj = rununtil()
        self.sut_ssh = None


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
        preprocessing will import the required modules, and it will return the absolute class name

        :param executable_path: executable path from the json file
        :param class_name: class name from json file

        :return: absolute class name path
        """
        self.cpof_log.info(str(self.preprocessing.__name__) + 'Called')

        try:
            cfg_file_default = Framework.CFG_FILE_PATH[self.exec_os]
        except KeyError:
            self.cpof_log.info("Error - execution OS " + str(self.exec_os) + " not supported!")
            raise RuntimeError("Error - execution OS " + str(self.exec_os) + " not supported!")

        self.arguments = BaseTestCase.parse_arguments(None, cfg_file_default)

        self.config_parameters = BaseTestCase.parse_config_file(self.arguments)
        print("config parameters", self.config_parameters)

        self.sut_os_cfg = self.config_parameters.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        print("class name ", class_name)

        test_log = log_utils.create_logger(class_name, False, self.config_parameters)
        print("test loggggggggggggggg", test_log)
        #quit()
        print("exe path ", executable_path)
        print("class name ", class_name)
        print("sys path ", sys.path)
        import_module(executable_path)
        mod = import_module(executable_path, class_name)
        current_class_name = getattr(mod, class_name)
        ob = current_class_name(test_log, self.arguments, self.config_parameters)
        # sut_ssh_cfg = cfg_opts.find(SshSutOsProvider.DEFAULT_CONFIG_PATH)
        # self.sut_os_cfg=ProviderFactory.create(sut_ssh_cfg, test_log)
        return ob

    def preexecution(self):
        print("Pre Executable Called")

    def check_sut_state(self):
        try:
            global class_name_list
            class_name = "RasScript"
            executable_path = "src.seamless.tests.bmc.functional.ras_script"
            if len(class_name_list) != 0:
                print("class name list ", class_name_list)
                for each_class in class_name_list:
                    if class_name == each_class.get("class_name"):
                        class_object = each_class.get("object")
                    else:
                        class_object = self.preprocessing(executable_path, class_name)
                        temp_dict = {"class_name": class_name, "object": class_object}
                        class_name_list.append(temp_dict)
            else:
                class_object = self.preprocessing(executable_path, class_name)
                temp_dict = {"class_name": class_name, "object": class_object}
                class_name_list.append(temp_dict)

            class_object.prepare()
            method_name = "call_sut_alive"
            result = eval(f"class_object.{method_name}()")
        except:
            result = False

        return result

    def executorhelper(self, executable_path, class_name, method_name):
        """
        executorhelper will call the function provided by input paramter using eval

        :param executable_path: executable path from the json file
        :param class_name: class name from json file
        :param method_name: method name from json file
        """
        global class_name_list
        self.cpof_log.info(str(self.executorhelper.__name__) + "Called\n")
        print('Class Name :' + str(class_name))
        print('Executable Path :' + str(executable_path))
        print('Method Name :' + str(method_name))
        #timer = 0
        '''while True:
            if not self.os.is_alive():
                if timer == 60:
                    print("System not alive from 1min, so retuning without executing the function")
                    return
                time.sleep(5)
                timer += 5
            else:
                break'''
        #try:
            # class_object = self.preprocessing(executable_path, class_name)
            # class_object.prepare()
            # eval(f"class_object.{method_name}()")
        class_object = None
        if len(class_name_list) != 0:
            print("class name list ", class_name_list)
            for each_class in class_name_list:
                if class_name == each_class.get("class_name"):
                    class_object = each_class.get("object")
                else:
                    class_object = self.preprocessing(executable_path, class_name)
                    temp_dict = {"class_name": class_name, "object": class_object}
                    class_name_list.append(temp_dict)
        else:
            class_object = self.preprocessing(executable_path, class_name)
            temp_dict = {"class_name": class_name, "object": class_object}
            class_name_list.append(temp_dict)
        class_object.prepare()
        eval(f"class_object.{method_name}()")
        '''except Exception as e:
            print(f"Exception Occurred {e} while running : {class_name} {method_name}")
            temp = {
                "class_name": class_name,
                "method_name": method_name,
                "exception": str(e)
            }
            store_function_exception(temp)
            self.cpof_log.info("In exception temp: \n")
            self.cpof_log.info(temp)'''

    def currentexeuctable(self, user_json_data):
        """
        current executable will create the object for each entry in the json, and it will call current_post_processing

        :param user_json_data : User JSON file
        """
        global process_obj
        self.cpof_log.info("Current Executable Called")
        executor = ProcessPoolExecutor(50)
        for step_object in user_json_data:
            # if step_object.get("execute_in_background"):
            current_executable = step_object.get("executable").get("current_executable")
            current_executable_count = len(current_executable)
            for each in range(current_executable_count): # easier and optimised solution --> for executable in current_executable: ## now executable becomes a dictionary ,
                # get required parameters from the user json file
                executable_path = current_executable[each].get("executable_path")
                class_name = current_executable[each].get("class_name")
                entry_method_name = current_executable[each].get("entry_method_name")

                temp_dict = {
                    "step_id": {
                        "process_id": None,
                        "executor": executor,
                        "current_id": current_executable[each].get("current_executable_id"),
                        "object": None,
                        "param": [executable_path, class_name, entry_method_name],
                        "Start_time": datetime.now(),
                        "force_terminate": False,
                        "loop_counter": 0
                    }
                }
                # Store the Process Object and it's details on a global variable which can be used through the program
                process_obj.append(temp_dict)
                print("Each block ", process_obj)

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
        #global process_sut_state

        # this loop is to run the functions which needed the parallelism
        self.cpof_log.info("Running Parallel Functions")
        print("Running Parallel Functions")
        for each_process in process_obj:
            print(f"HOWDO EACH PROCESS : {each_process}")
            process_id = each_process.get("step_id").get("current_id")
            print("process id ", process_id)
            if JsonParserHelper(process_id, JsonFunction.get_execute_in_background_status):
                print("json parser")
                # start parallel process here
                # parallel function should be executed when execute in background is set to True
                self.cpof_log.info('Starting :' + str(each_process.get("step_id").get("object")))
                # Update the process starting time
                each_process["step_id"]["Start_time"] = datetime.now()
                each_process["step_id"]["loop_counter"] = 1
                # Start the Process
                print(self.executorhelper)
                print(each_process.get("step_id").get("param")[0])
                print(each_process.get("step_id").get("param")[1])
                print(each_process.get("step_id").get("param")[2])

                pool_function = each_process.get("step_id").get("executor").submit(executorhelper1,
                                                                                   each_process.get("step_id").get(
                                                                                       "param")[0],
                                                                                   each_process.get("step_id").get(
                                                                                       "param")[1],
                                                                                   each_process.get("step_id").get(
                                                                                       "param")[2])
                each_process["step_id"]["object"] = pool_function
                each_process["step_id"]["process_id"] = os.getpid()
                #if each_process.get("step_id").get("param")[2] == "call_sut_alive":
                #    process_sut_state = pool_function


            else:
                # check for the functions which are not executed yet. when control reaches here, non-parallel functions
                # are left, so check for non-parallel functions and execute them directly
                # get the required parameters from the user json file
                current_executable_path = JsonParserHelper(process_id, JsonFunction.get_current_executable_path)
                current_class_name = JsonParserHelper(process_id, JsonFunction.get_current_class_name)
                current_method_name = JsonParserHelper(process_id, JsonFunction.get_current_method_name)
                print("exe bg false 222222", current_executable_path, current_class_name, current_method_name)
                print("no back ground",
                      self.executorhelper(current_executable_path, current_class_name, current_method_name))

        '''# wait for some time to catch the exception
        print("HOWDO PATKE FAILED PROCESS LIST")
        # for i in range(60):
        #     print("Timer : ", i)
        #     time.sleep(1)
        time.sleep(10)
        print("HOWDO PATKE DATA : ", get_function_exceptions())

        if len(get_function_exceptions()) > 0:
            print("Few Exceptions are raised while executing the functions are listed below with exception message")
            for each_failed_process in get_function_exceptions():
                print(f"Class Name : {each_failed_process['class_name']} Method Name : {each_failed_process['method_name']} Exception : {each_failed_process['exception']}")
        time.sleep(10)'''
        self.current_rununtil_processing()

    def current_rununtil_processing(self):
        """
        current rununtil processing will check for required run until conditions and if needed it will
        recreate the object and update the global data and rerun the process
        """
        global process_obj
        #global process_sut_state

        print("inside rununtil exception list:", get_function_exceptions())

        self.cpof_log.info("current_rununtil_processing Called")
        time_for_each_loop = 10
        status_check = True
        process_interrupted = []
        while status_check:
            # iterate through each process which is
            time.sleep(5)
            status_check = False
            for each_process in process_obj:

                self.cpof_log.info(
                    "status_check value at the beginning of for loop: " + str(status_check) + " " + str(
                        each_process.get("step_id").get("current_id")))
                self.cpof_log.info("In for loop")
                process_id = each_process.get("step_id").get("current_id")
                # self.cpof_log.info("Process status: " + str(each_process.get("step_id").get("object").running()) + " " + str(each_process.get("step_id").get("current_id")))
                # using the current step id check if that process is parallel process or not.
                # if execute in background is set, then it's parallel process

                if JsonParserHelper(process_id,
                                    JsonFunction.get_execute_in_background_status):  # and not each_process.get("step_id").get("object").running():
                    self.cpof_log.info("Inside run until")
                    self.cpof_log.info(
                        "Process status: " + str(each_process.get("step_id").get("object").running()) + " " + str(
                            each_process.get("step_id")))


                    '''sut_alive = process_sut_state.result()
                    self.cpof_log.info("SUT is alive status")
                    self.cpof_log.info(process_sut_state.result())
                    self.cpof_log.info(sut_alive)
                    self.cpof_log.info("In rununtil saving sut alive process object")
                    #self.cpof_log.info(pool_function)
                    #res_sut = pool_function.result()
                    #self.cpof_log.info(res_sut)
                    self.cpof_log.info(process_sut_state)
                    self.cpof_log.info(process_sut_state.exception())
                    self.cpof_log.info(process_sut_state.running())
                    self.cpof_log.info(process_sut_state.done())
                    if "call_sut_alive" in each_process["step_id"]["param"]:
                        self.cpof_log.info(each_process["step_id"]["object"].result())'''

                    # check if process was interrupted due to SSH exception (add a check for sut_is_alive)

                    '''try:
                        if "call_sut_alive" in each_process["step_id"]["param"]:
                            res = (each_process["step_id"]["object"]).result()
                            self.cpof_log.info("SUT is alive status")
                            sut_alive = res
                            self.cpof_log.info(sut_alive)
                        self.cpof_log.info("In try result")
                        self.cpof_log.info(each_process["step_id"]["param"])
                    except Exception as e:
                        process_interrupted.append(each_process)
                        self.cpof_log.info("In result exception:")
                        self.cpof_log.info(e)'''

                    # get the current time and calculate how much time the function has executed
                    current_time = datetime.now()
                    start_time = each_process.get("step_id").get("Start_time")
                    difference = ((current_time - start_time).total_seconds()) / 60
                    max_time = JsonParserHelper(each_process.get("step_id").get("current_id"),
                                                JsonFunction.get_max_time_out)

                    # Calling max timeout function
                    status_max_timeout, each_process, process_obj = self.rununtil_obj.check_rununtil_max_timeout(
                        difference, max_time, each_process, process_obj)
                    self.cpof_log.info(str(each_process.get("step_id").get("current_id")) + ", max time: " + str(
                        max_time) + ", difference: " + str(difference) + " max time status: " + str(status_max_timeout))

                    # Max Time is not yet reached, run till the min timeout
                    min_time_out = JsonParserHelper(each_process.get("step_id").get("current_id"),
                                                    JsonFunction.get_run_until_min_time_out)

                    # Calling min timeout function
                    status_min_timeout = self.rununtil_obj.check_rununtil_min_timeout(difference, min_time_out)
                    self.cpof_log.info(str(each_process.get("step_id").get("current_id")) + ", min time: " + str(
                        min_time_out) + ", difference: " + str(difference) + " status min time: " + str(
                        status_min_timeout))

                    # Calling step_id function
                    run_until_step_id = JsonParserHelper(each_process.get("step_id").get("current_id"),
                                                         JsonFunction.get_run_until_step_id)
                    status_step_id = self.rununtil_obj.check_rununtil_step_id(run_until_step_id, process_obj)
                    self.cpof_log.info(
                        str(each_process.get("step_id").get("current_id")) + " step id status:" + str(status_step_id))

                    # Calling loop function
                    run_until_loop = JsonParserHelper(each_process.get("step_id").get("current_id"),
                                                      JsonFunction.get_run_until_loop)
                    status_loop = self.rununtil_obj.check_rununtil_loop_count(run_until_loop, each_process)
                    self.cpof_log.info(str(each_process.get("step_id").get("current_id")) + " loop_counter: " + str(
                        each_process.get("step_id").get("loop_counter")) + " status loop: " + str(status_loop))

                    # Calling End of Life function
                    end_of_life = JsonParserHelper(each_process.get("step_id").get("current_id"),
                                                   JsonFunction.get_run_until_end_of_life)
                    self.cpof_log.info(
                        str(each_process.get("step_id").get("current_id")) + " end of life status : " + str(
                            end_of_life))

                    # Check for SUT alive(re-run if True)

                    sut_alive = True #self.check_sut_state()
                    self.cpof_log.info("=====================Sut status============")
                    self.cpof_log.info(sut_alive)

                    # Check for exception (re-run if False)
                    #process_exception = each_process.get("step_id").get("object").exception() # wait for function to complete

                    # if sut_alive and (status_min_timeout or status_step_id or status_loop or end_of_life) and not \
                    #
                    if status_min_timeout or status_step_id or status_loop or end_of_life and not status_max_timeout:
                    #if sut_alive and (status_min_timeout or status_step_id or end_of_life) and not status_max_timeout:

                        self.cpof_log.info("Check process status when conditional checks are True:")
                        self.cpof_log.info("Process status: " + str(each_process.get("step_id").get
                                                                    ("object").running()) + " " + str(
                            each_process.get("step_id")))

                        if not each_process.get("step_id").get("object").running():
                            param = each_process.get("step_id").get("param")

                            # Creating the process object
                            pool_function = each_process.get("step_id").get("executor").submit(executorhelper1,
                                                                                               param[0], param[1],
                                                                                               param[2])

                            # if each_process.get("step_id").get("param")[2] == "call_sut_alive":
                            #     self.process_sut_state = pool_function

                            # update the new process object to the global and local variable
                            for global_each1 in process_obj:
                                if each_process.get("step_id").get("current_id") == global_each1.get(
                                        "step_id").get("current_id"):
                                    # update the global and local process object
                                    global_each1["step_id"]["object"] = pool_function
                                    each_process["step_id"]["object"] = pool_function
                                    each_process["step_id"]["process_id"] = os.getpid()

                            self.cpof_log.info("Re running the process in run until: " + str(
                                each_process.get('step_id').get('current_id')))

                            # Increment loop counter before restarting
                            each_process["step_id"]["loop_counter"] = each_process.get("step_id").get(
                                "loop_counter") + 1

                            # Start the newly created process. (rerunning same function with new process)

                        if not end_of_life:
                            status_check = status_check or True
                        self.cpof_log.info(
                            "reset status_check value on passing run until cond: " + str(status_check) + " " + str(
                                each_process.get("step_id").get("current_id")))

                    elif not sut_alive:
                        self.cpof_log.info("status check reset to true as SUT not alive")
                        # status_check = True

                    else:
                        status_check = status_check or False or each_process.get("step_id").get("object").running()
                        # While loop continues till process ends gracefully
                        self.cpof_log.info(
                            "reset status_check value on failing run until cond: " + str(status_check) + " " + str(
                                each_process.get("step_id").get("current_id")))

                    #print("exception after sometime : ", get_function_exceptions())

            post_control_status = []
            '''for each_process_ in process_obj:
                print(each_process_)
                status = each_process_.get("step_id").get("object").running()
                post_control_status.append(not status)'''

            self.cpof_log.info("Status check: " + str(status_check))
            self.cpof_log.info("post_control_status:" + str(post_control_status))

            #time.sleep(time_for_each_loop)

        # Terminate processes with end of life set to true
        self.cpof_log.info("Call end of life terminate")
        for each_process in process_obj:
            end_of_life = JsonParserHelper(each_process.get("step_id").get("current_id"),
                                           JsonFunction.get_run_until_end_of_life)
            each_process_obj = each_process.get("step_id").get("object")
            self.cpof_log.info("")
            if end_of_life and each_process_obj.running():
                each_process_obj.cancel()
                self.cpof_log.info("Terminate process: " + str(each_process.get("step_id").get("current_id")))

        '''for each in process_obj:
            if each.get("step_id").get("object") is not None:
                try:
                    each.get("step_id").get("object").result()
                except:
                    self.cpof_log.error(
                        f'Exception came, Restarting the Process : {each.get("step_id").get("current_id")}')
                    param = each.get("step_id").get("param")
                    pool_function = each.get("step_id").get("executor").submit(self.executorhelper, param[0], param[1],
                                                                               param[2])
                    each["step_id"]["object"] = pool_function
                    each["step_id"]["process_id"] = os.getpid()'''


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
    print("user json file", userjsonfile)

    file = open(userjsonfile, 'r')
    userjsondata = json.load(file)


    '''if os.path.isdir(os.path.join(os.getcwd(), "temp_failures")):
        try:
            shutil.rmtree(os.path.join(os.getcwd(), "temp_failures"))
        except OSError as e:
            print("Error: %s - %s." % (e.filename, e.strerror))

    if not os.path.isdir(os.path.join(os.getcwd(), "temp_failures")):
        os.mkdir(os.path.join(os.getcwd(), "temp_failures"))'''

    # obj.preprocessing()
    # obj.preexecution()
    obj.currentexeuctable(userjsondata)
