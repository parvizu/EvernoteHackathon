

var lastText = '',
	currentText = '', 
	textStartTime, 
	textEndTime;

var log = {};

$(document).ready(function() {
	
	$('body').prepend("<div style='position: absolute;left:200px;z-index:100;'>Enter Group Session ID: <input id='session_id' type='text' width='200'><input id='btn_session_start' type='button' value='Start'><input id='btn_session_end' type='button' value='Stop' style='display:none;'></div>");

	$('#btn_session_start').click(function() {
		$.post('http://127.0.0.1:5000/enter_group', { groupid: $('#session_id').val() }, function( data ) {
			console.log(data);
			setTimeout(function() {
				console.log("Extension loaded");
				//$("#gwt-debug-sharingBar").next().next().html('<div id="output"><h1>Log:</h1></div>');
				loadEvents();
			},1000);
			$('#btn_session_start').hide();
			$('#btn_session_end').show();
		});
	});

	$('#btn_session_end').click(function() {
		currentText ="&&%%$$";
		$('#btn_session_end').hide();
		$('#btn_session_start').show();

		sendData();
	})

	
});


function getText()
{
	//var iframeEvernote = $("#gwt-debug-noteView").children()[0];
	var inTextField= $("#gwt-debug-sharingBar").next().find('iframe[allowtransparency=true]').contents().find('div').text()
	return inTextField;
}

function loadEvents() {
	console.log("Event listener initialized");
	setTimeout(function() {
		console.log(getText());
		console.log("Started Text Input");
		var textTemp = getText();
		//var textTemp = $("#textInput").val();
		textStartTime = $.now();
		currentText = textTemp;
		collectText(textTemp, textStartTime);
	},3000);
}

function collectText(input, time) {
	if(currentText != "&&%%$$") {
		setTimeout(function() {
			input = getText();
			//console.log(getText());
			if (input == currentText && input != '') {
				var addedText = getTextDifference(input, lastText)
				var logEntry = {
					'start':textStartTime,
					'text':addedText,
					'end': time,
					'guid': getUrl(),
					'userid': $(".User-nameText").text()
				};
				
				lastText = input;
				currentText = '';
				textStartTime = '';
				textEndTime = '';

				if (addedText != '')
				{
					log[textStartTime] = logEntry;
					console.log(JSON.stringify(logEntry))
				}
				collectText(currentText,$.now());
			} 
			else {
				currentText = input;
				setTimeout(function() {
					var newInput = getText();
					// var newInput = $("#textInput").val();
					collectText(newInput,$.now());
				},2000);
			}
		},2000)
	}
}

function getUrl()
{
	var url = document.URL;
	var t = url.slice(url.search("n=")+2);
	var res = t;
	if(t.search("&") != -1)
		res = t.slice(0,t.search("&"));
	return res;
}

function getTextDifference(input, old) {
	return input.slice(old.length);
}

function sendData()
{
	var newData ={}
	newData[$(".User-nameText").text()] = log;
	console.log("DATA SENT")
	console.log(newData);
	$.ajax({
		url: "http://127.0.0.1:5000/save_user_data",
		type: "POST",
		data: newData,
		success: function(data) {
			console.log(data);
			log = '';
		}
	})
}



