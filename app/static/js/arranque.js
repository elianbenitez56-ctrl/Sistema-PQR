// ── INIT ───────────────────────────────────────────────────────────────
(function() {
  var now = new Date();
  var opts = { weekday:'long', year:'numeric', month:'long', day:'numeric' };
  var el = document.getElementById('nav-date');
  if (el) el.textContent = now.toLocaleDateString('es-CO', opts);
  var bf = document.getElementById('ban-fecha');
  if (bf) bf.textContent = now.toLocaleDateString('es-CO', opts);
  var bh = document.getElementById('ban-hora');
  if (bh) bh.textContent = now.toLocaleTimeString('es-CO', {hour:'2-digit', minute:'2-digit'});
  var fd = document.getElementById('f-fecha');
  if (fd) fd.value = now.toLocaleDateString('en-CA'); // fecha local (no UTC) en formato AAAA-MM-DD
  var fh = document.getElementById('f-hora');
  if (fh) fh.value = now.toTimeString().slice(0, 5);
  actualizarUrgentes();
})();
