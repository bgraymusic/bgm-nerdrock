var BG = BG || {};

///////////////////////////////////////////////////
// Load and display discography

BG.Discography = class {
	drawAlbums = [];
	bgAlbums = [];

	// Important HTML DOM elements
	cont = undefined;

    constructor() {}

	// Classes applied to elements for styling
	static css = { cont: 'bg-music' }

	static discographyURL = 'https://94iml3erc4.execute-api.us-east-1.amazonaws.com/dev/api/discography';
	static discographyWithTokenURL = 'https://94iml3erc4.execute-api.us-east-1.amazonaws.com/dev/api/discography/{token}';

	static registerJQueryUI() {
		BG.Album.registerJQueryUI();
	}

	async bootstrap(token) {
		let musicDiv = document.getElementById(BG.Discography.css.cont);
		[...musicDiv.childNodes].forEach(el => el.remove());
		this.drawAlbums = [];
		this.bgAlbums = [];
        let discData = await this.fetchDiscography(token);
        this.addAlbums(discData.discography);
    	this.buildDOM(musicDiv);
    	BG.Discography.registerJQueryUI();
	}

	async fetchDiscography(token) {
		if (!token) {
			let response = await fetch(BG.Discography.discographyURL);
			let result = await response.json();
			return result;
		} else {
			let response = await fetch(BG.Discography.discographyWithTokenURL.replace('{token}', token))
			let result = await response.json();
			return result;
		}
	}

	buildDOM(musicDiv) {
		this.cont = musicDiv;
		$(this.cont).empty();
		$(this.cont).data().discography = this;
		var discography = this;
		$(this.drawAlbums).each(function() {
			if (this.tracks.length) {
				if ($('.'+BG.Album.css.cont).length) $(musicDiv).append($('<hr/>'));
				var album = new BG.Album(discography, this);
				discography.bgAlbums.push(album);
				var albumDiv = $('<div/>').addClass(BG.Album.css.cont);
				$(musicDiv).append(albumDiv);
				album.buildDOM(albumDiv);
			}
		});
	}

	addAlbums(albums) {
		var discography = this;
		$(albums).each(function() { discography.drawAlbums.push(this); });
	}

	addAlbum(album) {
		this.drawAlbums.push(album);
	}
}
