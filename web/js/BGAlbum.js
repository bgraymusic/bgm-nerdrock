var BG = BG || {};

BG.Album = function(discography, bcInfo) {
	this.discography = discography;

	for (var prop in bcInfo) { this[prop] = bcInfo[prop]; }
//	this.masterTracks = this.tracks.slice(0).reverse();
//	this.workingTracks = this.tracks.slice(0).reverse();
	this.masterTracks = [];
	this.workingTracks = [];

	// Important HTML DOM elements
	this.cont = undefined;
	this.accordion = undefined;

	return this;
}

// Classes applied to elements for styling
BG.Album.css = {
	cont: 'bg-album', row: 'bg-album-row', meta: {
		cont: 'bg-album-meta-cell', art: 'bg-album-art',
		onesong: 'bg-onesong-button', repeat: 'bg-repeat-button', shuffle: 'bg-shuffle-button', follow: 'bg-follow-button'
	}, content: {
		cont: 'bg-album-content-cell', art: 'bg-album-art-small', title: 'bg-album-title', accordion: 'bg-album-accordion'
	}
}

BG.Album.getFromElement = function(element) {
	var cont = $(element).closest('.'+BG.Album.css.cont);
	if (cont.length) return cont.data().album;
	else return null;
}

// We're styling this stuff as a table, so assume we start with a table and add divs as if they were
// rows, cells, etc
BG.Album.prototype.buildDOM = function(albumTable) {
	this.cont = albumTable;
	$(this.cont).empty();
	$(this.cont).data().album = this;

	var albumRow = $('<div/>').addClass(BG.Album.css.row);
	this.cont.append(albumRow);

	var metaCell = $('<div/>').addClass(BG.Album.css.meta.cont);
	albumRow.append(metaCell);
	this.buildMetaCell(metaCell);

	var albumContents = $('<div/>').addClass(BG.Album.css.content.cont);
	albumRow.append(albumContents);
	this.buildAlbumContents(albumContents);
}

BG.Album.prototype.buildMetaCell = function(metaCell) {
	metaCell.append($('<img/>').addClass(BG.Album.css.meta.art).attr('src', this.small_art_url));
	metaCell.append($('<br/>'));
	metaCell.append($('<button/>').attr('id', this.album_id + '_onesong').addClass(BG.Album.css.meta.onesong).attr('title', 'Stop at end of current song'));
	metaCell.append($('<button/>').attr('id', this.album_id + '_repeat').addClass(BG.Album.css.meta.repeat).attr('title', 'Repeat album'));
	metaCell.append($('<button/>').attr('id', this.album_id + '_shuffle').addClass(BG.Album.css.meta.shuffle).attr('title', 'Shuffle album'));
	metaCell.append($('<button/>').attr('id', this.album_id + '_follow').addClass(BG.Album.css.meta.follow).attr('title', 'Open info pane on song start'));
}

BG.Album.prototype.buildAlbumContents = function(albumContents) {
	albumContents.append($('<img/>').addClass(BG.Album.css.content.art).attr('src', this.small_art_url));
	albumContents.append($('<span/>').addClass(BG.Album.css.content.title).text(this.title));

	this.accordion = $('<div/>').addClass(BG.Album.css.content.accordion);
	albumContents.append(this.accordion); 
	this.buildAlbumAccordion(this.accordion);
}

BG.Album.prototype.buildAlbumAccordion = function(albumAccordion) {
	var album = this;
	$(this.tracks).each(function() {
		var bgInfo = trackInfo[this.track_id];
		if (!bgInfo) { for (id in trackInfo) { if (trackInfo[id].karaoke == this.track_id) {
			bgInfo = trackInfo[id]; bgInfo.jcc = null;
		}}}
		var track = new BG.Track(album, this, bgInfo);
		album.masterTracks.unshift(track);
		if (BG.NerdRock.getInstance().badges.hasBadge('sfw') && track.nsfw) return true;
		album.workingTracks.push(track)
		// ($.inArray(album.album_id, oldestFirst) > -1) ? album.workingTracks.push(track) : album.workingTracks.unshift(track);
	});
	$(album.workingTracks).each(function() {
		var track = this;
		var header = $('<div/>').addClass(BG.Track.css.hdr.cont);
		var body = $('<div/>').addClass(BG.Track.css.body.cont);
		albumAccordion.append(header, body);
		track.buildDOM(header, body);
	});
}

BG.Album.registerJQueryUI = function() {
	$('.'+BG.Album.css.meta.onesong).button({ icons: { primary: 'ui-icon-arrowthickstop-1-e' } }).addClass('bg-toggle').tooltip();
	$('.'+BG.Album.css.meta.repeat).button({ icons: { primary: 'ui-icon-refresh' } }).addClass('bg-toggle').tooltip();
	$('.'+BG.Album.css.meta.shuffle).button({ icons: { primary: 'ui-icon-shuffle' } }).addClass('bg-toggle').data('click', function(event, pressed) {
		var album = BG.Album.getFromElement(event.target);
		if (pressed) BG.Album.shuffle(album.workingTracks);
		else album.workingTracks = album.masterTracks.slice(0);
		$('.'+BG.Track.css.body.media).filter(':hidden').empty();
		$(album.workingTracks).each(function() { album.accordion.append(this.hdr, this.body); });
		album.accordion.accordion('refresh');
	}).tooltip();
	$('.'+BG.Album.css.meta.follow).button({ icons: { primary: 'ui-icon-info' } }).addClass('bg-toggle').tooltip();
	$('.bg-toggle').button().data('state', false).mousedown(function (event) {
			event.preventDefault();
    	this.checked = !this.checked;
    	this.checked ? $(this).addClass('ui-state-active') : $(this).removeClass('ui-state-active');
    	$(this).attr('aria-pressed', this.checked ? 'true' : 'false');
    	if ($(this).data('click')) $(this).data('click')(event, this.checked);
	});
	$('.'+BG.Album.css.meta.follow).button().mousedown();

	$('.'+BG.Album.css.content.accordion).accordion({
		collapsible: true, active: false, heightStyle: 'content', beforeActivate: function(event, ui) {
			$('.'+BG.Album.css.content.accordion).each(function() {
				if (this != event.target) $(this).accordion('option', 'active', false);
			});
			var mediaTab = ui.newPanel.find('.'+BG.Track.css.body.media+':empty');
			if (mediaTab.length) mediaTab.html(BG.Track.getFromElement(mediaTab).media);
			ui.newPanel.find('.'+BG.Track.css.body.media+':empty').each(function() {
				$(this).html(BG.Track.getFromElement(this).media);
			});
		}, beforeActivate(event, ui) {
			return $($(this).data().lmd).closest('.ui-slider').length == 0;
		}, activate: function(event, ui) {
			BG.NerdRock.getInstance().saveState();
		}
	}).mousedown(function(event) {
		$(this).closest('.ui-accordion').data('lmd', event.target);
	});

	BG.Track.registerJQueryUI();
}

BG.Album.shuffle = function(array) {
	var m = array.length, t, i;
	// While there remain elements to shuffle…
	while (m) {
		// Pick a remaining element…
		i = Math.floor(Math.random() * m--);
		// And swap it with the current element.
		t = array[m]; array[m] = array[i]; array[i] = t;
	}
}
