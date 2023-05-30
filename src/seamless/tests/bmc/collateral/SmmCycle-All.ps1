#
# Title  : SmmCycle-All.ps1
# Purpose: Automate running all of the SMM Code Injection tests
# Version: 1.1.34
# History: 1.1.34 - Fix DTAF system_configuration.xml
#                 - Disable RW.exe support if it cannot be found with flag control
#          1.1.33 - Add flag to disable CSR count
#                 - Added DTAF system_configuration.xml support
#                 - Removed pve-common support
#          1.1.32 - Comment out SMI stress functions until I can get it working correctly
#                 - Fix post-check elapsed time error
#                 - Fix occasional putty popup window
#                 - Fix last zip of the logs
#          1.1.31 - Delete log folder temp folder when done with it
#                 - Fix SMI & CSR count functions
#          1.1.30 - Fix ZipFiles() deleting everything
#                 - Added flag to mark pre & post check KPI failures as warnings
#                 - Added a flag to skip pre-check
#                 - Added a flag to skip post-check
#                 - Added a flag to override the test cycle count
#                 - Added a flag to override the delay between tests
#          1.1.28 - Fix errors from untested #1.1.27
#          1.1.27 - Change Execution KPI testing for specific capsule only
#                 - Update EGS capsules so they are the right ones for the specified test
#          1.1.26 - Add EGS support
#          1.1.25 - KPI defined as 9ms for capsules <= 128KB & 100ms for > 128KB
#                 - Removed unused capsules from the list
#          1.1.24 - Reverted timescale back
#          1.1.23 - Added KPI check
#                 - Added exitcode
#          1.1.22 - Switch CSR capsule to the sample one from WW45
#          1.1.21 - Fix SUT final ZIP
#                 - Added function to retrieve the SMI count
#          1.1.20 - Pull hack for SUT process implosion
#                 - Fix SUT launched RW
#          1.1.19 - Add SMI stress test support
#                 - Created ZipFiles function
#          1.1.18 - Add in telemetry test numbers
#                 - Auto-detecting if run from SUT
#                 - Creating main report log
#          1.1.17 - Add direct SUT usage capability
#                 - Setup SendCommand for IEX as well as Python
#          1.1.16 - Fixed TestCapsule miniTest Pass/Fail detection
#          1.1.15 - Speed up cycling by running SEAM_BMC_0015 script first and last & use SMMCodeInject.ps1 in-between
#          1.1.14 - Optimize log retrieval
#                 - Fixed log level testing
#          1.1.13 - Add log level testing
#          1.1.12 - Finish adding telemetry support
#          1.1.11 - Add parsing system_configuration.txt
#                 - Switched to GetBiosVersion.ps1
#                 - Sanity check COM ports
#          1.1.10 - Started adding support for telemetry
#                 - Switched to using 0015 built-in BIOS version command
#                 - Launch workloads flag
#          1.1.9  - Fix logic error in CapsuleSanityCheck()
#                 - Copy $rootPath to $rootPath.old before deleting
#                 - Allow hard coding COM ports
#          1.1.8  - Parse elapsed time from sanity check via split
#                 - Exclude this script if it is in pve-common when deleting
#          1.1.7  - Fixed sanity test to display pass/fail
#                 - Stop running script if pre-test sanity check fails
#                 - Grab latest automation scripts
#          1.1.6  - Cleaned up display text
#                 - Updated Glasgow test revisions
#                 - Simplified BIOS/BMC COM port detection
#          1.1.5  - Automatically detect IFWI version and use appropriate capsules
#          1.1.4  - Auto-detect BIOS
#                 - BMC serial port
#          1.1.3  - Added 15D16 capsules
#                 - Fixed BMC serial log file
#                 - Created function to return elapsed time
#                 - Created function for testing capsules
#          1.1.2  - Added capsule sanity check
#          1.1.1  - Added IFWI 14D95 capsules
#                 - Fix for missing log files
#                 - Updated elapsed time to include days
#          1.1.0  - Added chart
# TODO   :
#          - !!!Add comments on array weirdness!!!
#          - Speed up workload cycle testing by starting workloads; do cycling; & then stopping workloads
#          - Add IFWI version check on GetTelemetry and use old 4 call method if pre-15D16
#            - Add SUT method to the other low level functions
#          - SendCommand consolidate into one for IEX
#            - Consolidate Invoke-Command in CSR & SMI count; & start SMI stress functions
#          - Allow CLI parameters for:
#            - BIOS COM port
#            - BMC COM port
#            - Flag to update pve-common folder
#            - Launch workloads flag
#            - Using on SUT flag
#            - Pull everything from a config file
#            - Debug flag
#            - Skip pre-check
#            - Skip post-check
#            - Set all test cycles counts to xxx
#          - Find out why BMC debuguser account disabled at BMC command prompt
#          - Add dynamic CSR count support after building updated capsule
#

# Initialize variables
  $scriptVersion               = "1.1.34"
  $scriptDebug                 = "True"
  $launchWorkloads             = "False"
  $skipPreCheck                = "False"
  $skipPostCheck               = "False"
  $treatSanityKpiFailAsFailure = "False"
  $treatNoRwAsFailure          = "False"
  $csrEnabledFlag              = "False"
  $csrAddress                  = "0xC6122D28"
  $forceLoopCount              = 0
  $forceDelay                  = 0
  $smiStressFlag               = "False"
  $Global:launchedFromSut      = "False"
  $Global:SutUser              = ""
  $Global:SutPassword          = ""
  $Global:SutIp                = ""
  $Global:BiosComPort          = ""
  $Global:BiosBaudRate         = ""
  $Global:AutomationFramework  = ""
  $Global:BmcUser              = ""
  $Global:BmcPassword          = ""
  $Global:BmcIp                = ""
  $Global:BmcComPort           = ""
  $Global:BmcBaudRate          = ""
  $Global:RwSession            = ""
  $scriptStatus                = "Passed"
  $puttySession                = 'SMM_Script'
  $puttyRegistryPath           = 'Registry::HKEY_CURRENT_USER\Software\SimonTatham\PuTTY\Sessions\{0}' -f $puttySession
  $automationPath              = "C:\Automation"
  $automationFile              = "system_configuration.xml"
  $automationFilePath          = "{0}\{1}" -f $automationPath, $automationFile
  $rootPath                    = "C:\DTAF"
  $logFilePath                 = "C:\seamless-logs"
  $scriptPath                  = "seamless\tests\bmc\functional"
  $scriptFile                  = "SEAM_BMC_0015_smm_update.py"
  $collateralPath              = "{0}\..\collateral" -f $scriptPath
  $biosVersionScript           = "GetBiosVersion.ps1"
  $sruAppPath                  = "C:\Windows\System32\SruApp.exe"
  $telemetryAppPath            = "C:\Windows\System32\sruTelemetryApp.exe"
  $rwAppPath                   = '"C:\Program Files\RW-Everything\Rw.exe"'
  $puttyAppPath                = '"C:\Program Files\PuTTY\putty.exe"'
  $executionKpiCapsule         = "Not defined yet"
  $reportLogName               = "SmmCycle-{0:yyyy-MM-dd_HH-mm-ss}" -f $(Get-Date)
  $reportLogPath               = "{0}\{1}.rst" -f $logFilePath, $reportLogName
  $majorSeparator              = "+==========+======+=============+========+==========+=============+`n"
  $minorSeparator              = "+----------+------+-------------+--------+----------+-------------+`n"
  $headerLine                  = "| Glasgow  | Test | Status      | Cycles | Failures | Time        |`n"
  $blockedCommentCount         = 0
  $blockedComments             = ""
  $testArray = @(
    # #0         #1        #2                                       #3       #4       #5            #6         #7     #8      #9           #10
    ("Glasgow", "Test #", "Blocked",                               "Delay", "Count", "Pass",       "Fail",    "Pre", "Post", "Pre Count", "Post Count"   ),
    ("67482.03", "#01",    "",                                      "250",   "10",    (3),          (0),        0,     0,      (0),         (0)          ),
    ("67887.03", "#02",    "",                                      "250",   "10",    (0),          (6),        0,     0,      (0),         (0)          ),
    ("67483.03", "#03",    "",                                      "250",   "10",    (4),          (0),        0,     0,      (0),         (0)          ),
    ("67484.05", "#04",    "",                                      "250",   "10",    (0),          (8),        0,     0,      (0),         (0)          ),
    ("67485.04", "#05",    "",                                      "250",   "10",    (0),          (7),        0,     0,      (0),         (0)          ),
    ("67486.06", "#06",    "",                                      "250",   "500",   (3, 4),       (1, 6, 7), -1,    -2,      (200),       (1, 300, 500)),
    ("67888.05", "#07",    "",                                      "250",   "500",   (3),          (6),       -3,    -3,      (0),         (0)          ),
    ("67889.04", "#08",    "",                                      "250",   "500",   (4),          (5),        0,     0,      (0),         (0)          ),
    ("67890.04", "#09",    "",                                      "250",   "500",   (3),          (2),        0,     0,      (0),         (0)          ),
    ("67891.05", "#10",    "",                                      "250",   "500",   (3),          (1),        3,     0,      (1),         (0)          ),
    ("67892.03", "#11",    "",                                      "250",   "500",   (3),          (6),        0,     0,      (0),         (0)          ),
    ("67560.04", "#12",    "",                                      "250",   "500",   (3),          (1),       -1,    -2,      (200),       (1, 300, 500)),
    ("69663.02", "#13",    "",                                      "250",   "10",    (9),          (0),        0,     0,      (0),         (0)          ),
    ("69796.02", "#14",    "",                                      "250",   "10",    (10),         (0),        0,     0,      (0),         (0)          ),
    ("69797.01", "#15",    "",                                      "250",   "10",    (11),         (0),        0,     0,      (0),         (0)          ),
    ("69798.00", "#16",    "",                                      "250",   "500",   (9, 10, 11),  (0),        0,     0,      (0),         (0)          )
  )
  # NOTE: Test capsules are in a certain order and need to match against those in $testArray
  #       so the right capsules are being tested for the correct test.
  # Test capsules used for Alpha BKC, IFWI = 14D90
  $testCapsules14D90 = @(
    ("Name",                                                                                    "Pass\Fail", "Telemetry", "LogLevel", "KPI" ), #00 - label
    ("SaiStandalone.efi_VER_0x00000001_LSV_0x00000000.Cap",                                     "Fail",      "False",     "False",    "9"   ), #01 - 1:0
    ("SaiStandalone.efi_VER_0x00000001_LSV_0x00000001.Cap",                                     "Fail",      "False",     "False",    "9"   ), #02 - 1:1
    ("SaiStandalone.efi_VER_0x00000000_LSV_0x00000001.Cap",                                     "Pass",      "False",     "False",    "9"   ), #03 - 0:1
    ("4MB_VER_0x0_LVS_0x1.Cap",                                                                 "Pass",      "False",     "False",    "999" ), #04 - 0:1 =4MB
    ("Bigger_than_4MB_VER_0x0_LSV_0x1.Cap",                                                     "Fail",      "False",     "False",    "999" ), #05 - 0:1 >4MB
    ("SaiStandalone.efi_VER_0x00000000_LSV_0x00000001_BLACKLIST_SIGN.Cap",                      "Fail",      "False",     "False",    "9"   ), #06 - 0:1 blacklisted
    ("emptypayload_VER_0_LSV_1_ID_0C3D193E-88B9-4186-ACF1-6440320BCDDC.Cap",                    "Fail",      "False",     "False",    "9"   ), #07 - 0:1 empty payload
    ("SaiStandalone_VER_0_LSV_1_ID_0C3D193E-88B9-4186-ACF1-6440320BCDDC.Cap",                   "Fail",      "False",     "False",    "9"   ), #08 - 0:1 wrong Platform ID
    ("AllLogLevel_VER_0x0_LSV_0x1.Cap",                                                         "Pass",      "True",      "True",     "9"   ), #09 - 0:1 all log levels
    ("Rollover-1_VER_0x0_LSV_0x1.Cap",                                                          "Pass",      "True",      "False",    "9"   ), #10 - 0:1 Roll log once
    ("Rollover-3_VER_0x0_LSV_0x1.Cap",                                                          "Pass",      "True",      "False",    "9"   )  #11 - 0:1 Roll log 3 times
  )
  # Test capsules used for IFWI >= 14D95 & < 15D16
  $testCapsules14D95 = @(
    ("Name",                                                                                    "Pass\Fail", "Telemetry", "LogLevel", "KPI" ), #00 - label
    ("SaiStandalone_VER_1_LSV_0_ID_0C3D193E-88B9-4186-ACF1-6440320BCDDC.Cap",                   "Fail",      "False",     "False",    "9"   ), #01 - 1:0
    ("SaiStandalone_VER_1_LSV_1_ID_0C3D193E-88B9-4186-ACF1-6440320BCDDC.Cap",                   "Fail",      "False",     "False",    "9"   ), #02 - 1:1
    ("SaiStandalone_VER_0_LSV_1_ID_0C3D193E-88B9-4186-ACF1-6440320BCDDC.Cap",                   "Pass",      "False",     "False",    "9"   ), #03 - 0:1
    ("4MB_VER_0_LSV_1_ID_0C3D193E-88B9-4186-ACF1-6440320BCDDC.Cap",                             "Pass",      "False",     "False",    "999" ), #04 - 0:1 =4MB
    ("BiggerThan4MB_VER_0_LSV_1_ID_0C3D193E-88B9-4186-ACF1-6440320BCDDC.Cap",                   "Fail",      "False",     "False",    "999" ), #05 - 0:1 >4MB
    ("SaiStandalone_VER_0_LSV_1_ID_0C3D193E-88B9-4186-ACF1-6440320BCDDC_BLACKLIST_SIGN.Cap",    "Fail",      "False",     "False",    "9"   ), #06 - 0:1 blacklisted
    ("emptypayload_VER_0_LSV_1_ID_0C3D193E-88B9-4186-ACF1-6440320BCDDC.Cap",                    "Fail",      "False",     "False",    "9"   ), #07 - 0:1 empty payload
    ("SaiStandalone.efi_VER_0x00000000_LSV_0x00000001.Cap",                                     "Fail",      "False",     "False",    "9"   ), #08 - 0:1 wrong Platform ID
    ("AllLogLevelTestCase_VER_0_LSV_1_ID_0C3D193E-88B9-4186-ACF1-6440320BCDDC.Cap",             "Pass",      "True",      "True",     "9"   ), #09 - 0:1 all log levels
    ("Rollover-1_VER_0_LSV_1_ID_0C3D193E-88B9-4186-ACF1-6440320BCDDC.Cap",                      "Pass",      "True",      "False",    "9"   ), #10 - 0:1 Roll log once
    ("Rollover-3_VER_0_LSV_1_ID_0C3D193E-88B9-4186-ACF1-6440320BCDDC.Cap",                      "Pass",      "True",      "False",    "9"   )  #11 - 0:1 Roll log 3 times
  )
  # Test capsules used for IFWI >= 15D16
  $testCapsules15D16 = @(
    ("Name",                                                                                                                           "Pass\Fail", "Telemetry", "LogLevel", "KPI" ), #00 - label
    ("cpucsr_VER_1_LSV_0_ID_0C3D193E-88B9-4186-ACF1-6440320BCDDC_TYPE_0.Cap",                                                          "Fail",      "False",     "False",    "9"   ), #01 - 1:0
    ("cpucsr_VER_1_LSV_1_ID_0C3D193E-88B9-4186-ACF1-6440320BCDDC_TYPE_0.Cap",                                                          "Fail",      "False",     "False",    "9"   ), #02 - 1:1
    ("SampleStandAloneMMModule.efi_VER_0_LSV_1_ID_0C3D193E-88B9-4186-ACF1-6440320BCDDC_TYPE_00000000-0000-0000-0000-000000000000.Cap", "Pass",      "False",     "False",    "9"   ), #03 - 0:1
    ("Almost4MB_VER_0_LSV_1_ID_0C3D193E-88B9-4186-ACF1-6440320BCDDC_TYPE_0.Cap",                                                       "Pass",      "False",     "False",    "999" ), #04 - 0:1 =4MB
    ("BiggerThan4MB_VER_0_LSV_1_ID_0C3D193E-88B9-4186-ACF1-6440320BCDDC_TYPE_0.Cap",                                                   "Fail",      "False",     "False",    "999" ), #05 - 0:1 >4MB
    ("cpucsr_VER_0_LSV_1_ID_0C3D193E-88B9-4186-ACF1-6440320BCDDC_TYPE_0_BLACKLIST_SIGN.Cap",                                           "Fail",      "False",     "False",    "9"   ), #06 - 0:1 blacklisted
    ("emptypayload_VER_0_LSV_1_ID_0C3D193E-88B9-4186-ACF1-6440320BCDDC_TYPE_0.Cap",                                                    "Fail",      "False",     "False",    "9"   ), #07 - 0:1 empty payload
    ("SaiStandalone.efi_VER_0x00000000_LSV_0x00000001.Cap",                                                                            "Fail",      "False",     "False",    "9"   ), #08 - 0:1 wrong Platform ID
    ("AllLogLevelTestCase_VER_0_LSV_1_ID_0C3D193E-88B9-4186-ACF1-6440320BCDDC_TYPE_0.Cap",                                             "Pass",      "True",      "True",     "9"   ), #09 - 0:1 all log levels
    ("Rollover1TestCase_VER_0_LSV_1_ID_0C3D193E-88B9-4186-ACF1-6440320BCDDC_TYPE_0.Cap",                                               "Pass",      "True",      "False",    "9"   ), #10 - 0:1 Roll log once
    ("Rollover3TestCase_VER_0_LSV_1_ID_0C3D193E-88B9-4186-ACF1-6440320BCDDC_TYPE_0.Cap",                                               "Pass",      "True",      "False",    "9"   )  #11 - 0:1 Roll log 3 times
  )

  # Test capsules used for Alpha EGS BKC, IFWI = 56D18
  $testCapsules56D18 = @(
    ("Name",                                                                                                                               "Pass\Fail", "Telemetry", "LogLevel", "KPI" ), #00 - label
    ("cpucsr_VER_1_LSV_0_ID_63462139-a8b1-aa4e-9024-f2bb53ea4723_TYPE_0.Cap",                                                              "Fail",      "False",     "False",    "9"   ), #01 - 1:0
    ("cpucsr_VER_1_LSV_1_ID_63462139-a8b1-aa4e-9024-f2bb53ea4723_TYPE_0.Cap",                                                              "Fail",      "False",     "False",    "9"   ), #02 - 1:1
    ("SCI_SampleStandAloneMMModule.efi_VER_0_LSV_1_ID_63462139-a8b1-aa4e-9024-f2bb53ea4723_TYPE_00000000-0000-0000-0000-000000000000.Cap", "Pass",      "False",     "False",    "9"   ), #03 - 0:1
    ("4MB_VER_0_LSV_1_ID_63462139-a8b1-aa4e-9024-f2bb53ea4723_TYPE_0.Cap",                                                                 "Pass",      "False",     "False",    "999" ), #04 - 0:1 =4MB
    ("BiggerThan4MB_VER_0_LSV_1_ID_63462139-a8b1-aa4e-9024-f2bb53ea4723_TYPE_0.Cap",                                                       "Fail",      "False",     "False",    "999" ), #05 - 0:1 >4MB
    ("cpucsr_VER_0_LSV_1_ID_63462139-a8b1-aa4e-9024-f2bb53ea4723_TYPE_0_denied_list_SIGN.Cap",                                             "Fail",      "False",     "False",    "9"   ), #06 - 0:1 blacklisted
    ("emptypayload_VER_0_LSV_1_ID_63462139-a8b1-aa4e-9024-f2bb53ea4723_TYPE_0.Cap",                                                        "Fail",      "False",     "False",    "9"   ), #07 - 0:1 empty payload
    ("cpucsr_VER_0_LSV_1_ID_63462139-a8b1-aa4e-9024-f2bb53ea4723_TYPE_0_InvalidGUID.Cap",                                                  "Fail",      "False",     "False",    "9"   ), #08 - 0:1 wrong Platform ID
    ("AllLogLevelTestCase_VER_0_LSV_1_ID_63462139-a8b1-aa4e-9024-f2bb53ea4723_TYPE_0.Cap",                                                 "Pass",      "True",      "True",     "9"   ), #09 - 0:1 all log levels
    ("Rollover1TestCase_VER_0_LSV_1_ID_63462139-a8b1-aa4e-9024-f2bb53ea4723_TYPE_0.Cap",                                                   "Pass",      "True",      "False",    "9"   ), #10 - 0:1 Roll log once
    ("Rollover3TestCase_VER_0_LSV_1_ID_63462139-a8b1-aa4e-9024-f2bb53ea4723_TYPE_0.Cap",                                                   "Pass",      "True",      "False",    "9"   )  #11 - 0:1 Roll log 3 times
   )
  $ifwiVersions = @(
    ("0014D90", "testCapsules14D90"),
    ("0014D95", "testCapsules14D95"),
    ("0015D16", "testCapsules15D16"),
    ("0056D18", "testCapsules56D18")
  )
  $logLevelList = @(
    ("error",   "SMM_TELEMETRY_ERROR"),
    ("warning", "SMM_TELEMETRY_WARN"),
    ("info",    "SMM_TELEMETRY_INFO"),
    ("verbose", "SMM_TELMEMTRY_VERBOSE")  #NOTE: Telemetry misspelled and might get fixed in the future.
  )
  $automationList = @(
    ("/core/suts/sut/providers/sut_os/driver/ssh/credentials/user",     "SutUser"),
    ("/core/suts/sut/providers/sut_os/driver/ssh/credentials/password", "SutPassword"),
    ("/core/suts/sut/providers/sut_os/driver/ssh/ipv4",                 "SutIp"),
    ("/core/suts/sut/providers/console_log/driver/com/port",            "BiosComPort"),
    ("/core/suts/sut/providers/console_log/driver/com/baudrate",        "BiosBaudRate"),
    ("/core/suts/sut/providers/dc/driver/ipmi/cmd",                     "AutomationFramework"),
    ("/core/suts/sut/providers/flash/driver/redfish/username",          "BmcUser"),
    ("/core/suts/sut/providers/flash/driver/redfish/password",          "BmcPassword"),
    ("/core/suts/sut/providers/flash/driver/redfish/ip",                "BmcIp"),
    ("/core/suts/sut/providers/flash/driver/redfish/bmcport",           "BmcComPort"),
    ("/core/suts/sut/providers/flash/driver/redfish/baudrate",          "BmcBaudRate")
  )

# Functions
  Function CapsuleSanityCheck {
    # Sanity check used capsules and return pass/fail and elapsed time
    $sanityStartTime = $(Get-Date)
    $sanityFailure = "False"
    $activeTests = @()
    ForEach ($test in $testArray) {
      $testTag         = $test[0]
      $testNum         = $test[1]
      $testBlocked     = $test[2]
      $testDelay       = $test[3]
      $testCount       = $test[4]
      $testPass        = $test[5]
      $testFail        = $test[6]
      $testPreCapsule  = $test[7]
      $testPostCapsule = $test[8]
      $testPreCount    = $test[9]
      $testPostCount   = $test[10]
      If ($testBlocked -eq "") {
        # This is an active test
        If ($testPass -gt 0) {
          ForEach ($passTest in $testPass) {
            If ((-Not ($activeTests -Contains $passTest)) -And ($passTest -gt 0)) {
              $activeTests += $passTest
            }
          }
        }
        If ($testFail -gt 0) {
          ForEach ($failTest in $testFail) {
            If ((-Not ($activeTests -Contains $failTest)) -And ($failTest -gt 0)) {
              $activeTests += $failTest
            }
          }
        }
        If ($testPreCapsule -gt 0) {
          If ((-Not ($activeTests -Contains $testPreCapsule)) -And ($testPreCapsule -gt 0)) {
            $activeTests += $testPreCapsule
          }
        }
        If ($testPostCapsule -gt 0) {
          If ((-Not ($activeTests -Contains $testPostCapsule)) -And ($testPostCapsule -gt 0)) {
            $activeTests += $testPostCapsule
          }
        }
      }
    }
    $activeTests = $activeTests | Sort-Object
    $sanityCheckResults = ""
    ForEach ($test in $activeTests) {
      # Run each test
        $testResult      = TestCapsule $test "NUL" "False" "True"
        $executionResult = $testResult.Split("|")[1]
        $executionResult = $executionResult.Trim()
        $testResult      = $testResult.Split("|")[0]
        $testResult      = $testResult.Trim()
      # Check for correct log level
        If ($testCapsules[$test][3] -ieq "True") {
          If ($executionResult -ieq "False") {
            $testResult = "Fail"
          }
        }
      # Add in results
        $sanityCheckResults += "   - " + $testCapsules[$test][0] + " " + $testResult + "`n"
        If ($testResult -ieq "Fail") {
          $sanityFailure = "True"
        }
    }

    # Add test results
      If ($sanityFailure -ieq "True") {
        $sanityCheckResults = "   - Active tests sanity check FAILED!!!`n" + $sanityCheckResults
      } Else {
        $sanityCheckResults = "   - Active tests sanity check passed!!!`n" + $sanityCheckResults
      }

    # Add elapsed time
      $sanityElapsedTime = "   - Elapsed time = {0}" -f (ElapsedTime $sanityStartTime)
      $sanityCheckResults = $sanityCheckResults + $sanityElapsedTime

    Return $sanityCheckResults
  }

  Function ElapsedTime {
    # Return elapsed time string
    # - $args[0] = startTime
      $elapsedTime = $(Get-Date) - $args[0]
      $elapsedTime = "{0}" -f ($elapsedTime.ToString("dd\:hh\:mm\:ss"))

    Return $elapsedTime
  }

  Function EmptyComBuffer {
    # Launches BMC journal if it is not already running
    # - $args[0] - COM object
      $comObject  = $args[0]
      $emptyCount = 0
      $result     = ""
      $waitCount  = 600
      While ($waitCount -gt 0) {
        $read      = ($comObject.ReadExisting() | Out-String).Split([Environment]::NewLine)
        $readItems = ""
        ForEach ($line in $read) {
          $line = $line.Trim().TrimEnd()
          If ($line -ne "") {
            $readItems += $line + [Environment]::NewLine
          }
        }
        If ($readItems -eq "") {
          $emptyCount += 1
          If ($emptyCount -gt 3) {Break}
        } Else {
          $result += $readItems.Trim()
        }
        Start-Sleep -m 50
        $waitCount -= 1
      }

    Return $result.TrimEnd()
  }

  Function ExitBmcJournal {
    # Exits BMC journal if it is running
    # - $args[0] - BMC Com port
    # - $args[1] - BMC BAUD rate
      $bmcPort = $args[0]
      $bmcBaud = $args[1]

      # Create BMC serial port object and open
      $bmcSerialPort = New-Object System.IO.Ports.SerialPort $bmcPort,$bmcBaud,None,8,One
      $bmcSerialPort.Open()
      # Exit journal if inside
      $read = WriteSerial $bmcSerialPort ([char]0x03) ""
      # Exit login
      $read = WriteSerial $bmcSerialPort "exit" ""
      # Close BMC serial port
      $bmcSerialPort.Close()
  }

  Function FindApp {
    # Sends a command to be executed
    # - $args[0] = App to find
    # - $args[1] = remoteFlag
    # Find app
      Write-Host (" - Find App {0}..." -f $args[0])
      # Find app
        $params = $args[0]
        $s      = ""
        If ($args[1] -ieq "False") {
          # Find local App
            try {
              $output = (Get-Command $args[0]).Path
            }
            catch {
              $output = ''
            }
        } Else {
          # Find remote App
            try {
              $pass = ConvertTo-SecureString -String $SutPassword -AsPlainText -Force
              $cred = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $SutUser, $pass
              $s = New-PSSession -ComputerName $SutIp -credential $cred
              $output = Invoke-Command -ScriptBlock {Param($params) (Get-Command $params).Path} -ArgumentList($params) -Session $s
              Remove-PSSession -Session $s
            }
            catch {
              $output = ''
            }
        }
    If ($scriptDebug -ieq "True") {Write-Host ("   - output = {0}" -f $output)}
    Return $output
  }

  Function GetBiosSerialPort {
    If ($launchedFromSut -ieq "True") {
      $comPort = "NUL"
    } Else {
      # Send <ENTER> to determine which COM port is the BIOS serial port
        $comPort = TestSerialPort "SAC>" $BiosComPort $BiosBaudRate
    }
    Return $comPort
  }

  Function GetBmcSerialPort {
    If ($launchedFromSut -ieq "True") {
      $comPort = "NUL"
    } Else {
      # Send <ENTER> to determine which COM port is the BMC serial port
        $comPort = TestSerialPort "intel-obmc" $BmcComPort $BmcBaudRate
    }
    Return $comPort
  }

  Function GetCapsuleLabel {
    # Returns the label of the array of capsules to use based on an IFWI version
    # - $args[0] - IFWI version
      $detectedMajorVersion = [int]$args[0].SubString(0,4)
      $detectedMinorVersion = [int]$args[0].SubString($args[0].length - 2, 2)
      $currentLabel         = ""
      $detectedLabel        = ""
      $lastLabel            = ""
      ForEach ($ifwiLabel in $ifwiVersions) {
        $lastLabel = $currentLabel
        $currentLabel = $ifwiLabel[1]
        $currentMajorVersion = [int]$ifwiLabel[0].SubString(0,4)
        $currentMinorVersion = [int]$ifwiLabel[0].SubString($ifwiLabel[0].length - 2, 2)
        If ($currentMajorVersion -eq $detectedMajorVersion) {
          # We match current major version
          If ($currentMinorVersion -eq $detectedMinorVersion) {
            # We match current minor version
              $detectedLabel = $currentLabel
              Break
          } ElseIf ($currentMinorVersion -gt $detectedMinorVersion) {
            # Current minor is more than detected minor version
              $detectLabel = $lastLabel
              Break
          } Else {
            # Current minor is less than detected minor version
              $detectedLabel = $currentLabel
          }
        } ElseIf ($currentMajorVersion -gt $detectedMajorVersion) {
          # Current major is more than detected major version
            $detectLabel = $lastLabel
            Break
        } Else {
          # Current major is less than detected major version
            $detectedLabel = $currentLabel
        }
      }
      If ($detectedLabel -eq "") {
        $detectedLabel = $ifwiVersions[0][1]
      }
    Return $detectedLabel
  }

  Function GetCsrCount {
    # Grab CSR count
      Write-Host (" - Get CSR Count...")
      # Grab CSR count from machine
      If ((-Not($csrEnabledFlag -ieq "True")) -Or ($rwAppPath -ieq '')) {
        Write-Host ("   - Get CSR Count disabled")
        $csrCount = 'Disabled'
      } Else {
        #TODO: Need to find a way to get the CSR magic address dynamically
          $logFileName = "CsrCount.log"
          $logFile     = "{0}\{1}" -f $logFilePath, $logFileName
          $params      = '{0} /command="R32 {1}; RWExit" /logfile={2}' -f $rwAppPath, $csrAddress, $logFile
          $s           = ""
          If ($launchedFromSut -ieq "True") {
            $output = SendCommand $params "NUL" "IEX"
            ForEach ($line in $output) {
              Write-Host ("   - output = [{0}]" -f $line)
            }
            # Wait for file
              $delayCount = 100   # Wait up to 1 second for the file to appear
              While (-Not (Test-Path $logFile -PathType Leaf)) {
                Start-Sleep -m 10
                $delayCount -= 1
                If ($delayCount -eq 0) {Break}
              }
              Start-Sleep -m 25   # Extra 25ms to allow the file to close
              If (Test-Path $logFile -PathType Leaf) {
                $output = [IO.File]::ReadAllText($logFile)
                $output = $output -Split "`r`n"
              } Else {
                $output = ""
              }
          } Else {
            # Make sure RW is not running
              StopSmiStress
            # Grab CSR count
              $pass = ConvertTo-SecureString -String $SutPassword -AsPlainText -Force
              $cred = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $SutUser, $pass
              $s    = New-PSSession -ComputerName $SutIp -credential $cred
              Invoke-Command -ScriptBlock {Param($logFilePath) New-Item -Path $logFilePath -ItemType directory -ErrorAction SilentlyContinue} -ArgumentList($logFilePath) -Session $s
              Invoke-Command -ScriptBlock {Param($logFile) Remove-Item $logFile -Force -ErrorAction SilentlyContinue} -ArgumentList($logFile) -Session $s
              Invoke-Command -ScriptBlock {Param($params) (Invoke-Expression "& $params *>&1") -Split "`r`n"} -ArgumentList($params) -Session $s
              # Wait for file to show up
                $delayCount = 100   # Wait up to 1 second for the file to appear
                While (-Not (Invoke-Command -ScriptBlock {Param($logFile) Test-Path $logFile -PathType Leaf} -ArgumentList($logFile) -Session $s)) {
                  Start-Sleep -m 10
                  $delayCount -= 1
                  If ($delayCount -eq 0) {Break}
                }
                Start-Sleep -m 25   # Extra 25ms to allow the file to close
              $output = Invoke-Command -ScriptBlock {Param($logFile) (Get-Content $logFile) -Split "`r`n"} -ArgumentList($logFile) -Session $s
              Invoke-Command -ScriptBlock {Param($logFile) Remove-Item $logFile -Force -ErrorAction SilentlyContinue} -ArgumentList($logFile) -Session $s
          }
        # Get CSR count from log
          $csrCount = "Unknown"
          ForEach ($line in $output) {
            If ($line.Contains("Read Memory Address")) {
              # $line = Read Memory Address 0xC6122D28 = 0xFFFFFFFF
              $csrCount = $line.Split("=")[1]
              $csrCount = $csrCount.Trim()
              Break
            }
          }
        # Close session if it exists
          If ($s -ne "") {
            Remove-PSSession -Session $s
          }
        # Kill log file
          $temp = "{0}\*" -f $logFilePath
          Get-ChildItem -Path $temp -Filter $logFileName | Remove-Item -Force -ErrorAction SilentlyContinue
      }
    Return $csrCount
  }

  Function GetExecutionTelemetry {
    # Grab the execution log
    # - $args[0] = rev
    # - $args[1] = logLevel
    # - $args[2] = logFile
    #   - "NUL" means send to bit-bucket
    # - $args[3] = startWorkload
    # - $args[4] = useCollateral
    # - returns telemetry log
    $telemetry = GetTelemetry $args[0] "execution" $args[1] $args[2] $args[3] $args[4]
    Return $telemetry
  }

  Function GetHistoryTelemetry {
    # Grab the history log
    # - $args[0] = rev
    # - $args[1] = logFile
    #   - "NUL" means send to bit-bucket
    # - $args[2] = startWorkload
    # - $args[3] = useCollateral
    # - returns telemetry log
    $telemetry = GetTelemetry $args[0] "history" "verbose" $args[1] $args[2] $args[3]
    Return $telemetry
  }

  Function GetIfwiVersion {
    # Grabs the IFWI version and returns it
      If ($launchedFromSut -ieq "True") {
        # Running on the SUT, just ask for it directly
          $result = "{0}" -f (Get-WmiObject -class Win32_Bios | Select-Object -ExpandProperty SMBIOSBIOSVersion)
      } Else {
        $logFile = "{0}\IFWI-Version.log" -f $logFilePath
        $params  = '"{0}" -computer {1} -user {2} -password {3}' -f $biosVersionScriptPath, $SutIp, $SutUser, $SutPassword
        $output  = SendCommand $params $logFile "IEX"
        $result  = Select-String -Path $logFile -Pattern "SMBIOSBIOSVersion :"
        $result  = (("{0}" -f $result) -Split " : ")[1]
      }
      If ($result) {
        $result = $result.Split(".")[2] + $result.Split(".")[3]
      } Else {
        $result = ""
      }
      $temp = "{0}\*" -f $logFilePath
      Get-ChildItem -Path $temp -Filter "IFWI-Version.log" | Remove-Item -Force -ErrorAction SilentlyContinue
    Return $result
  }

  Function GetLogData {
    # Get log data
    # - $args[0] = logFile
    #   - "NUL" means send to bit-bucket
    # - $args[1] = startWorkload
    # - $args[2] = useCollateral
      If ($args[2] -ieq "True") {
        # Get logfile
          If ($args[0] -ieq "NUL") {
            $logFile = "{0}\LogData.log" -f $logFilePath
          } Else {
            $logFile = $args[0]
          }
        # Get log size
          $params  = '"{0}\SMMInfo.ps1" -computer {1} -user {2} -password {3} getLogSize' -f $collateralPath, $SutIp, $SutUser, $SutPassword
          $output  = SendCommand $params $logFile "IEX"
          $log     = [IO.File]::ReadAllText($logFile)
          $log     = $log -Split "`r`n"
          $logSize = "0x00010000"
          ForEach ($line in $log) {
            If ($line.Contains("MaxDataChunkSize")) {
              $logSize = $line.Split(":")[1]
              $logSize = $logSize.Trim()
              Break
            }
          }
        # Get Log data
          $params = '"{0}\SMMGetLogData.ps1" -computer {1} -user {2} -password {3} {4}' -f $collateralPath, $SutIp, $SutUser, $SutPassword, $logSize
          $output = SendCommand $params $logFile "IEX"
        # Delete temporary files if necessary
          If ($args[0] -ieq "NUL") {
            $temp = "{0}\*" -f $logFilePath
            Get-ChildItem -Path $temp -Include "LogData.log" | Remove-Item -Force -ErrorAction SilentlyContinue
          }
      } Else {
        If ($args[1] -ieq "True") {
          $params = $scriptFilePath, '--smm_command', 'get_log_data', '--start_workload'
        } Else {
          $params = $scriptFilePath, '--smm_command', 'get_log_data'
        }
        $null = SendCommand $params $args[0] "Python"
      }
  }

  Function GetLogFile {
    # Get log file
    # - $args[0] = logFile
    #   - "NUL" means send to bit-bucket
    # - $args[1] = startWorkload
    # - $args[2] = useCollateral
    # - returns telemetry log
      $filteredLog = @()
      $startMarker = "SMMGetLogFile.ps1"
      $endMarker   = "remote powershell complete"
      If ($args[2] -ieq "True") {
        # Get logfile
          If ($args[0] -ieq "NUL") {
            $logFile = "{0}\Telemetry.log" -f $logFilePath
          } Else {
            $logFile = $args[0]
          }
          Add-Content $logFile $startMarker
        # Extract data file contents
          $params = '"{0}\SMMGetLogFile.ps1" -computer {1} -user {2} -password {3}' -f $collateralPath, $SutIp, $SutUser, $SutPassword
          $output = SendCommand $params $logFile "IEX"
          Add-Content $logFile $endMarker
        If ($args[0] -ieq "NUL") {
          # Extract log
            $log = [IO.File]::ReadAllText($logFile)
            $filteredLog = $log -Split "`r`n"
          # Delete temporary file
            $temp = "{0}\*" -f $logFilePath
            Get-ChildItem -Path $temp -Filter "Telemetry.log" | Remove-Item -Force -ErrorAction SilentlyContinue
        }
      } Else {
        If ($args[1] -ieq "True") {
          $params = $scriptFilePath, '--smm_command', 'get_log_file', '--start_workload'
        } Else {
          $params = $scriptFilePath, '--smm_command', 'get_log_file'
        }
        $null = SendCommand $params $args[0] "Python"
      }
    # Extract log
      If ($filteredLog.Length -eq 0) {
        If (-Not($args[0] -ieq "NUL")) {
          # Read in log file into variable
            $log = [IO.File]::ReadAllText($args[0])
            $log = $log -Split "`r`n"
          # Loop thru lines looking for beginning and ending markers
            $startedFlag = "False"
            ForEach ($line in $log) {
              If (-Not($startedFlag -ieq "True")) {
                # Look for beginning marker
                If ($line.Contains($startMarker)) {
                  $startedFlag  = "True"
                  $filteredLog += $line
                }
              } Else {
                If ($line.Contains($endMarker)) {
                  # Found end marker. Bail.
                  Break
                }
                $filteredLog += $line
              }
            }
        }
      }
    Return $filteredLog
  }

  Function GetSmiCount {
    # Grab SMI count
      Write-Host (" - Get SMI Count...")
      If ($rwAppPath -ieq '') {
        $smiCount = "Unknown"
      } Else {
        # Grab SMI count from machine
          $logFileName = "SmiCount.log"
          $logFile     = "{0}\{1}" -f $logFilePath, $logFileName
          $params      = '{0} /command="RDMSR 0x34; RWExit" /logfile={1}' -f $rwAppPath, $logFile
          $s           = ""
          If ($launchedFromSut -ieq "True") {
            $output = SendCommand $params "NUL" "IEX"
            ForEach ($line in $output) {
              Write-Host ("   - output = [{0}]" -f $line)
            }
            # Wait for file
              $delayCount = 100   # Wait up to 1 second for the file to appear
              While (-Not (Test-Path $logFile -PathType Leaf)) {
                Start-Sleep -m 10
                $delayCount -= 1
                If ($delayCount -eq 0) {Break}
              }
              Start-Sleep -m 25   # Extra 25ms to allow the file to close
              If (Test-Path $logFile -PathType Leaf) {
                $output = [IO.File]::ReadAllText($logFile)
                $output = $output -Split "`r`n"
              } Else {
                $output = ""
              }
          } Else {
            # Make sure RW is not running
              StopSmiStress
            # Grab SMI count
              $pass = ConvertTo-SecureString -String $SutPassword -AsPlainText -Force
              $cred = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $SutUser, $pass
              $s    = New-PSSession -ComputerName $SutIp -credential $cred
              Invoke-Command -ScriptBlock {Param($logFilePath) New-Item -Path $logFilePath -ItemType directory -ErrorAction SilentlyContinue} -ArgumentList($logFilePath) -Session $s
              Invoke-Command -ScriptBlock {Param($logFile) Remove-Item $logFile -Force -ErrorAction SilentlyContinue} -ArgumentList($logFile) -Session $s
              Invoke-Command -ScriptBlock {Param($params) (Invoke-Expression "& $params *>&1") -Split "`r`n"} -ArgumentList($params) -Session $s
              # Wait for file to show up
                $delayCount = 100   # Wait up to 1 second for the file to appear
                While (-Not (Invoke-Command -ScriptBlock {Param($logFile) Test-Path $logFile -PathType Leaf} -ArgumentList($logFile) -Session $s)) {
                  Start-Sleep -m 10
                  $delayCount -= 1
                  If ($delayCount -eq 0) {Break}
                }
                Start-Sleep -m 25   # Extra 25ms to allow the file to close
              $output = Invoke-Command -ScriptBlock {Param($logFile) (Get-Content $logFile) -Split "`r`n"} -ArgumentList($logFile) -Session $s
              Invoke-Command -ScriptBlock {Param($logFile) Remove-Item $logFile -Force -ErrorAction SilentlyContinue} -ArgumentList($logFile) -Session $s
          }
        # Get SMI count from log
          $smiCount = "Unknown"
          ForEach ($line in $output) {
            If ($line.Contains("Read MSR 0x34")) {
              # $line = Read MSR 0x34: High 32bit(EDX) = 0xFEDCBA98, Low 32bit(EAX) = 0x76543210
              $smiCount     = $line.Split("=")[1] + $line.Split("=")[2]   # " 0xFEDCBA98, Low 32bit(EAX)  0x76543210"
              $smiCountHigh = $smiCount.Split("x")[1]                     # "FEDCBA98, Low 32bit(EAX)  0"
              $smiCountHigh = $smiCountHigh.Trim()                        # "FEDCBA98, Low 32bit(EAX)  0"
              $smiCountHigh = $smiCountHigh.Split(",")[0]                 # "FEDCBA98"
              $smiCountHigh = $smiCountHigh.Trim()                        # "FEDCBA98"
              $smiCountLow  = $smiCount.Split("x")[2]                     # "76543210"
              $smiCountLow  = $smiCountLow.Trim()                         # "76543210"
              $smiCount     = "0x" + $smiCountHigh + $smiCountLow         # "0xFEDCBA9876543210"
              Break
            }
          }
        # Close session if it exists
          If ($s -ne "") {
            Remove-PSSession -Session $s
          }
        # Kill log file
          $temp = "{0}\*" -f $logFilePath
          Get-ChildItem -Path $temp -Filter $logFileName | Remove-Item -Force -ErrorAction SilentlyContinue
      }
    Return $smiCount
  }

  Function GetTelemetry {
    # Grab the telemetry log
    # - $args[0] = rev
    # - $args[1] = logType
    # - $args[2] = logLevel
    # - $args[3] = logFile
    #   - "NUL" means send to bit-bucket
    # - $args[4] = startWorkload
    # - $args[5] = useCollateral
    # - returns telemetry log
    If ($launchedFromSut -ieq "True") {
      If ($args[1] -ieq "execution") {
        $params = '"{0}" -e' -f $telemetryAppPath
      } Else {
        $params = '"{0}" -v' -f $telemetryAppPath
      }
      $log = SendCommand $params "NUL" "IEX"
      $logFile = ""
      ForEach ($line in $log) {
        If ($line.Contains("WRITTEN TO")) {
          $logFile = ($line -Split "WRITTEN TO")[1]
          $logFile = $logFile.Trim()
        }
      }
      If ($logFile) {
        $log = [IO.File]::ReadAllText($logFile)
        $log = $log -Split "`r`n"
      } Else {
        $log = ""
      }
    } Else {
      # Set log revision
        SetLogRev $args[0] $args[3] $args[4] $args[5]
      # Set log type
        SetLogType $args[1] $args[3] $args[4] $args[5]
      # Get log data
        GetLogData $args[3] $args[4] $args[5]
      # Get log file
        $log = GetLogFile $args[3] $args[4] $args[5]
    }
    Return $log
  }

  Function KillProcess {
    # Kill process
    # - $args[0] = processName
    # - $args[1] = remoteFlag
      If (($args[1] -ieq "True") -And ($launchedFromSut -ieq "False")) {
        $pass    = ConvertTo-SecureString -String $SutPassword -AsPlainText -Force
        $cred    = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $SutUser, $pass
        $s       = New-PSSession -ComputerName $SutIp -credential $cred
        $process = $args[0]
        $null    = Invoke-Command -ScriptBlock {Param($process) Stop-Process -Name $process -Force -ErrorAction SilentlyContinue} -ArgumentList($process) -Session $s -ErrorAction SilentlyContinue
        Remove-PSSession -Session $s
        Start-Sleep -m 250
      } Else {
        $process = Get-Process $args[0] -ErrorAction SilentlyContinue
        While ($process) {
          # Kill it with a sledge hammer.
            $process | Stop-Process -Force
            Start-Sleep -m 250
            $process = Get-Process $args[0] -ErrorAction SilentlyContinue
        }
        Remove-Variable process
      }
  }

  Function LaunchBmcJournal {
    # Launches BMC journal if it is not already running
    # - $args[0] - BMC Com port
    # - $args[1] - BMC BAUD rate
    # - $args[2] - BMC user
    # - $args[3] - BMC password
      $bmcPort       = $args[0]
      $bmcBaud       = $args[1]
      $bmcUser       = $args[2]
      $bmcPassword   = $args[3]
      $bmcSerialPort = New-Object System.IO.Ports.SerialPort $bmcPort,$bmcBaud,None,8,One
      $bmcSerialPort.Open()

      $read = WriteSerial $bmcSerialPort "" "intel-obmc login:"
      $result = $read + [Environment]::NewLine
      #Write-Host ("   - Enter sent = [{0}]" -f $read)
      If ($read -ne "") {
        $read = WriteSerial $bmcSerialPort $bmcUser "Password:"
        $result += $read + [Environment]::NewLine
        #Write-Host ("   - User sent = [{0}][{1}]" -f $bmcUser, $read)
        If ($read -ne "") {
          $read = WriteSerial $bmcSerialPort $bmcPassword "@intel-obmc:"
          $result += $read + [Environment]::NewLine
          #Write-Host ("   - Password sent = [{0}][{1}]" -f $bmcPassword, $read)
          If ($read -ne "") {
            $read = WriteSerial $bmcSerialPort "journalctl -f" ""
            $result += $read + [Environment]::NewLine
            #Write-Host ("   - journalctl -f sent = [{0}]" -f $read)
          }
        }
      }
      $bmcSerialPort.Close()
      #Write-Host ("   - result = [{0}]" -f $result.TrimEnd())
  }

  Function ParseAutomationSystemFile {
    # Parses the automation system file for parameters and writes them to global variables
    # - Returns Pass/Fail
    # Assume it fails
    $result = "Fail"
    If ($scriptDebug -ieq "True") {Write-Host ("ParseAutomationSystemFile() - starting...")}
    # Determine if we are on the SUT
      If ($launchedFromSut -ieq "False") {
        If ((Test-Path $sruAppPath -PathType Leaf) -And (Test-Path $telemetryAppPath -PathType Leaf)) {
          Set-Variable -Name launchedFromSut -Value "True" -Option AllScope -Scope Global
        }
      }
      If ($scriptDebug -ieq "True") {Write-Host ("ParseAutomationSystemFile() - launchedFromSut = {0}" -f $launchedFromSut)}
      If ($launchedFromSut -ieq "False") {
        # Make sure file exists
          If ($scriptDebug -ieq "True") {Write-Host ("ParseAutomationSystemFile() - checking for [{0}]..." -f $automationFilePath)}
          If (Test-Path $automationFilePath -PathType Leaf) {
            If ($scriptDebug -ieq "True") {Write-Host ("ParseAutomationSystemFile() - found {0}..." -f $automationFilePath)}
            [xml]$config = Get-Content -Path $automationFilePath
            $result = "Pass"
            ForEach ($item in $automationList) {
              $endNode  = $item[0].Split("/")[-1]
              $testNode = $item[0].TrimEnd($endNode)
              $testNode = $testNode.TrimEnd("/")
              [string]$search = Select-Xml -xml $config -XPath $testNode | ForEach-Object { $_.Node.$endNode }
              If ($scriptDebug -ieq "True") {Write-Host ("ParseAutomationSystemFile() - [{0}]  [{1}]  [{2}]  [{3}]" -f $search, $item[0], $testNode, $endNode)}
              If ($search -eq "") {
                # Failed to find this item
                $result = "Fail"
              } Else {
                If ($item[1] -ieq "AutomationFramework") {
                  $search = ($search -Split("\\seamless"))[0]
                }
                Set-Variable -Name $item[1] -Value $search -Option AllScope -Scope Global
              }
            }
          }
      }
    Return $result
  }

  Function SendCommand {
    # Sends a command to be executed
    # - $args[0] = params
    # - $args[1] = logFile
    #   - "NUL" means send to bit-bucket
    # - $args[2] = type of command
      $params = $args[0]
      If ($args[2] -ieq "Python") {
        If ($args[1] -ieq "NUL") {
          & python.exe @params *>&1 > $null
        } Else {
          & python.exe @params *>&1 >> $args[1]
        }
        $output = ""
      } ElseIf ($args[2] -ieq "IEX") {
        $params += " *>&1"
        If ($args[1] -ine "NUL") {
          $params += (" >>{0}" -f $args[1])
        }
        $output = (Invoke-Expression "& $params") -Split "`r`n"
      }
    Return $output
  }

  Function SetLogLevel {
    # Set log level
    # - $args[0] = level
    # - $args[1] = logFile
    #   - "NUL" means send to bit-bucket
    # - $args[2] = startWorkload
    # - $args[3] = useCollateral
      If ($launchedFromSut -ieq "True") {
        $params = '"{0}" -s {1}' -f $telemetryAppPath, $args[0]
        $null = SendCommand $params "NUL" "IEX"
      } Else {
        If ($args[3] -ieq "True") {
          $params = '"{0}\SMMSetLogLevel.ps1" -computer {1} -user {2} -password {3} {4}' -f $collateralPath, $SutIp, $SutUser, $SutPassword, $args[0]
          $output = SendCommand $params $args[1] "IEX"
        } Else {
          If ($args[2] -ieq "True") {
            $params = $scriptFilePath, '--smm_command', 'set_log_level', '--log_level', $args[0], '--start_workload'
          } Else {
            $params = $scriptFilePath, '--smm_command', 'set_log_level', '--log_level', $args[0]
          }
          $null = SendCommand $params $args[1] "Python"
        }
      }
  }

  Function SetLogRev {
    # Set log revision
    # - $args[0] = rev
    # - $args[1] = logFile
    #   - "NUL" means send to bit-bucket
    # - $args[2] = startWorkload
    # - $args[3] = useCollateral
      If ($args[3] -ieq "True") {
        $params = '"{0}\SMMSetLogVer.ps1" -computer {1} -user {2} -password {3} {4}' -f $collateralPath, $SutIp, $SutUser, $SutPassword, $args[0]
        $output = SendCommand $params $args[1] "IEX"
      } Else {
        If ($args[2] -ieq "True") {
          $params = $scriptFilePath, '--smm_command', 'set_log_rev', '--log_rev', $args[0], '--start_workload'
        } Else {
          $params = $scriptFilePath, '--smm_command', 'set_log_rev', '--log_rev', $args[0]
        }
        $null = SendCommand $params $args[1] "Python"
      }
  }

  Function SetLogType {
    # Set log type
    # - $args[0] = logType
    # - $args[1] = logFile
    #   - "NUL" means send to bit-bucket
    # - $args[2] = startWorkload
    # - $args[3] = useCollateral
      If ($args[3] -ieq "True") {
        $params = '"{0}\SMMSetLogType.ps1" -computer {1} -user {2} -password {3} {4}' -f $collateralPath, $SutIp, $SutUser, $SutPassword, $args[0]
        $output = SendCommand $params $args[1] "IEX"
      } Else {
        If ($args[2] -ieq "True") {
          $params = $scriptFilePath, '--smm_command', 'set_log_type', '--log_type', $args[0], '--start_workload'
        } Else {
          $params = $scriptFilePath, '--smm_command', 'set_log_type', '--log_type', $args[0]
        }
        $null = SendCommand $params $args[1] "Python"
      }
  }

  Function StartSmiStress {
    # This is where we launch RWEveryting script
    If (($smiStressFlag -ieq "True") -And (-Not($rwAppPath -ieq ''))) {
      Write-Host (" - Starting periodic SMI...")
      # Currently set to 720,000 cycles with a 10ms delay between is about 120 minutes
      $cycles = 720000
      $params = '/command="LOOP{{{0}, DELAY 10; O16 0xB2 0x0000}}"' -f $cycles
      If ($launchedFromSut -ieq "True") {
        $null = SendCommand '{0} $params' -f $rwAppPath "NUL" "IEX"
      } Else {
        If ($RwSession -ne "") {
          StopSmiStress
        }
        $pass   = ConvertTo-SecureString -String $SutPassword -AsPlainText -Force
        $cred   = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $SutUser, $pass
        $s      = New-PSSession -ComputerName $SutIp -credential $cred
        Invoke-Command -ScriptBlock {Param($rwAppPath, $params) Start-Process $rwAppPath $params} -ArgumentList($rwAppPath, $params) -Session $s
        Set-Variable -Name RwSession -Value $s -Option AllScope -Scope Global
        Write-Host ("   - Command sent [{0}]..." -f $params)
      }
    }
  }

  Function StopSmiStress {
    # This is where we kill the RWEveryting script
    If (($smiStressFlag -ieq "True") -And (-Not($rwAppPath -ieq ''))) {
      Write-Host (" - Stopping periodic SMI...")
      If ($launchedFromSut -ieq "True") {
        KillProcess RW "False"
      } Else {
        If ($RwSession -ne "") {
          Remove-PSSession -Session $RwSession
          Set-Variable -Name RwSession -Value "" -Option AllScope -Scope Global
        }
        KillProcess RW "True"
      }
    }
  }

  Function TestCapsule {
    # Test capsule and return pass/fail
    # - $args[0] = testNumber
    # - $args[1] = logFile
    #   - "NUL" means send to bit-bucket
    # - $args[2] = startWorkload
    # - $args[3] = miniTestFlag
    # Returns Pass/Fail
    If ($testCapsules[$args[0]][2] -ieq "True") {
      # Need to set the log level before injecting the capsule
        $executionLogLevel = $logLevelList[(Get-Random -Maximum @($logLevelList).length)]
        SetLogLevel $executionLogLevel[0] ("{0}\execution.log" -f $logFilePath) $args[2] "True"
      # Delete temporary file
        $temp = "{0}\*" -f $logFilePath
        Get-ChildItem -Path $temp -Include "execution.log" | Remove-Item -Force -ErrorAction SilentlyContinue
    }
    # Send test capsule
      $maxKpi = $testCapsules[$args[0]][4]
      $maxKpi = [int]$maxKpi.Trim()
      If (($launchedFromSut -ieq "True") -Or ($args[3] -ieq "True")) {
#TODO: Need to get file size and set KPI if KPI is set to 0
        If ($launchedFromSut -ieq "True") {
          $params = '"{0}" -i {1}' -f $sruAppPath, $testCapsules[$args[0]][0]
        } Else {
          $params = '"{0}\SMMCodeInject.ps1" -computer {1} -user {2} -password {3} {4}' -f $collateralPath, $SutIp, $SutUser, $SutPassword, $testCapsules[$args[0]][0]
        }
        $output = SendCommand $params "NUL" "IEX"
        # Parse output to see if we failed
          $testResult = ""
          ForEach ($line in $output) {
            If ($args[1] -ine "NUL") {
              Add-Content $args[1] $line
            }
            If ($line.Contains("Execution Succeeded")) {
              $testResult += "Pass"
            }
            If ($line.Contains("ERROR")) {
              $testResult += "Fail"
            }
            If (($launchedFromSut -ieq "True") -Or ($args[3] -ieq "True")) {
              If (($line.Contains("Authentication Time")) -Or (($line.Contains("Execution Time")) -And ($testCapsules[$args[0]][0] -ieq $executionKpiCapsule))) {
                # Grab time and convert to ms
                $checkKpi  = ($line -Split ":")[1]
                $checkKpi  = ($checkKpi -Split "nSec")[0]
                $checkKpi  = [int]$checkKpi.Trim()
                $checkKpi /= [math]::Pow(10, 6)
                If ($checkKpi -ge $maxKpi) {
                  If (($treatSanityKpiFailAsFailure -ieq "False") -And ($args[3] -ieq "True")) {
                    Write-Host (" - WARNING: Failed due to KPI!  {0}   [{1}ms : {2}ms]" -f $line, $checkKpi, $maxKpi)
                    $testResult += "Pass"
                  } Else {
                    Write-Host (" - ERROR: Failed due to KPI!  {0}   [{1}ms : {2}ms]" -f $line, $checkKpi, $maxKpi)
                    $testResult += "Fail"
                  }
                }
              }
            }
          }
        # Translate "PassFail"/"FailPass"/"Fail" to "Fail" and "PassPass"/"Pass" to "Pass"
          If ($testResult.Contains("Fail")) {
            $testResult = "Fail"
          } Else {
            $testResult = "Pass"
          }
        # Check test to see if we passed or failed
          If ((($testResult -ieq "Fail") -And ($testCapsules[$args[0]][1] -ieq "Pass")) -Or (($testResult -ieq "Pass") -And ($testCapsules[$args[0]][1] -ieq "Fail"))) {
            $testResult = "Fail"
          } Else {
            $testResult = "Pass"
          }
      } Else {
        If ($args[2] -ieq "True") {
          $params = $scriptFilePath, '--smm_command', 'code_inject', '--expected_ver', '0x00000001', '--KPI', $maxKpi, '--smm_capsule', $testCapsules[$args[0]][0], '--start_workload'
        } Else {
          $params = $scriptFilePath, '--smm_command', 'code_inject', '--expected_ver', '0x00000001', '--KPI', $maxKpi, '--smm_capsule', $testCapsules[$args[0]][0]
        }
        $null = SendCommand $params $args[1] "Python"
        # Determine pass/fail
          If ((($LASTEXITCODE -ne 0) -And ($testCapsules[$args[0]][1] -ieq "Pass")) -Or (($LASTEXITCODE -eq 0) -And ($testCapsules[$args[0]][1] -ieq "Fail"))) {
            $testResult = "Fail"
          } Else {
            $testResult = "Pass"
          }
      }
    # Get telemetry if enabled for this capsule
      $executionFlag = "Blank"
      If ($testCapsules[$args[0]][2] -ieq "True") {
        If (-Not($args[1] -ieq "NUL")) {
          $logFile = $args[1]
          $logFile = $logFile.TrimEnd(".log")
          # Get history log
            $historyLogFile = "{0}-history.log" -f $logFile
            $historyLog     = GetHistoryTelemetry "2" ("{0}\history.log" -f $logFilePath) $args[2] "True"
          # Get execution log
            $executionLogFile  = "{0}-execution.log" -f $logFile
            $executionLog      = GetExecutionTelemetry "2" $executionLogLevel[0] ("{0}\execution.log" -f $logFilePath) $args[2] "True"
          # Check execution log to see if level is in there
            $executionFlag = "False"
            ForEach ($line in $executionLog) {
              If ($line.Contains($executionLogLevel[1])) {
                $executionFlag = "True"
                Break
              }
            }
          # Filter out the telemetry info
            Set-Content -Path $historyLogFile -Value $historyLog
            Set-Content -Path $executionLogFile -Value $executionLog
            Add-Content $executionLogFile ("`n`nLog level = {0} [{1}]" -f $executionLogLevel[0], $executionLogLevel[1])
          # Delete temporary files
            $temp = "{0}\*" -f $logFilePath
            Get-ChildItem -Path $temp -Filter "history.log"   | Remove-Item -Force -ErrorAction SilentlyContinue
            Get-ChildItem -Path $temp -Filter "execution.log" | Remove-Item -Force -ErrorAction SilentlyContinue
        }
      }
      $testResult += ("|{0}" -f $executionFlag)
    Return $testResult
  }

  Function TestSerialPort {
    # Send <ENTER> to all of the COM ports looking for $args[0] in the response
    # - $args[0] value to look for in the COM response to <ENTER>
    # - $args[1] Sanity check this comport first
    # - $args[2] Baud rate
    # - returns COM port
      $testString = $args[0]
      $testPort   = $args[1]
      $testBaud   = $args[2]
      If (-Not($testBaud)) {
        $testBaud = 115200
      } Else {
        $testBaud = [int]$testBaud
      }
      $testComPort = ""
      $comPortList = [System.IO.Ports.SerialPort]::getportnames()
      KillProcess putty "False"
      Start-Sleep -m 100
      If (($testPort) -And (-Not($testPort -eq "")) -And ($comPortList.Contains($testPort))) {
        $testComPort = TestSerialPortWorker $testString $testPort $testBaud
      }
      If ($testComPort -eq "") {
        ForEach ($comPort in $comPortList) {
          $testComPort = TestSerialPortWorker $testString $comPort $testBaud
          If ($testComPort -ne "") {Break}
        }
      }
    Return $testComPort
  }

  Function TestSerialPortWorker {
    # Send <ENTER> to all of the COM ports looking for $args[0] in the response
    # - $args[0] value to look for in the COM response to <ENTER>
    # - $args[1] Sanity check this comport first
    # - $args[2] Baud rate
    # - returns COM port
      $testString = $args[0]
      $testPort   = $args[1]
      $testBaud   = $args[2]
      If (-Not($testBaud)) {
        $testBaud = 115200
      } Else {
        $testBaud = [int]$testBaud
      }
      $testComPort = ""
      $result      = " " + $testPort + " "
      $serialPort  = New-Object System.IO.Ports.SerialPort $testPort,$testBaud,None,8,One
      $serialPort.Open()
      Start-Sleep -m 50
      For ($idx = 1; $idx -le 3; $idx++) {
        $serialPort.WriteLine("`n")
        Start-Sleep -m 50
        $result += ($serialPort.ReadExisting() | Out-String)
        Start-Sleep -m 50
      }
      $serialPort.Close()
      If ($result.Contains($testString)) {
        # Found the serial port
          $testComPort = $testPort
      }
    Return $testComPort
  }

  Function WriteSerial {
    # Writes to serial port and waits for input
    # - $args[0] - COM object
    # - $args[1] - Data out
    # - $args[2] - Wait for string
      $comObject     = $args[0]
      $dataOut       = $args[1]
      $waitForString = $args[2]
      $dataIn        = ""

      # Empty buffer
      $null = EmptyComBuffer $comObject

      # Send data
      $comObject.WriteLine($dataOut)
      Start-Sleep -m 50

      # Get return data
      $result = ""
      If ($waitForString -ne "") {
        $waitCount = 600
        While ($waitCount -gt 0) {
          $read = ($comObject.ReadExisting() | Out-String).Split([Environment]::NewLine)
          $line = ""
          ForEach ($line in $read) {
            $line = $line.Trim().TrimEnd()
            If ($line -ne "") {
              # Strip out ESC sequences
              If (-Not($line.StartsWith([char](0x1B)))) {
                If ($line -ine $dataOut) {$result += $line + [Environment]::NewLine}
              }
              If ($line.Contains($waitForString)) {Break}
            }
          }
          If ($line.Contains($waitForString)) {Break}
          Start-Sleep -m 50
          $waitCount -= 1
        }
        If ($waitCount -eq 0) {
          Write-Host ("   - WARNING: Failed to recieve {0} --> [{1}]" -f $waitForString, $result)
        }
        # Empty buffer
        $null = EmptyComBuffer $comObject
      } Else {
        # Empty buffer
        $result = (EmptyComBuffer $comObject).TrimStart($dataOut)
      }
      $dataIn = $result.TrimEnd()

    Return $dataIn
  }

  Function ZipFiles {
    # Zips up files matching a given pattern
    # - $args[0] = path
    # - $args[1] = filePattern to include
    # - $args[2] = filePattern to exclude
    #              - NUL means exclude nothing
    # - $args[3] = zipFilePath
    # - $args[4] = deleteFlag
    If ($scriptDebug -ieq "True") {
      Write-Output ("- ZipFiles() - args[0] - path                   = {0}" -f $args[0])
      Write-Output ("- ZipFiles() - args[1] - filePattern to include = {0}" -f $args[1])
      Write-Output ("- ZipFiles() - args[2] - filePattern to exclude = {0}" -f $args[2])
      Write-Output ("- ZipFiles() - args[3] - zipFilePath            = {0}" -f $args[3])
      Write-Output ("- ZipFiles() - args[4] - deleteFlag             = {0}" -f $args[4])
    }
    $zipFN = "{0}\{1}-logs.zip" -f $logFilePath, $testTag
    $fileToZip = ("{0}\*.log" -f $logFilePath)
    If ($args[2] -ieq "NUL") {
      Get-ChildItem -Path ("{0}\*" -f $args[0]) -File -Filter $args[1] | Compress-Archive -DestinationPath $args[3] -Update
    } Else {
      Get-ChildItem -Path ("{0}\*" -f $args[0]) -File -Filter $args[1] -Exclude $args[2] | Compress-Archive -DestinationPath $args[3] -Update
    }
    If ($args[4] -ieq "True") {
      If ($args[2] -ieq "NUL") {
        Get-ChildItem -Path ("{0}\*" -f $args[0]) -File -Filter $args[1] | Remove-Item -Force -ErrorAction SilentlyContinue
      } Else {
        Get-ChildItem -Path ("{0}\*" -f $args[0]) -File -Filter $args[1] -Exclude $args[2] | Remove-Item -Force -ErrorAction SilentlyContinue
      }
    }
  }

#==================================================================================================
# Start of main script
#==================================================================================================
# Make sure the log directory exists
  $null = New-Item -Path $logFilePath -ItemType directory -ErrorAction SilentlyContinue

# Dump script info
  Write-Output ("{0} script.  Version #{1}" -f $(split-path $PSCommandPath -Leaf), $scriptVersion | Tee-Object -FilePath $reportLogPath -Append)

# Parse automation system info file
  Write-Output (" - Getting default configuration information..." | Tee-Object -FilePath $reportLogPath -Append)
  $return = ParseAutomationSystemFile
  If (-Not($return -ieq "Pass")) {
    Write-Output ("ERROR: Failed to find/parse {0}!!!" -f $automationFilePath | Tee-Object -FilePath $reportLogPath -Append)
    Exit
  }
  If (($scriptDebug -ieq "True") -And ($launchedFromSut -ieq "False")) {
    Write-Output ("- SutUser               = {0}" -f $SutUser             | Tee-Object -FilePath $reportLogPath -Append)
    Write-Output ("- SutPassword           = {0}" -f $SutPassword         | Tee-Object -FilePath $reportLogPath -Append)
    Write-Output ("- SutIp                 = {0}" -f $SutIp               | Tee-Object -FilePath $reportLogPath -Append)
    Write-Output ("- BiosComPort           = {0}" -f $BiosComPort         | Tee-Object -FilePath $reportLogPath -Append)
    Write-Output ("- BiosBaudRate          = {0}" -f $BiosBaudRate        | Tee-Object -FilePath $reportLogPath -Append)
    Write-Output ("- AutomationFramework   = {0}" -f $AutomationFramework | Tee-Object -FilePath $reportLogPath -Append)
    Write-Output ("- BmcUser               = {0}" -f $BmcUser             | Tee-Object -FilePath $reportLogPath -Append)
    Write-Output ("- BmcPassword           = {0}" -f $BmcPassword         | Tee-Object -FilePath $reportLogPath -Append)
    Write-Output ("- BmcIp                 = {0}" -f $BmcIp               | Tee-Object -FilePath $reportLogPath -Append)
    Write-Output ("- BmcComPort            = {0}" -f $BmcComPort          | Tee-Object -FilePath $reportLogPath -Append)
    Write-Output ("- BmcBaudRate           = {0}" -f $BmcBaudRate         | Tee-Object -FilePath $reportLogPath -Append)
  }

# Sanity checks
  # Check for putty
  $puttyAppPath = FindApp "putty.exe" "False"
  Write-Output ("   - Local Putty @ {0}" -f $puttyAppPath | Tee-Object -FilePath $reportLogPath -Append)
  If ($puttyAppPath -ieq '') {
    Write-Output ("ERROR: Failed to find either a local copy of Putty!!!" | Tee-Object -FilePath $reportLogPath -Append)
    Exit
  }
  $registry = Get-ItemProperty -Path $puttyRegistryPath -ErrorAction SilentlyContinue
  If ($registry.Length -eq 0) {
    Write-Output (' - WARNING: Missing putty session {0}!!!' -f $puttySession                                   | Tee-Object -FilePath $reportLogPath -Append)
    Write-Output ('   - Please follow the steps below to fix this issue and then re-run the script.'            | Tee-Object -FilePath $reportLogPath -Append)
    Write-Output ('     - #1. Open the putty GUI.'                                                              | Tee-Object -FilePath $reportLogPath -Append)
    Write-Output ('     - #2. Look for a saved session called "{0}" & load it if it is there.' -f $puttySession | Tee-Object -FilePath $reportLogPath -Append)
    Write-Output ('     - #3. If it is not there, in the "Saved Sessions" box, type "{0}".' -f $puttySession    | Tee-Object -FilePath $reportLogPath -Append)
    Write-Output ('     - #4. Expand "Session" on the left, at the top.'                                        | Tee-Object -FilePath $reportLogPath -Append)
    Write-Output ('     - #5. Click on "Logging".'                                                              | Tee-Object -FilePath $reportLogPath -Append)
    Write-Output ('     - #6. Make sure the radio button "Always append to the end of it" is selected.'         | Tee-Object -FilePath $reportLogPath -Append)
    Write-Output ('     - #7. Click on "Session" on the left.'                                                  | Tee-Object -FilePath $reportLogPath -Append)
    Write-Output ('     - #8. Click on "Save"'                                                                  | Tee-Object -FilePath $reportLogPath -Append)
    Exit
  }

  # Check for RW
  If ($launchedFromSut -ieq "True") {
    $rwAppPath = FindApp "rw.exe" "False"
    Write-Output ("   - Local RW    @ {0}" -f $rwAppPath    | Tee-Object -FilePath $reportLogPath -Append)
  } Else {
    $rwAppPath = FindApp "rw.exe" "True"
    Write-Output ("   - Remote RW   @ {0}" -f $rwAppPath    | Tee-Object -FilePath $reportLogPath -Append)
  }
  If ($rwAppPath -ieq '') {
    If ($treatNoRwAsFailure -ieq "False") {
      Write-Output ("WARNING: Failed to find RW!!!"                               | Tee-Object -FilePath $reportLogPath -Append)
      Write-Output ("         SMI count, SMI harassment, and CSR count disabled." | Tee-Object -FilePath $reportLogPath -Append)
    } Else {
      Write-Output ("ERROR: Failed to find RW!!!" | Tee-Object -FilePath $reportLogPath -Append)
      Exit
    }
  }

# Update globals
  Write-Output (" - Updating global variables..." | Tee-Object -FilePath $reportLogPath -Append)
  If ($launchedFromSut -ieq "True") {
    $rootPath               = "C:\Windows\System32"
    $scriptPath             = "Not used."
    $scriptFilePath         = "Not used."
    $collateralPath         = "Not used."
    $biosVersionScriptPath  = "Not used."
    $updateScripts          = "False"
  } Else {
    $rootPath               = $AutomationFramework
    $scriptPath             = "{0}\{1}" -f $rootPath,       $scriptPath
    $scriptFilePath         = "{0}\{1}" -f $scriptPath,     $scriptFile
    $collateralPath         = "{0}\{1}" -f $rootPath,       $collateralPath
    $biosVersionScriptPath  = "{0}\{1}" -f $collateralPath, $biosVersionScript
  }
  If ($scriptDebug -ieq "True") {
    Write-Output ("- rootPath              = {0}" -f $rootPath              | Tee-Object -FilePath $reportLogPath -Append)
    Write-Output ("- scriptPath            = {0}" -f $scriptPath            | Tee-Object -FilePath $reportLogPath -Append)
    Write-Output ("- scriptFilePath        = {0}" -f $scriptFilePath        | Tee-Object -FilePath $reportLogPath -Append)
    Write-Output ("- collateralPath        = {0}" -f $collateralPath        | Tee-Object -FilePath $reportLogPath -Append)
    Write-Output ("- biosVersionScriptPath = {0}" -f $biosVersionScriptPath | Tee-Object -FilePath $reportLogPath -Append)
    Write-Output ("- sruAppPath            = {0}" -f $sruAppPath            | Tee-Object -FilePath $reportLogPath -Append)
    Write-Output ("- telemetryAppPath      = {0}" -f $telemetryAppPath      | Tee-Object -FilePath $reportLogPath -Append)
  }

# Get IFWI version and select capsules
  Write-Output (" - Getting IFWI version..." | Tee-Object -FilePath $reportLogPath -Append)
  $ifwiVersion = GetIfwiVersion
  Write-Output ("   - IFWI version = {0}" -f $ifwiVersion | Tee-Object -FilePath $reportLogPath -Append)
  $ifwiLabel = GetCapsuleLabel $ifwiVersion
  $testCapsules = Get-Variable -Name $ifwiLabel -ValueOnly
  Write-Output ("   - IFWI label   = {0}" -f $ifwiLabel | Tee-Object -FilePath $reportLogPath -Append)

# Sanity check com ports & file locations
  Write-Output (" - Getting BMC/BIOS COM ports..." | Tee-Object -FilePath $reportLogPath -Append)
  KillProcess putty "False"
  If ($biosComPort -eq "") {
    # BIOS COM port is not hard coded, try to detect it
    $biosComPort = GetBiosSerialPort
  }
  Write-Output ("   - BIOS COM     = {0}" -f $biosComPort | Tee-Object -FilePath $reportLogPath -Append)
  If ($bmcComPort -eq "") {
    # BMC COM port is not hard coded, try to detect it
    $bmcComPort = GetBmcSerialPort
  }
  Write-Output ("   - BMC COM      = {0}" -f $bmcComPort | Tee-Object -FilePath $reportLogPath -Append)
  $targetPorts = 0
  If ($biosComPort) {
    $targetPorts++
  }
  If ($bmcComPort) {
    $targetPorts++
  }
  If ($targetPorts -lt 2) {
    # Failed to find BIOS and/or BMC com ports
      Write-Output ("ERROR: Failed to find BIOS[{0}] and/or BMC[{1}] COM port(s)!!!" -f $biosComPort, $bmcComPort | Tee-Object -FilePath $reportLogPath -Append)
  } ElseIf (-Not (Test-Path $rootPath)) {
    # Failed to find the test Python folder
      Write-Output ("ERROR: Failed to find the test folder {0}!!!" -f $rootPath | Tee-Object -FilePath $reportLogPath -Append)
  } ElseIf ((-Not (Test-Path $scriptFilePath -PathType Leaf)) -And ($launchedFromSut -ieq "False")) {
    # Failed to find the test Python script
      Write-Output ("ERROR: Failed to find the test script {0}!!!" -f $scriptFilePath | Tee-Object -FilePath $reportLogPath -Append)
  } Else {
    # Clear out the log folder and sub-folders
      Get-ChildItem -Path $logFilePath -Recurse -Directory | ForEach-Object {Remove-Item -Path $_.FullName -Recurse -Force -ErrorAction SilentlyContinue}
      Get-ChildItem -Path ("{0}\*" -f $logFilePath) -File -Exclude ("{0}.rst" -f $reportLogName) | Remove-Item -Force -ErrorAction SilentlyContinue

    # Get global start time
      $globalStartTime = $(Get-Date)

    # Print header
      $testReport = $majorSeparator + $headerLine + $majorSeparator
      $reportLines = 0

    # Launch BMC journal
      Write-Output (" - Turning on BMC journal..." | Tee-Object -FilePath $reportLogPath -Append)
      LaunchBmcJournal $bmcComPort $BmcBaudRate 'root' $BmcPassword

    # Perform pre-loop sanity test
      If ($skipPreCheck -ieq "True") {
        Write-Output (" - WARNING: Pre sanity checking of capsules skipped!!!" | Tee-Object -FilePath $reportLogPath -Append)
        $sanityPreCheckFlag = "Pass"
      } Else {
        Write-Output (" - Sanity checking used test capsules..." | Tee-Object -FilePath $reportLogPath -Append)
        $sanityPreCheck = CapsuleSanityCheck
        Write-Output ("{0}" -f $sanityPreCheck | Tee-Object -FilePath $reportLogPath -Append)
        If (($sanityPreCheck -Split '\n')[0].Contains("FAILED!!!")) {
          $sanityPreCheckFlag = "Fail"
          $scriptStatus       = "FAILED"
          $sanityCheck        = "Pre test sanity check FAILED!!!"
        } Else {
          $sanityPreCheckFlag = "Pass"
          $sanityCheck        = "Pre test sanity check passed."
        }
        # Get elapsed time for sanity checking
          $sanityElapsedTime = (($sanityPreCheck -Split '\n') | Select -Last 1)
          $sanityElapsedTime = ($sanityElapsedTime -Split '-')[1]
          $sanityElapsedTime = $sanityElapsedTime.Trim()
        # Add info to report
          $sanityCheck  = "{0,-35} {1,27}" -f $sanityCheck, $sanityElapsedTime
          $testReport += "| {0} |`n" -f $sanityCheck
      }

    If ($sanityPreCheckFlag -ieq "Pass") {
      $testReport += $minorSeparator
      If ($forceDelay -gt 0) {
        Write-Output ("WARNING: Delay is forced to {0}ms" -f $forceDelay | Tee-Object -FilePath $reportLogPath -Append)
      }
      If ($forceLoopCount -gt 0) {
        Write-Output ("WARNING: Loop count is forced to {0}" -f $forceLoopCount | Tee-Object -FilePath $reportLogPath -Append)
      }
      # Loop thru the testArray and execute the active tests $testArray[row][column]
        ForEach ($test in $testArray) {
          # Initialize cycle variables
            $testTag         = $test[0]
            $testNum         = $test[1]
            $testBlocked     = $test[2]
            $testDelay       = $test[3]
            $testCount       = $test[4]
            $testPass        = $test[5]
            $testFail        = $test[6]
            $testPreCapsule  = $test[7]
            $testPostCapsule = $test[8]
            $testPreCount    = $test[9]
            $testPostCount   = $test[10]
            If ($forceDelay     -gt 0) {$testDelay = $forceDelay}
            If ($forceLoopCount -gt 0) {$testCount = $forceLoopCount}
            $testLogFile = "{0}\{1}.rst" -f $logFilePath, $testTag
            If ($scriptDebug -ieq "True") {
              Write-Output ("testTag         = {0}" -f $testTag         | Tee-Object -FilePath $reportLogPath -Append)
              Write-Output ("testNum         = {0}" -f $testNum         | Tee-Object -FilePath $reportLogPath -Append)
              Write-Output ("testBlocked     = {0}" -f $testBlocked     | Tee-Object -FilePath $reportLogPath -Append)
              Write-Output ("testDelay       = {0}" -f $testDelay       | Tee-Object -FilePath $reportLogPath -Append)
              Write-Output ("testCount       = {0}" -f $testCount       | Tee-Object -FilePath $reportLogPath -Append)
              Write-Output ("testPreCapsule  = {0}" -f $testPreCapsule  | Tee-Object -FilePath $reportLogPath -Append)
              Write-Output ("testPostCapsule = {0}" -f $testPostCapsule | Tee-Object -FilePath $reportLogPath -Append)
              Write-Output ("testPreCount    = {0}" -f $testPreCount    | Tee-Object -FilePath $reportLogPath -Append)
              Write-Output ("testPostCount   = {0}" -f $testPostCount   | Tee-Object -FilePath $reportLogPath -Append)
            }

          # Check to see if we need a divider
            If ((($reportLines % 3) -eq 0) -And ($reportLines -gt 0)) {
              $testReport += $minorSeparator
            }

          If ($testBlocked -eq "") {
            If ($testPass -eq 0) {
              $testPass = ""
            }
            If ($testFail -eq 0) {
              $testFail = ""
            }

            # Now execute test
              Write-Output ("{0} {1}: Starting {2} cycles..." -f $testTag, $testNum, $testCount | Tee-Object -FilePath $reportLogPath -Append | Tee-Object -FilePath $testLogFile -Append)
              $testStartTime = $(Get-Date)

            # Get current SMI count
              $smiCount = GetSmiCount
              Write-Output (" - Starting SMI count = {0}" -f $smiCount | Tee-Object -FilePath $reportLogPath -Append | Tee-Object -FilePath $testLogFile -Append)

            # Open BIOS & BMC serial coms. Use Putty because Powershell serial tools suck.
              KillProcess putty "False"
              $biosLogFile = "{0}\{1}-BIOS.log" -f $logFilePath, $testTag
              If (Test-Path $biosLogFile -PathType Leaf) {
                Write-Output ("- WARNING: BIOS log file {0} already exists!!!" -f $biosLogFile | Tee-Object -FilePath $reportLogPath -Append)
                Write-Output ("           - Trying to kill it" | Tee-Object -FilePath $reportLogPath -Append)
                $temp = "{0}\*" -f $logFilePath
                Get-ChildItem -Path $temp -Filter $biosLogFile | Remove-Item -Force -ErrorAction SilentlyContinue
              }
              If ($biosComPort -ine "NUL") {
                $params = '-load', $puttySession, '-serial', $biosComPort, '-sercfg', ('{0},8,n,1,N' -f $BiosBaudRate), '-sessionlog', $biosLogFile
                & $puttyAppPath @params
              } Else {
                $null = New-Item $biosLogFile -Type file -ErrorAction SilentlyContinue
              }
              $bmcLogFile = "{0}\{1}-BMC.log" -f $logFilePath, $testTag
              If (Test-Path $bmcLogFile -PathType Leaf) {
                Write-Output ("- WARNING: BMC log file {0} already exists!!!" -f $bmcLogFile | Tee-Object -FilePath $reportLogPath -Append)
                Write-Output ("           - Trying to kill it" | Tee-Object -FilePath $reportLogPath -Append)
                $temp = "{0}\*" -f $logFilePath
                Get-ChildItem -Path $temp -Filter $bmcLogFile | Remove-Item -Force -ErrorAction SilentlyContinue
              }
              If ($bmcComPort -ine "NUL") {
                $params = '-load', $puttySession, '-serial', $bmcComPort, '-sercfg', ('{0},8,n,1,N' -f $BmcBaudRate), '-sessionlog', $bmcLogFile
                & $puttyAppPath @params
                Start-Sleep -m $testDelay
              } Else {
                $null = New-Item $bmcLogFile -Type file -ErrorAction SilentlyContinue
              }

            # Run cycles
              $preCsrCount  = "Disabled"
              $testFailures = 0
              For ($i = 1; $i -le $testCount; $i++) {
                $cycleStartTime = $(Get-Date)

                # Get randomly selected capsule
                  $capsule = ""
                  If ((Get-Random -Maximum 2) -eq 0) {
                    $capsules = $testPass
                  } Else {
                    $capsules = $testFail
                  }
                  If (-Not $capsules) {
                    # capsule is currently blank
                      If ($testPass) {
                        $capsules = $testPass
                      } ElseIf ($testFail) {
                        $capsules = $testFail
                      }
                  }
                  If ($scriptDebug -ieq "True") {Write-Output ("capsules        = {0}" -f $capsules | Tee-Object -FilePath $reportLogPath -Append)}
                  If (-Not $capsules) {
                    Write-Output ("ERROR: Unable to identify a good capsule list!" | Tee-Object -FilePath $reportLogPath -Append)
                  } Else {
                    # Select capsule from capsule list
                      $capsuleNum = $capsules[(Get-Random -Maximum @($capsules).length)]
                      $capsule    = $testCapsules[$capsuleNum][0]
                  }
                  If ($scriptDebug -ieq "True") {Write-Output ("capsuleNum      = {0}" -f $capsuleNum | Tee-Object -FilePath $reportLogPath -Append)}
                  If ($scriptDebug -ieq "True") {Write-Output ("capsule         = {0}" -f $capsule | Tee-Object -FilePath $reportLogPath -Append)}

                # Run test
                  If (-Not $capsule) {
                    Write-Output ("ERROR: Unable to identify a good capsule!" | Tee-Object -FilePath $reportLogPath -Append)
                  } Else {
                    # Set cycle variables
                      $cycleLogFile = "{0}\{1}-{2:d4}.log" -f $logFilePath, $testTag, $i
                      If ($scriptDebug -ieq "True") {Write-Output ("cycleLogFile    = {0}" -f $cycleLogFile | Tee-Object -FilePath $reportLogPath -Append)}

                    # Run any pre test SMM capsule
                      If ($testPreCapsule -gt 0) {
                        If (($testPreCount[0] -eq 0) -Or ($testPreCount -Contains $i)) {
                          $null = TestCapsule $testPreCapsule "NUL" "False" "True"
                        }
                      } ElseIf ($testPreCapsule -eq -1) {
                        # Start SMI stress testing
                          If (($testPreCount[0] -eq 0) -Or ($testPreCount -Contains $i)) {
                            StartSmiStress
                          }
                      } ElseIf ($testPreCapsule -eq -2) {
                        # Stop SMI stress testing
                          If (($testPreCount[0] -eq 0) -Or ($testPreCount -Contains $i)) {
                            StopSmiStress
                          }
                      } ElseIf ($testPreCapsule -eq -3) {
                        # Get CSR count
                          If (($testPreCount[0] -eq 0) -Or ($testPreCount -Contains $i)) {
                            $preCsrCount = GetCsrCount
                          }
                      }

                    # Spike logs
                      $temp = "`n`nCycle #{0:d4} starting..." -f $i
                      Add-Content -Path $biosLogFile -Value $temp
                      Add-Content -Path $bmcLogFile -Value $temp

                    # Run test
                      Start-Sleep -m $testDelay
                      If (($i -eq 1) -Or ($i -eq $testCount)) {
                        # This is either the first and/or last cycle
                          $miniTestFlag = "False"
                      } Else {
                        $miniTestFlag = "True"
                      }
                      $testResult      = TestCapsule $capsuleNum $cycleLogFile $launchWorkloads $miniTestFlag
                      $executionResult = $testResult.Split("|")[1]
                      $executionResult = $executionResult.Trim()
                      $testResult      = $testResult.Split("|")[0]
                      $testResult      = $testResult.Trim()

                    # Check for correct log level
                      If ($testCapsules[$capsuleNum][3] -ieq "True") {
                        If ($executionResult -ieq "False") {
                          $testResult = "Fail"
                        }
                      }

                    # Run any post test SMM capsule
                      If ($testPostCapsule -gt 0) {
                        If (($testPostCount[0] -eq 0) -Or ($testPostCount -Contains $i)) {
                          $null = TestCapsule $testPostCapsule "NUL" "False" "True"
                        }
                      } ElseIf ($testPostCapsule -eq -1) {
                        # Start SMI stress testing
                          If (($testPostCount[0] -eq 0) -Or ($testPostCount -Contains $i)) {
                            StartSmiStress
                          }
                      } ElseIf ($testPostCapsule -eq -2) {
                        # Stop SMI stress testing
                          If (($testPostCount[0] -eq 0) -Or ($testPostCount -Contains $i)) {
                            StopSmiStress
                          }
                      } ElseIf ($testPreCapsule -eq -3) {
                        # Get CSR count
                          If (($testPreCount[0] -eq 0) -Or ($testPreCount -Contains $i)) {
                            If ($preCsrCount -ieq "Disabled") {
                              If ($csrEnabledFlag -ieq "True") {
                                Write-Output ("WARNING: Unable to get CSR count!!!" | Tee-Object -FilePath $reportLogPath -Append)
                              }
                            } Else {
                              $postCsrCount = GetCsrCount
                              If ($postCsrCount -ieq "Disabled") {
                                If ($csrEnabledFlag -ieq "True") {
                                  Write-Output ("WARNING: Unable to get CSR count!!!" | Tee-Object -FilePath $reportLogPath -Append)
                                }
                              } Else {
                                $preCsrCount  = [Int32]$preCsrCount
                                $postCsrCount = [Int32]$postCsrCount
                                Write-Output (" - Starting CSR count = 0x{0}" -f $preCsrCount.ToString("X8")  | Tee-Object -FilePath $reportLogPath -Append | Tee-Object -FilePath $testLogFile -Append)
                                Write-Output (" - Ending CSR count   = 0x{0}" -f $postCsrCount.ToString("X8") | Tee-Object -FilePath $reportLogPath -Append | Tee-Object -FilePath $testLogFile -Append)
                                If ($testCapsules[$capsuleNum][1] -ieq "Pass") {
                                  # CSR count should be between 0x00 and 0x3E in MOD 2 = 0 format with wrapping past 0x3E
                                  $adjustedCsrCount = $preCsrCount + 2
                                  If ($adjustedCsrCount -gt 0x0000003E) {$adjustedCsrCount = 0}
                                  Write-Output (" - Adjusted CSR count = 0x{0}" -f $adjustedCsrCount.ToString("X8") | Tee-Object -FilePath $reportLogPath -Append | Tee-Object -FilePath $testLogFile -Append)
                                  If ($adjustedCsrCount -ne $postCsrCount) {
                                    Write-Output (" - {0} failed because adjusted CSR count 0x{1} <> post 0x{2}!!!" -f $testTag, $adjustedCsrCount.ToString("X8"), $postCsrCount.ToString("X8") | Tee-Object -FilePath $reportLogPath -Append)
                                    $testResult = "Fail"
                                  }
                                } Else {
                                  # CSR count should be the same since this capsule should have failed
                                  If ($preCsrCount -ne $postCsrCount) {
                                    Write-Output (" - {0} failed because CSR count pre 0x{1} <> post 0x{2}!!!" -f $testTag, $preCsrCount.ToString("X8"), $postCsrCount.ToString("X8") | Tee-Object -FilePath $reportLogPath -Append)
                                    $testResult = "Fail"
                                  }
                                }
                              }
                            }
                          }
                      }

                    # Spike logs
                      $temp = "Cycle #{0:d4} ending..." -f $i
                      Add-Content -Path $biosLogFile -Value $temp
                      Add-Content -Path $bmcLogFile -Value $temp

                    # Get cycle elapsed time
                      $cycleElapsedTime = "Elapsed time = {0}" -f (ElapsedTime $cycleStartTime)

                    # Dump pass/fail result
                      If ($testResult -ieq "Pass") {
                        $temp = " - Cycle {0}/{1} PASSED!!!   [{2}]" -f $i, $testCount, $cycleElapsedTime
                      } Else {
                        $testFailures++
                        $temp = " - Cycle {0}/{1} FAILED!!!   [{2}]" -f $i, $testCount, $cycleElapsedTime
                      }
                      Add-Content -Path $cycleLogFile -Value $temp
                      Add-Content -Path $testLogFile -Value $temp
                  }
              }

            # Kill putty
              KillProcess putty "False"

            # Zip up and then delete logs
              Start-Sleep -m $testDelay
              ZipFiles $logFilePath "*.log" "NUL" ("{0}\{1}-logs.zip" -f $logFilePath, $testTag) "True"

            # Dump elapsed time
              $testElapsedTime = ElapsedTime $testStartTime
              Write-Output (" - Elapsed time = {0}" -f $testElapsedTime | Tee-Object -FilePath $reportLogPath -Append | Tee-Object -FilePath $testLogFile -Append)
              Write-Output (" - with {0} failures." -f $testFailures | Tee-Object -FilePath $reportLogPath -Append | Tee-Object -FilePath $testLogFile -Append)

            # Get current SMI count
              $smiCount = GetSmiCount
              Write-Output (" - Ending SMI count = {0}" -f $smiCount | Tee-Object -FilePath $reportLogPath -Append | Tee-Object -FilePath $testLogFile -Append)

            # Add test results to report
              If ($testFailures -eq 0) {
                $testResult = "PASSED"
              } Else {
                $testResult   = "FAILED"
                $scriptStatus = "FAILED"
              }
              $testReport += "| {0,7} | {1,4} | {2,-11} | {3,6} | {4,8} | {5,11} |`n" -f $testTag, $testNum, $testResult, $testCount, $testFailures, $testElapsedTime
              $reportLines++

            # Delay a bit
              Start-Sleep -m $testDelay
          } Else {
            If ($testTag -ine "Glasgow") {
              Write-Output ("{0} {1}: blocked by: {2}" -f $testTag, $testNum, $testBlocked | Tee-Object -FilePath $reportLogPath -Append)
              $blockedCommentCount++
              $blockedComments = "{0}#{1:d2} {2} blocked by: {3}`n" -f $blockedComments, $blockedCommentCount, $testTag, $testBlocked
              $temp = "Blocked #{0:d2}" -f $blockedCommentCount
              $testReport += "| {0,7} | {1,4} | {2,-11} | {3,6} | {4,8} | {5,11} |`n" -f $testTag, $testNum, $temp , $testCount, " ", " "
              $reportLines++
            }
          }
        }

      # Perform post-loop sanity test
        If ($skipPostCheck -ieq "True") {
          Write-Output (" - WARNING: Post sanity checking of capsules skipped!!!" | Tee-Object -FilePath $reportLogPath -Append)
        } Else {
          Write-Output (" - Sanity checking used test capsules..." | Tee-Object -FilePath $reportLogPath -Append)
          $sanityPostCheck = CapsuleSanityCheck
          Write-Output ("{0}" -f $sanityPostCheck | Tee-Object -FilePath $reportLogPath -Append)
          If ($sanityPostCheck -Contains "FAILED!!!") {
            $scriptStatus = "FAILED"
            $sanityCheck  = "Post test sanity check FAILED!!!"
          } Else {
            $sanityCheck = "Post test sanity check passed."
          }
          # Get elapsed time for sanity checking
              $sanityElapsedTime = (($sanityPostCheck -Split '\n') | Select -Last 1)
              $sanityElapsedTime = ($sanityElapsedTime -Split '-')[1]
              $sanityElapsedTime = $sanityElapsedTime.Trim()

          # Add info to report
            $sanityCheck  = "{0,-35} {1,27}" -f $sanityCheck, $sanityElapsedTime
            $testReport += $minorSeparator + "| {0} |`n" -f $sanityCheck
        }
    }
    # Cleanup
      StopSmiStress

    # Kill off BMC journal
      Write-Output (" - Turning off BMC journal..." | Tee-Object -FilePath $reportLogPath -Append)
      ExitBmcJournal $bmcComPort $BmcBaudRate

    # Dump elapsed time
      $globalElapsedTime = ElapsedTime $globalStartTime
      $globalElapsedTime = " - Total script elapsed time = {0}" -f $globalElapsedTime
      Write-Output ("{0}" -f $globalElapsedTime | Tee-Object -FilePath $reportLogPath -Append)

    # Dump test results
      $testReport += $majorSeparator + $blockedComments + $globalElapsedTime
      Write-Output ("`n`n{0}" -f $testReport | Tee-Object -FilePath $reportLogPath -Append)

    # Dump script status
      Write-Output ("`nScript status = {0}" -f $scriptStatus | Tee-Object -FilePath $reportLogPath -Append)

    # Zip the logs up
      $null = New-Item -Path ("{0}\temp" -f $logFilePath) -ItemType directory -ErrorAction SilentlyContinue
      Get-ChildItem -Path ("{0}\*.rst" -f $logFilePath) | Rename-Item -NewName { $_.Name -replace '.rst', '.log' }
      $zipFN = ("{0}\temp\{1}.zip" -f $logFilePath, $reportLogName)
      ZipFiles $logFilePath "*.log" "NUL" $zipFN "True"
      ZipFiles $logFilePath "*.zip" "NUL" $zipFN "True"
      Move-Item -Path $zipFN -Destination $logFilePath -ErrorAction SilentlyContinue

    # Delete temporary folder
      Get-ChildItem -Path ("{0}\temp\*" -f $logFilePath) -Recurse | Remove-Item -Force -ErrorAction SilentlyContinue
      Remove-Item ("{0}\temp" -f $logFilePath) -Force -ErrorAction SilentlyContinue

    # Return exitcode according to $scriptStatus
      If ($scriptStatus -ieq "PASSED") {
        $exitcode = 0
      } Else {
        $exitcode = 1
      }
      Exit $exitcode
  }
