#!/usr/bin/env bash
for iax_path in /sys/bus/dsa/devices/iax*
    do
        i=${iax_path##*iax}
        accel-config config-engine iax${i}/engine${i}.0 --group-id=0
        accel-config config-engine iax${i}/engine${i}.1 --group-id=0
        accel-config config-wq iax${i}/wq${i}.0 -g 0 -s 16 -p 8 -m dedicated -y kernel -n dmaengine -d dmaengine
        accel-config config-wq iax${i}/wq${i}.1 -g 0 -s 16 -p 8 -m dedicated -y kernel -n dmaengine -d dmaengine
        accel-config config-wq iax${i}/wq${i}.2 -g 0 -s 16 -p 8 -m dedicated -y kernel -n dmaengine -d dmaengine
        accel-config config-wq iax${i}/wq${i}.3 -g 0 -s 16 -p 8 -m dedicated -y kernel -n dmaengine -d dmaengine
        
        accel-config config-engine iax${i}/engine${i}.2 --group-id=1
        accel-config config-engine iax${i}/engine${i}.3 --group-id=1
        accel-config config-wq iax${i}/wq${i}.4 -g 1 -s 16 -p 8 -m dedicated -y kernel -n dmaengine -d dmaengine
        accel-config config-wq iax${i}/wq${i}.5 -g 1 -s 16 -p 8 -m dedicated -y kernel -n dmaengine -d dmaengine
        accel-config config-wq iax${i}/wq${i}.6 -g 1 -s 16 -p 8 -m dedicated -y kernel -n dmaengine -d dmaengine
        accel-config config-wq iax${i}/wq${i}.7 -g 1 -s 16 -p 8 -m dedicated -y kernel -n dmaengine -d dmaengine
        
        # Enable Devices
        accel-config enable-device iax${i}
        accel-config enable-wq iax${i}/wq${i}.0 iax${i}/wq${i}.1 iax${i}/wq${i}.2 iax${i}/wq${i}.3 iax${i}/wq${i}.4 iax${i}/wq${i}.5 iax${i}/wq${i}.6 iax${i}/wq${i}.7

    done
