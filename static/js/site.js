if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
if (window.location.hash === '#invitation') {
  history.replaceState(null, '', `${window.location.pathname}${window.location.search}`);
  window.scrollTo(0, 0);
} else if (!window.location.hash) {
  window.scrollTo(0, 0);
}

const revealItems = document.querySelectorAll('.reveal');
if ('IntersectionObserver' in window) {
  const observer = new IntersectionObserver((entries) => entries.forEach((entry) => {
    if (entry.isIntersecting) { entry.target.classList.add('is-visible'); observer.unobserve(entry.target); }
  }), { threshold: 0.12 });
  revealItems.forEach((item) => observer.observe(item));
} else revealItems.forEach((item) => item.classList.add('is-visible'));

document.querySelectorAll('.flash').forEach((message) => {
  window.setTimeout(() => {
    message.classList.add('is-dismissing');
    window.setTimeout(() => message.remove(), 500);
  }, 4000);
});

const fireflyField = document.querySelector('.fireflies');
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
if (fireflyField && !prefersReducedMotion) {
  for (let index = 0; index < 18; index += 1) {
    const firefly = document.createElement('i');
    firefly.className = 'firefly';
    firefly.style.left = `${8 + Math.random() * 84}%`;
    firefly.style.top = `${8 + Math.random() * 76}%`;
    firefly.style.setProperty('--x', `${-28 + Math.random() * 56}px`);
    firefly.style.setProperty('--y', `${-36 + Math.random() * 72}px`);
    firefly.style.setProperty('--drift', `${3.5 + Math.random() * 4}s`);
    firefly.style.animationDelay = `${Math.random() * -5}s`;
    fireflyField.appendChild(firefly);
  }
}

const hero = document.querySelector('.hero');
const parallaxItems = document.querySelectorAll('.hero-parallax');
if (hero && parallaxItems.length && !prefersReducedMotion) {
  hero.addEventListener('pointermove', (event) => {
    const x = (event.clientX / window.innerWidth - 0.5) * 10;
    const y = (event.clientY / window.innerHeight - 0.5) * 6;
    parallaxItems.forEach((item, index) => {
      const depth = index ? 0.45 : 1;
      item.style.transform = `translate(${x * depth}px, ${y * depth}px)`;
    });
  });
  hero.addEventListener('pointerleave', () => {
    parallaxItems.forEach((item) => { item.style.transform = ''; });
  });
}

const lightbox = document.querySelector('.lightbox');
const lightboxImage = lightbox?.querySelector('img');
const lightboxCaption = lightbox?.querySelector('figcaption');
const closeLightboxButton = lightbox?.querySelector('.lightbox-close');
let previouslyFocusedElement;

const closeLightbox = () => {
  if (!lightbox) return;
  lightbox.classList.remove('is-open');
  lightbox.setAttribute('aria-hidden', 'true');
  document.body.classList.remove('lightbox-open');
  if (previouslyFocusedElement) previouslyFocusedElement.focus();
};

document.querySelectorAll('.gallery-trigger').forEach((trigger) => {
  trigger.addEventListener('click', () => {
    if (!lightbox || !lightboxImage) return;
    previouslyFocusedElement = trigger;
    lightboxImage.src = trigger.dataset.lightboxSrc;
    lightboxImage.alt = trigger.dataset.lightboxAlt || '';
    lightboxCaption.textContent = trigger.dataset.lightboxAlt || '';
    lightbox.classList.add('is-open');
    lightbox.setAttribute('aria-hidden', 'false');
    document.body.classList.add('lightbox-open');
    closeLightboxButton?.focus();
  });
});

closeLightboxButton?.addEventListener('click', closeLightbox);
lightbox?.addEventListener('click', (event) => {
  if (event.target === lightbox) closeLightbox();
});
document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && lightbox?.classList.contains('is-open')) closeLightbox();
});

document.querySelectorAll('.court-scroll-toggle').forEach((toggle) => {
  toggle.addEventListener('click', () => {
    const scroll = toggle.closest('.court-scroll');
    const isOpen = scroll.classList.toggle('is-open');
    toggle.setAttribute('aria-expanded', String(isOpen));
  });
});