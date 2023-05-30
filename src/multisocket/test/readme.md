
###############################################################
For phoenix ID: 16013719256 PI_stress_with_mixed_UPI_using_MLC_L
step 1: update the system configuration file
replace <cscripts>
        </cscripts> tag with  pythonsv tag shown below
    
        <pythonsv>
        <unlocker>C:\PushUtil\PushUtil.exe</unlocker>
        <debugger_interface_type>IPC</debugger_interface_type>
        <silicon>
            <cpu_family>SPR</cpu_family>
            <pch_family>EMT</pch_family>
        </silicon>
        <components>
            <component>pch</component>
            <component>socket</component>
        </components>
    </pythonsv>

step 2: update content config

        <mlc_iterations>5</mlc_iterations>

step 3: run now

#############################################################
Phoenix ID: 16014692076, upi_stressapptest_UPI_max_linkspeed

step 1: same as phoenix ID: 16013719256 step 1
step 2: run now