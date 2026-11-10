export async function showStatus(element, request = fetch) {
  try {
    const response = await request('/api/status');
    if (!response.ok) throw new Error('Status request failed');
    const data = await response.json();
    element.textContent = data.status;
  } catch {
    element.textContent = 'Status unavailable';
  }
}

if (typeof document !== 'undefined') {
  showStatus(document.querySelector('#status'));
}
