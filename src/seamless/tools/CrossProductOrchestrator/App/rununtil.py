import os
import signal


class rununtil():

    def __init__(self):
        pass

    def check_rununtil_step_id(self, run_until_step_id, process_obj):
        status = False
        for each_rununtil_step_id in run_until_step_id:
            # process_obj is global
            #print(each_rununtil_step_id)
            for each in process_obj:
                #print(each)
                if each_rununtil_step_id == each.get("step_id").get("current_id"):
                    run_until_process_obj = each.get("step_id").get("object")
                    if run_until_process_obj.running():
                        #print("Run unitl step id is true")
                        status = True
        return status

    def check_rununtil_min_timeout(self, difference, min_time_out):
        # If run time is still less than min timeout return True
        if difference < float(min_time_out):
            return True
        else:
            return False

    def check_rununtil_max_timeout(self, difference, max_time, each_process, process_obj):
        #global process_obj
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
            # if each_process_obj.is_alive():
            # print(each_process.get("step_id").get("current_id"), "exceeds the Max Time")
            # Terminate the process since it reaches to its maximum limit if its alive
            if each_process.get("step_id").get("process_id") is not None:
                os.kill(each_process.get("step_id").get("process_id"), signal.SIGTERM)
            status = True
        else:
            status = False
        return status, each_process, process_obj

    def check_rununtil_loop_count(self, run_until_loop, each_process):
        # We have already completed first iteration when we start the function first time
        # Here we will restart when loop count>1
        if each_process.get("step_id").get("loop_counter") < run_until_loop:
            return True
        else:
            return False
