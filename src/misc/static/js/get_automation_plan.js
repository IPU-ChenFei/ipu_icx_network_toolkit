$(document).ready(function(){
    $("#send_email").change(function(){
        var send_email_field = $("#send_email").val();
        if (send_email_field.toLowerCase() === "true"){
            $("#email_field").show();
        }
    });

   $("#automation_plan").submit(function(e){
	// prevent from normal form behaviour
	    e.preventDefault();
        var serializedData = $(this).serialize();
        var platform = $("#platform").val();
        var bkc = $("#bkc_candidate").val();
        var ww = $("#ww").val();
        if (platform === "Choose Platform"){
            alert("Select the platform");
            return;
        }
        if (bkc === "Choose BKC Candidate"){
            alert("Select the BKC Candidate");
            return;
        }
        if (ww === "Choose WW"){
            alert("Select the Work Week");
            return;
        }
        var send_email_field = $("#send_email").val();

        if (send_email_field.toLowerCase() === "true"){
            var email_field = $("#email_recipients").val();
            if (email_field == ""){
                alert("Email list is required.. Ex: email@intel.com, email1@intel.com");
                return;
            }
        }

    	// serialize the form data
        var server = $("#myscript").attr("server");
      	$.ajax({
      		type : 'POST',
      		url :  server + "automation/automation_dev_tracker/" + platform + "/" + bkc + "/" + ww + "/",
      		data : serializedData,
      		dataType: "html",
      		success : function(response){
			    alert("Automation Plan is going to be populated");
			    //console.log(response);
			    $("#automation_plan_data").html(response);
      		},
      		error : function(response){
      		console.log(response);
      			alert("Failed to get the automation plan");
      		}
      	});
   });
});