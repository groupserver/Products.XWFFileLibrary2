var cb_paneLoader = function( data, paneId ) {
    el = document.getElementById(paneId);
    el.innerHTML = data;
}

var cb_failedLoad = function(type, evt) {
    alert("failed to load pane data");
}

function paneLoader(someUrl, somePaneId) {
        new Ajax.Request(someUrl,
                         {onSuccess: function (transport, json) { cb_paneLoader(transport.responseText, somePaneId) },
                          onFailure: cb_failedLoad,
                          method: "GET"});
}
