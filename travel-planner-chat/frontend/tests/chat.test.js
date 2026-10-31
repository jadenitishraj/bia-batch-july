import { afterEach, expect, test, vi } from 'vitest';
import { $, response, startApp, trip } from './helpers.js';

afterEach(() => { vi.unstubAllGlobals(); });

async function send(message = 'Create a trip') {
  $('#chat-input').value = message;
  $('#chat-form').dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
  await vi.waitFor(() => { expect($('#chat-send').disabled).toBe(false); });
}

test('opens and closes chat, sends history, refreshes trips and renders safe text', async () => {
  const fetchMock = vi.fn().mockImplementation((path) => Promise.resolve(response(
    path === '/api/chat' ? { reply: '<img src=x onerror=alert(1)> Saved.' } : [trip])));
  await startApp(fetchMock);
  expect($('#chat-panel').hidden).toBe(true);
  $('#chat-toggle').click();
  expect($('#chat-input')).toBe(document.activeElement);
  expect($('#chat-toggle').getAttribute('aria-expanded')).toBe('true');
  await send();
  expect($('#chat-messages img')).toBeNull();
  expect($('#chat-messages').textContent).toContain('Saved.');
  expect($('#chat-input').value).toBe('');
  await send('Change the budget');
  const sent = fetchMock.mock.calls.filter(([path]) => path === '/api/chat');
  expect(JSON.parse(sent[1][1].body).history).toHaveLength(2);
  expect(sent[0][1].headers.Authorization).toBe('Bearer test-jwt');
  $('#chat-close').click();
  expect($('#chat-panel').hidden).toBe(true);
  expect(document.activeElement).toBe($('#chat-toggle'));
  $('#chat-toggle').click();
  $('#chat-toggle').click();
  expect($('#chat-panel').hidden).toBe(true);
  $('#logout').click();
  expect($('#chat-messages').textContent).toBe('');
});

test('preserves input after failure, refreshes trips and prevents duplicate submissions', async () => {
  let finish;
  const fetchMock = vi.fn().mockImplementation((path) => path === '/api/chat'
    ? new Promise((resolve) => { finish = resolve; }) : Promise.resolve(response([])));
  await startApp(fetchMock);
  $('#chat-toggle').click();
  $('#chat-input').value = 'Create Jaipur';
  const submit = () => $('#chat-form').dispatchEvent(new Event('submit', { cancelable: true }));
  submit();
  submit();
  expect(fetchMock.mock.calls.filter(([path]) => path === '/api/chat')).toHaveLength(1);
  finish(response({ error: 'Chat unavailable' }, false));
  await vi.waitFor(() => { expect($('#chat-send').disabled).toBe(false); });
  expect($('#chat-error').textContent).toBe('Chat unavailable');
  expect($('#chat-input').value).toBe('Create Jaipur');
  expect(fetchMock.mock.calls.filter(([path]) => path === '/api/trips')).toHaveLength(2);
  $('#chat-input').value = '   ';
  submit();
  expect(fetchMock.mock.calls.filter(([path]) => path === '/api/chat')).toHaveLength(1);
});

test('logout ignores a late chat reply and clears conversation', async () => {
  let finish;
  const fetchMock = vi.fn().mockImplementation((path) => path === '/api/chat'
    ? new Promise((resolve) => { finish = resolve; }) : Promise.resolve(response([])));
  await startApp(fetchMock);
  $('#chat-toggle').click();
  $('#chat-input').value = 'Plan Jaipur';
  $('#chat-form').dispatchEvent(new Event('submit', { cancelable: true }));
  $('#logout').click();
  finish(response({ reply: 'Private answer' }));
  await new Promise((resolve) => { setTimeout(resolve, 0); });
  expect($('#chat-messages').textContent).toBe('');
  expect($('#chat-panel').hidden).toBe(true);
});
