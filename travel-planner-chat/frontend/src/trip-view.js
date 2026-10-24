const $ = (selector) => document.querySelector(selector);

export function renderTrips(trips, selectedId, onSelect) {
  $('#trip-list').replaceChildren();
  for (const trip of trips) {
    const button = document.createElement('button');
    button.className = 'trip-link';
    button.setAttribute('aria-current', String(trip.id === selectedId));
    const title = document.createElement('strong');
    title.textContent = trip.title;
    const summary = document.createElement('small');
    summary.textContent = `${trip.destination} · ${trip.days} days`;
    button.append(title, summary);
    button.onclick = () => onSelect(trip.id);
    $('#trip-list').append(button);
  }
  const trip = trips.find((item) => item.id === selectedId);
  $('#trip').hidden = !trip;
  $('#empty').hidden = Boolean(trip);
  $('#list-status').textContent = trips.length ? '' : 'No saved trips yet.';
  if (!trip) return;
  $('#trip-title').textContent = trip.title;
  $('#destination').textContent = trip.destination;
  $('#metadata').textContent = `${trip.days} days · ${trip.travelers} travelers · Estimated ₹${trip.budget.toLocaleString('en-IN')}`;
  $('#plan').textContent = trip.plan;
}

