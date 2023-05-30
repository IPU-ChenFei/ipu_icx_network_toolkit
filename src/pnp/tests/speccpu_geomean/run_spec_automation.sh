#!/bin/bash


valid_runparameter=('intrate gcc8 avx512' 'intrate gcc8 avx512 1' 'intrate icc18 avx2' 'fprate gcc8 avx512' 'fprate gcc8 avx512 1' 'fprate icc18 avx2') 
intrate_sub=('perlbench_r' 'gcc_r' 'mcf_r' 'omnetpp_r' 'xalancbmk_r' 'x264_r' 'deepsjeng_r' 'leela_r' 'exchange2_r' 'xz_r')
fprate_sub=("bwaves_r" "cactuBSSN_r" "namd_r" "parest_r" "povray_r" "lbm_r" "wrf_r" "blender_r" "cam4_r" "imagick_r" "nab_r" "fotonik3d_r" "roms_r")

runparameter=$1

if [[ ! " ${valid_runparameter[@]} " =~ " ${runparameter} " ]]; then
        echo -e "\nError: Invalid value '${threads}'. Allowed Strings: " "${valid_runparameter[@]}\n"
        exit 1
fi

IFS=' ' read -ra seperate_arr <<< "$runparameter"
rate_sub="${seperate_arr[0]}"
echo "${rate_sub}"


arr_key=${runparameter// /_}
arr_val="${seperate_arr[1]} ${seperate_arr[2]}"
rm -rf ./speccpu_automation_results_${arr_key}.csv
echo ${arr_key}
echo ${arr_val}
if [[ $rate_sub -eq "intrate" ]]; then
	for mode in "${intrate_sub[@]}"
	do 
		echo "** running SPEC CPU ${mode} ${arr_val} iteration ${i}"
		bash run_spec.sh ${mode} ${arr_val} | tee $(pwd)/console_output.txt
		testcase="${mode} ${arr_val}"
		score=$(cat console_output.txt | grep -E "^${mode}:" | awk -F " " '{print $2}')
		core_freq=$(cat console_output.txt | grep "core_freq:" | awk -F " " '{print $2}')
		uncore_freq=$(cat console_output.txt | grep "uncorefreq:" | awk -F " " '{print $2}')
		pkg_power=$(cat console_output.txt | grep "package_power:" | awk -F " " '{print $2}')
		echo "${testcase}"
		echo "${score}"
		echo "${core_freq}"
		echo "${uncore_freq}"
		echo "${pkg_power}"
		if [[ ${score} == "" ]]; then
			score=0.00
		fi
		if [[ "$core_freq" =~ ^([0-9]+\.[0-9]+)$ ]]; then 
			echo "inside core if"
			
		else
			echo "inside core else"
			core_freq=0.00
		fi
		if [[ "$uncore_freq" =~ ^([0-9]+\.[0-9]+)$ ]]; then
			echo "inside uncore if"
			
		else
			echo "inside uncore else"
			uncore_freq=0.00
		fi
		if [[ "$pkg_power" =~ ^([0-9]+\.[0-9]+)$ ]]; then
			echo "inside package if"
			
		else
			echo "inside package else"
			pkg_power=0.00
		fi
			
		echo -e "${testcase},${score},${core_freq},${uncore_freq},${pkg_power}" >> ./speccpu_automation_results_${arr_key}.csv
	done
	
	testcase_geomean="${rate_sub} ${arr_val}"
	score_geomean=$(awk -F "," 'BEGIN{E = exp(1);} $1>0{tot+=log($3); c++} END{m=tot/c; printf "%.2f\n", E^m}' speccpu_automation_results_${arr_key}.csv)
	core_freq_geomean=$(awk -F "," 'BEGIN{E = exp(1);} $1>0{tot+=log($4); c++} END{m=tot/c; printf "%.2f\n", E^m}' speccpu_automation_results_${arr_key}.csv)
	uncore_freq_geomean=$(awk -F "," 'BEGIN{E = exp(1);} $1>0{tot+=log($5); c++} END{m=tot/c; printf "%.2f\n", E^m}' speccpu_automation_results_${arr_key}.csv)
	pkg_power_geomean=$(awk -F "," 'BEGIN{E = exp(1);} $1>0{tot+=log($6); c++} END{m=tot/c; printf "%.2f\n", E^m}' speccpu_automation_results_${arr_key}.csv)

	echo -e "${testcase_geomean},${score_geomean},${core_freq_geomean},${uncore_freq_geomean},${pkg_power_geomean}\n" >> ./speccpu_automation_results_${arr_key}.csv

elif [[ $rate_sub -eq "fprate" ]]; then
	for mode in "${fprate_sub[@]}"
	do 
		echo "** running SPEC CPU ${mode} ${arr_val} iteration ${i}"
		./run_spec.sh $mode $arr_val 2>$1 | tee $(pwd)/console_output.txt
		testcase="${mode} ${arr_val}"
		score=$(cat console_output.txt | grep -E "^${mode}:" | awk -F " " '{print $2}')
		core_freq=$(cat console_output.txt | grep "core_freq:" | awk -F " " '{print $2}')
		uncore_freq=$(cat console_output.txt | grep "uncorefreq:" | awk -F " " '{print $2}')
		pkg_power=$(cat console_output.txt | grep "package_power:" | awk -F " " '{print $2}')
		echo "${testcase}"
		echo "${score}"
		echo "${core_freq}"
		echo "${uncore_freq}"
		echo "${pkg_power}"
		if [[ ${score} == "" ]]; then
			score=0.00
		fi
		if [[ "$core_freq" =~ ^([0-9]+\.[0-9]+)$ ]]; then 
			echo "inside core if"
			
		else
			echo "inside core else"
			core_freq=0.00
		fi
		if [[ "$uncore_freq" =~ ^([0-9]+\.[0-9]+)$ ]]; then
			echo "inside uncore if"
			
		else
			echo "inside uncore else"
			uncore_freq=0.00
		fi
		if [[ "$pkg_power" =~ ^([0-9]+\.[0-9]+)$ ]]; then
			echo "inside package if"
			
		else
			echo "inside package else"
			pkg_power=0.00
		fi
		echo -e "${testcase},${score},${core_freq},${uncore_freq},${pkg_power}" >> ./speccpu_automation_results_${arr_key}.csv
	done
	
	testcase_geomean="${rate_sub} ${arr_val}"
	score_geomean=$(awk -F "," 'BEGIN{E = exp(1);} $1>0{tot+=log($3); c++} END{m=tot/c; printf "%.2f\n", E^m}' speccpu_automation_results_${arr_key}.csv)
	core_freq_geomean=$(awk -F "," 'BEGIN{E = exp(1);} $1>0{tot+=log($4); c++} END{m=tot/c; printf "%.2f\n", E^m}' speccpu_automation_results_${arr_key}.csv)
	uncore_freq_geomean=$(awk -F "," 'BEGIN{E = exp(1);} $1>0{tot+=log($5); c++} END{m=tot/c; printf "%.2f\n", E^m}' speccpu_automation_results_${arr_key}.csv)
	pkg_power_geomean=$(awk -F "," 'BEGIN{E = exp(1);} $1>0{tot+=log($6); c++} END{m=tot/c; printf "%.2f\n", E^m}' speccpu_automation_results_${arr_key}.csv)

	echo -e "${testcase_geomean},${score_geomean},${core_freq_geomean},${uncore_freq_geomean},${pkg_power_geomean}\n" >> ./speccpu_automation_results_${arr_key}.csv

fi


