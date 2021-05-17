var BG = BG || {};

BG.Discography = function() {
	this.drawAlbums = [];
	this.bgAlbums = [];

	// Important HTML DOM elements
	this.cont = undefined;

	return this;
}

// Classes applied to elements for styling
BG.Discography.css = { cont: 'bg-music' }

BG.Discography.getInstance = function(element) {
	var discography = $('#'+BG.Discography.css.cont);
	if (discography.length) return discography.data().discography;
	else return null;
}

BG.Discography.prototype.buildDOM = function(musicDiv) {
	this.cont = musicDiv;
	$(this.cont).empty();
	$(this.cont).data().discography = this;
	var discography = this;
	$(this.drawAlbums.sort(function(a,b) {
		for (idx in albumOrder) {
			if (albumOrder[idx] == a.album_id) return -1;
			if (albumOrder[idx] == b.album_id) return 1;
		}
		return 0;
	})).each(function() {
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

BG.Discography.registerJQueryUI = function() {
	BG.Album.registerJQueryUI();
}

BG.Discography.prototype.addAlbums = function(albums) {
	var discography = this;
	$(albums).each(function() { discography.drawAlbums.push(this); });
}

BG.Discography.prototype.addAlbum = function(album) {
	this.drawAlbums.push(album);
}
