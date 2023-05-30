import subprocess
my_command = 'script_in_py2.exe arg1 arg2'
process = subprocess.Popen(my_command.split(), stdout=subprocess.PIPE)
output, error = process.communicate()
