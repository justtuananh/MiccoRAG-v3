import test from 'node:test';
import assert from 'node:assert/strict';
import { buildChatHistory } from '../src/utils/chatHistory.js';
import { ragChatApi } from '../src/utils/api.js';

test('history keeps only the last five completed question and answer pairs', () => {
  const messages = Array.from({ length: 7 }, (_, i) => [
    { role: 'user', content: `question ${i}` },
    { role: 'assistant', content: `answer ${i}` },
  ]).flat();
  assert.deepEqual(buildChatHistory(messages), messages.slice(-10));
  assert.deepEqual(buildChatHistory(messages, 0), []);
});

test('history drops failed, streaming, orphaned, and empty replies with their questions', () => {
  const messages = [
    { role: 'user', content: 'orphaned' },
    { role: 'user', content: 'good question' },
    { role: 'assistant', content: 'good answer' },
    { role: 'user', content: 'failed question' },
    { role: 'assistant', content: 'partial', streamError: 'connection lost' },
    { role: 'user', content: 'streaming question' },
    { role: 'assistant', content: 'partial', streaming: true },
    { role: 'user', content: 'empty question' },
    { role: 'assistant', content: '  ' },
    { role: 'user', content: 'still waiting' },
  ];
  assert.deepEqual(buildChatHistory(messages), [
    { role: 'user', content: 'good question' },
    { role: 'assistant', content: 'good answer' },
  ]);
});

test('streaming and regular chat use persisted server context rather than client history', async () => {
  const oldFetch = globalThis.fetch;
  const oldStorage = globalThis.localStorage;
  const calls = [];
  globalThis.localStorage = { getItem: () => null };
  globalThis.fetch = async (url, options) => {
    calls.push({ url, body: JSON.parse(options.body) });
    return new Response(null, { status: 200 });
  };
  const history = [{ role: 'user', content: 'earlier' }, { role: 'assistant', content: 'reply' }];
  try {
    await ragChatApi.streamChat(42, 'follow up', { history });
    await ragChatApi.chat(42, 'follow up', { history });
    assert.deepEqual(calls.map(({ body }) => body.history), [undefined, undefined]);
    assert.deepEqual(calls.map(({ url }) => url), [
      '/api/v1/rag/chat/42/stream', '/api/v1/rag/chat/42',
    ]);
  } finally {
    globalThis.fetch = oldFetch;
    globalThis.localStorage = oldStorage;
  }
});
