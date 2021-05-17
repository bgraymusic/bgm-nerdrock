var BG = BG || {};

BG.Nag = function(config) {
	var container = this.container = config.container;
	this.onHeightDetermined = config.heightDetermined;
	this.onClose = config.close;
	this.onResize = function() { config.heightDetermined($(container).height()); }

	// Only show the nag div if we're sure we can hide it forever after they've seen it
	// Better never to show it than to be annoying
	if (typeof(Storage) !== 'undefined') {
		if (localStorage.getItem('nonag')) return this;
		else localStorage.setItem('nonag', true);
	}

	$(container).find('#bg-nag-dismiss').button().click(function() {
		$(window).off('resize', null, this.onResize);
		container.css('display', 'none');
		config.close();
	});

	$(window).resize(this.onResize);
	this.onResize();

	container.css('display', 'block');

	return this;
}
