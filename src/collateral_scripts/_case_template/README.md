## Test Content Development Guide 

### Preparation
#### SS/Domain: Content readiness 
* Clear steps and expected result
* No unsupported steps 
  * GUI
  * Hardware hot plug
  * Refer to automation release note for limitation of current version
* Scripts os commands
  * bat/powershell
  * Linux shell
  * Python
#### Content developer: 
either SS/domain engineer or execution CW
* Understand your case and platform, manual dry run first
* Be clear about each steps, and expected result
* knows feature readiness status
* Platform known issues

### Guidelines 
* In-band script preferred - script on SUT
  * For multiple commands in SUT OS
  * multi-thread/process scenarios 
  * sut.execute_shell_cmd_async is always the last choice
* Setup in advance instead of adding these steps in script
  * Deploy tools to SUT in advance instead of copying them in test case
  * Configure CR as 1LM as a separate script instead of steps in each case
    * Could design fancy domain APIs in future as what we did for bios knobs
    * But let’s keep it simple at beginning 
  * Etc
* Clean up if necessary 


### Useful Info
[**User Guide**](https://teams.microsoft.com/l/file/EEC4B0BA-E5B3-420A-9D20-EA6285F0FA2C?tenantId=46c98d88-e344-4ed4-8496-4ed7712e255d&fileType=doc&objectUrl=https%3A%2F%2Fintel.sharepoint.com%2Fsites%2Fpavixpivshanghai%2FShared%20Documents%2FAutomation%2Fautomation_user_guide.doc&baseUrl=https%3A%2F%2Fintel.sharepoint.com%2Fsites%2Fpavixpivshanghai&serviceName=teams&threadId=19:aeb3b6e9ffa249e8b795449bca03235e@thread.tacv2&groupId=05435597-0d4c-4df1-a49f-8762f7f29680)

[**Training Foil**](https://teams.microsoft.com/l/file/F7C84A1A-5B91-44A0-A857-5D495F955851?tenantId=46c98d88-e344-4ed4-8496-4ed7712e255d&fileType=pptx&objectUrl=https%3A%2F%2Fintel.sharepoint.com%2Fsites%2Fpavixpivshanghai%2FShared%20Documents%2FAutomation%2Ftraining%2Fautomation%20training.pptx&baseUrl=https%3A%2F%2Fintel.sharepoint.com%2Fsites%2Fpavixpivshanghai&serviceName=teams&threadId=19:aeb3b6e9ffa249e8b795449bca03235e@thread.tacv2&groupId=05435597-0d4c-4df1-a49f-8762f7f29680)

[**Training Video**](https://intel.sharepoint.com/sites/pavixpivshanghai/Shared%20Documents/Automation/training/Automation%20training%20for%20content%20developer-20210702_090416-Meeting%20Recording.mp4)