var BG = BG || {};

///////////////////////////////////////////////////
// Main Nerd Rock application class

BG.NerdRock = class {
    static BLOGROOT = 'https://briangraymusic.wordpress.com';

    badges = new BG.Badges();
    discography = new BG.Discography();

    // CONSTRUCTION (use BG.NerdRock.getInstance())
    // constructor() {}
    static #INSTANCE = null;
    static getInstance() {
        if (!this.INSTANCE) this.INSTANCE = new BG.NerdRock();
        return this.INSTANCE;
    }

    // Used to detect initial (useless) popstate.
    // If history.state exists, assume browser isn't going to fire initial popstate.
    popped = ('state' in window.history && window.history.state !== null);
    initialURL = location.href;

    // Initialization steps
    async main() {
        console.log('BG.NerdRock.main() called');
        this.registerGlobalJQueryUI();
        await this.badges.bootstrap();
        await this.discography.bootstrap(this.badges.token);
        this.navigate({
                    toptab: $.url().param('toptab'), blog: $.url().param('blog'),
                    song: $.url().param('song'), songtab: $.url().param('songtab')
                });
    }

    registerGlobalJQueryUI() {
        $(document).tooltip();
        $('#bg-prefs-button').button({ icons: { primary: 'ui-icon-gear' }, text: false });
        $('.bg-top-level-tabs').tabs({ activate: function(event, ui) { BG.NerdRock.getInstance().saveState(); } });
    	$('#bg-github').repo({ user: 'bgraymusic', name: 'bgm-nerdrock' });
        $(window).bind('popstate', function(event) {
            // Ignore inital popstate that some browsers fire on page load
            var initialPop = !this.popped && location.href == this.initialURL;
            this.popped = true;
            if (!this.initialPop) {
                this.navigate({
                    toptab: $.url().param('toptab'), blog: $.url().param('blog'),
                    song: $.url().param('song'), songtab: $.url().param('songtab')
                });
            }
        });
        $('.bg-patreon-button').button().click(function(event) {
            event.stopPropagation();
            window.open("http://patreon.com/BrianGray");
        });
	    (function(d, s, id) {
            var js, fjs = d.getElementsByTagName(s)[0];
            if (d.getElementById(id)) return;
            js = d.createElement(s);
            js.id = id;
            js.src = "//connect.facebook.net/en_US/sdk.js#xfbml=1&version=v2.5";
            fjs.parentNode.insertBefore(js, fjs);
        } (document, 'script', 'facebook-jssdk'));
    }

    async fetchDiscography(token) {
        let response = await this.discography.fetchDiscography(token);
        return response.discography;
    }

    saveState() {
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
    navigate(params) {
        if (params['toptab']) {
            $('#bg-top-level-tabs').tabs('option', 'active', params['toptab']);
        }
        if (params['song']) {
            var track;
            $(this.discography.bgAlbums).each(function() {
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
        $('#bg-blogframe').attr('src', BG.NerdRock.BLOGROOT + (params['blog'] ? params['blog'] : ''));
    }
}

// Application entry point (fire main() on content ready)

if (document.readyState === 'loading') {  // Loading hasn't finished yet
  document.addEventListener('DOMContentLoaded', BG.NerdRock.getInstance().main());
} else {  // `DOMContentLoaded` has already fired
  BG.NerdRock.getInstance().main();
}
