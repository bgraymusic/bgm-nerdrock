import cf from 'cloudfront';

const kvsHandle = cf.kvs();

async function handler(event) {
	let request = event.request;
	let viewer = event.viewer;

	try {
		const allowed_ip = await kvsHandle.get('allowed-ip');
		if (viewer.ip != allowed_ip) {
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
	return request;
}
