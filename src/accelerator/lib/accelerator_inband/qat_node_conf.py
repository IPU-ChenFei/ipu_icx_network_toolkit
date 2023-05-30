import sys
import argparse
from lnx_exec_with_check import lnx_exec_command
from get_cpu_num import get_cpu_num
from constant import *
from log import logger
import re

def qat_node_conf():
	"""
		  Purpose: Using the information above to create device configuration files that focuses on all cores.
		  Args:
			  No
		  Returns:
			  No
		  Raises:
			  RuntimeError: If any errors
		  Example:
			  Simplest usage: Using the information above to create device configuration files that focuses on all cores.
					qat_node_conf()
	"""
	get_cpu_num()
	cpu_num = int((lnx_exec_command('cat /home/logs/cpu_num.log')[1]).strip())
	if cpu_num in [2, 4, 8]:
		_, out, err = lnx_exec_command('lscpu |grep NUMA', timeout=60)
		line_list = out.strip().split('\n')
		line_num = 0
		for line in line_list:
			if line_num == 0:
				node_list1 = []
				node_list2 = []
			else:
				if line_num % 2 == 1:
					node_list1 = re.findall(r'(\d+)-(\d+)', line)
					thread_num = int(node_list1[0][1]) - int(node_list1[0][0]) + 1
					lnx_exec_command(f'python3 create_gen4_config.py {line_num*4}-{line_num*4+1} 28 {node_list1[0][0]}-{node_list1[0][1]} 0 0-0 asym 4xxx')
					lnx_exec_command(f'python3 create_gen4_config.py {line_num*4+2}-{line_num*4+3} 28 {node_list1[1][0]}-{node_list1[1][1]} 0 0-0 asym 4xxx')
				else:
					node_list2 = re.findall(r'(\d+)-(\d+)', line)
					thread_num = int(node_list2[0][1]) - int(node_list2[0][0]) + 1
					lnx_exec_command(f'python3 create_gen4_config.py {line_num*4-8}-{line_num*4-7} 28 {node_list2[0][0]}-{node_list2[0][1]} 0 0-0 asym 4xxx')
					lnx_exec_command(f'python3 create_gen4_config.py {line_num*4-6}-{line_num*4-5} 28 {node_list2[1][0]}-{node_list2[1][1]}  0 0-0 asym 4xxx')
			line_num = line_num + 1
	else:
		logger.error('Socket number is not in 2,4,8')
		raise Exception('Socket number is not in 2,4,8')


if __name__ == '__main__':
	qat_node_conf()



