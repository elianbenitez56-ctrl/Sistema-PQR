// ── HERO CAROUSEL ─────────────────────────────────────────────────────────
(function(){
  var slides = document.querySelectorAll('#hero-form .hero-slide');
  var dots = document.getElementById('hero-dots');
  if (!slides.length || !dots) return;
  var idx = 0;
  function mostrar(i){
    slides.forEach(function(s){ s.classList.remove('on'); });
    dots.querySelectorAll('.hero-dot').forEach(function(d){ d.classList.remove('on'); });
    slides[i].classList.add('on');
    dots.children[i].classList.add('on');
    idx = i;
  }
  slides.forEach(function(_,i){
    var d = document.createElement('button');
    d.className = 'hero-dot' + (i===0?' on':'');
    d.setAttribute('aria-label','Imagen '+(i+1));
    d.addEventListener('click',function(){ mostrar(i); });
    dots.appendChild(d);
  });
  setInterval(function(){
    mostrar((idx+1) % slides.length);
  },5000);
})();

// ── SIDEBAR TOGGLE ─────────────────────────────────────────────────────
function toggleSidebar() {
  var s = document.getElementById('sidebar');
  var o = document.getElementById('sidebar-overlay');
  var h = document.getElementById('hamburger');
  var isOpen = s.classList.toggle('open');
  o.classList.toggle('open', isOpen);
  h.classList.toggle('open', isOpen);
  h.setAttribute('aria-label', isOpen ? 'Cerrar menú' : 'Abrir menú');
  document.body.style.overflow = isOpen && window.innerWidth <= 600 ? 'hidden' : '';
}
function closeSidebar() {
  var s = document.getElementById('sidebar');
  var o = document.getElementById('sidebar-overlay');
  var h = document.getElementById('hamburger');
  s.classList.remove('open');
  o.classList.remove('open');
  h.classList.remove('open');
  h.setAttribute('aria-label', 'Abrir menú');
  document.body.style.overflow = '';
}
