var btn_index = $('#ballot').children().length;

$(function() {
	$( "#teams-accordion" ).accordion({
		collapsible: true,
		active: false
	});
});

$('.nav-tabs a').click(function(){
	$(this).tab('show');
});

$(function() {
	$( ".teamlist" ).sortable({
		revert: true,
		connectWith: "#ballot",
		
		helper: function(event,li) {
			this.copyHelper = li.clone().insertAfter(li);
			$(this).data('copied',false);
			return li.clone();
		},
		
		stop: function(event,ui) {
			var copied = $(this).data('copied');
			
			if (!copied) {
				this.copyHelper.remove();
				$(this).sortable('cancel');
			} else if ($("#ballot").children().length > 25) {
				ballotSizeExceededWarning();
				this.copyHelper.remove();
				$(this).sortable('cancel');
			} else if (isAlreadyInBallot(ui.item)){
				ballotDuplicateWarning();
				this.copyHelper.remove();
				$(this).sortable('cancel');
			} else {
				transformTeamToBallotEntry(ui.item);
			}
			
			this.copyHelper = null;
		},
		
		over: function(event,ui) {
			this.copyHelper.hide();
		},
		
		out: function(event,ui) {
			this.copyHelper.show();
		},
	});
	
	$( "#ballot" ).sortable({
		revert: true,
		cancel: ':input,button,.rationale',
		receive: function (event,ui) {
			ui.sender.data('copied',true);
		},
	});

	$('#ballot-save').on('submit', function(event){
        event.preventDefault();
        console.log("ballot saved!");
        save_ballot();
    });

    $('#ballot-submit').on('submit', function(event){
        event.preventDefault();
        console.log("ballot submitted!");
        submit_ballot();
    }).hide();

    $('.close-button').button().click(function() {
        $(this).closest('li').remove();
    }).prop("disabled", false);

    $('#validate-button').button().click(function(){
        $('#poll-type').prop("disabled", true);
        disableBallot();
        var is_valid = runValidationCheck();
        if (is_valid) {
            $('#validation-results').html($('#validation-results').html()
                + 'Validation complete. No errors found.<br>');
            $('#ballot-submit').show();
        };
        $('#unlock-button').prop("disabled", false);
        $(this).prop("disabled", true);
    }).prop("disabled", false);

    $('#unlock-button').button().click(function(){
        $('#poll-type').prop("disabled", false);
        enableBallot();
        $('#validation-results').html("");
        $('#ballot-submit').hide();
        $(this).prop("disabled", true);
        $('#validate-button').prop("disabled", false);
    }).prop("disabled", true);

    $('#poll-type').prop("disabled", false);

    $('#leave-button').button().click(function(){
        window.location.replace("/my_ballots/")
    });

    $('#retract-button').button().click(function(){
        $.ajax({
            type: "POST",
            url: "retract_ballot/",
            success: function() {
                $('#ballot-retract-dialog').modal('hide');
            },
            error: function() {
                var text = "";
                text += '<div class="alert alert-danger alert-dismissible" role="alert">'
                text += '<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>'
                text += '<strong>Error:</strong> Failed to retract ballot.</div>'
                $("#retract-dialog-body").html($("#retract-dialog-body").html() + text);
            },
        });
    });
});

function ballotSizeExceededWarning() {
	var text = "";
	text += '<div class="alert alert-warning alert-dismissible" role="alert">'
	text += '<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>'
	text += '<strong>Warning:</strong> Ballot is full. Remove a team to add another.</div>'
	$("#alert-container").html($("#alert-container").html() + text);
}

function isAlreadyInBallot(item) {
    var team_name = item.find(".team-name").html();

    var current_entries = $("#ballot").children();
    var entry;

    var foundSoFar = 0;

    for (i = 0; i < current_entries.length; i++) {
        entry = $(current_entries[i]);
        if (entry.find(".team-name").html() == team_name) {
            foundSoFar++;
            if (foundSoFar == 2) {
                return true;
            }
        }
    }

	return false;
}

function ballotDuplicateWarning() {
	var text = "";
	text += '<div class="alert alert-warning alert-dismissible" role="alert">'
	text += '<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>'
	text += '<strong>Warning:</strong> Team is already on ballot.</div>'
	$("#alert-container").html($("#alert-container").html() + text);
}

function transformTeamToBallotEntry(item) {
	item.append('<span class="ui-icon ui-icon-closethick close-button"></span>');
	
	item.append('<button class="btn btn-primary btn-xs rationale-button" type="button" data-toggle="collapse" data-target="#rationale' + btn_index + '" aria-expanded="false">Reason</button>');
	
	item.find('.close-button').button().click(function() {
			$(this).closest('li').remove();
		});
		
	item.append('<div id="rationale' + btn_index + '" class="rationale collapse" type="text" contenteditable="true" aria-expanded="false"></div>');
	
	btn_index++;
}

function save_ballot() {
    post_data = get_ballot_data();

    $.ajax({
        type: "POST",
        url: "save_ballot/",
        data: post_data,
        dataType: 'json',
        success: function() {
            ballotSavedNotice();
        },
        error: function() {
            ballotSaveError();
        },
    });
};

function get_ballot_data() {
    var entries = [];
    var poll_type = $("#poll-type option:selected").text();
    var overall_rationale = encodeURIComponent($("#overall-rationale").text());

    var teams = $("#ballot").children();

    for (i = 0; i < teams.length; i++) {
        var entry = [];
        entry = { rank : i+1,
                  team : $(teams[i]).find(".team-handle").val(),
                  rationale : encodeURIComponent($(teams[i]).find(".rationale").text())
                };
        entries.push(entry);
    }

    return { poll_type : poll_type,
             overall_rationale : overall_rationale,
             entries : JSON.stringify(entries),
    };
}

function submit_ballot() {
    post_data = get_ballot_data();

    $.ajax({
        type: "POST",
        url: "submit_ballot/",
        data: post_data,
        dataType: 'json',
        success: function() {
            window.location.replace("/my_ballots/")
        },
        error: function() {
            ballotSubmitError();
        },
    });

}

function ballotSavedNotice() {
	var text = "";
	text += '<div class="alert alert-success alert-dismissible" role="alert">'
	text += '<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>'
	text += 'Ballot Saved!</div>'
	$("#alert-container").html($("#alert-container").html() + text);
}

function ballotSaveError() {
	var text = "";
	text += '<div class="alert alert-danger alert-dismissible" role="alert">'
	text += '<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>'
	text += '<strong>Error:</strong> Failed to save ballot to server.</div>'
	$("#alert-container").html($("#alert-container").html() + text);
}

function ballotSubmitError() {
	var text = "";
	text += '<div class="alert alert-danger alert-dismissible" role="alert">'
	text += '<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>'
	text += '<strong>Error:</strong> Failed to submit ballot to server.</div>'
	$("#alert-container").html($("#alert-container").html() + text);
}

function runValidationCheck() {
    var is_valid = true;

    if (lessThan25Teams()) {
        is_valid = false;
    };

    if (pollTypeNotFilledIn()) {
        is_valid = false;
    };

    return is_valid;
}

function lessThan25Teams() {
    entries = $('#ballot').children();
    if (entries.length < 25) {
        $('#validation-results').html($('#validation-results').html()
            + '<strong>Error:</strong> Less than 25 teams selected.<br>');
        return true;
    } else {
        return false;
    }
}

function pollTypeNotFilledIn() {
    if ($("#poll-type option:selected").text() == '(unspecified)') {
        $('#validation-results').html($('#validation-results').html()
            + '<strong>Error:</strong> Must select poll type.<br>');
        return true;
    } else {
        return false;
    }
}

function disableBallot() {
    $('#ballot').sortable("disable");
    $('.close-button').prop("disabled", true);
}

function enableBallot() {
    $('#ballot').sortable("enable");
    $('.close-button').prop("disabled", false);
}