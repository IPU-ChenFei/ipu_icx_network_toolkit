[Pre_Condition setup summary for all the BKC UNIQ TCDs]  
Before you run BKC UNIQ TCDs, pls prepare following steps:
1. install a python3 in the SUT, and create a python link point to python3.x under /usr/bin/python
2. run a pre_condition setup script: python BKC_UNIQ_pre_condition.py,  no errors reports
3. copy the ipmitool 1.8.18 for windows to HOST ---> C:\\BKCPkg\\ipmitoolkit_1.8.18
4. copy the memrw64 for windows to SUT C:\BKCPkg\domains\bkc_uniq\sut_scripts\
5. For TCD: 1509944103 Stress_Bonnie++_iPerf_L, need to manually setup an iperf server:
        Another SUT or a linux server with proper NIC installed works as iperf server, 
        assign a static IP 192.168.1.120 , and has iperf3 installed, and run "iperf -s " on the server.