import './style.css';
import { request } from './api.js';
import { renderTrips } from './trip-view.js';

const $ = (selector) => document.querySelector(selector);
let trips = [];
let selectedId = null;
let editingId = null;
let loading = false;


function render() {
  renderTrips(trips, selectedId, (id) => {
    selectedId = id;
    render();
    $('#main').focus();
  });
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
  if (loading) {return;}
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
  for (const field of ['days', 'travelers', 'budget']) {values[field] = Number(values[field]);}
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
