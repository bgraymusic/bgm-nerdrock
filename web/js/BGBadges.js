var BG = BG || {};

///////////////////////////////////////////////
// Badge creation, validation, storage, and UI
BG.Badges = class {
	badges = [];
	token = '';

	cont = $('#bg-badge-stuff');
	badgesDiv = $('#bg-badges');
	button = $('#bg-add-badge-button');
	dialog = $('#bg-add-badge-dialog');
	alert = $('#bg-new-badge-alert');
	error = $('#bg-cannot-save-badges-alert');
	nsfw = $('#bg-nsfw-alert');

    // CONSTRUCTION (use BG.Badges.getInstance())
    constructor() {
		this.dialog.val = $('#bg-add-badge-value');
		this.dialog.submit = $('#bg-add-badge-submit');
	}

	static generateURL = 'https://94iml3erc4.execute-api.us-east-1.amazonaws.com/dev/api/badges';
	static validateURL = 'https://94iml3erc4.execute-api.us-east-1.amazonaws.com/dev/api/badges/{token}';
	static addURL = 'https://94iml3erc4.execute-api.us-east-1.amazonaws.com/dev/api/badges/{token}/{key}';

	static SPEC = {
		'j': { id: 'jcc',       img: 'img/jcc_boat.svg',            title: 'Sea Monkey' },
		'p': { id: 'patreon',   img: 'img/patreon_logo.png',        title: 'Patron' },
		's': { id: 'spintunes', img: 'img/spintunes_starburst.gif', title: 'Spin Tuner' },
		'k': { id: 'karaoke',   img: 'img/karaoke.png',             title: 'Karaoke' },
		'w': { id: 'sfw',       img: 'img/safety.png',              title: 'Safe for Work' }
	};

	// INITIALIZATION

	async bootstrap() {
        let token = this.loadToken();
		let response = await this.validateToken(token);
        let tuple = {
            token: response.token,
            badges: response.badges
        };
        this.recordBadges(tuple);
        tuple = await this.addURIBadges(tuple);
		this.draw();
		this.registerJQueryUI();
	}

    async addURIBadges(tuple) {
        var queryKeyList = new URL(window.location.href).searchParams.get('badges');
        var queryKeyArray = queryKeyList ? queryKeyList.split(',') : [];
        var revisedBadges = [...this.badges];
		let changed = false;
		for (const key of queryKeyArray) {
            let response = await this.addBadgeToToken(tuple.token, key);
            tuple.token = response.token;
            revisedBadges = response.badges;
			changed = true;
		};
        tuple.badges = revisedBadges;
        if (changed) this.recordBadges(tuple);
		return tuple;
    }

	// USER INTERFACE

	draw() {
		var spec = BG.Badges.SPEC;
		$(this.badgesDiv).empty();
		let instance = this;
		this.badges.forEach(badge => {
			$(instance.badgesDiv).append($('<img/>').attr('id', 'badge-' + spec[badge].id).attr('src', spec[badge].img).attr('title', spec[badge].title));
		});
		// $.each(this.badges, function() {
		// 	$(this.badgesDiv).append($('<img/>').attr('id', 'badge-' + spec[this].id).attr('src', spec[this].img).attr('title', spec[this].title));
		// });
	}

	registerJQueryUI() {
		this.registerAddDialog();
		this.registerErrorDialog();
		this.registerAlertDialog();
		this.registerNSFWDialog();
	}
	
	registerAddDialog() {
		let instance = BG.NerdRock.getInstance().badges;
		$(this.button).button({ icons: { primary: 'ui-icon-plus' } }).data('state', false).click(function(event) {
			event.stopPropagation();
			instance.checked = !instance.checked;
			if (instance.checked) instance.open();
			else instance.close();
		});
		$(this.dialog.val).button().keypress(function(e) { if (e.which == 13) { $('#bg-add-badge-submit').click(); return false; } });
		$(this.dialog.submit).button().click(function(event) {
			event.stopPropagation();
			// if (instance.addNewBadge(instance.dialog.val.val())) bgInit();
			instance.addNewBadge(instance.dialog.val.val());
		});
	}

	registerErrorDialog() {
		$(this.error).dialog({ autoOpen: false, resizable: false, modal: true, buttons: {
			'Don\'t tell me what to do': function() { $(this).dialog('close'); }, 'Ok': function() { $(this).dialog('close'); }
		}});
	}

	registerAlertDialog() {
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
	}

	registerNSFWDialog() {
		$(this.nsfw).dialog({ autoOpen: false, resizable: false, modal: true, width: 400, buttons: {
			'Stay Safe': function() { $(this).dialog('close'); },
			'Enter NSFW Mode': function() {
				var instance = BG.NerdRock.getInstance().badges;
				var idx = instance.badges.indexOf(BG.Badges.getHashForId('sfw'));
				if (idx > -1) { instance.badges.splice(idx, 1); instance.store(); bgInit(); instance.draw(); }
				$(this).dialog('close');
			}
		}});
	}

	open() {
		$(this.button).addClass('ui-state-active');
		$(this.button).attr('aria-pressed', 'true');
		$(this.button).button('option', 'icons', { primary: 'ui-icon-minus' } );
		$(this.button).attr('title', 'Close');
		$(this.dialog.val).val('');
		$(this.dialog).removeClass('bg-hide');
	}

	close() {
		$(this.button).removeClass('ui-state-active');
		$(this.button).attr('aria-pressed', 'false');
		$(this.button).button('option', 'icons', { primary: 'ui-icon-plus' } );
		$(this.button).attr('title', 'Add new badge…');
		$(this.dialog).addClass('bg-hide');
	}

	// BADGE MANAGEMENT

	hasBadges() { return !!this.badges.length; }

	hasBadge(id) { return BG.Badges.SPEC.hasOwnProperty(id); }

	async addNewBadge(key) {
		// var hash = BG.Badges.getHashForCode(key);
		// if (this.badges.indexOf(hash) === -1 && BG.Badges.SPEC[hash]) {
		// 	this.badges.push(hash);
		// 	this.store();
		// 	this.close();
		// 	this.draw();
		// 	$('#bg-new-badge-alert').data('badge', BG.Badges.SPEC[hash]);
		// 	$('#bg-new-badge-alert').dialog('open');

		// 	$(discography.allAlbums).each(function() {
		// 		if (this.album_id == BG.Badges.SPEC[hash].aid) discography.drawAlbums.push(this);
		// 	});

		// 	return true;
		// } else { return false; }
		let response = await this.addBadgeToToken(this.token, key);
        let tuple = {
            token: response.token,
            badges: response.badges
        };
        this.recordBadges(tuple);
		this.close();
		this.draw();
		if (response.added_code) {
			$(this.alert).data('badge', BG.Badges.SPEC[response.added_code]);
			$(this.alert).dialog('open');
		}
		BG.NerdRock.getInstance().discography.bootstrap(tuple.token);
        // let discData = await BG.NerdRock.getInstance().fetchDiscography(tuple.token);
        // BG.NerdRock.getInstance().discography.addAlbums(discData);
    	// BG.NerdRock.getInstance().discography.buildDOM(document.getElementById(BG.Discography.css.cont));
    	// BG.Discography.registerJQueryUI();
	}

	// Client/server interactions

	async generateNewToken() {
		let response = await fetch(BG.Badges.generateURL);
		let result = await response.json();
		return result;
	}

	async validateToken(token) {
		if (!token) {
			let result = await this.generateNewToken();
			return result;
		} else {
			let response = await fetch(BG.Badges.validateURL.replace('{token}', token))
			let result = await response.json();
			return result;
		}
	}

	async addBadgeToToken(token, key) {
		let response = await fetch(BG.Badges.addURL.replace('{token}', token).replace('{key}', key));
		let result = await response.json();
		return result;
	}

	// Badge and token local storage management

	loadToken() {
		if (typeof (Storage) !== 'undefined') {
			return localStorage.getItem('token');
		} else return null;
	}

    recordBadges(tuple) {
        console.log('Recording authorizations:\n\tToken: ' + tuple.token + '\n\tBadges: ' + tuple.badges);
        this.storeToken(tuple.token);
        this.token = tuple.token;
        this.badges = tuple.badges;
    }

	canStoreToken() {
		try {
			if (typeof (Storage) !== 'undefined') {
				let testString = 'foo';
				localStorage.setItem('testTokenStore', testString);
				let fetched = localStorage.getItem('testStoreToken');
				localStorage.removeItem('testTokenStore');
				return fetched == testString;
			} else {
				return false;
			}
		} catch (e) { return false; }
	}

	storeToken(token) {
		try {
			if (typeof (Storage) !== 'undefined') {
				if (token) localStorage.setItem('token', token);
				else localStorage.removeItem('token');
			}
		} catch (e) { $('#bg-cannot-save-badges-alert').dialog('open'); }
	}

};
