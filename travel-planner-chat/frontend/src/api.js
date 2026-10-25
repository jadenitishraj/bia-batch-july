let accessToken = null;

export function setAccessToken(token) {
  accessToken = token;
}

export async function request(path, options = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (accessToken) {headers.Authorization = `Bearer ${accessToken}`;}
  const sentToken = accessToken;
  const response = await fetch(path, { ...options, headers });
  if (sentToken && sentToken !== accessToken) {throw new Error('Session changed. Please retry.');}
  const data = await response.json();
  if (!response.ok) {
    if (response.status === 401 && accessToken) {
      accessToken = null;
      window.dispatchEvent(new Event('auth-expired'));
    }
    throw new Error(data.error || 'Something went wrong. Please try again.');
  }
  return data;
}
