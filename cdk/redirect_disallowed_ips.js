import cf from "cloudfront";

const kvsHandle = cf.kvs();

async function handler(event) {
  var request = event.request;
  var viewer = event.viewer;

  try {
    allowed_ip = await kvsHandle.get("allowed_ip");
    if (viewer.ip != allowed_ip) {
      return {
        statusCode: 302,
        statusDescription: "Found",
        headers: {
          location: { value: newurl },
        },
      };
    }
  } catch (err) {
    return request;
  }
  return request;
}
