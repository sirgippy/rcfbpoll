$(function() {
	$('#message-form').on('submit', function(event){
        event.preventDefault();
        console.log("sending message...");
        send_message();
    });
});

function send_message() {
    message_data = get_message_data();

    $.ajax({
        type: "POST",
        url: "send_message/",
        data: message_data,
        dataType: 'json',
        success: function() {
            messageSentNotice();
        },
        error: function() {
            messageSendError();
        },
    });
};

function get_message_data() {
    var recipient = $("#recipient option:selected").text();
    var title = $("#title").val();
    var message_body = $("#message-body").val();

    return { recipient : recipient,
             title : title,
             message_body : message_body,
    };
}

function messageSentNotice() {
	var text = "";
	text += '<div class="alert alert-success alert-dismissible" role="alert">'
	text += '<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>'
	text += 'Message Sent!</div>'
	$("#messenger-results").html($("#messenger-results").html() + text);
}

function messageSendError() {
	var text = "";
	text += '<div class="alert alert-danger alert-dismissible" role="alert">'
	text += '<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>'
	text += '<strong>Error:</strong> Failed to send message.</div>'
	$("#messenger-results").html($("#messenger-results").html() + text);
}
