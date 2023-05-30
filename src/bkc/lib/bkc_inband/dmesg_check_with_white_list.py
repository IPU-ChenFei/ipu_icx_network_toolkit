import os

print("\nprint the whole dmesg log\n")
print(os.popen("dmesg -T ").read().strip())


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

