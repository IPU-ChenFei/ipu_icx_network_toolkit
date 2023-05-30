### Test Case: 18014075324 - PI_SPR_DSA_Opcode_testing_L

	OS: CentOS
	Step 1: Generate Personal access Token
		Github account -> settings -> Developer Settings-> Personal access Token -> Generate new Token ->(copy the token)
			-> configure SSO -> Authenticate
	Step 2: Update the Content_configuration.xml file
	 1. repo_name (update if required)
	 2. access_token (update the token with copied)
```
    <accelerator>
        #refer the readme to update repo name and access token in src/virtualization/tests/dsa
        <repo_name>https://github.com/intel-sandbox/pv-dsa-iax-bkc-tests.git</repo_name>
        <access_token>None</access_token>
    </accelerator>
```
	step 3: Run the Test case now.

