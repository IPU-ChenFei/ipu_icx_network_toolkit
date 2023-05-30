#!/usr/bin/env bash
####################################################
# Date: 20210801
# Multi VM setup script
#
# Launch Multiple VMs with MDEV Devices
# 
# Recommended: Setup master image with ssh keys or no password. 
#
# Tested with:
# accel-config: 3.4+
# idxd: 1.00
####################################################
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

# source config and library
for f in config.sh lib.sh ; do 
    if [[ -f ${DIR}/${f} ]] ; then
        . ${DIR}/${f}
    else 
        echo -e "\n${f} not found!"
        exit 1
    fi
done

# check for BIOS and image files
for c in VM_IMAGE VM_BIOS ; do 
    if [[ ! -f ${!c} ]] ; then 
        echo -e "Error: ${!c} Does not exist. Please verify configuration in ${DIR}/config.sh"
        exit 1 
    fi
done

command -v accel-config &> /dev/null
[[ $? -ne 0 ]] && { echo -e "\n$0 requires: accel-config\n" ; exit 1 ; }

# verify QEMU installed
command -v /usr/libexec/qemu-kvm &> /dev/null
[[ $? -ne 0 ]] && { echo -e "\n$0 requires /usr/libexec/qemu-kvm\n" ; }

# check for root
[[ $UID -ne 0 ]] && { echo "$0 requires root privileges" ; exit 1 ; }

IOMMU_CONFIGS=( "gpa" "giova" "gva" )
# default variables
ssh_cmd='ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR  '
number_of_vm=''
shutdown_vms=false
vm_cmd=''
cores=1
mdev_devices_per_vm=1
iommu_config="gva"
iax_devices="dsa"

# Start Functions
function show_help () {
    echo -e "\nUseage: $0 <options>"
    echo -e "\nOptions:"
    echo -e "\n\t-h\tShow Help."
    echo -e "\t-s\tShutdown running VMs."
    echo -e "\t-r\t \"<command>\"\t\tCommand to run on VMs."
    echo -e "\t-i\tUse IAX devices. Default is ${iax_devices}."

    echo -e "\nConfiguration Options:"
    echo -e "\t-n\t <VMs>\t\tNumber of VMs to create."
    echo -e "\t-c\t <cores>\tNumber of CPU cores. Default: ${cores}"
    echo -e "\t-m\t <MDEVS>\tMax number MDEV devices per VM. Actual number may be limited by config Default: ${mdev_devices_per_vm}"
    echo -e "\t-q \"<IOMMU CONFIG>\"\tQEMU IOMMU device configuration. Default ${iommu_config}\n\tAvailable IOMMU config options: ${IOMMU_CONFIGS[@]}"
    echo -e "\t-v \"<MiB>\"\tMemory used for VM in MiB.\n\tDefault ${VM_MEMORY}"
    
    echo -e ""
}

# parse command line options
type_options=0
while getopts "hisc:m:n:q:r:v:" arg ; do
    case $arg in
        c)
            if ! [[ "${cores}" =~ ^[0-9]+$ ]]; then
                echo -e "Cores '-c' must be an integer!"
                show_help
                exit 0
            fi
			cores="$OPTARG"
            ;;
        m)
            if ! [[ "${OPTARG}" =~ ^[0-9]+$ ]]; then
                echo -e "MDEVs per VM '-m' must be a number!"
                show_help
                exit 0
            fi
			mdev_devices_per_vm="$OPTARG"
            ;;
        n)
            if ! [[ "${OPTARG}" =~ ^[0-9]+$ ]]; then
                echo -e "Number of VMs '-n' must be a number!"
                show_help
                exit 0
            fi
			number_of_vm="$OPTARG"
            ;;
        r)
            vm_cmd="$OPTARG"
            ;;
        q)
            if ! [[ " ${IOMMU_CONFIGS[@]} " =~ " ${OPTARG} " ]]; then
                echo -e "\nOops: iommu configuration must be in list of available iommu configurations!" 
                show_help
                exit 0
            fi
			iommu_config="$OPTARG"
            ;;
        s)
            shutdown_vms=true
            ;;
        i)
            iax_devices=iax
            ;;
        v)
            if ! [[ "${OPTARG}" =~ ^[0-9]+$ ]]; then
                echo -e "-v <MiB> must be an int!"
                show_help
                exit 0
            fi
            VM_MEMORY="$OPTARG"
            ;;
        h)
            show_help
            exit 0
            ;;
        \?)
            echo -e "Invalid option $OPTARG" >&2
            show_help
            exit 1
            ;;
        :) 
            echo "Missing option argument for -$OPTARG" >&2
            show_help
            exit 1
            ;;
        *)
            show_help
            exit 1
            ;;
    esac
done

# Sanity check 
if [[ $OPTIND == 1 ]]; then
   echo -e "\nNo options given."
   show_help
   exit 1
fi


# End Functions


# Main Execution
if [[ ${number_of_vm} ]] ; then 
    
    # Create log
    log_dir="${DIR}/logs/Multi_VM-$TIMESTAMP"
    [[ -d "${log_dir}" ]] || { mkdir -p "${log_dir}" ; }
    
    shutdown_running_vms
    
    devices_to_test=( $(get_enabled_wqs mdev ${iax_devices}) )
    
    if [[ "${#devices_to_test[@]}" -eq 0 ]] ; then 
        echo -e "No 'mdev' type work-queues found! \nTry configuring devices first." 
        exit 1 
    fi
    
    create_qcow_images ${number_of_vm}
    launch_vms ${number_of_vm} "${iax_devices}" ${mdev_devices_per_vm} ${iommu_config} ${devices_to_test[@]}
    echo -n "Launching ${number_of_vm} Virtual Machines"
    for i in $(seq 10) ; do echo -n '.' ; sleep 1 ; done
    sleep 10
#    running_vms=$( get_running_vms )
#    echo -e "\n\nChecking for devices."
#    run_cmd_vms "lspci | egrep '0b25|0cfe'"

#    echo -e "\n### VM SSH Connection Info ###"
#    for v in ${running_vms} ; do
#        echo -e "VM running on port ${v}..." | tee -a ${log_dir}/multi_vm.log
#        echo -e "to connect to VM: ssh -p ${v} localhost" | tee -a ${log_dir}/multi_vm.log
#    done
#    echo -e "\nCheck logs in ${log_dir}"
#fi

#if [[ ${vm_cmd} ]] ; then 
#    log_dir="${DIR}/logs/Multi_VM-$TIMESTAMP"
#    [[ -d "${log_dir}" ]] || { mkdir -p "${log_dir}" ; }
#    run_cmd_vms_parallel "${vm_cmd}"
#    echo -e "\nCheck logs in ${log_dir}\n"
#fi

#if [[ ${shutdown_vms} = true ]] ; then 
#    shutdown_running_vms
fi



