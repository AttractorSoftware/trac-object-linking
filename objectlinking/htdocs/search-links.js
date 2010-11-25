jQuery(document).ready(function() {

    jQuery( "#linkTarget" ).autocomplete({
        source: function( enteredSoFar, autoCompleteCallback ) {
            jQuery.ajax(
            {
                'dataType':'json',
                'data':{'q':enteredSoFar.term},
                'url': base_url,
                'success': function(data, textStatus, XMLHttpRequest)
                {
                    var autoCompleteOptions = new Array();
                    var n = data.length;
                    for (var i = 0; n > i; i++ )
                    {
                        autoCompleteOptions.push(data[i].type + ":" + data[i].id + " : " + data[i].title)
                    }
                    autoCompleteCallback(autoCompleteOptions);
                }
            });
        },
        minLength: 3,
        select: function( event, ui ) {
//            log( ui.item ?
//                "Selected: " + ui.item.label :
//                "Nothing selected, input was " + this.value);
        },
        open: function() {
            jQuery( this ).removeClass( "ui-corner-all" ).addClass( "ui-corner-top" );
        },
        close: function() {
            jQuery( this ).removeClass( "ui-corner-top" ).addClass( "ui-corner-all" );
        }
    });
});
