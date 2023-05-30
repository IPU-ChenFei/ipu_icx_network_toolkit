## Multisocket Scripts Setup
```text
Any case that is not mentioned here do not require any additional manual steps
```

### 1. mltskt_config.txt
```text
Located under path:
    
    src\multisocket\lib\multisocket_ofband

Update this config file everytime SUT hardware changes, including:
    
    Topology input
    Silicon platform
    Add-in card changes
    
Further details can be found within the file
```


### 2. Windows stress case
```text
Windows stress cases require stress tools to be installed in SUT OS manually before running

    1509646651  Multisocket_Stability_iwvss_idlestate_check_W
    16014505936 Multisocket_Stress_Mixed_UPI_Link_Speed_Linpack_4S_W
    15011013943 Multisocket_Stress_Mixed_UPI_Link_Speed_Linpack_8S_W
    1509646605  Multisocket_Stress_MLC_CPU_Mem_stress_W
    1509725482  Multisocket_Stress_StreamBenchmark_CPU_MEM_stress_W
    1509722989  Multisocket_UPI_IO_Mixed_UPI_Link_Speed_W
```

### 3. IO cycling cases
```text
IO cycling cases would require a pcie card added onto the SUT (Any PCIE add-in card would do)

    1509647284  Multisocket_Stability_IO_G3_cycling_L
    1509725450  Multisocket_Stability_IO_G3_cycling_W
    1509647337  Multisocket_Stability_IO_S5_cycling_L    
    1509725466  Multisocket_Stability_IO_S5_cycling_W 
    1509647237  Multisocket_Stability_IO_WarmReset_cycling_L   
    1509639067  Multisocket_Stability_IO_WarmReset_cycling_W   
```