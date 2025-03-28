var BG = BG || {};

///////////////////////////////////////////////////
// Main Nerd Rock application class

BG.NerdRock = class {
	static BLOGROOT =
		window.location.hostname == 'localhost' ? 'http://localhost:4001' : 'https://blog.briangraymusic.com';

	badges = new BG.Badges();
	discography = new BG.Discography();
	blogUri = '';

	// CONSTRUCTION (use BG.NerdRock.getInstance())
	// constructor() {}
	static #INSTANCE = null;
	static getInstance() {
		if (!this.INSTANCE) this.INSTANCE = new BG.NerdRock();
		return this.INSTANCE;
	}

	// Used to detect initial (useless) popstate.
	// If history.state exists, assume browser isn't going to fire initial popstate.
	popped = 'state' in window.history && window.history.state !== null;
	initialURL = location.href;

	// Initialization steps
	async main() {
		this.drawGlobalUI();
		this.registerPopstateHandler();
		await this.badges.bootstrap();
		await this.discography.bootstrap(this.badges.token);
		this.navigate(this.getTabStateFromUrl());
		window.addEventListener('message', function (event) {
			switch (event.data.message) {
				case 'navigate':
					if (event.data.params['blog']) event.data.params['blog'] = event.data.params['blog'].replace('/', '');
					BG.NerdRock.getInstance().navigate(event.data.params);
					break;
				case 'updateBlogUri':
					BG.NerdRock.getInstance().blogUri = event.data.blogUri.replace(/^\/+|\/+$/g, '');
					BG.NerdRock.getInstance().saveState();
					break;
			}
		});
	}

	getTabStateFromUrl() {
		// Allow 'news' and 'blog' both to lead to the News tab
		const validTopTabs = ['news', 'blog', 'music', 'studio', 'code'];
		const url = new URL(window.location.href);
		let state = {
			topTab: 'news',
			blogUri: '',
			song: undefined,
			songTab: undefined,
		};

		// From URI first
		const resources = url.pathname
			.toLowerCase()
			.replace(/^\/+|\/+$/g, '')
			.split('/');
		if (resources.length == 0 || !validTopTabs.includes(resources[0])) return state;

		state.topTab = resources[0];
		switch (state.topTab) {
			case 'news':
			case 'blog':
				state.topTab = 'news';
				if (resources.length > 1) state.blogUri = resources[1];
				break;
			case 'music':
				if (resources.length > 1) state.song = resources[1];
				if (resources.length > 2) state.songTab = resources[2];
				break;
		}

		// Any query params overwrite URI values. To support legacy links, expect query params to use integer indices
		// to tabs instead of the more readable tab titles. Both are subject to change with the site, but words are
		// easier to accommodate with coded synonyms (like 'news' and 'blog')
		const params = new URLSearchParams(
			Array.from(url.searchParams, ([key, value]) => [key.toLowerCase(), value.toLowerCase()])
		);

		if (params.get('toptab')) {
			state.topTab =
				parseInt(params.get('toptab')) == NaN ? params.get('toptab') : this.topTabIdxToName(params.get('toptab'));

			switch (state.topTab) {
				case 'news':
				case 'blog':
					state.topTab = 'news';
					if (params.get('blog')) state.blogUri = params.get('blog');
					break;
				case 'music':
					if (params.get('song')) {
						state.song = params.get('song');
						if (params.get('songtab')) {
							state.songTab =
								parseInt(params.get('songtab')) == NaN
									? params.get('songtab')
									: this.songTabIdxToName(state.song, params.get('songtab'));
						}
					}
					break;
			}
		}

		return state;
	}

	topTabIdxToName(idx) {
		let tabs = $('#bg-top-level-tabs').tabs('instance').tabs;
		return tabs.length > idx ? tabs[idx].textContent.toLowerCase() : null;
	}

	topTabNameToIdx(name) {
		let tabs = $('#bg-top-level-tabs').tabs('instance').tabs;
		let idx = false;
		tabs.each(function (i) {
			if (this.textContent.toLowerCase() == name.toLowerCase()) {
				idx = i;
				return false;
			}
		});
		return idx;
	}

	songTabIdxToName(song, idx) {
		let songTabName = null;
		$('.bg-album-accordion>.bg-accordion-header').each(function () {
			if ($(this).attr(song) == song) {
				songTabName = $(this).next().tabs('instance').tabs[idx].textContent.toLowerCase();
				return false;
			}
		});
		return songTabName;
	}

	songTabNameToIdx(tabsCont, name) {
		let idx = false;
		$(tabsCont).each(function (i) {
			if ($(this).innerText == name) {
				idx = i;
				return false;
			}
		});
		return idx;
	}

	getTabStateFromDOM() {
		let state = {
			topTab: undefined,
			blogUri: this.blogUri,
			song: undefined,
			songTab: undefined,
		};

		let topTabs = $('#bg-top-level-tabs').tabs('instance');
		state.topTab = topTabs.tabs[state.topTabIdx].textContent.toLowerCase();

		$('.bg-album-accordion').each(function () {
			var idx = $(this).accordion('option', 'active');
			if (idx !== false) {
				var header = $(this).find('.bg-accordion-header')[idx];
				state.song = $(header).attr('song');
				let songTabs = $(header).next().tabs('instance');
				if (songTabs.options.active !== false)
					state.songTab = songTabs.tabs[songTabs.options.active].textContent.toLowerCase();
				return false;
			}
		});

		return state;
	}

	drawGlobalUI() {
		// GLOBAL
		$(document).tooltip();

		// HEADER
		$('.bg-patreon-button')
			.button()
			.click(function (event) {
				event.stopPropagation();
				window.open('http://patreon.com/BrianGray');
			});
		(function (d, s, id) {
			var js,
				fjs = d.getElementsByTagName(s)[0];
			if (d.getElementById(id)) return;
			js = d.createElement(s);
			js.id = id;
			js.src = '//connect.facebook.net/en_US/sdk.js#xfbml=1&version=v2.5';
			fjs.parentNode.insertBefore(js, fjs);
		})(document, 'script', 'facebook-jssdk');
		$('#bg-prefs-button').button({ icons: { primary: 'ui-icon-gear' }, text: false });

		// TOP LEVEL TABS
		$('.bg-top-level-tabs').tabs({
			activate: function (event, ui) {
				// repo.js starts closed; simulate a click to expand the home directory
				if (ui.newTab[0].innerText == 'Code') ui.newPanel.find('.repo a')[0].click();
				BG.NerdRock.getInstance().saveState();
			},
		});
		$('#bg-blogframe').attr('src', BG.NerdRock.BLOGROOT + ($.url().param('blog') ? $.url().param('blog') : ''));
		$('#bg-github').repo({ user: 'bgraymusic', name: 'bgm-nerdrock', branch: 'trunk' });
	}

	registerPopstateHandler() {
		$(window).bind('popstate', function (event) {
			// Ignore inital popstate that some browsers fire on page load
			var initialPop = !this.popped && location.href == this.initialURL;
			this.popped = true;
			if (!initialPop) this.navigate(this.getTabStateFromUrl());
		});
	}

	async fetchDiscography(token) {
		let response = await this.discography.fetchDiscography(token);
		return response.discography;
	}

	saveState() {
		var state = {};
		let topTabIdx = $('#bg-top-level-tabs').tabs('option', 'active');
		state.topTab = $('#bg-top-level-tabs').tabs('instance').tabs[topTabIdx].textContent.toLowerCase();
		$('.bg-album-accordion').each(function () {
			var idx = $(this).accordion('option', 'active');
			if (idx !== false) {
				var header = $(this).find('.bg-accordion-header')[idx];
				state.song = $(header).attr('song');
				let songTabIdx = $(header).next().tabs('option', 'active');
				if (songTabIdx !== undefined)
					state.songTab = $(header).next().tabs('instance').tabs[songTabIdx].textContent.toLowerCase();
				else state.songTab = undefined;
			}
		});
		let url = new URL(window.location.href);
		let pushUrl = url.origin + '/' + state.topTab;
		if (state.topTab == 'music') {
			if (state.song !== undefined) pushUrl += '/' + state.song;
			if (state.songTab !== undefined) pushUrl += '/' + state.songTab;
		} else if (state.topTab == 'news') {
			if (this.blogUri.length) pushUrl += '/' + this.blogUri;
		}
		window.history.pushState(state, '', pushUrl);
	}

	// params: topTab(name), song(title), songTab(name), blogUri(relative path off blogroot)
	navigate(params) {
		if (params['topTab']) {
			$('#bg-top-level-tabs').tabs('option', 'active', this.topTabNameToIdx(params['topTab']));
		}
		if (params['song']) {
			var track;
			$(this.discography.bgAlbums).each(function () {
				$(this.masterTracks).each(function () {
					if (BG.Track.mashTitle(this.title) == BG.Track.mashTitle(params['song'])) {
						track = this;
						return false;
					}
				});
			});
			if (track.nsfw && this.badges.hasBadge('sfw')) {
				$('#bg-nsfw-alert').dialog('open');
			}

			$('.bg-album-accordion').each(function () {
				var header = $(this).find('.bg-accordion-header[song=' + BG.Track.mashTitle(params['song']) + ']');
				var index = $(this).find('.bg-accordion-header').index(header);
				if (index >= 0) {
					$(this).accordion('option', 'active', index);
					$('#bg-contents').animate({ scrollTop: header.position().top }, 1000);
					if (params['songTab']) {
						let tabsCont = header.next();
						tabsCont.tabs('option', 'active', this.songTabNameToIdx(tabsCont, params['songTab']));
					}
					return false;
				}
			});
		}
		if (params['blogUri']) {
			$('#bg-blogframe').attr('src', BG.NerdRock.BLOGROOT + '/' + params['blogUri']);
		}
	}
};

// Application entry point (fire main() on content ready)

if (document.readyState === 'loading') {
	// Loading hasn't finished yet
	document.addEventListener('DOMContentLoaded', BG.NerdRock.getInstance().main());
} else {
	// `DOMContentLoaded` has already fired
	BG.NerdRock.getInstance().main();
}
