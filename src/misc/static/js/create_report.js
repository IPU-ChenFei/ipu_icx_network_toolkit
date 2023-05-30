$(document).ready(function(){
   $("#create-report").submit(function(e){
	// prevent from normal form behaviour
        $("#progress").show();
        var serializedData = $(this).serialize();
      	e.preventDefault();
    	// serialize the form data
        var server = $("#myscript").attr("server");
      	$.ajax({
      		type : 'POST',
      		url :  server + "automation/reports/generate_report/",
      		data : serializedData,
      		dataType: "html",
      		success : function(response){
			    alert(response);
			    $("#progress").hide();
      		},
      		error : function(response){
      			alert(response);
      			$("#progress").hide();
      		}
      	});
   });
});