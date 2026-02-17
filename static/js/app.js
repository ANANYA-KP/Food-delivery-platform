/* ================================================
   Food Delivery Platform - Main JavaScript
   ================================================ */

const API = '/api/v1';

// ── TOKEN MANAGEMENT ──
const Auth = {
  getToken: () => localStorage.getItem('token'),
  getUser:  () => JSON.parse(localStorage.getItem('user') || 'null'),
  setAuth:  (token, user) => { localStorage.setItem('token', token); localStorage.setItem('user', JSON.stringify(user)); },
  clear:    () => { localStorage.removeItem('token'); localStorage.removeItem('user'); },
  isLoggedIn: () => !!localStorage.getItem('token'),
  headers:  () => ({ 'Content-Type': 'application/json', 'Authorization': `Bearer ${Auth.getToken()}` })
};

// ── API HELPER ──
async function api(method, path, body = null, auth = true) {
  const opts = { method, headers: auth ? Auth.headers() : { 'Content-Type': 'application/json' } };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(API + path, opts);
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Request failed');
  return data;
}

// ── TOAST ──
function toast(msg, type = 'info') {
  let c = document.getElementById('toast-container');
  if (!c) { c = document.createElement('div'); c.id = 'toast-container'; document.body.appendChild(c); }
  const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.innerHTML = `<span>${icons[type]||'ℹ️'}</span><span>${msg}</span>`;
  c.appendChild(t);
  setTimeout(() => { t.style.opacity = '0'; t.style.transform = 'translateX(60px)'; t.style.transition = '0.3s'; setTimeout(() => t.remove(), 300); }, 3000);
}

// ── CART ──
const Cart = {
  items: JSON.parse(localStorage.getItem('cart') || '[]'),
  restaurantId: localStorage.getItem('cart_restaurant') || null,
  restaurantName: localStorage.getItem('cart_restaurant_name') || '',

  save() {
    localStorage.setItem('cart', JSON.stringify(this.items));
    localStorage.setItem('cart_restaurant', this.restaurantId || '');
    localStorage.setItem('cart_restaurant_name', this.restaurantName || '');
    this.updateBadge();
    this.renderSidebar();
  },

  add(item, restaurantId, restaurantName) {
    if (this.restaurantId && this.restaurantId != restaurantId) {
      if (!confirm('Your cart has items from another restaurant. Clear and add new item?')) return;
      this.clear(false);
    }
    this.restaurantId = restaurantId;
    this.restaurantName = restaurantName;
    const existing = this.items.find(i => i.id === item.id);
    if (existing) existing.qty++;
    else this.items.push({ id: item.id, name: item.name, price: item.discount_price || item.price, qty: 1 });
    this.save();
    toast(`${item.name} added to cart 🛒`, 'success');
  },

  remove(itemId) {
    const idx = this.items.findIndex(i => i.id === itemId);
    if (idx === -1) return;
    if (this.items[idx].qty > 1) this.items[idx].qty--;
    else this.items.splice(idx, 1);
    if (!this.items.length) this.clear(false);
    this.save();
  },

  clear(notify = true) {
    this.items = []; this.restaurantId = null; this.restaurantName = '';
    localStorage.removeItem('cart'); localStorage.removeItem('cart_restaurant'); localStorage.removeItem('cart_restaurant_name');
    this.updateBadge(); this.renderSidebar();
    if (notify) toast('Cart cleared', 'info');
  },

  total() { return this.items.reduce((s, i) => s + i.price * i.qty, 0); },
  count() { return this.items.reduce((s, i) => s + i.qty, 0); },

  updateBadge() {
    const cnt = this.count();
    document.querySelectorAll('.cart-count').forEach(el => el.textContent = cnt);
    document.querySelectorAll('.cart-float').forEach(el => el.style.display = cnt ? 'flex' : 'none');
  },

  renderSidebar() {
    const sidebar = document.getElementById('cart-sidebar');
    if (!sidebar) return;
    const itemsEl = sidebar.querySelector('.cart-items');
    const footerEl = sidebar.querySelector('.cart-footer');
    if (!this.items.length) {
      itemsEl.innerHTML = `<div class="empty-state"><div class="empty-icon">🛒</div><h3>Your cart is empty</h3><p>Add items from a restaurant to get started</p></div>`;
      footerEl.innerHTML = '';
      return;
    }
    itemsEl.innerHTML = this.items.map(item => `
      <div class="cart-item">
        <div style="flex:1">
          <div style="font-weight:600;font-size:.9rem">${item.name}</div>
          <div style="color:var(--primary);font-weight:700">₹${(item.price * item.qty).toFixed(0)}</div>
        </div>
        <div class="qty-control">
          <button class="qty-btn" onclick="Cart.remove(${item.id}); Cart.renderSidebar()">−</button>
          <span class="qty-display">${item.qty}</span>
          <button class="qty-btn" onclick="Cart.add({id:${item.id},name:'${item.name.replace(/'/g,"\\'")}',price:${item.price}},${this.restaurantId},'')">+</button>
        </div>
      </div>`).join('');

    const sub = this.total();
    const tax = sub * 0.05;
    const del = 30;
    const total = sub + tax + del;
    footerEl.innerHTML = `
      <div class="cart-total-row"><span>Subtotal</span><span>₹${sub.toFixed(0)}</span></div>
      <div class="cart-total-row"><span>Tax (5%)</span><span>₹${tax.toFixed(0)}</span></div>
      <div class="cart-total-row"><span>Delivery</span><span>₹${del}</span></div>
      <div class="cart-total-row grand"><span>Total</span><span>₹${total.toFixed(0)}</span></div>
      <button class="btn btn-primary" style="width:100%;margin-top:14px;justify-content:center" onclick="goCheckout()">
        Place Order →
      </button>`;
  },

  openSidebar()  { document.getElementById('cart-sidebar')?.classList.add('open'); },
  closeSidebar() { document.getElementById('cart-sidebar')?.classList.remove('open'); }
};

function goCheckout() {
  if (!Auth.isLoggedIn()) { openModal('login-modal'); toast('Please login to place order', 'warning'); return; }
  Cart.closeSidebar();
  window.location.href = '/checkout';
}

// ── NAVBAR RENDER ──
function renderNavbar() {
  const user = Auth.getUser();
  const navBtns = document.getElementById('nav-btns');
  if (!navBtns) return;
  if (user) {
    navBtns.innerHTML = `
      <span style="font-size:.9rem;color:var(--muted)">Hi, <b>${user.full_name.split(' ')[0]}</b></span>
      ${user.role === 'admin' ? '<a href="/admin" class="btn btn-ghost btn-sm">🔧 Admin</a>' : ''}
      ${user.role === 'restaurant' ? '<a href="/restaurant" class="btn btn-ghost btn-sm">🍽️ Dashboard</a>' : ''}
      <a href="/orders" class="btn btn-ghost btn-sm">📦 Orders</a>
      <button onclick="logout()" class="btn btn-outline btn-sm">Logout</button>`;
  } else {
    navBtns.innerHTML = `
      <button onclick="openModal('login-modal')"  class="btn btn-outline btn-sm">Login</button>
      <button onclick="openModal('signup-modal')" class="btn btn-primary btn-sm">Sign Up</button>`;
  }
}

function logout() {
  Auth.clear(); Cart.clear(false);
  toast('Logged out successfully', 'info');
  setTimeout(() => window.location.href = '/', 800);
}

// ── MODALS ──
function openModal(id)  { document.getElementById(id)?.classList.add('open'); }
function closeModal(id) { document.getElementById(id)?.classList.remove('open'); }
document.addEventListener('click', e => {
  if (e.target.classList.contains('modal-overlay')) e.target.classList.remove('open');
});

// ── AUTH FORMS ──
async function handleLogin(e) {
  e.preventDefault();
  const btn = e.target.querySelector('button[type=submit]');
  btn.disabled = true; btn.textContent = 'Logging in...';
  try {
    const data = await api('POST', '/auth/login', {
      email_or_phone: document.getElementById('login-email').value,
      password: document.getElementById('login-password').value
    }, false);
    Auth.setAuth(data.access_token, data.user);
    closeModal('login-modal');
    toast(`Welcome back, ${data.user.full_name.split(' ')[0]}! 👋`, 'success');
    renderNavbar();
    setTimeout(() => location.reload(), 800);
  } catch(err) {
    toast(err.message, 'error');
  } finally { btn.disabled = false; btn.textContent = 'Login'; }
}

async function handleSignup(e) {
  e.preventDefault();
  const btn = e.target.querySelector('button[type=submit]');
  btn.disabled = true; btn.textContent = 'Creating account...';
  try {
    const data = await api('POST', '/auth/register', {
      email: document.getElementById('signup-email').value,
      password: document.getElementById('signup-password').value,
      full_name: document.getElementById('signup-name').value,
      role: document.getElementById('signup-role').value
    }, false);
    Auth.setAuth(data.access_token, data.user);
    closeModal('signup-modal');
    toast(`Account created! Welcome, ${data.user.full_name.split(' ')[0]}! 🎉`, 'success');
    renderNavbar();
    setTimeout(() => location.reload(), 800);
  } catch(err) {
    toast(err.message, 'error');
  } finally { btn.disabled = false; btn.textContent = 'Create Account'; }
}

// ── INIT ──
document.addEventListener('DOMContentLoaded', () => {
  renderNavbar();
  Cart.updateBadge();
  Cart.renderSidebar();
});
