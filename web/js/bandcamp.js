// DISCOGRAPHY API
///////////////////////////////////////////////////////////////////////////////////////////////////

function Bandcamp() {
	return this;
}

Bandcamp.apiURL = 'https://94iml3erc4.execute-api.us-east-1.amazonaws.com/dev/api/discography/{token}';
Bandcamp.discography = {};

Bandcamp.prototype = {
	getBandcampData: function(cb, badges) {
		Bandcamp.discography = {};
		var oReq = new XMLHttpRequest();
		oReq.addEventListener("load", function() {
			Bandcamp.discography = JSON.parse(this.responseText).discography;
			console.log('Discography fetched:');
			console.log(JSON.parse(this.responseText));
			cb(Bandcamp.discography);
		});
		oReq.open("GET", Bandcamp.apiURL.replace('{token}', badges.getToken()));
		oReq.setRequestHeader('accept-encoding', 'gzip');
		oReq.send();
	}
}
