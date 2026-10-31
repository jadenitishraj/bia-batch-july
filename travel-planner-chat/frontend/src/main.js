import './style.css';
import { listTrips, deleteTrip } from './trip-api.js';
import { $ } from './dom.js';
import { setupEditor } from './trip-editor.js';
import { renderTrips } from './trip-view.js';
import { setupAuth } from './auth.js';

let trips = [];
let selectedId = null;
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
    trips = await listTrips();
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

const resetEditor = setupEditor(loadTrips, () => trips.find((trip) => trip.id === selectedId),
  () => loading);
$('#retry').onclick = () => loadTrips();

$('#delete').onclick = () => {
  $('#delete-error').textContent = '';
  $('#delete-dialog').showModal();
};
$('#cancel-delete').onclick = () => $('#delete-dialog').close();
$('#confirm-delete').onclick = async () => {
  $('#confirm-delete').disabled = true;
  try {
    await deleteTrip(selectedId);
    $('#delete-dialog').close();
    await loadTrips(null);
    $('#notice').textContent = 'Trip deleted.';
  } catch (error) {
    $('#delete-error').textContent = error.message;
  } finally {
    $('#confirm-delete').disabled = false;
  }
};
setupAuth(() => loadTrips(null), () => {
  trips = [];
  selectedId = null;
  resetEditor();
  $('#notice').textContent = '';
  for (const id of ['#trip-title', '#destination', '#metadata', '#plan']) {$(id).textContent = '';}
  $('#delete-dialog').close();
  render();
});
