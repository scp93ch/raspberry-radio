/*
	This code is copyright Stephen C Phillips (http://scphillips.com).
	It is licensed under GPL v3.
*/

$(document).ajaxError(function(evnt, jqXHR, ajaxSettings, thrownError) {
	$("#error").text(thrownError);
});

function ajaxFail(jqXHR, textStatus, errorThrown) {
	var data = {status: ""};
	switch (jqXHR.status) {
		case 0:
			data.status = "Network error";
			break;
		case 404:
			data.status = "No such station";
			break;
		case 503:
			data.status = "Server error";
			break;
	}
	update_status(data);
}

function update_status(data) {
	$("i.fa-refresh").removeClass("fa-spin");
	if (data.status == "Stopped") {
		// update status and select the "Stop" button
		$("#status").text("Stopped");
		$("input[id='Stopped']").iCheck("check");
	} else if (data.status == "Playing") {
		// change status to radio station name and select the right radio button
		$("#status").text(data.station);
		$("input[value='" + data.id + "']").iCheck("check");
	} else {
		// update status and deselect all radio buttons
		$("#status").text(data.status);
		$("input[name='station']").iCheck("uncheck");
	}
}

function reset() {
	$.ajax({
		type: "POST",
		url: "/reset",
		success: update_status,
		dataType: "json"
	}).fail(ajaxFail);
}

function status() {
	$.ajax({
		type: "GET",
		url: "/playing",
		success: update_status,
		dataType: "json"
	}).fail(ajaxFail);
}

function play(station) {
	if (station != "") {
		$("#status").text("Tuning...");
		$("i.fa-refresh").addClass("fa-spin");
	}
	$.ajax({
		type: "POST",
		url: "/playing", 
		data: {"station": station},
		success: update_status,
		dataType: "json",
	}).fail(ajaxFail);
}
