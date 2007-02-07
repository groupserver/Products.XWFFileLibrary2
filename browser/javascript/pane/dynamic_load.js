var cb_paneLoader = function(type, data, evt, kwArgs) {
    el = document.getElementById(kwArgs['paneId']);
    el.innerHTML = data;
}

var cb_failedLoad = function(type, evt) {
    alert("failed to load pane data");
}

function paneLoader(someUrl, somePaneId) {
	dojo.io.bind({
    	    url: someUrl,
        	load: cb_paneLoader,
	        error: cb_failedLoad,
	        paneId: somePaneId,
    	    mimetype: "text/plain", /* optional */
	        /* sync: true, option default = async */
    	    transport: "XMLHTTPTransport" /* optional default = "XMLHTTPTransport" */
	});
}
