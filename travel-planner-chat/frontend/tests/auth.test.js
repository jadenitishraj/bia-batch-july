import { afterEach, expect, test, vi } from 'vitest';
import { $, response, startApp, trip } from './helpers.js';

const session = { access_token: 'signed-test-token', user: { email: 'learner@example.com' } };
afterEach(() => vi.unstubAllGlobals());

async function authenticate(create = false) {
  $('#auth-email').value = 'learner@example.com';
  $('#auth-password').value = 'correct-password';
  $('#register-account').checked = create;
  $('#auth-form').dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
  await vi.waitFor(() => expect($('#auth-submit').disabled).toBe(false));
}

test('does not request database records until login, then sends the returned JWT', async () => {
  const fetchMock = vi.fn().mockResolvedValueOnce(response(session))
    .mockResolvedValueOnce(response([trip]));
  await startApp(fetchMock, false);
  expect(fetchMock).not.toHaveBeenCalled();
  expect($('#workspace').hidden).toBe(true);
  await authenticate();
  expect(fetchMock.mock.calls[0][0]).toBe('/api/auth/login');
  expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({
    email: 'learner@example.com', password: 'correct-password',
  });
  expect(fetchMock.mock.calls[0][1].headers.Authorization).toBeUndefined();
  expect(fetchMock.mock.calls[1][1].headers.Authorization).toBe('Bearer signed-test-token');
  expect($('#account').textContent).toBe('learner@example.com');
  expect($('#trip-title').textContent).toBe(trip.title);
  expect($('#auth-panel').hidden).toBe(true);
  $('#logout').click();
  expect($('#workspace').hidden).toBe(true);
  expect($('#trip-list').textContent).toBe('');
  expect($('#account').textContent).toBe('');
  expect(document.activeElement).toBe($('#auth-email'));
});

test('registers through the same form and clears the password after success', async () => {
  const fetchMock = vi.fn().mockResolvedValueOnce(response(session))
    .mockResolvedValueOnce(response([]));
  await startApp(fetchMock, false);
  await authenticate(true);
  expect(fetchMock.mock.calls[0][0]).toBe('/api/auth/register');
  expect($('#auth-password').value).toBe('');
});

test('shows rejected login and network errors without exposing the workspace', async () => {
  const fetchMock = vi.fn().mockResolvedValueOnce(response({ error: 'Invalid email or password.' }, false))
    .mockRejectedValueOnce(new Error('Offline'));
  await startApp(fetchMock, false);
  await authenticate();
  expect($('#auth-error').textContent).toBe('Invalid email or password.');
  expect($('#workspace').hidden).toBe(true);
  expect($('#auth-email').value).toBe('learner@example.com');
  await authenticate();
  expect($('#auth-error').textContent).toBe('Offline');
});

test('expired JWT returns to login and removes the previous account data', async () => {
  const denied = { ...response({ error: 'Expired token.' }, false), status: 401 };
  const fetchMock = vi.fn().mockResolvedValueOnce(response(session)).mockResolvedValueOnce(denied);
  await startApp(fetchMock, false);
  await authenticate();
  expect($('#workspace').hidden).toBe(true);
  expect($('#auth-error').textContent).toBe('Session expired. Please log in again.');
});

test('prevents repeated login submissions while waiting', async () => {
  let resolve;
  const fetchMock = vi.fn().mockReturnValueOnce(new Promise((done) => { resolve = done; }))
    .mockResolvedValueOnce(response([]));
  await startApp(fetchMock, false);
  const pending = authenticate();
  $('#auth-form').dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
  expect(fetchMock).toHaveBeenCalledTimes(1);
  resolve(response(session));
  await pending;
});

test('ignores a database response that arrives after logout', async () => {
  let finish;
  const fetchMock = vi.fn().mockResolvedValueOnce(response(session))
    .mockReturnValueOnce(new Promise((done) => { finish = done; }));
  await startApp(fetchMock, false);
  const pending = authenticate();
  await vi.waitFor(() => expect($('#logout').hidden).toBe(false));
  $('#logout').click();
  finish(response([trip]));
  await pending;
  expect($('#trip-list').textContent).toBe('');
});
