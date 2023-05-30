
# Initialize variables
  $BiosBaudRate    = 115200
  $BiosComPort     = ""
  $BmcBaudRate     = 115200
  $BmcComPort      = ""
  $BmcPassword     = "0penBmc1"
  $BmcUser         = "root"
  $launchedFromSut = "False"

# Functions
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
      If ($read -ne "") {
        $read = WriteSerial $bmcSerialPort $bmcUser "Password:"
        $result += $read + [Environment]::NewLine
        If ($read -ne "") {
          $read = WriteSerial $bmcSerialPort $bmcPassword "@intel-obmc:"
          $result += $read + [Environment]::NewLine
          If ($read -ne "") {
            $read = WriteSerial $bmcSerialPort "journalctl -f" ""
            $result += $read + [Environment]::NewLine
          }
        }
      }
      $bmcSerialPort.Close()
      $result = $result.TrimEnd()
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
  Function BMCcmd {
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
      If ($read -ne "") {
        $read = WriteSerial $bmcSerialPort $bmcUser "Password:"
        $result += $read + [Environment]::NewLine
        If ($read -ne "") {
          $read = WriteSerial $bmcSerialPort $bmcPassword "@intel-obmc:"
          $result += $read + [Environment]::NewLine
          If ($read -ne "") {
            $read = WriteSerial $bmcSerialPort "rm -rf /run/log/journal/*" ""
            $result = $read + [Environment]::NewLine
            $read = WriteSerial $bmcSerialPort "exit" ""
          }
        }
      }
       Write-Host ("   - ghuie: test {0}" -f $result)
      $bmcSerialPort.Close()
      $result = $result.TrimEnd()
  }

#==================================================================================================
# Start of main script
#==================================================================================================
  #$biosComPort = GetBiosSerialPort
  #Write-Host (" - BIOS com = [{0}]" -f $biosComPort)
  $bmcComPort  = GetBmcSerialPort
  Write-Host (" - BMC com  = [{0}]" -f $bmcComPort)
  If ($bmcComPort -ne "") {
    BMCcmd $bmcComPort $BmcBaudRate $BmcUser $BmcPassword
    #ExitBmcJournal   $bmcComPort $BmcBaudRate
  }
