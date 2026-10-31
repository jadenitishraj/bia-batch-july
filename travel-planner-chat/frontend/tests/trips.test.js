import { afterEach, expect, test, vi } from 'vitest';
import { $, fillTrip, response, startApp, submit, trip } from './helpers.js';

afterEach(() => vi.unstubAllGlobals());

test('shows empty state and loads saved plans with selectable accessible buttons', async () => {
  await startApp();
  expect($('#empty').hidden).toBe(false);
  expect($('#list-status').textContent).toBe('No saved trips yet.');
  const other = { ...trip, id: 2, title: 'Japan spring', destination: 'Tokyo' };
  await startApp(vi.fn().mockResolvedValue(response([trip, other])));
  expect($('#trip-title').textContent).toBe(trip.title);
  const buttons = document.querySelectorAll('.trip-link');
  expect(buttons[0].getAttribute('aria-current')).toBe('true');
  buttons[1].click();
  expect($('#trip-title').textContent).toBe('Japan spring');
  expect(buttons[1].textContent).toContain('Tokyo');
  expect(document.activeElement).toBe($('#main'));
});

test('creates a plan with numeric fields and renders the saved server result', async () => {
  const fetchMock = vi.fn().mockResolvedValueOnce(response([]))
    .mockResolvedValueOnce(response(trip)).mockResolvedValueOnce(response([trip]));
  await startApp(fetchMock);
  $('#first-trip').click();
  expect($('#editor').open).toBe(true);
  fillTrip();
  await submit();
  const [url, options] = fetchMock.mock.calls[1];
  expect(url).toBe('/api/trips');
  expect(options.method).toBe('POST');
  expect(JSON.parse(options.body)).toMatchObject({ days: 4, travelers: 2, budget: 85000 });
  expect($('#editor').open).toBe(false);
  expect($('#plan').textContent).toBe(trip.plan);
  expect($('#metadata').textContent).toContain('85,000');
});

test('opens an existing plan for editing and sends an update to the correct record', async () => {
  const updated = { ...trip, title: 'Updated title', plan: 'Day 1 — A different plan' };
  const fetchMock = vi.fn().mockResolvedValueOnce(response([trip]))
    .mockResolvedValueOnce(response(updated)).mockResolvedValueOnce(response([updated]));
  await startApp(fetchMock);
  $('#edit').click();
  expect($('#trip-form').elements.title.value).toBe(trip.title);
  fillTrip(updated);
  await submit();
  expect(fetchMock.mock.calls[1][0]).toBe('/api/trips/1');
  expect(fetchMock.mock.calls[1][1].method).toBe('PUT');
  expect($('#trip-title').textContent).toBe('Updated title');
});

test('requires confirmation, supports cancel, and deletes only the selected trip', async () => {
  const fetchMock = vi.fn().mockResolvedValueOnce(response([trip]))
    .mockResolvedValueOnce(response({ deleted: true })).mockResolvedValueOnce(response([]));
  await startApp(fetchMock);
  $('#delete').click();
  $('#cancel-delete').click();
  expect(fetchMock).toHaveBeenCalledTimes(1);
  $('#delete').click();
  $('#confirm-delete').click();
  await vi.waitFor(() => expect($('#delete-dialog').open).toBe(false));
  expect(fetchMock.mock.calls[1][1].method).toBe('DELETE');
  expect($('#empty').hidden).toBe(false);
});

test('renders HTML-like input as text instead of executable markup', async () => {
  const unsafe = { ...trip, title: '<script>alert(1)</script>', plan: '<img src=x onerror=alert(1)>' };
  await startApp(vi.fn().mockResolvedValue(response([unsafe])));
  expect($('#trip-title').textContent).toBe(unsafe.title);
  expect($('#plan').querySelector('img')).toBeNull();
  expect($('#trip-list').querySelector('script')).toBeNull();
});

test('creating after cancelling an edit never overwrites the previously selected trip', async () => {
  const created = { ...trip, id: 2, title: 'A second trip' };
  const fetchMock = vi.fn().mockResolvedValueOnce(response([trip]))
    .mockResolvedValueOnce(response(created)).mockResolvedValueOnce(response([created, trip]));
  await startApp(fetchMock);
  $('#edit').click();
  $('#cancel-editor').click();
  $('#new-trip').click();
  expect($('#editor-title').textContent).toBe('Create a trip');
  expect($('#trip-form').elements.title.value).toBe('');
  fillTrip(created);
  await submit();
  expect(fetchMock.mock.calls[1][0]).toBe('/api/trips');
  expect(fetchMock.mock.calls[1][1].method).toBe('POST');
  expect($('#trip-title').textContent).toBe(created.title);
});
