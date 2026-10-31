import { request, setAccessToken } from './api.js';
import { $ } from './dom.js';

function showSession(user = null) {
  $('#auth-panel').hidden = Boolean(user);
  $('#workspace').hidden = !user;
  $('#new-trip').hidden = !user;
  $('#logout').hidden = !user;
  $('#account').textContent = user?.email ?? '';
}

export function setupAuth(onLogin, onLogout) {
  showSession();
  $('#auth-form').onsubmit = async (event) => {
    event.preventDefault();
    if ($('#auth-submit').disabled) {return;}
    $('#auth-submit').disabled = true;
    $('#auth-error').textContent = '';
    const values = Object.fromEntries(new FormData(event.currentTarget));
    const route = $('#register-account').checked ? 'register' : 'login';
    try {
      const session = await request(`/api/auth/${route}`, {
        method: 'POST', body: JSON.stringify(values),
      });
      setAccessToken(session.access_token);
      $('#auth-form').reset();
      showSession(session.user);
      await onLogin();
    } catch (error) {
      $('#auth-error').textContent = error.message;
    } finally {
      $('#auth-submit').disabled = false;
    }
  };
  $('#logout').onclick = () => {
    setAccessToken(null);
    showSession();
    onLogout();
    $('#auth-email').focus();
  };
  window.addEventListener('auth-expired', () => {
    $('#logout').click();
    $('#auth-error').textContent = 'Session expired. Please log in again.';
  });
}
