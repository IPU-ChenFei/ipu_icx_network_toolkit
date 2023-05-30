For Windows driver Test cases
Download the Network Drivers from BKC and Update the Path in content_configuration.xml in drivers/network_drivers
Driver inf file name and device ID should be updated in content_configuration.xml file
Network Cable has to be Connected to Foxville Port and Need to Enable Serial Communication in SUT.

Serial Communication setup details:

1.	Download latest sut_agent from below link and copy to SUT
https://af01p-png.devtools.intel.com/artifactory/webapp/#/artifacts/browse/tree/General/dtaf-framework-release-png-local/sutagent/1.11.0/sutagent-1.11.0-py2.py3-none-any.whl 

pip3 install sutagent-1.11.0-py2.py3-none-any.whl –proxy http://proxy-chain.intel.com:911
3. Add the path "C:\Python3.6\ite-packages\" path to env path PYTHONPATH
4. Update run.bat replace python2.7 with python3
5. Run setup.bat and to configure
6. Go to folder in SUT ‘C:\Python3.6\ite-packages\sutagent\Lib\Configuration’
a. Update SUT_Config according to SUT COM port(This varies is every system.
[Main Serial Port Configuration]
port = COM3
[SUTAgent Serial Port Configuration]
port = COM3

Once all done once reboot the system. Sut agent will start automatically.
(After reboot sutagent terminal will open in the SUT)

	
System configuration Update:
<sut_os name="Windows" subtype="Win" version="10" kernel="4.18>
    <shutdown_delay>5.0</shutdown_delay>
    <driver>
        <com>
            <port>COM100</port>
            <baudrate>115200</baudrate>
            <timeout>5</timeout>
        </com>
    </driver>
</sut_os>
Content_Configuration Update:
    <drivers>
        <network_drivers>C:\Automation\BKC\Drivers\25_1.zip</network_drivers>
    </drivers>
<network>
    <spr>
        <foxville>
              <devices>
                  <device>
                      <inf_file_name>e2f68.inf</inf_file_name>
                      <deviceid>DEV_15F2</deviceid>
                  </device>
              </devices>
          </foxville>
    </spr>
</network>