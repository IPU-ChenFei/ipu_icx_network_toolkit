$(document).ready(function(){
   $("#add-user").submit(function(e){
	// prevent from normal form behaviour
        var serializedData = $(this).serialize();
      	e.preventDefault();
    	// serialize the form data
        var server = $("#myscript").attr("server");
      	$.ajax({
      		type : 'POST',
      		url :  server + "automation/users/update_user/",
      		data : serializedData,
      		dataType: "html",
      		success : function(response){
			    alert(response);
      		},
      		error : function(response){
      			alert(response);
      		}
      	});
   });
});