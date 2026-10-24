import { afterEach, expect, test, vi } from 'vitest';
import { $, fillTrip, response, startApp, submit, trip } from './helpers.js';
import { request } from '../src/api.js';

afterEach(() => vi.unstubAllGlobals());

test('shows a load error and recovers through Retry', async () => {
  const fetchMock = vi.fn().mockRejectedValueOnce(new Error('Offline'))
    .mockResolvedValueOnce(response([trip]));
  await startApp(fetchMock);
  expect($('#list-status').textContent).toBe('Could not load trips.');
  expect($('#retry').hidden).toBe(false);
  $('#retry').click();
  await vi.waitFor(() => expect($('#trip-title').textContent).toBe(trip.title));
  expect($('#retry').hidden).toBe(true);
});

test('preserves entered values and shows server validation errors on failed save', async () => {
  await startApp(vi.fn().mockResolvedValueOnce(response([]))
    .mockResolvedValueOnce(response({ error: 'Title is required.' }, false)));
  $('#new-trip').click();
  fillTrip();
  await submit();
  expect($('#editor').open).toBe(true);
  expect($('#form-error').textContent).toBe('Title is required.');
  expect($('#trip-form').elements.plan.value).toBe(trip.plan);
  expect($('#save').disabled).toBe(false);
  $('#cancel-editor').click();
  expect($('#editor').open).toBe(false);
});

test('keeps a plan visible when deleting fails and allows retry', async () => {
  await startApp(vi.fn().mockResolvedValueOnce(response([trip]))
    .mockResolvedValueOnce(response({ error: 'Database unavailable.' }, false)));
  $('#delete').click();
  $('#confirm-delete').click();
  await vi.waitFor(() => expect($('#delete-error').textContent).toBe('Database unavailable.'));
  expect($('#delete-dialog').open).toBe(true);
  expect($('#trip-title').textContent).toBe(trip.title);
  expect($('#confirm-delete').disabled).toBe(false);
});

test('disables Save while a request is pending and supports closing an editor', async () => {
  let finish;
  const pending = new Promise((resolve) => { finish = resolve; });
  const fetchMock = vi.fn().mockResolvedValueOnce(response([]))
    .mockReturnValueOnce(pending).mockResolvedValueOnce(response([trip]));
  await startApp(fetchMock);
  $('#new-trip').click();
  $('#close-editor').click();
  expect($('#editor').open).toBe(false);
  $('#new-trip').click();
  fillTrip();
  $('#trip-form').dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
  expect($('#save').disabled).toBe(true);
  finish(response(trip));
  await vi.waitFor(() => expect($('#save').disabled).toBe(false));
});

test('API helper reports a useful fallback when the error has no message', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response({}, false)));
  await expect(request('/api/trips')).rejects.toThrow('Something went wrong. Please try again.');
});
