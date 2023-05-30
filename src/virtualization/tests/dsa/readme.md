### Test Cases: 18014075503 - PI_SPR_DSA_DMA_testing_L
                16014809767 - PI_SPR_IAX_Dma_Test_L
                16014809930 - PI_SPR_IAX_Test_User_Type_WorkQueues

	OS: CentOS
	Step 1: Generate Personal access Token
		Github account -> settings -> Developer Settings-> Personal access Token -> Generate new Token ->(copy the token)
			-> configure SSO -> Authenticate
	Step 2: Update the Content_configuration.xml file 
	 1. repo (update if required)
	 2. token (update the token with copied)
	step 3: Run the Test case now.
