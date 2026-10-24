import pageHtml from '../index.html?raw';
import { vi } from 'vitest';

export const trip = { id: 1, title: 'Singapore escape', destination: 'Singapore',
  days: 4, travelers: 2, budget: 85000, plan: 'Day 1 — Arrive\nRelax.\n\nDay 2 — Gardens' };
export const $ = (selector) => document.querySelector(selector);
export const response = (data, ok = true) => ({ ok, json: async () => data });

export async function startApp(fetchMock = vi.fn().mockResolvedValue(response([]))) {
  vi.resetModules();
  document.documentElement.innerHTML = pageHtml;
  // jsdom lacks native dialog behavior; all application events and DOM rendering stay real.
  HTMLDialogElement.prototype.showModal = function () { this.open = true; };
  HTMLDialogElement.prototype.close = function () { this.open = false; };
  vi.stubGlobal('fetch', fetchMock);
  await import('../src/main.js');
  await vi.waitFor(() => { if ($('#new-trip').disabled) throw new Error('Still loading'); });
  return fetchMock;
}

export function fillTrip(values = trip) {
  for (const field of ['title', 'destination', 'days', 'travelers', 'budget', 'plan']) {
    $('#trip-form').elements[field].value = values[field];
  }
}

export async function submit() {
  $('#trip-form').dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
  await vi.waitFor(() => { if ($('#save').disabled) throw new Error('Still saving'); });
}
