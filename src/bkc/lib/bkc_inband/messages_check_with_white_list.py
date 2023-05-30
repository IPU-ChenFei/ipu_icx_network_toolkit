import os

print("\nprint the whole messages log\n")
print(os.popen("cat /var/log/messages ").read().strip())


print("\n[[[  ","dmesg error log  white list","   ]]]\n")

white_list=['ERST: Error Record Serialization Table (ERST) support is initialized',
            'xpmem: module verification failed: signature and/or required key missing',
            'ACPI Error: No handler for Region [SYSI]',
            'ACPI Error: Region IPMI',
            'ACPI Error: Aborting method \\_SB.PMI0._GHL',
            'ACPI Error: Aborting method \\_SB.PMI0._PMC',
            'ACPI Error: AE_NOT_EXIST, Evaluating _PMC',
            'blk_update_request: I/O error',
            'tpm tpm0: tpm_try_transmit',
            'ice: module verification failed: signature and/or required key missing',
            'isgx: module verification failed:',
            '4xxx 0000:6b:00.0: QAT: Failed to enable AER, error code -5',
            '4xxx 0000:70:00.0: QAT: Failed to enable AER, error code -5',
            '4xxx 0000:75:00.0: QAT: Failed to enable AER, error code -5',
            '4xxx 0000:7a:00.0: QAT: Failed to enable AER, error code -5',
            '4xxx 0000:e8:00.0: QAT: Failed to enable AER, error code -5',
            '4xxx 0000:ed:00.0: QAT: Failed to enable AER, error code -5',
            '4xxx 0000:f2:00.0: QAT: Failed to enable AER, error code -5',
            '4xxx 0000:f7:00.0: QAT: Failed to enable AER, error code -5',
            'pci 0000:81:00.0: BAR 6: failed to assign [mem size 0x00100000 pref]',
            'SVKL: get table failed',
            'fail to initialize ptp_kvm',
            'emmitsburg-pinctrl INTC1071:00: failed to lookup the default state',
            'emmitsburg-pinctrl INTC1071:00: failed to lookup the sleep state'
            ]

for line in white_list:
    print("-------",line)



print("\n[[[   ","print out all the errors in dmesg log", "   ]]]\n")
dmesg_error_content=os.popen("dmesg -T | grep -iE 'Error|Fail|Failed'").read().split('\n')
dmesg_error_content.pop()
for line in dmesg_error_content:
    print("-------",line)



print("\n[[[","Compare the errors with white list", "   ]]]\n")

error_report=[]
true_error=[]
#Get the same error in white list
for line in dmesg_error_content:
    for item in white_list:
        if item in line:
            error_report.append(line)
            #dmesg_error_content.remove(line) # this method cause orginal list change, failed


#filter out the errors not in the white list
for line in dmesg_error_content:
    if line not in error_report:
        print("+++++++",line)
        true_error.append(line)


print("============================================")
print(true_error)


if len(true_error) == 0:
    print("dmesg log check pass, no extra Errors found out of white list")
else:
    raise Exception('[[[   dmesg show error   ]]]')

