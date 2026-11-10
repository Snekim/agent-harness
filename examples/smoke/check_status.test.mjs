import assert from 'node:assert/strict';
import test from 'node:test';
import { showStatus } from './status.mjs';

test('shows the server message as text and requests the existing endpoint', async () => {
  const element = { textContent: 'Loading…' };
  const paths = [];
  await showStatus(element, async (path) => {
    paths.push(path);
    return { ok: true, json: async () => ({ status: 'ok', message: 'Message from server' }) };
  });
  assert.deepEqual(paths, ['/api/status']);
  assert.equal(element.textContent, 'Message from server');
});

test('shows a useful fallback for a failed request', async () => {
  const element = { textContent: 'Loading…' };
  await showStatus(element, async () => ({ ok: false }));
  assert.equal(element.textContent, 'Status unavailable');
});
