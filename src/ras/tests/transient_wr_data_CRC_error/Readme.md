HPALM ID : 81514
This test verifies Transient WR CRC Data Error using Cscripts
Steps to be noted before running the Test case:
 1. Please update the Socket, channel and MC number in the Content_configuration.xml file found in the path:
dtaf_content\src\configuration\content_configuration.xml
   2. Elements to update the values:
ras
        memory
            socket 0 
            channel 0 
            micro_controller 0
    