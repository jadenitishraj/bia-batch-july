const $ = (selector) => document.querySelector(selector);
let trips = [];
let selectedId = null;
let editingId = null;
let loading = false;

async function request(path, options = {}) {
  const response = await fetch(path, { ...options, headers: { 'Content-Type': 'application/json' } });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Something went wrong. Please try again.');
  return data;
}

function render() {
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
    button.onclick = () => { selectedId = trip.id; render(); $('#main').focus(); };
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

async function loadTrips(preferredId = selectedId) {
  loading = true;
  $('#new-trip').disabled = true;
  $('#first-trip').disabled = true;
  $('#list-status').textContent = 'Loading trips…';
  $('#retry').hidden = true;
  try {
    trips = await request('/api/trips');
    selectedId = trips.some((trip) => trip.id === preferredId) ? preferredId : trips[0]?.id;
    render();
  } catch {
    $('#list-status').textContent = 'Could not load trips.';
    $('#retry').hidden = false;
  } finally {
    loading = false;
    $('#new-trip').disabled = false;
    $('#first-trip').disabled = false;
  }
}

function openEditor(trip = null) {
  if (loading) return;
  editingId = trip?.id ?? null;
  $('#trip-form').reset();
  $('#form-error').textContent = '';
  $('#editor-title').textContent = trip ? 'Edit trip' : 'Create a trip';
  if (trip) {
    for (const field of ['title', 'destination', 'days', 'travelers', 'budget', 'plan']) {
      $('#trip-form').elements[field].value = trip[field];
    }
  }
  $('#editor').showModal();
}

$('#new-trip').onclick = () => openEditor();
$('#first-trip').onclick = () => openEditor();
$('#retry').onclick = () => loadTrips();
$('#edit').onclick = () => openEditor(trips.find((trip) => trip.id === selectedId));
for (const id of ['#close-editor', '#cancel-editor']) {
  $(id).onclick = () => $('#editor').close();
}

$('#trip-form').onsubmit = async (event) => {
  event.preventDefault();
  const values = Object.fromEntries(new FormData(event.currentTarget));
  for (const field of ['days', 'travelers', 'budget']) values[field] = Number(values[field]);
  $('#save').disabled = true;
  $('#form-error').textContent = '';
  try {
    const trip = await request(editingId ? `/api/trips/${editingId}` : '/api/trips', {
      method: editingId ? 'PUT' : 'POST', body: JSON.stringify(values),
    });
    $('#editor').close();
    await loadTrips(trip.id);
    $('#notice').textContent = 'Trip saved.';
  } catch (error) {
    $('#form-error').textContent = error.message;
  } finally {
    $('#save').disabled = false;
  }
};

$('#delete').onclick = () => {
  $('#delete-error').textContent = '';
  $('#delete-dialog').showModal();
};
$('#cancel-delete').onclick = () => $('#delete-dialog').close();
$('#confirm-delete').onclick = async () => {
  $('#confirm-delete').disabled = true;
  try {
    await request(`/api/trips/${selectedId}`, { method: 'DELETE' });
    $('#delete-dialog').close();
    await loadTrips(null);
    $('#notice').textContent = 'Trip deleted.';
  } catch (error) {
    $('#delete-error').textContent = error.message;
  } finally {
    $('#confirm-delete').disabled = false;
  }
};
loadTrips();
