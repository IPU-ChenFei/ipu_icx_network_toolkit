# Inband Validation Set: Network

### Environment Preparation
* Mov `network-inband` package to sut os
* Run `setup/setup.[bat|sh]`
* Run `network.py` in the same console :)

### Network Configuration
![](network/_topology/network-topology-v2.png)
* Hardware Configuration Topology
  * **RED LINE** is used for ssh communication
* Software Configuration
  * network/network.ini/[server] -> SUT1
  * network/network.ini/[client] -> SUT2
  * network/network.ini/[connection] -> \<nic cable>
    
### Usage Demo
```python
Module Usage::
python network.py --step=prepare_server_client_connection --conn=col_conn_v4
python network.py --step=prepare_server_client_ipaddr
python network.py --step=test_server_client_connect

Note::
Essential <Prepare-Steps> that MUST be executed after booting to OS before all Steps:
    --step=prepare_server_client_connection --conn=col_conn_v4
    --step=prepare_assign_server_client_ipaddr
```

### Dryrun Steps (todo:)
```text
1. Setup different sutos environment (windows/linux)
    windows server -> windows client
    windows server -> linux client
    linux server -> linux client
    linux server -> windows client
2. Run sequence from tests/blocks-demo-network-v4.py
    Fixme: 1> ~ 10>
        Make sure most of them get a PASS result
        network/__runtime.ini shows correct configuration when running tests
```