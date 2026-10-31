import { $ } from './dom.js';
import { saveTrip } from './trip-api.js';

// The editor owns only its form; the workspace owns the trip list.
export function setupEditor(loadTrips, selectedTrip, isLoading) {
  let editingId = null;
  function openEditor(trip = null) {
    if (isLoading()) {
      return;
    }
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
  $('#first-trip').onclick = $('#new-trip').onclick;
  $('#edit').onclick = () => openEditor(selectedTrip());
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
      const trip = await saveTrip(values, editingId);
      $('#editor').close();
      await loadTrips(trip.id);
      $('#notice').textContent = 'Trip saved.';
    } catch (error) {
      $('#form-error').textContent = error.message;
    } finally {
      $('#save').disabled = false;
    }
  };

  return () => {
    editingId = null;
    $('#editor').close();
  };
}
