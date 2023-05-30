## ac providers

### soundwave2k

```xml
<ac>
    <driver>
        <soundwave2k enable_s3_detect="False">
            <baudrate>115200</baudrate>
            <serial type="1"></serial>
            <port>COM101</port>
            <voltagethreholds>
                <main_power>
                    <low>0.8</low>
                    <high>2.85</high>
                </main_power>
                <dsw>
                    <low>0.8</low>
                    <high>2.85</high>
                </dsw>
                <memory>
                    <low>0.45</low>
                    <high>2.85</high>
                </memory>
            </voltagethreholds>
        </soundwave2k>
    </driver>
    <timeout>
        <power_on>5</power_on>
        <power_off>20</power_off>
    </timeout>
</ac>            
```

### pdu

```xml
<!-->single outlet<-->
<ac>
    <timeout>
        <power_on>5</power_on>
        <power_off>20</power_off>
    </timeout>
    <driver>
        <pdu brand="raritan" model="px-5052R">
            <ip>10.239.181.249</ip>
            <port>22</port>
            <username>admin</username>
            <password>raritan</password>
            <timeout>
                <powerstate>10</powerstate>
                <invoke>0</invoke>
            </timeout>
            <outlets>
                <outlet>1</outlet>
            </outlets>
        </pdu>
    </driver>
</ac>
```

```xml
<!-->multi-outlets<-->
<ac>
    <timeout>
        <power_on>5</power_on>
        <power_off>20</power_off>
    </timeout>
    <driver>
        <pdu brand="raritan" model="px-5052R">
            <ip>10.239.181.249</ip>
            <port>22</port>
            <username>admin</username>
            <password>raritan</password>
            <timeout>
                <powerstate>10</powerstate>
                <invoke>0</invoke>
            </timeout>
            <outlets>
                <outlet>1</outlet>
            </outlets>
        </pdu>
    </driver>
</ac>
```

### pduusb

```xml
<ac>
    <driver>
        <pduusb>
            <outlets>
                <outlet>1</outlet>
            </outlets>
        </pduusb>
    </driver>
    <timeout>
        <power_on>2</power_on>
        <power_off>6</power_off>
    </timeout>
</ac>
```

### rsc2

```xml
<ac>
    <driver>
        <rsc2>
        </rsc2>
    </driver>
    <timeout>
        <power_on>5</power_on>
        <power_off>20</power_off>
    </timeout>
</ac>
```

### bmc redfish

```xml
<ac>
    <driver>
        <redfish>
            <bmc_type>intel</bmc_type>
            <ip>192.168.1.100</ip>
            <username>root</username>
            <password>0penBmc1</password>
        </redfish>
    </driver>
    <timeout>
        <power_on>5</power_on>
        <power_off>20</power_off>
    </timeout>
</ac>
```

### bmc redfish ac

```xml
<ac>
    <driver>
        <redfish>
            <bmc_type>intel</bmc_type>
            <ip>192.168.1.100</ip>
            <username>root</username>
            <password>0penBmc1</password>
        </redfish>
    </driver>
    <timeout>
        <power_on>5</power_on>
        <power_off>20</power_off>
    </timeout>
</ac>
```

### rasp

```xml
<ac>
    <driver>
        <rasp>
            <token>79085785516500bffetabb3d12ac4ce9</token>
            <systemid>4733</systemid>
            <entry>https://onecloudapi.intel.com</entry>
        </rasp>
    </driver>
    <timeout>
        <power_on>5</power_on>
        <power_off>20</power_off>
    </timeout>
</ac>
```

### simics

```xml
<ac>
    <driver>
        <simics>
            <mode>
                <real-time>True</real-time>
            </mode>
            <serial_port>2122</serial_port>
            <host>
                <name>10.148.205.212</name>
                <port>22</port>
                <username>sys_pvauto</username>
                <password>xxx</password>
            </host>
            <os>centos_stream</os>
            <service_port>2123</service_port>
            <app>/nfs/site/disks/simcloud_users/czhao/workarea/projects/gnr-6.0/2021ww35.3/simics</app>
            <project>/nfs/site/disks/simcloud_users/czhao/workarea/projects/gnr-6.0/2021ww35.3</project>
            <script>/nfs/site/disks/simcloud_users/czhao/workarea/projects/gnr-6.0/2021ww35.3/targets/birchstream/birchstream-ap.simics</script>
            <disk_image>/nfs/site/disks/simcloud_zijianhu_002/Auto_Image/centos_22314.craff</disk_image>
        </simics>
    </driver>
    <timeout>
        <power_on>5</power_on>
        <power_off>20</power_off>
    </timeout>
</ac>
```

## dc providers

### soundwave2k

```xml
<dc>
    <driver>
        <soundwave2k enable_s3_detect="False">
            <baudrate>115200</baudrate>
            <serial type="1"></serial>
            <port>COM101</port>
            <voltagethreholds>
                <main_power>
                    <low>0.8</low>
                    <high>2.85</high>
                </main_power>
                <dsw>
                    <low>0.8</low>
                    <high>2.85</high>
                </dsw>
                <memory>
                    <low>0.45</low>
                    <high>2.85</high>
                </memory>
            </voltagethreholds>
        </soundwave2k>
    </driver>
    <timeout>
        <power_on>5</power_on>
        <power_off>20</power_off>
    </timeout>
</dc> 
```

### banino

```xml
<dc>
    <driver>
        <banino>
            <banino_dll_path>C:\banino\Banino_SxState\x64\ladybird.dll</banino_dll_path>
            <banino_power_cmd>C:\banino\Banino_SxState</banino_power_cmd>
            <ladybird_driver_serial>404242433</ladybird_driver_serial>
        </banino>
    </driver>
    <timeout>
        <power_on>3</power_on>
        <power_off>6</power_off>
    </timeout>
</dc>
```

### rsc2

```xml
<dc>
    <driver>
        <rsc2>
        </rsc2>
    </driver>
    <timeout>
        <power_on>5</power_on>
        <power_off>20</power_off>
    </timeout>
</dc>
```

### bmc redfish

```xml
<dc>
    <driver>
        <redfish>
            <bmc_type>intel</bmc_type>
            <ip>192.168.1.100</ip>
            <username>root</username>
            <password>0penBmc1</password>
        </redfish>
    </driver>
    <timeout>
        <power_on>5</power_on>
        <power_off>20</power_off>
    </timeout>
</dc>
```

### ad-usb/usb-relay

```
<dc>
	<driver>
		<pin>
			<power_state>
				<port>COM20</port>
				<baudrate>115200</baudrate>
				<threholds>
					<high>1.7</high>
					<low>0.6</low>
				</threholds>
			</power_state>
			<front_panel>
				<port>COM20</port>
				<baudrate>115200</baudrate>
			</front_panel>
			<jumper>
				<port>COM21</port>
				<baudrate>9200</baudrate>
			</jumper>
		</pin>

	</driver>
	<timeout>
		<power_on>3</power_on>
		<power_off>6</power_off>
	</timeout>
</dc>
```

### simics

```xml
<dc>
    <driver>
        <simics>
            <mode>
                <real-time>True</real-time>
            </mode>
            <serial_port>2122</serial_port>
            <host>
                <name>10.148.205.212</name>
                <port>22</port>
                <username>sys_pvauto</username>
                <password>xxx</password>
            </host>
            <os>centos_stream</os>
            <service_port>2123</service_port>
            <app>/nfs/site/disks/simcloud_users/czhao/workarea/projects/gnr-6.0/2021ww35.3/simics</app>
            <project>/nfs/site/disks/simcloud_users/czhao/workarea/projects/gnr-6.0/2021ww35.3</project>
            <script>/nfs/site/disks/simcloud_users/czhao/workarea/projects/gnr-6.0/2021ww35.3/targets/birchstream/birchstream-ap.simics</script>
            <disk_image>/nfs/site/disks/simcloud_zijianhu_002/Auto_Image/centos_22314.craff</disk_image>
        </simics>
    </driver>
    <timeout>
        <power_on>5</power_on>
        <power_off>20</power_off>
    </timeout>
</dc>
```

## physical providers 

### soundwave2k

```xml
<physical_control>
    <driver>
        <soundwave2k enable_s3_detect="False">
            <baudrate>115200</baudrate>
            <serial type="1"></serial>
            <port>COM101</port>
            <voltagethreholds>
                <main_power>
                    <low>0.8</low>
                    <high>2.85</high>
                </main_power>
                <dsw>
                    <low>0.8</low>
                    <high>2.85</high>
                </dsw>
                <memory>
                    <low>0.45</low>
                    <high>2.85</high>
                </memory>
            </voltagethreholds>
        </soundwave2k>
    </driver>
    <host_usb md5="True">d:\</host_usb>
    <timeout>
        <power_on>5</power_on>
        <power_off>20</power_off>
        <usbswitch>10</usbswitch>
    </timeout>
</physical_control>
```

### banino

```xml
<physical_control>
    <driver>
        <banino>
            <banino_dll_path>C:\banino\Banino_SxState\x64\ladybird.dll</banino_dll_path>
            <banino_power_cmd>C:\banino\Banino_SxState</banino_power_cmd>
            <ladybird_driver_serial>404242433</ladybird_driver_serial>
        </banino>   
    </driver>
    <timeout>
        <usbswitch>4</usbswitch>
        <clearcmos>3</clearcmos>>
    </timeout>
</physical_control>
```

### rsc2

```xml
<physical_control>
    <driver>
        <rsc2>
        </rsc2>
    </driver>
    <timeout>
        <power_on>5</power_on>
        <power_off>20</power_off>
    </timeout>
</physical_control>
```

### ad-usb/usb-relay

ad-usb supports power_state and front_panel.

usb-relay supports jumper.

```xml
<physical_control>
    <driver>
        <pin>
            <power_state>
                <port>COM20</port>
                <baudrate>115200</baudrate>
            </power_state>
            <front_panel>
                <port>COM20</port>
                <baudrate>115200</baudrate>
            </front_panel>    
            <jumper>
                <port>COM30</port>
                <baudrate>9200</baudrate>
            </jumper>
        </pin>
    </driver>
</physical_control>
```

### usbblaster(only support get postcode)

```xml
<physical_control>
    <driver>
        <usbblaster>
            <cpld_application_path>
                C:\intelFPGA_pro\19.2\qprogrammer\quartus\bin64\
            </cpld_application_path>
            <primary_image_path></primary_image_path>
            <primary_image_name></primary_image_name>
            <secondary_image_path></secondary_image_path>
            <secondary_image_name></secondary_image_name>
        </usbblaster>
    </driver>
    <timeout>
        <usbswitch>4</usbswitch>
        <clearcmos>3</clearcmos>>
    </timeout>
</physical_control>
```

### ad-usb/usb-relay

```
<physical_control>
	<driver>
		<pin>
			<power_state>
				<port>COM20</port>
				<baudrate>115200</baudrate>
				<threholds>
					<high>1.7</high>
					<low>1.1</low>
				</threholds>
			</power_state>
			<front_panel>
				<port>COM20</port>
				<baudrate>115200</baudrate>
			</front_panel>
			<jumper>
				<port>COM21</port>
				<baudrate>9200</baudrate>
			</jumper>
		</pin>
	</driver>
</physical_control>
```

## ssh providers

### windows

```xml
<sut_os name="Windows" subtype="windows" version="10" kernel="3.10" id="Windows Boot Manager">
    <shutdown_delay>5.0</shutdown_delay>
    <driver>
        <ssh>
            <credentials user="administrator" password="password"/>
            <ipv4>192.168.0.2</ipv4>
            <port>22</port>
        </ssh>
    </driver>
</sut_os>

```

### redhat

```xml
<sut_os name="Linux" subtype="redhat" version="8.2" kernel="4.18" id="Red Hat Enterprise Linux">
    <shutdown_delay>5.0</shutdown_delay>
    <driver>
        <ssh>
            <credentials user="root" password="password"/>
            <ipv4>192.168.0.2</ipv4>
            <port>22</port>
        </ssh>
    </driver>
</sut_os>
```

### centos

```xml
<sut_os name="Linux" subtype="centos" version="8.2" kernel="4.18" id="CentOS Linux">
    <shutdown_delay>5.0</shutdown_delay>
    <driver>
        <ssh>
            <credentials user="root" password="password"/>
            <ipv4>192.168.0.2</ipv4>
            <port>22</port>
        </ssh>
    </driver>
</sut_os>
```

### vmware

```xml
<sut_os name="Linux" subtype="vmware" version="8.2" kernel="4.18" id="VMware ESXi">
    <shutdown_delay>5.0</shutdown_delay>
    <driver>
        <ssh>
            <credentials user="root" password="password"/>
            <ipv4>192.168.0.2</ipv4>
            <port>22</port>
        </ssh>
    </driver>
</sut_os>
```

### fedora

```xml
<sut_os name="Linux" subtype="fedora" version="8.2" kernel="4.18" id="Fedora">
    <shutdown_delay>5.0</shutdown_delay>
    <driver>
        <ssh>
            <credentials user="root" password="password"/>
            <ipv4>192.168.0.2</ipv4>
            <port>22</port>
        </ssh>
    </driver>
</sut_os>
```

## com bios providers

### setup menu

```xml
<bios_setupmenu>
    <driver>
        <com>
            <baudrate>115200</baudrate>
            <port>COM100</port>
            <timeout>5</timeout>
        </com>
    </driver>
    <efishell_entry select_item="UEFI Internal Shell">
        <path>
            <node>Boot Manager Menu</node>
        </path>
    </efishell_entry>
    <continue select_item="Continue"/>
    <reset press_key="\33R\33r\33R" parse="False"/>
</bios_setupmenu>
```

### boot menu

```xml
<bios_bootmenu>
    <driver>
        <com>
            <baudrate>115200</baudrate>
            <port>COM100</port>
            <timeout>5</timeout>
        </com>
    </driver>
    <efishell_entry select_item="UEFI Internal Shell"/>
</bios_bootmenu>
```

### uefi shell

```xml
<uefi_shell>
    <driver>
        <com>
            <port>COM100</port>
            <baudrate>115200</baudrate>
            <timeout>5</timeout>
        </com>
    </driver>
</uefi_shell>
```

## xmlcli bios provider

### linux xmlcli

```xml
<bios>
    <driver>
        <xmlcli>
            <sutospath>/opt/APP/xmlcli/</sutospath>
            <bios_cfgfilepath>/opt/APP/xmlcli/</bios_cfgfilepath>
            <bios_cfgfilename>PlatformConfig.xml</bios_cfgfilename>
            <ip>192.168.0.2</ip>
            <port>22</port>
            <user>root</user>
            <password>password</password>
            <python_path>C:\Python36\</python_path>
        </xmlcli>
    </driver>
</bios>
```

### windows xmlcli

```xml
<bios>
    <driver>
        <xmlcli>
            <sutospath>C:\BKCPkg\xmlcli\</sutospath>
            <bios_cfgfilepath>/opt/APP/xmlcli/</bios_cfgfilepath>
            <bios_cfgfilename>PlatformConfig.xml</bios_cfgfilename>
            <ip>192.168.0.2</ip>
            <port>22</port>
            <user>administrator</user>
            <password>password</password>
            <python_path>C:\Python36\</python_path>
        </xmlcli>
    </driver>
</bios>
```

### vmware xmlcli

```xml
<bios>
    <driver>
        <xmlcli>
            <sutospath>/var/tmp/xmlcli/</sutospath>
            <bios_cfgfilepath>/opt/APP/xmlcli/</bios_cfgfilepath>
            <bios_cfgfilename>PlatformConfig.xml</bios_cfgfilename>
            <ip>192.168.0.2</ip>
            <port>22</port>
            <user>root</user>
            <password>password</password>
            <python_path>C:\Python36\</python_path>
        </xmlcli>
    </driver>
</bios>
```

## sol bios providers

### setup menu

```xml
<bios_setupmenu>
    <driver>
        <sol>
            <address>192.168.0.2</address>
            <port>2200</port>
            <timeout>60</timeout>
            <credentials user="root" password="0penBmc1"/>
        </sol>
    </driver>
    <efishell_entry select_item="Launch EFI Shell">
        <path>
            <node>Setup Menu</node>
            <node>Boot Manager</node>
        </path>
    </efishell_entry>
    <continue select_item="Continue"/>
    <reset press_key="\33R\33r\33R" parse="False"/>
</bios_setupmenu>
```

### boot menu

```xml
<bios_bootmenu>
    <driver>
        <sol>
            <address>192.168.0.2</address>
            <port>2200</port>
            <timeout>60</timeout>
            <credentials user="root" password="0penBmc1"/>
        </sol>
    </driver>
    <efishell_entry select_item="UEFI Internal Shell"/>
</bios_bootmenu>
```

### uefi_shell

```xml
<uefi_shell>
    <driver>
        <sol>
            <address>192.168.0.2</address>
            <port>2200</port>
            <timeout>60</timeout>
            <credentials user="root" password="0penBmc1"/>
        </sol>
    </driver>
</uefi_shell>
```

## simics bios providers

### setup menu

```xml
<bios_setupmenu>
    <driver>
        <simics>
            <mode>
                <real-time>True</real-time>
            </mode>
            <serial_port>2122</serial_port>
            <host>
                <name>10.148.205.212</name>
                <port>22</port>
                <username>sys_pvauto</username>
                <password>xxx</password>
            </host>
            <service_port>2123</service_port>
            <app>/nfs/site/disks/simcloud_users/czhao/workarea/projects/gnr-6.0/2021ww35.3/simics</app>
            <project>/nfs/site/disks/simcloud_users/czhao/workarea/projects/gnr-6.0/2021ww35.3</project>
            <script>/nfs/site/disks/simcloud_users/czhao/workarea/projects/gnr-6.0/2021ww35.3/targets/birchstream/birchstream-ap.simics</script>
        </simics>
    </driver>
    <efishell_entry select_item="Launch EFI Shell">
        <path>
            <node>Setup Menu</node>
            <node>Boot Manager</node>
        </path>
    </efishell_entry>
    <continue select_item="Continue"/>
    <reset press_key="\33R\33r\33R" parse="False"/>
</bios_setupmenu>
```

### boot menu

```xml
<bios_bootmenu>
    <driver>
        <simics>
            <mode>
                <real-time>True</real-time>
            </mode>
            <serial_port>2122</serial_port>
            <host>
                <name>10.148.205.212</name>
                <port>22</port>
                <username>sys_pvauto</username>
                <password>xxx</password>
            </host>
            <service_port>2123</service_port>
            <app>/nfs/site/disks/simcloud_users/czhao/workarea/projects/gnr-6.0/2021ww35.3/simics</app>
            <project>/nfs/site/disks/simcloud_users/czhao/workarea/projects/gnr-6.0/2021ww35.3</project>
            <script>/nfs/site/disks/simcloud_users/czhao/workarea/projects/gnr-6.0/2021ww35.3/targets/birchstream/birchstream-ap.simics</script>
        </simics>
    </driver>
    <efishell_entry select_item="UEFI Internal Shell"/>
</bios_bootmenu>
```

### uefi shell

```xml
<uefi_shell>
    <some></some>
    <driver>
        <simics>
            <mode>
                <real-time>True</real-time>
            </mode>
            <serial_port>2122</serial_port>
            <host>
                <name>10.148.205.212</name>
                <port>22</port>
                <username>sys_pvauto</username>
                <password>xxx</password>
            </host>
            <service_port>2123</service_port>
            <app>/nfs/site/disks/simcloud_users/czhao/workarea/projects/gnr-6.0/2021ww35.3/simics</app>
            <project>/nfs/site/disks/simcloud_users/czhao/workarea/projects/gnr-6.0/2021ww35.3</project>
            <script>/nfs/site/disks/simcloud_users/czhao/workarea/projects/gnr-6.0/2021ww35.3/targets/birchstream/birchstream-ap.simics</script>
        </simics>
    </driver>
</uefi_shell>
```

## console log providers

### bios com log

```xml
<console_log>
    <runwith/>
    <logpath>C:\toolkit_logs\bios.log</logpath>
    <driver>
        <com>
            <port>COM100</port>
            <baudrate>115200</baudrate>
            <timeout>5</timeout>
        </com>
    </driver>
    <timestamp>true</timestamp>
</console_log>
```

## bmc console provider

### bmc console

```xml
<console>
    <driver>
        <com>
            <baudrate>115200</baudrate>
            <port>COM102</port>
            <timeout>10</timeout>
        </com>
    </driver>
    <credentials user="root" password="0penBmc1"/>
    <login_time_delay>60</login_time_delay>
</console>
```

## flash providers

### dediprog

```xml
<flash>
    <driver>
        <sf100 cli_path="C:\Program Files (x86)\DediProg\SF Programmer\">
            <pch name="SF600961" chip="MX25L51245G" />
            <bmc name="DP025750" chip="MX66L1G45G" />
        </sf100>
    </driver>
</flash>
```

### y2prog

```
<flash>
	<driver>
		<y2prog>
			<cli_path>"C:\Program file\Y2progCli.exe"</cli_path>
			<bmc>
				<sn>306HWW58</sn>
				<image>OBMC-egs-0.91-107-g91b3fb-9248c75-pfr-full.ROM</image>
			</bmc>
			<bios>
				<sn>306DUHC2</sn>
				<image>EGSDCRB.SYS.OR.64.2022.15.4.03.1538.0_SPR_EBG_SPS.bin</image>
			</bios>
		</y2prog>
	</driver>
</flash>
```



