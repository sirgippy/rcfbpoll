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
        console.log("ballot saved!")
        save_ballot();
    });

    $('#ballot-submit').on('submit', function(event){
        event.preventDefault();
        console.log("ballot submitted!")
        submit_ballot();
    });

    $('.close-button').button().click(function() {
        $(this).closest('li').remove();
    });

    $('#validate-button').button().click(function(){
        $('#poll-type').prop("disabled", true);
        $('#ballot').disable();
        $(this).hide()
        var is_valid = runValidationCheck();
        $('#unlock-button').show();
        if is_valid {
            $('#submit-button').show();
        }
    });

    $('#unlock-button').button().click(function(){
        $('#poll-type').prop("disabled", false);
        $('#ballot').enable();
        $('#validate-button').show();
        $('#validation-results').html("");
        $(this).hide();
        $('#submit-button').hide();
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

    var post_data = { poll_type : poll_type,
                      overall_rationale : overall_rationale,
                      entries : JSON.stringify(entries),
                    };

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

function submit_ballot() {

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

function runValidationCheck() {
    var is_valid = true;

    
}