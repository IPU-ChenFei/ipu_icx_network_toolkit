search_dir="automation_testcases"
manageability="manageability"
pythonsv="pythonsv"
cscript="cscript"

events_package="events"
egs_installation_package="egs_installation_events"
copy_egs_build="CopyDpgBuild"
parameter_runtime="bkc_capi_allocation_events"
clean_dpg_build="post_event_framework_clearnup"

echo "<TestCases>" > testCases.xml

for f in $search_dir/*.txt;
	do echo "Processing $f file..";
      base_file_name=$(basename	$f)
	package_name="${base_file_name%%.*}"
	cat $f | while read LINE;
	do
		echo "${LINE}";
		LINE=`echo ${LINE} | tr -d '\n\r'`
        IFS=, read tc_name tc_arg python_exe <<< ${LINE}
        h=$(dirname $tc_arg)
        d="${h##/*/}"
        e="${d%/*}"
        domain="${e##*/}"
        echo "    <TestCase>" >> testCases.xml
        echo "            <PackageName>${package_name}</PackageName>" >> testCases.xml
        echo "            <categories>       <category>${domain}</category>     </categories>" >> testCases.xml
        echo "            <TestCaseName>${tc_name}</TestCaseName>" >> testCases.xml

        #if [[ "$package_name" =~ "$manageability" ]]
        if [[ "$tc_name" == "$copy_egs_build" ]]
        then
            echo "            <Command>powershell</Command>" >> testCases.xml
        elif [[ "$tc_name" == "$clean_dpg_build" ]]
        then
            echo "            <Command>powershell</Command>" >> testCases.xml
        elif [[ "$package_name" =~ "$manageability" ]] || [[ "$python_exe" == "$pythonsv" ]]
        then
            echo "            <Command>python.exe</Command>" >> testCases.xml
         else # elif [[ "$python_exe" == "$cscript" ]]
            echo "            <Command>C:/Intel/DFPython/virtualenv/white/py38/cscripts/Scripts/python.exe</Command>" >> testCases.xml
        fi

        echo "            <Arguments>${tc_arg}</Arguments>" >> testCases.xml

        # Mark testcase as event if filename contains "events" keyword
        if [[ "$package_name" =~ "$events_package" ]]
        then

            # Configuration files list should be added ONLY to EGS installation events
            if [[ "$package_name" == "$egs_installation_package" ]]
                then
                    echo "            <IsEvent>true</IsEvent>" >> testCases.xml
                    echo "            <ConfigsSeparator>;</ConfigsSeparator>" >> testCases.xml
                    echo "            <ConfigParameterName>-c</ConfigParameterName>" >> testCases.xml
                    if [[ "$tc_name" == "$copy_egs_build" ]]
                      then
                          echo "            <ConfigsInheritanceMode>None</ConfigsInheritanceMode>" >> testCases.xml
                      else
                          echo "            <ConfigsInheritanceMode>All</ConfigsInheritanceMode>" >> testCases.xml
                    fi
            fi
            if [[ "$package_name" == "$parameter_runtime" ]]
                then
                  echo "            <IsEvent>false</IsEvent>" >> testCases.xml
                else
                  echo ""

            fi

        else
            echo "            <IsEvent>false</IsEvent>" >> testCases.xml
            if [[ "$package_name" =~ "$events_package"  ]]
                then
                  echo ""
            else
              echo "            <PassOutputPathAsParameter>true</PassOutputPathAsParameter>" >> testCases.xml
              echo "            <OutputPathParameter>-o</OutputPathParameter>" >> testCases.xml
            fi
        fi
        echo "    </TestCase>" >> testCases.xml
	done
done
echo "</TestCases>" >> testCases.xml
