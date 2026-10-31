import { request } from './api.js';

// Trip URLs and HTTP methods live here, away from screen interactions.
const TRIPS_URL = '/api/trips';

export function listTrips() {
  return request(TRIPS_URL);
}

export function saveTrip(values, tripId) {
  const path = tripId ? `${TRIPS_URL}/${tripId}` : TRIPS_URL;
  return request(path, {
    method: tripId ? 'PUT' : 'POST',
    body: JSON.stringify(values),
  });
}

export function deleteTrip(tripId) {
  return request(`${TRIPS_URL}/${tripId}`, { method: 'DELETE' });
}
