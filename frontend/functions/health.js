import { proxyToBackend } from './_utils/proxy.js';

export async function onRequest(context) {
  return proxyToBackend(context);
}
