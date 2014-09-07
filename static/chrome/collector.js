

var lastText = '',
	currentText = '', 
	textStartTime, 
	textEndTime;

var log = {};

$(document).ready(function() {
	setTimeout(function() {
		console.log("Extension loaded");
		//$("#gwt-debug-sharingBar").next().next().html('<div id="output"><h1>Log:</h1></div>');
		loadEvents();
	},1000);
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
	setTimeout(function() {
		input = getText();
		//console.log(getText());
		if (input == currentText && input != '') {
			var addedText = getTextDifference(input, lastText)
			var logEntry = {
				'start':formatTimeOfDay(textStartTime),
				'text':addedText,
				'end': formatTimeOfDay(time),
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

function getUrl()
{
	var url = document.URL;
	var t = url.slice(url.search("n=")+2);
	var res = t;
	if(t.search("&") != -1)
		res = t.slice(0,t.search("&"));
	return res;
}
function formatTimeOfDay(millisSinceEpoch) {
  var secondsSinceEpoch = (millisSinceEpoch / 1000) | 0;
  var secondsInDay = ((secondsSinceEpoch % 86400) + 86400) % 86400;
  var seconds = secondsInDay % 60;
  var minutes = ((secondsInDay / 60) | 0) % 60;
  var hours = (secondsInDay / 3600) | 0;
  return hours + (minutes < 10 ? ":0" : ":")
      + minutes + (seconds < 10 ? ":0" : ":")
      + seconds;
}

function getTextDifference(input, old) {
	return input.slice(old.length);
}

function sendData()
{
	var newData ={}
	newData[$(".User-nameText").text()] = log;

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



