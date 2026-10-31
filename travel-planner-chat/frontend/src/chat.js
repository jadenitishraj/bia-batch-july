import { request } from './api.js';
import { $ } from './dom.js';

export function setupChat(refreshTrips) {
  let history = [];
  let session = 0;

  function addMessage(role, text) {
    const message = document.createElement('p');
    message.className = `chat-message ${role}`;
    message.textContent = text;
    $('#chat-messages').append(message);
    message.scrollIntoView?.({ block: 'nearest' });
  }

  $('#chat-toggle').onclick = () => {
    const open = $('#chat-panel').hidden;
    $('#chat-panel').hidden = !open;
    $('#chat-toggle').setAttribute('aria-expanded', String(open));
    if (open) {$('#chat-input').focus();}
  };
  $('#chat-close').onclick = () => {
    $('#chat-panel').hidden = true;
    $('#chat-toggle').setAttribute('aria-expanded', 'false');
    $('#chat-toggle').focus();
  };
  $('#chat-form').onsubmit = async (event) => {
    event.preventDefault();
    const message = $('#chat-input').value.trim();
    if (!message || $('#chat-send').disabled) {return;}
    const sentSession = session;
    $('#chat-send').disabled = true;
    $('#chat-error').textContent = '';
    addMessage('user', message);
    try {
      const data = await request('/api/chat', {
        method: 'POST', body: JSON.stringify({ message, history: history.slice(-12) }),
      });
      if (sentSession !== session) {return;}
      addMessage('assistant', data.reply);
      history.push({ role: 'user', content: message }, { role: 'assistant', content: data.reply });
      $('#chat-input').value = '';
    } catch (error) {
      if (sentSession === session) {$('#chat-error').textContent = error.message;}
    } finally {
      if (sentSession === session) {
        $('#chat-send').disabled = false;
        await refreshTrips();
      }
    }
  };
  return () => {
    session += 1;
    history = [];
    $('#chat-messages').replaceChildren();
    $('#chat-error').textContent = '';
    $('#chat-input').value = '';
    $('#chat-send').disabled = false;
    $('#chat-panel').hidden = true;
    $('#chat-toggle').setAttribute('aria-expanded', 'false');
  };
}
