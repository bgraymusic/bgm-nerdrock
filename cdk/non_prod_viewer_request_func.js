import cf from 'cloudfront';

const kvsHandle = cf.kvs();

async function handler(event) {
	const request = event.request;
	const viewer = event.viewer;

	try {
		const allowed_ips = await kvsHandle.get('allowed-ips');
		if (!allowed_ips.includes(viewer.ip)) {
			console.log('Non-prod request from ' + viewer.ip + ' (only ' + allowed_ips + ' allowed); redirecting to prod…');
			return {
				statusCode: 302,
				statusDescription: 'Found',
				headers: {
					location: { value: 'https://briangraymusic.com' },
				},
			};
		}
	} catch (err) {
		console.log(err);
		return request;
	}

	['news', 'blog', 'music', 'studio', 'code'].forEach((prefix) => {
		if (request.uri.startsWith('/' + prefix)) {
			request.uri = '/';
		}
	});

	return request;
}
