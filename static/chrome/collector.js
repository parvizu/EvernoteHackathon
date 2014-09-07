

var lastText = '',
	currentText = '', 
	textStartTime, 
	startTime,
	textEndTime;

var log = {};

$(document).ready(function() {
	
	$('body').prepend("<div style='position: absolute;left:200px;z-index:100;'>Enter Group Session ID: <input id='session_id' type='text' width='200'><input id='btn_session_start' type='button' value='Start'><input id='btn_session_end' type='button' value='Stop' style='display:none;'></div>");

	$('#btn_session_start').click(function() {
		$.post('http://timenote.herokuapp.com/enter_group', { groupid: $('#session_id').val() }, function( data ) {
			console.log(data);
			startTime = $.now();
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

				if (addedText != '')
				{
					log[textStartTime] = logEntry;
					var entry = {}
					entry[$.now()] = logEntry;
					console.log(JSON.stringify(logEntry))
					sendEntry(entry);

					lastText = input;
					currentText = '';
					textStartTime = '';
					textEndTime = '';
				}
				collectText(currentText,$.now());
			} 
			else {
				currentText = input;
				if(textStartTime == '')
					textStartTime = $.now();

				setTimeout(function() {
					var newInput = getText();
					// var newInput = $("#textInput").val();
					collectText(newInput,$.now());
				},3000);
			}
		},3000)
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


function sendEntry(entry)
{
	console.log(JSON.stringify(entry));
	$.ajax({
		url: "http://timenote.herokuapp.com/save_user_data",
		type: "POST",
		contentType: 'application/json; charset=utf-8',
		dataType: 'json',
		data: JSON.stringify(entry),
		success: function(data) {
			console.log(data);
		}
	})
}



