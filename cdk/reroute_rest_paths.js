async function handler(event) {
	const request = event.request;

	['news', 'blog', 'music', 'studio', 'code'].forEach((prefix) => {
		if (request.uri.startsWith('/' + prefix)) {
			request.uri = '/';
		}
	});

	return request;
}
