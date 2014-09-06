// var iframe = $(".gwt-Frame")[0];
// var text = $(iframe).contents().find(".ennote div").text();

var lastText = '',
	currentText = '', 
	textStartTime, 
	textEndTime;

var log = {};

$("#textInput").on("keyup",function() {
	if(currentText == '') {
		console.log("Started Text Input");
		//var textTemp = $(iframe).contents().find(".ennote div").text();
		var textTemp = $("#textInput").val();
		textStartTime = $.now();
		currentText = textTemp;
		collectText(textTemp, textStartTime);
	}
});

function collectText(input, time) {
	setTimeout(function() {
		input = $("#textInput").val();
		if (input == currentText) {
			var addedText = getTextDifference(input, lastText)
			var logEntry = {
				'start':formatTimeOfDay(textStartTime),
				'text':addedText,
				'end': formatTimeOfDay(time)
			};
			log[textStartTime] = logEntry;
			lastText = input;
			currentText = '';
			textStartTime = '';
			textEndTime = '';

			$("#output").append(JSON.stringify(logEntry)+"<br>");
			return null
		}

		currentText = input;
		setTimeout(function() {
			// var newInput = $(iframe).contents().find(".ennote div").text();
			var newInput = $("#textInput").val();
			return collectText(newInput,$.now());
		},2000);
	},2000)
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