For test case H81603 - PI_Powermanagement_Check_CPU_temperature_L,
To verify DTS CPU and Die CPU temperature.

and For test case 18016909531 - PI_Powermanagement_Check_CPU_PCH_temperature_L,
To verify CPU cores temperature.

1) Operating system : Linux 
2) BMC should be enabled.
In system_configuration.xml, under providers tag, we need to add,
   <console id="BMC">
        <driver>
            <com>
                <baudrate>115200</baudrate>
                <port>COM39</port>
                <timeout>10</timeout>
            </com>
        </driver>
        <credentials user="root" password="0penBmc1"/>
        <login_time_delay>60</login_time_delay>
    </console> 

port will be BMC serial cable connected COM port in the Host.

By using BMC, we are running CPU cooling fan with 100% RPM Speed.
pwm16 is for the first CPU fan and pwm15 is for the second CPU fan.
J9K2 - CPU0 Fan, J1K2 - CPU1 Fan

Commands to set CPU Fan speed to 100% is : 
echo 255 > /sys/class/hwmon/hwmon0/pwm16, echo 255 > /sys/class/hwmon/hwmon0/pwm15

Commands to display value : 
cat /sys/class/hwmon/hwmon0/pwm16, cat /sys/class/hwmon/hwmon0/pwm15

Note: Heat sink mounting should proper.
