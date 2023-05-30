def keep_running_process(step_object, run_until):
    for pre_exe_object in step_object.get("executable").get("pre_executable"):
        #
        pass
    while run_until.step_id() or run_until.min_timeout() or run_until.loo() or run_until.eol():

        for current_exe_object in step_object.get("executable").get("current_executable"):
            #
            pass

    for post_exe_object in step_object.get("executable").get("post_executable"):
        #
        pass



