// EarningsBloom — Frontend JS

// ── Copy to clipboard utility ─────────────────────────────
function copyText(text, btn) {
  navigator.clipboard.writeText(text).then(() => {
    const orig = btn.textContent;
    btn.textContent = '✓ Copied!';
    btn.style.color = 'var(--accent)';
    setTimeout(() => { btn.textContent = orig; btn.style.color = ''; }, 2000);
  });
}

// ── Fade-in on scroll ─────────────────────────────────────
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.style.opacity = '1';
      entry.target.style.transform = 'translateY(0)';
    }
  });
}, { threshold: 0.08 });

document.querySelectorAll('.fade-in').forEach(el => {
  el.style.opacity = '0';
  el.style.transform = 'translateY(16px)';
  el.style.transition = 'opacity .45s ease, transform .45s ease';
  observer.observe(el);
});

// ── Navbar search — submit on Enter ───────────────────────
const navSearchInput = document.querySelector('.nav-search input');
if (navSearchInput) {
  navSearchInput.addEventListener('keydown', e => {
    if (e.key === 'Enter') {
      window.location.href = '/search?q=' + encodeURIComponent(navSearchInput.value.trim());
    }
  });
}

// ── Highlight active nav link ─────────────────────────────
document.querySelectorAll('.nav-link').forEach(link => {
  if (link.href === window.location.href) link.classList.add('active');
});
