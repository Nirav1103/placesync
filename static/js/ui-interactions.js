/* =============================================================
   PlaceSync — Premium SaaS UI Interactions Engine
   3D Tilt · Count-Up Stats · Theme Switcher · Toast Engine
   Scroll Reveal · Ripple Buttons · Keyboard Shortcuts
   ============================================================= */

document.addEventListener('DOMContentLoaded', () => {
  init3DTiltEffect();
  initCountUpAnimation();
  initScrollReveal();
  initButtonRipples();
  initBackToTop();
  initKeyboardShortcuts();
  initToastEngine();
});

/* ─────────────── 2. 3D MOUSE HOVER TILT EFFECT ─────────────── */
function init3DTiltEffect() {
  const cards = document.querySelectorAll('.sp-card-hover, .sp-stat, .sp-badge-card');

  cards.forEach(card => {
    card.style.transformStyle = 'preserve-3d';
    card.style.transition = 'transform 0.15s ease-out, box-shadow 0.25s ease';

    card.addEventListener('mousemove', (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      const centerX = rect.width / 2;
      const centerY = rect.height / 2;

      const rotateX = ((y - centerY) / centerY) * -6; // max -6deg
      const rotateY = ((x - centerX) / centerX) * 6;  // max 6deg

      card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-4px) scale3d(1.015, 1.015, 1.015)`;
    });

    card.addEventListener('mouseleave', () => {
      card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0px) scale3d(1, 1, 1)';
    });
  });
}

/* ─────────────── 3. COUNT-UP STATISTICAL NUMBERS ─────────────── */
function initCountUpAnimation() {
  const statValues = document.querySelectorAll('.sp-stat-value, .sp-score-num');

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const el = entry.target;
        const text = el.innerText.trim();
        const numericMatch = text.match(/^([\D]*)(\d+(?:\.\d+)?)([\D]*)$/);

        if (numericMatch && !el.getAttribute('data-counted')) {
          el.setAttribute('data-counted', 'true');
          const prefix = numericMatch[1] || '';
          const targetValue = parseFloat(numericMatch[2]);
          const suffix = numericMatch[3] || '';

          const duration = 1200;
          const startTime = performance.now();

          function step(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const easeOutQuad = 1 - Math.pow(1 - progress, 3);
            const currentValue = (targetValue * easeOutQuad).toFixed(targetValue % 1 === 0 ? 0 : 1);

            el.innerText = `${prefix}${currentValue}${suffix}`;

            if (progress < 1) {
              requestAnimationFrame(step);
            } else {
              el.innerText = text; // Restore original exact formatting
            }
          }

          requestAnimationFrame(step);
        }
        observer.unobserve(el);
      }
    });
  }, { threshold: 0.2 });

  statValues.forEach(el => observer.observe(el));
}

/* ─────────────── 4. SCROLL REVEAL ANIMATIONS ─────────────── */
function initScrollReveal() {
  const revealElements = document.querySelectorAll('.sp-card, .sp-stat, .sp-welcome, .sp-assistant-box');

  revealElements.forEach(el => el.classList.add('reveal-on-scroll'));

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('revealed');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  revealElements.forEach(el => observer.observe(el));
}

/* ─────────────── 5. BUTTON RIPPLE EFFECT ─────────────── */
function initButtonRipples() {
  const buttons = document.querySelectorAll('.sp-btn');

  buttons.forEach(btn => {
    btn.addEventListener('click', function(e) {
      const rect = this.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      const ripple = document.createElement('span');
      ripple.classList.add('sp-btn-ripple');
      ripple.style.left = `${x}px`;
      ripple.style.top = `${y}px`;

      this.appendChild(ripple);

      setTimeout(() => {
        ripple.remove();
      }, 600);
    });
  });
}

/* ─────────────── 6. FLOATING BACK-TO-TOP BUTTON ─────────────── */
function initBackToTop() {
  const backToTopBtn = document.getElementById('sp-back-to-top');

  if (backToTopBtn) {
    window.addEventListener('scroll', () => {
      if (window.scrollY > 300) {
        backToTopBtn.classList.add('visible');
      } else {
        backToTopBtn.classList.remove('visible');
      }
    }, { passive: true });

    backToTopBtn.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }
}

/* ─────────────── 7. KEYBOARD SHORTCUTS (⌘K / Ctrl+K) ─────────────── */
function initKeyboardShortcuts() {
  const searchInput = document.querySelector('.sp-header-search input');

  document.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      if (searchInput) {
        searchInput.focus();
        searchInput.select();
      }
    } else if (e.key === 'Escape') {
      if (document.activeElement === searchInput) {
        searchInput.blur();
      }
    }
  });
}

/* ─────────────── 8. FLOATING TOAST NOTIFICATION ENGINE ─────────────── */
function initToastEngine() {
  window.showToast = function(message, type = 'info') {
    const container = document.getElementById('sp-toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `sp-toast sp-toast-${type}`;

    const icon = type === 'success' ? '✓' : type === 'error' ? '✕' : type === 'warning' ? '⚠️' : 'ℹ️';

    toast.innerHTML = `
      <span class="sp-toast-icon">${icon}</span>
      <span class="sp-toast-msg">${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
      toast.classList.add('show');
    }, 10);

    setTimeout(() => {
      toast.classList.remove('show');
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  };
}
