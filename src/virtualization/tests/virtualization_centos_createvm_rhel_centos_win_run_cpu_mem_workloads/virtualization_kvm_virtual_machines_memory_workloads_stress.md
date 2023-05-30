TC:16014379575 - ["Virtualization-CreateVirtualmachines-Rhel-Centos-Win-CPU-Mem-Workloads"]
For the above Test Case user has to use mlc_v3 tool.
Need to run test for 200 VM so make sure that SUT has available storage space and mac id for running 
tc 
MLC tested on RHEl and CentOS 
Edit the content_config xml file for MLC runtime under <mlc> tag
<mlc_runtime>1500</mlc_runtime>
tag inside content_configuration.xml file & call it from
content_configuration.py file.
