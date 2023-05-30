For test cases listed below: 
1. 16014494318 PI_Cold_Reset_Cycle_With_Sandstone_Test 
2. 16014494148 PI_Warm_Reset_Cycle_With_Sandstone_Test
Operating system : Linux

In content_configuration.xml, we need to update the below tag value,

    <!--Sandstone container version-->
	<sandstone_test_version_number>93</sandstone_test_version_number>

Get the version number from the variable "env.JENKINS_TEST_TAG="93"" of this path and substitute the value in the content configuration:
https://gitlab.devtools.intel.com/sandstone/prt-int-cluster/-/blob/master/sandstone/sandstone-release.base
