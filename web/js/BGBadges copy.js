///////////////////////////////////////////////
// STRING HASH EXTENSION

String.prototype.hashCode = function() {
  var hash = 0, i, chr, len;
  if (this.length == 0) return hash;
  for (i = 0, len = this.length; i < len; i++) {
//    chr   = this.charCodeAt(i);
    hash  = ((hash << 5) - hash) + this.charCodeAt(i);
    hash |= 0; // Convert to 32bit integer
  }
  return hash;
};

var BG = BG || {};

///////////////////////////////////////////////
// CONSTRUCTION (use BG.Badges.getInstance)

BG.Badges = function() {
	this.badges = [];

	this.cont = $('#bg-badge-stuff');
	this.badgesDiv = $('#bg-badges');
	this.button = $('#bg-add-badge-button');
	this.dialog = $('#bg-add-badge-dialog');
	this.dialog.val = $('#bg-add-badge-value');
	this.dialog.submit = $('#bg-add-badge-submit');
	this.alert = $('#bg-new-badge-alert');
	this.error = $('#bg-cannot-save-badges-alert');
	this.nsfw = $('#bg-nsfw-alert');

	return this;
}

BG.Badges.getInstance = function() {
	var instance = $('#bg-badge-stuff').data().badges;
	if (!instance) { instance = new BG.Badges(); $('#bg-badge-stuff').data('badges', instance); }
	return instance;
}

///////////////////////////////////////////////
// STATIC SPEC STUFF

BG.Badges.SPEC = {
	'1646334178':  { id: 'jcc',       img: 'img/jcc_boat.svg',            title: 'Sea Monkey', aid: 24668382 },
	'-1309368522': { id: 'patreon',   img: 'img/patreon_logo.png',        title: 'Patron',     aid: 3599490148 },
	'-1883201621': { id: 'spintunes', img: 'img/spintunes_starburst.gif', title: 'Spin Tuner', aid: 444214854 },
	'1201146268':  { id: 'karaoke',   img: 'img/karaoke.png',             title: 'Karaoke',    aid: 3939645898},
	'113796':      { id: 'sfw',       img: 'img/safety.png',              title: 'Safe for Work' }
};

BG.Badges.getBadgeSpec = function(id) { var spec; $.each(BG.Badges.SPEC, function(k, v) { if (v.id === id) spec = this; }); return spec; }
BG.Badges.getHashForCode = function(code) { return code.toLowerCase().hashCode().toString(); }
BG.Badges.getHashForId = function(id) { var hash; $.each(BG.Badges.SPEC, function(k, v) { if (v.id === id) hash = k; }); return hash; }

BG.Badges.prototype = {

	///////////////////////////////////////////////
	// INITIALIZATION

	bootstrap: function() {
		this.load();
		this.registerJQueryUI();
		var newBadges = this.loadFromQueryString();
		this.store(newBadges.length > 0);
		this.draw();
	},

	loadFromQueryString: function() {
		var queryBadges = $.url().param('badges') ? $.url().param('badges').split(',') : []; var newBadges = []; var instance = this;
		$.each(queryBadges, function() {
			var hash = BG.Badges.getHashForCode(this);
			if (instance.badges.indexOf(hash) === -1 && BG.Badges.SPEC[hash]) { newBadges.push(hash); instance.addNewBadge(this); }
		});
		return newBadges;
	},

	///////////////////////////////////////////////
	// USER INTERFACE

	draw: function() {
		var spec = BG.Badges.SPEC; var div = this.badgesDiv;
		$(div).empty();
		$.each(this.badges, function() {
			$(div).append($('<img/>').attr('id', 'badge-' + spec[this].id).attr('src', spec[this].img).attr('title', spec[this].title));
		});
	},

	registerJQueryUI: function() {
		this.registerAddDialog();
		this.registerErrorDialog();
		this.registerAlertDialog();
		this.registerNSFWDialog();
	},
	
	registerAddDialog: function() {
		var instance = BG.Badges.getInstance();
		$(this.button).button({ icons: { primary: 'ui-icon-plus' } }).data('state', false).click(function(event) {
			event.stopPropagation();
			this.checked = !this.checked;
			if (this.checked) instance.open();
			else instance.close();
		});
		$(this.dialog.val).button().keypress(function(e) { if (e.which == 13) { $('#bg-add-badge-submit').click(); return false; } });
		$(this.dialog.submit).button().click(function(event) {
			event.stopPropagation();
			if (instance.addNewBadge(instance.dialog.val.val())) bgInit();
		});
	},

	registerErrorDialog: function() {
		$(this.error).dialog({ autoOpen: false, resizable: false, modal: true, buttons: {
			'Don\'t tell me what to do': function() { $(this).dialog('close'); }, 'Ok': function() { $(this).dialog('close'); }
		}});
	},

	registerAlertDialog: function() {
		$(this.alert).dialog({
			autoOpen: false,
			resizable: false,
			modal: true,
			buttons: { 'Woo-hoo!': function() { $(this).dialog('close'); }, 'Just Ok': function() { $(this).dialog('close'); } },
			open: function(event, ui) {
				$('#bg-new-badge-icon').attr('src', $(this).data().badge.img);
				$('#bg-new-badge-msg').text($(this).data().badge.title);
			}
		});
	},

	registerNSFWDialog: function() {
		$(this.nsfw).dialog({ autoOpen: false, resizable: false, modal: true, width: 400, buttons: {
			'Stay Safe': function() { $(this).dialog('close'); },
			'Enter NSFW Mode': function() {
				var instance = BG.Badges.getInstance();
				var idx = instance.badges.indexOf(BG.Badges.getHashForId('sfw'));
				if (idx > -1) { instance.badges.splice(idx, 1); instance.store(); bgInit(); instance.draw(); }
				$(this).dialog('close');
			}
		}});
	},

	open: function() {
		$(this.button).addClass('ui-state-active');
		$(this.button).attr('aria-pressed', 'true');
		$(this.button).button('option', 'icons', { primary: 'ui-icon-minus' } );
		$(this.button).attr('title', 'Close');
		$(this.dialog.val).val('');
		$(this.dialog).removeClass('bg-hide');
	},

	close: function() {
		$(this.button).removeClass('ui-state-active');
		$(this.button).attr('aria-pressed', 'false');
		$(this.button).button('option', 'icons', { primary: 'ui-icon-plus' } );
		$(this.button).attr('title', 'Add new badge…');
		$(this.dialog).addClass('bg-hide');
	},

	///////////////////////////////////////////////
	// BADGE MANAGEMENT

	hasBadges: function() { return !!this.badges.length; },

	hasBadge: function(id) { var found = false; $.each(this.badges, function() { if (BG.Badges.SPEC[this].id === id) found = true; }); return found; },

	addNewBadge: function(code) {
		var hash = BG.Badges.getHashForCode(code);
		if (this.badges.indexOf(hash) === -1 && BG.Badges.SPEC[hash]) {
			this.badges.push(hash);
			this.store();
			this.close();
			this.draw();
			$('#bg-new-badge-alert').data('badge', BG.Badges.SPEC[hash]);
			$('#bg-new-badge-alert').dialog('open');

			$(discography.allAlbums).each(function() {
				if (this.album_id == BG.Badges.SPEC[hash].aid) discography.drawAlbums.push(this);
			});

			return true;
		} else { return false; }
	},

	///////////////////////////////////////////////
	// LOCAL STORAGE

	load: function() {
		if (typeof(Storage) !== 'undefined') {
			if (!localStorage.getItem('badges')) this.badges = [];
			else this.badges = JSON.parse(localStorage.getItem('badges'));
		} else this.badges = [];
	},

	store: function(gotNewBadges) {
		try {
			if (typeof(Storage) !== 'undefined') {
				localStorage.setItem('badges', JSON.stringify(this.badges));
			} else if (gotNewBadges) {
				$('#bg-cannot-save-badges-alert').dialog('open');
			}
		} catch(e) { $('#bg-cannot-save-badges-alert').dialog('open'); }
	}

};
