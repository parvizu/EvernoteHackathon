$('body').prepend("<div style='position: absolute;left:200px;z-index:100;'>Enter Group Session ID: <input id='session_id' type='text' width='200'><input id='btn_session_start' type='submit' value='Start'></div>")
$('#btn_session_start').click(function() {
	$.post('http://127.0.0.1:5000/enter_group', { groupid: $('#session_id').val() }, function( data ) {
		console.log(data);
	});
	
});