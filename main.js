/**
 * NexStock — main.js
 * Blue Ocean Design System
 */
document.addEventListener('DOMContentLoaded', function () {

  // 1. LIVE CLOCK
  const clock = document.getElementById('topbarClock');
  function tick() {
    if (!clock) return;
    const n = new Date();
    clock.textContent = n.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }
  tick(); setInterval(tick, 1000);

  // 2. SIDEBAR TOGGLE
  window.toggleSidebar = function () {
    const sb = document.getElementById('sidebar');
    const ov = document.getElementById('sidebarOverlay');
    const open = sb.classList.toggle('open');
    ov.classList.toggle('open', open);
    document.body.style.overflow = open ? 'hidden' : '';
  };
  window.closeSidebar = function () {
    document.getElementById('sidebar').classList.remove('open');
    document.getElementById('sidebarOverlay').classList.remove('open');
    document.body.style.overflow = '';
  };

  // 3. MODAL HELPERS (global)
  window.openModal = function (id) {
    document.getElementById(id).classList.add('open');
    document.body.style.overflow = 'hidden';
  };
  window.closeModal = function (id) {
    document.getElementById(id).classList.remove('open');
    document.body.style.overflow = '';
  };
  // Close on backdrop click
  document.querySelectorAll('.modal-bg').forEach(function (el) {
    el.addEventListener('click', function (e) { if (e.target === el) closeModal(el.id); });
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') document.querySelectorAll('.modal-bg.open').forEach(m => closeModal(m.id));
  });

  // 4. AUTO-DISMISS ALERTS (4.5s)
  document.querySelectorAll('.ns-alert').forEach(function (el) {
    setTimeout(function () {
      el.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
      el.style.opacity = '0'; el.style.transform = 'translateX(-8px)';
      setTimeout(() => el.remove(), 400);
    }, 4500);
  });

  // 5. COUNTER ANIMATION (KPI)
  document.querySelectorAll('.counter[data-target]').forEach(function (el) {
    const t = parseInt(el.getAttribute('data-target'), 10);
    if (isNaN(t) || t === 0) { el.textContent = '0'; return; }
    let c = 0; const step = t / (650 / 16);
    const timer = setInterval(function () {
      c = Math.min(c + step, t);
      el.textContent = Math.floor(c);
      if (c >= t) clearInterval(timer);
    }, 16);
  });

  // 6. PROGRESS BARS ANIMATE
  document.querySelectorAll('.prog-bar[data-w]').forEach(function (bar) {
    setTimeout(function () { bar.style.width = bar.getAttribute('data-w'); }, 500);
  });

  // 7. TABLE ROW STAGGER
  document.querySelectorAll('.ns-table tbody tr').forEach(function (row, i) {
    row.style.opacity = '0'; row.style.transform = 'translateY(6px)';
    row.style.transition = 'opacity 0.2s ease, transform 0.2s ease';
    setTimeout(function () { row.style.opacity = '1'; row.style.transform = 'translateY(0)'; }, 40 + i * 30);
  });

  // 8. KPI CARD STAGGER
  document.querySelectorAll('.kpi-card').forEach(function (card, i) {
    card.style.opacity = '0'; card.style.transform = 'translateY(14px)';
    card.style.transition = 'opacity 0.3s ease, transform 0.3s ease, box-shadow 0.22s ease';
    setTimeout(function () { card.style.opacity = '1'; card.style.transform = 'translateY(0)'; }, 60 + i * 70);
  });

  // 9. CAT CARD STAGGER
  document.querySelectorAll('.cat-card').forEach(function (card, i) {
    card.style.opacity = '0'; card.style.transform = 'translateY(16px)';
    card.style.transition = 'opacity 0.3s ease, transform 0.3s ease, box-shadow 0.22s, border-color 0.22s';
    setTimeout(function () { card.style.opacity = '1'; card.style.transform = 'translateY(0)'; }, 80 + i * 60);
  });

  // 10. SEARCH HIGHLIGHT
  const q = new URLSearchParams(window.location.search).get('search');
  if (q && q.trim()) {
    const rx = new RegExp(`(${q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    document.querySelectorAll('.prod-name').forEach(function (el) {
      el.innerHTML = el.textContent.replace(rx,
        '<mark style="background:rgba(136,189,242,0.35);color:var(--navy-dark);border-radius:3px;padding:0 2px;">$1</mark>'
      );
    });
  }

  // 11. STOCK OUT MAX VALIDATE
  const sForm = document.getElementById('stockForm');
  if (sForm) {
    sForm.addEventListener('submit', function (e) {
      const inp = document.getElementById('stockMqty');
      if (!inp) return;
      const mx = parseInt(inp.max, 10), v = parseInt(inp.value, 10);
      if (!isNaN(mx) && v > mx) {
        e.preventDefault();
        inp.style.borderColor = 'var(--danger)';
        inp.style.boxShadow = '0 0 0 3px rgba(224,92,110,0.2)';
        inp.animate([
          { transform: 'translateX(-4px)' }, { transform: 'translateX(4px)' },
          { transform: 'translateX(-3px)' }, { transform: 'translateX(0)' }
        ], { duration: 280 });
        setTimeout(() => { inp.style.borderColor = ''; inp.style.boxShadow = ''; }, 1500);
      }
    });
  }

});
