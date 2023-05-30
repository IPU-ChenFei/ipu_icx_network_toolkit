$(document).ready(function(){
   $("#testcaseupdate").submit(function(e){
	// prevent from normal form behaviour
        $("#progress").show();
        //console.log($("#testcaseupdate").attr("data-id"));
        var serializedData = $(this).serialize();
      	//console.log(serializedData);
      	//var csrftoken = $('input').attr('name');
      	e.preventDefault();
    	// serialize the form data
        var id = $("#test_case_id").val();
        var server = $("#myscript").attr("server");

      	$.ajax({
      		type : 'POST',
      		url :  server + "automation/testcases/EGS/" + id + "/update/",
      		data : serializedData,
      		dataType: "html",
      		success : function(response){
			    alert(response);
			    $("#progress").hide();
      		},
      		error : function(response){
      		    console.log(response);
      			alert(response);
      			$("#progress").hide();
      		}
      	});
   });
});