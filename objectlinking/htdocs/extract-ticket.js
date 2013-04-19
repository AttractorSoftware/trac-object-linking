var extractTicketButton;
var currentSelectionText;

function getSelectionCoordinates () {
    var markerTextChar = "\ufeff";
    var markerTextCharEntity = "&#xfeff;";

    var markerEl, markerId = "sel_" + new Date().getTime() + "_" + Math.random().toString().substr(2);

    var sel, range;

    if (document.selection && document.selection.createRange) {
        // Clone the TextRange and collapse
        range = document.selection.createRange().duplicate();
        range.collapse(false);

        if (document.getSelection)
        {
            currentSelectionText = document.getSelection().toString();
        }

        // Create the marker element containing a single invisible character by creating literal HTML and insert it
        range.pasteHTML('<span id="' + markerId + '" style="position: relative;">' + markerTextCharEntity + '</span>');
        markerEl = document.getElementById(markerId);
    } else if (window.getSelection) {
        sel = window.getSelection();

        if (sel.getRangeAt) {
            if (sel.toString().length > 0) {
                range = sel.getRangeAt(0).cloneRange();
            } else {
                return false;
            }
        } else {
            // Older WebKit doesn't have getRangeAt
            range.setStart(sel.anchorNode, sel.anchorOffset);
            range.setEnd(sel.focusNode, sel.focusOffset);

            // Handle the case when the selection was selected backwards (from the end to the start in the
            // document)
            if (range.collapsed !== sel.isCollapsed) {
                range.setStart(sel.focusNode, sel.focusOffset);
                range.setEnd(sel.anchorNode, sel.anchorOffset);
            }
        }
        if (range !== null)
        {
            range.collapse(false);

            // Create the marker element containing a single invisible character using DOM methods and insert it
            markerEl = document.createElement("span");
            markerEl.id = markerId;
            markerEl.appendChild( document.createTextNode(markerTextChar) );
            range.insertNode(markerEl);

            currentSelectionText = sel.toString();
        }
    }

    if (markerEl) {

        // Find markerEl position http://www.quirksmode.org/js/findpos.html
        var obj = markerEl;
        var left = 0,
            top = 0;
        do {
            left += obj.offsetLeft;
            top += obj.offsetTop;
        } while (obj = obj.offsetParent);

        markerEl.parentNode.removeChild(markerEl);

        return {top: top, left: left}
    }
    return false
}

function tryToPlaceButton()
{
    setTimeout(function () {
        var coordinates = getSelectionCoordinates();
        if (coordinates) {
            placeButtonAt(coordinates);
        } else {
            removeButton();
        }
    }, 50);
}

function placeButtonAt (coordinates) {
    extractTicketButton.css('left', (parseInt(coordinates.left) + 5) + 'px');
    extractTicketButton.css('top', (parseInt(coordinates.top) + 17) + 'px');
    extractTicketButton.show();
}

function removeButton() {
    if (extractTicketButton)
        extractTicketButton.hide();
}

function extractTicket() {
    console.log(currentSelectionText);
    if (currentSelectionText.length > 0) {
        var text = encodeURIComponent(currentSelectionText.replace(/<(?:.|\n)*?>/gm, ''));
        var link = $('#extractTicketLink').val() + '&description=' + text;
        console.log(link);
        window.location = link;
    }
}

function escapeHtml(text) {
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function createExtractTicketButton() {
    extractTicketButton = $('<div></div>').addClass('extract-ticket-button').html('Ctrl + Q to extract');
    $('body').append(extractTicketButton);
}

jQuery(document).ready(function() {

    createExtractTicketButton();

    jQuery(document).on('keypress', function(e) {
        if (e.ctrlKey && e.keyCode == 13) // Ctrl + M
        {
            extractTicket();
        }
    });

    jQuery(document).on('mouseup', function() {
        tryToPlaceButton();
    });

    jQuery(document).on('keyup', function() {
        tryToPlaceButton();
    });

    extractTicketButton.on('click', function() {
        extractTicket();
    });

});