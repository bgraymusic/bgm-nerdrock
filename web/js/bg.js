var blogroot = 'https://briangraymusic.wordpress.com';
var bc = new Bandcamp();
var discography = new BG.Discography();
var nag;
var debugLyricTimings = false;

// Used to detect initial (useless) popstate.
// If history.state exists, assume browser isn't going to fire initial popstate.
var popped = ('state' in window.history && window.history.state !== null), initialURL = location.href;

$(function() {
	nag = new BG.Nag({
		container: $('#bg-nag'),
		heightDetermined: function(height) {
			console.log('Nag height: ' + height);
			$('#bg-contents').css('top', height + 80 + 'px');
		},
		close: function() {
			$('#bg-contents').css('top', 80 + 'px');
		}
	});
	BG.Badges.getInstance().bootstrap();
	if (bc.getBandcampData(onDataComplete, BG.Badges.getInstance())) { $('.bg-err').removeClass('bg-hide'); }
	// BG.Badges.getInstance().validateToken('uyasegfkawygfkasjhfgds');
});

function onDataComplete(bcData) {
	discography.addAlbums(bcData, true);
	bgInit();
}

function bgInit() {
	discography.buildDOM($('#'+BG.Discography.css.cont));
	registerGlobalJQueryUI();
	BG.Discography.registerJQueryUI();

	navigate({
		toptab: $.url().param('toptab'), blog: $.url().param('blog'),
		song: $.url().param('song'), songtab: $.url().param('songtab')
	});
}

function registerGlobalJQueryUI() {
	$(document).tooltip();
	$('#bg-prefs-button').button({ icons: { primary: 'ui-icon-gear' }, text: false });
	$('.bg-top-level-tabs').tabs({ activate: function(event, ui) { saveState(); } });
//	$('#bg-github').repo({ user: 'bgraymusic', name: 'nerdrock' });
	$(window).bind('popstate', function(event) {
		// Ignore inital popstate that some browsers fire on page load
		var initialPop = !popped && location.href == initialURL;
		popped = true;
		if (!initialPop) {
			navigate({
				toptab: $.url().param('toptab'), blog: $.url().param('blog'),
				song: $.url().param('song'), songtab: $.url().param('songtab')
			});
		}
	});
	$('.bg-patreon-button').button().click(function(event) {
		event.stopPropagation();
		window.open("http://patreon.com/BrianGray");
	});
}

function saveState() {
	var state = {};
	state.toptab = $('#bg-top-level-tabs').tabs('option', 'active');
	$('.bg-album-accordion').each(function() {
		var idx = $(this).accordion('option', 'active');
		if (idx !== false) {
			var header = $(this).find('.bg-accordion-header')[idx];
			state.song = $(header).attr('song');
			state.songtab = $(header).next().tabs('option', 'active');
		}
	});
	var url = '?toptab=' + state.toptab;
	if (state.song !== undefined) url += '&song=' + state.song;
	if (state.songtab !== undefined) url += '&songtab=' + state.songtab;
	window.history.pushState(state, '', url);
}

// params: toptab(0-n), song(title), songtab(0-n), blog(relative path off blogroot)
function navigate(params) {
	if (params['toptab']) {
		$('#bg-top-level-tabs').tabs('option', 'active', params['toptab']);
	}
	if (params['song']) {
		var track;
		$(discography.bgAlbums).each(function() {
			$(this.masterTracks).each(function() {
				if (BG.Track.mashTitle(this.title) == BG.Track.mashTitle(params['song'])) { track = this; return false; }
			});
		});
		if (track.nsfw && BG.Badges.getInstance().hasBadge('sfw')) {
			$('#bg-nsfw-alert').dialog('open');
		}

		$('.bg-album-accordion').each(function() {
			var header = $(this).find('.bg-accordion-header[song=' + BG.Track.mashTitle(params['song']) + ']');
			var index = $(this).find('.bg-accordion-header').index(header);
			if (index >= 0) {
				$(this).accordion('option', 'active', index);
				$('#bg-contents').animate({ scrollTop: header.position().top }, 1000);
				if (params['songtab']) header.next().tabs('option', 'active', params['songtab']);
				return false;
			}
		});
	}
	$('#bg-blogframe').attr('src', blogroot + (params['blog'] ? params['blog'] : ''));
}

function getURL(url) {
	var oReq = new XMLHttpRequest();
	oReq.addEventListener("load", function () {
		let result = JSON.parse(this.responseText);
		console.log('URL fetched:');
		console.log(result);
	});
	oReq.open("GET", url);
	oReq.send();
}
