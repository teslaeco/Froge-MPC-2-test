// Run after the production build with: workerd test tests/worker-pairing.capnp
// Exercises the actual Workers Request constructor and crypto implementation.
// D1 and the remote HTTP response are controlled fixtures; no real account or tunnel is used.
import app from 'app.mjs';
function assert(value, message) { if (!value) throw new Error(message); }
export default {
  async test() {
    const credential = 'test-worker-token-'.repeat(3);
    let stored = null, requests = 0, upstreamStatus = 200;
    const nativeFetch = globalThis.fetch;
    globalThis.fetch = async (url, options) => {
      requests++;
      const outbound = new Request(url, options);
      assert(outbound.redirect === 'manual', 'Credentials must not follow redirects');
      return upstreamStatus === 200 ? Response.json({token: credential}) : new Response(null, {status: upstreamStatus, headers: {location: 'https://untrusted.example/collect'}});
    };
    const env = { BLENDER_SETTINGS_KEY: '12'.repeat(32), DB: {prepare(sql) {
      let args;
      return {
        bind(...values) { args = values; return this; },
        async first() { return stored; },
        async run() { assert(sql.startsWith('INSERT INTO blender_connections'), 'Unexpected write'); stored = {owner: args[0], endpoint: args[1], credential: args[2]}; return {meta: {changes: 1}}; }
      };
    }}};
    function request() { return new Request('https://studio.test/api/blender/connection', {method: 'POST', headers: {'content-type': 'application/json', origin: 'https://studio.test', 'oai-authenticated-user-id': 'test-owner'}, body: JSON.stringify({endpoint: 'https://test-only.trycloudflare.com', code: 'a'.repeat(32)})}); }
    try {
      const result = await app.fetch(request(), env);
      assert(result.status === 200, 'Pairing should succeed in Workers: ' + await result.text());
      assert(stored && !stored.credential.includes(credential), 'Credential must be encrypted');
      console.log('Successful pairing and encrypted storage passed in Workers.');
      for (const status of [301, 302, 303, 307, 308]) {
        stored = null; requests = 0; upstreamStatus = status;
        const rejected = await app.fetch(request(), env);
        assert(rejected.status === 502 && stored === null && requests === 1, 'Redirect must fail without following or saving');
      }
      console.log('All redirect rejection checks passed in Workers.');
    } finally { globalThis.fetch = nativeFetch; }
  }
};
