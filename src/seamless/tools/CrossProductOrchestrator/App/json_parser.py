import enum
import json
import os


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
    get_pre_executable_current_id = 12
    get_execute_in_background_status_new = 13


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

    elif request_data == JsonFunction.get_execute_in_background_status_new:
        for step_object in user_json_data:
            if current_step_id == step_object.get("step_id"):
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

    elif request_data == JsonFunction.get_pre_executable_path:
        for step_object in user_json_data:
            pre_executable = step_object.get("executable").get("pre_executable")
            for each in pre_executable:
                if current_step_id == each.get("pre_executable_id"):
                    return each.get("executable_path")

    elif request_data == JsonFunction.get_pre_class_name:
        for step_object in user_json_data:
            pre_executable = step_object.get("executable").get("pre_executable")
            for each in pre_executable:
                if current_step_id == each.get("pre_executable_id"):
                    return each.get("class_name")

    elif request_data == JsonFunction.get_pre_method_name:
        for step_object in user_json_data:
            pre_executable = step_object.get("executable").get("pre_executable")
            for each in pre_executable:
                if current_step_id == each.get("pre_executable_id"):
                    return each.get("entry_method_name")

    print("Invalid Data Requested")
    return None
