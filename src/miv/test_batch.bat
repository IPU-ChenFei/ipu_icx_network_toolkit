py -3 C:\dtaf_content\src\miv\miv_wrapper.py -f miv_nm_power_limit_accuracy_d0_30min.tdf -P
py -3 C:\dtaf_content\src\miv\miv_wrapper.py -f miv_nm_power_limit_accuracy_d1_30min.tdf -P
py -3 C:\dtaf_content\src\miv\miv_wrapper.py -f miv_nm_power_limit_accuracy_d2_30min.tdf -P
py -3 C:\dtaf_content\src\miv\miv_wrapper.py -f miv_nm_power_limit_accuracy_d1_2hr.tdf -P
py -3 C:\dtaf_content\src\miv\miv_wrapper.py -f miv_nm_power_limit_accuracy_d2_2hr.tdf -P
py -3 C:\dtaf_content\src\miv\miv_wrapper.py -f miv_nm_power_limit_zerowatt_d0_aggressive.tdf -t 0:30:0
py -3 C:\dtaf_content\src\miv\miv_wrapper.py -f miv_nm_power_limit_d3_monolithic.tdf
py -3 C:\dtaf_content\src\miv\miv_wrapper.py -f miv_nm_power_limit_hard_accuracy_d0.tdf
py -3 C:\dtaf_content\src\miv\miv_wrapper.py -f miv_nm_power_limitingpolicy.tdf  -P
py -3 C:\dtaf_content\src\miv\miv_wrapper.py -f miv_nm_power_limit_accuracy_d0_4hrs.tdf -P
py -3 C:\dtaf_content\src\miv\miv_wrapper.py -f miv_nm_power_limit_accuracy_d1_2hr.tdf -P
py -3 C:\dtaf_content\src\miv\miv_wrapper.py -f miv_nm_power_limit_accuracy_d2_2hr.tdf -P
py -3 C:\dtaf_content\src\miv\miv_wrapper.py -f miv_nm_power_limit_zerowatt_d1.tdf -t 2:0:0
py -3 C:\dtaf_content\src\miv\miv_wrapper.py -f miv_nm_power_limit_zerowatt_d2.tdf -t 2:0:0
py -3 C:\dtaf_content\src\miv\miv_wrapper.py -f PECI_Validation.tdf
py -3 C:\dtaf_content\src\miv\miv_wrapper.py -f miv_reset_me_reset_idle.tdf -t 2:0:0
py -3 C:\dtaf_content\src\miv\miv_wrapper.py -f miv_meras_merecovery_force_me_recovery.tdf -t 0:15:0
py -3 C:\dtaf_content\src\miv\miv_wrapper.py -f miv_reset_warm.tdf -t 00:30:00
py -3 C:\dtaf_content\src\miv\miv_wrapper.py -f miv_reset_dc_0W.tdf -t 0:30:0
py -3 C:\dtaf_content\src\miv\miv_wrapper.py -f miv_reset_alert_shutdown_pm.tdf
py -3 C:\dtaf_content\src\miv\miv_wrapper.py -f miv_reset_me_reset_0W.tdf
py -3 C:\dtaf_content\src\miv\miv_wrapper.py -f miv_nm_power_limit_suspend_periods.tdf
py -3 C:\dtaf_content\src\miv\miv_wrapper.py -f miv_nm_k-coefficient.tdf -t 0:30:0
py -3 C:\dtaf_content\src\miv\miv_wrapper.py -f miv_nm_commands_checkout.tdf -P
py -3 C:\dtaf_content\src\miv\miv_wrapper.py -f miv_reset_warm_0W.tdf -t 2:00:0
py -3 C:\dtaf_content\src\miv\miv_wrapper.py -f miv_nm_dca.tdf -t 1:0:0