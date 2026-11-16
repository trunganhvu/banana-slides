/**
 * Shared Cloudflare Pages Functions reverse-proxy helper.
 * Routes /api/*, /files/*, and /health requests from the Cloudflare Pages origin
 * to the AWS Backend defined in the BACKEND_ORIGIN environment variable.
 */

function normalizeOrigin(rawOrigin) {
  if (typeof rawOrigin !== 'string') return '';
  const trimmed = rawOrigin.trim().replace(/\/+$/, '');
  if (!/^https?:\/\/[^/\s]+$/i.test(trimmed)) return '';
  return trimmed;
}

export async function proxyToBackend(context) {
  const { request, env } = context;
  const backendOrigin = normalizeOrigin(env?.BACKEND_ORIGIN);

  if (!backendOrigin) {
    return new Response(
      JSON.stringify({
        success: false,
        error: 'BACKEND_ORIGIN is not configured on Cloudflare Pages.',
        hint: 'Set BACKEND_ORIGIN (e.g. https://api.yourdomain.com) in Cloudflare Pages environment variables, or build the frontend with VITE_API_BASE_URL.',
      }),
      {
        status: 503,
        headers: {
          'Content-Type': 'application/json; charset=utf-8',
          'Cache-Control': 'no-store',
        },
      }
    );
  }

  const incomingUrl = new URL(request.url);
  const targetUrl = `${backendOrigin}${incomingUrl.pathname}${incomingUrl.search}`;

  const forwardedHeaders = new Headers(request.headers);
  forwardedHeaders.delete('host');
  forwardedHeaders.delete('content-length');

  const clientIp = request.headers.get('CF-Connecting-IP');
  if (clientIp) {
    forwardedHeaders.set('X-Real-IP', clientIp);
  }
  forwardedHeaders.set('X-Forwarded-Host', incomingUrl.host);
  forwardedHeaders.set('X-Forwarded-Proto', incomingUrl.protocol.replace(':', ''));

  const method = request.method.toUpperCase();
  const init = {
    method,
    headers: forwardedHeaders,
    redirect: 'manual',
  };

  if (method !== 'GET' && method !== 'HEAD') {
    init.body = request.body;
  }

  try {
    const upstreamResponse = await fetch(targetUrl, init);
    const responseHeaders = new Headers(upstreamResponse.headers);

    const contentType = responseHeaders.get('content-type') || '';
    if (contentType.includes('text/event-stream')) {
      responseHeaders.set('Cache-Control', 'no-cache');
      responseHeaders.set('X-Accel-Buffering', 'no');
    }

    return new Response(upstreamResponse.body, {
      status: upstreamResponse.status,
      statusText: upstreamResponse.statusText,
      headers: responseHeaders,
    });
  } catch (error) {
    return new Response(
      JSON.stringify({
        success: false,
        error: 'Failed to reach upstream backend service.',
        detail: error instanceof Error ? error.message : String(error),
      }),
      {
        status: 502,
        headers: {
          'Content-Type': 'application/json; charset=utf-8',
          'Cache-Control': 'no-store',
        },
      }
    );
  }
}
