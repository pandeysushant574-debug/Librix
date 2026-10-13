/* ============================================================
   auth.js — login.html logic only
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('login-form');
  const errorEl = document.getElementById('login-error');
  const submitBtn = document.getElementById('login-submit');

  // If already logged in, skip straight to the dashboard.
  Api.get('/auth/me').then(() => { window.pageGo('dashboard.html'); }).catch(() => {});

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    errorEl.textContent = '';
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;

    if (!username || !password) {
      errorEl.textContent = 'Please enter both username and password.';
      return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = 'Signing in…';
    try {
      await Api.post('/auth/login', { username, password });
      window.pageGo('dashboard.html');
    } catch (err) {
      errorEl.textContent = err.message || 'Login failed.';
      submitBtn.disabled = false;
      submitBtn.textContent = 'Sign In';
    }
  });
});
