import pageHtml from '../index.html?raw';
import { vi } from 'vitest';

export const trip = { id: 1, title: 'Singapore escape', destination: 'Singapore',
  days: 4, travelers: 2, budget: 85000, plan: 'Day 1 — Arrive\nRelax.\n\nDay 2 — Gardens' };
export const $ = (selector) => document.querySelector(selector);
export const response = (data, ok = true) => ({ ok, json: async () => data });

export async function startApp(fetchMock = vi.fn().mockResolvedValue(response([])), signIn = true) {
  vi.resetModules();
  document.documentElement.innerHTML = pageHtml;
  // jsdom lacks native dialog behavior; all application events and DOM rendering stay real.
  HTMLDialogElement.prototype.showModal = function () { this.open = true; };
  HTMLDialogElement.prototype.close = function () { this.open = false; };
  const session = { access_token: 'test-jwt', user: { email: 'class@example.com' } };
  vi.stubGlobal('fetch', signIn ? (path, options) => path.startsWith('/api/auth/')
    ? Promise.resolve(response(session)) : fetchMock(path, options) : fetchMock);
  await import('../src/main.js');
  if (signIn) {
    $('#auth-email').value = 'class@example.com';
    $('#auth-password').value = 'class-test-password';
    $('#auth-form').dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
    await vi.waitFor(() => { if ($('#auth-submit').disabled) {throw new Error('Signing in');} });
  }
  await vi.waitFor(() => { if ($('#new-trip').disabled) {throw new Error('Still loading');} });
  return fetchMock;
}

export function fillTrip(values = trip) {
  for (const field of ['title', 'destination', 'days', 'travelers', 'budget', 'plan']) {
    $('#trip-form').elements[field].value = values[field];
  }
}

export async function submit() {
  $('#trip-form').dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
  await vi.waitFor(() => { if ($('#save').disabled) {throw new Error('Still saving');} });
}
