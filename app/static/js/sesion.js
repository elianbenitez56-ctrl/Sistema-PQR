// ── SESIÓN Y MENÚ DE USUARIO ─────────────────────────────────────────
var adminMode = false;
var loggedIn = false;
var currentUser = null;

function rolActual() { return currentUser ? currentUser.rol : null; }
function cargarDatosRecepcion() {
  if (!currentUser) return;

  var valores = {
    'f-recibe': currentUser.nombre || '',
    'f-doc-rec': currentUser.documento || '',
    'f-correo-rec': currentUser.correo || '',
    'f-tel-rec': currentUser.telefono ? fmtTel(currentUser.telefono) : '',
    'f-cargo': currentUser.cargo || '',
    'f-centro': currentUser.area || currentUser.linea_producto || ''
  };

  Object.keys(valores).forEach(function(id) {
    var campo = document.getElementById(id);
    if (campo) campo.value = valores[id];
  });
}

function rolPuede(rol, tipo) {
  if (tipo === 'seg') return rol === 'ADMIN' || rol === 'LIDER_CALIDAD' || rol === 'LIDER_COMERCIAL'
    || rol === 'COORDINADORA COMERCIAL' || rol === 'DIRECTORA COMERCIAL' || rol === 'COMERCIAL';
  if (tipo === 'us') return rol === 'ADMIN' || rol === 'LIDER_CALIDAD';
  if (tipo === 'dash' || tipo === 'bd') return rol === 'ADMIN' || rol === 'LIDER_CALIDAD' || rol === 'LIDER_COMERCIAL'
    || rol === 'COORDINADORA COMERCIAL' || rol === 'DIRECTORA COMERCIAL' || rol === 'COMERCIAL'
    || rol === 'DIRECTOR DE PRODUCCION';
  return false;
}

function renderUserMenu() {
  var nombre = currentUser ? currentUser.nombre : 'Usuario';
  var rol = currentUser ? currentUser.rol : null;
  var rolLabel = rol ? rol.replace(/_/g, ' ') : 'Usuario';
  var ini = currentUser
    ? currentUser.nombre.trim().split(/\s+/).map(function(x){ return x.charAt(0); }).join('').slice(0,2).toUpperCase()
    : 'US';
  var un = document.getElementById('user-name');
  if (un) un.textContent = nombre;
  var umn = document.getElementById('user-menu-name');
  if (umn) umn.textContent = nombre;
  var av = document.getElementById('user-avatar');
  if (av) av.textContent = ini;
  var uma = document.getElementById('user-menu-avatar');
  if (uma) uma.textContent = ini;
  var label = document.getElementById('user-role-label');
  if (label) label.textContent = rolLabel;
  var role = document.getElementById('menu-role');
  if (role) role.textContent = rolLabel;
  var badge = document.getElementById('admin-badge');
  if (badge) badge.style.display = adminMode ? '' : 'none';
  var items = { dash: rolPuede(rol,'dash'), bd: rolPuede(rol,'bd'), seg: rolPuede(rol,'seg'), us: rolPuede(rol,'us') };
  var ids = { dash: 'dash-item', bd: 'bd-item', seg: 'seg-item', us: 'us-item' };
  Object.keys(items).forEach(function(k) {
    var el = document.getElementById(ids[k]);
    if (el) el.style.display = items[k] ? '' : 'none';
  });
  var adm = document.getElementById('admin-section');
  if (adm) adm.style.display = (items.dash || items.bd || items.seg || items.us) ? '' : 'none';
}
function mostrarErrorLogin(msg) {
  var err = document.getElementById('login-err');
  if (!err) return;
  err.textContent = msg;
  setTimeout(function() { err.textContent = ''; }, 4000);
}
function loginUsuarios() {
  var u = document.getElementById('login-user').value.trim();
  var p = document.getElementById('login-pass').value;
  if (!u || !p) { mostrarErrorLogin('Ingrese usuario y contraseña.'); return; }
  var btn = document.getElementById('login-btn');
  if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spin" style="width:16px;height:16px;border-color:#fff transparent #fff transparent"></span> Validando...'; }
  fetch('/api/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ usuario: u, contrasena: p })
  })
  .then(function(r) { return r.json(); })
  .then(function(d) {
    if (btn) { btn.disabled = false; btn.innerHTML = '<span class="material-symbols-outlined" style="font-size:18px">login</span> INICIAR SESIÓN'; }
    if (!d.ok) { mostrarErrorLogin(d.mensaje || 'Credenciales incorrectas.'); return; }
    currentUser = d.usuario;
    adminMode = currentUser.rol === 'ADMIN';
    loggedIn = true;
    if (rolPuede(currentUser.rol, 'bd')) activarModulo('bd');
    if (rolPuede(currentUser.rol, 'dash')) activarModulo('dash');
    if (rolPuede(currentUser.rol, 'seg')) activarModulo('seg');
    if (rolPuede(currentUser.rol, 'us')) activarModulo('us');
    document.getElementById('login-screen').classList.add('hide');
    renderUserMenu();
    cargarDatosRecepcion();
     var btnNav = document.querySelector('.nav-item');
     if (btnNav) goTab('formulario', btnNav);
     abrirSeguimientoEnlazado();
     toast('Bienvenido, ' + currentUser.nombre, 'success');
  })
  .catch(function(err) {
    console.error(err);
    if (btn) { btn.disabled = false; btn.innerHTML = '<span class="material-symbols-outlined" style="font-size:18px">login</span> INICIAR SESIÓN'; }
    mostrarErrorLogin('Error de conexión con el servidor.');
  });
}
function logout() {
  fetch('/api/logout', { method: 'POST', cache: 'no-store' }).catch(function() {});
  if (adminMode) { adminMode = false; }
  cerrar('bd'); cerrar('seg'); cerrar('dash'); cerrar('us');
  currentUser = null;
  loggedIn = false;
  ['f-recibe','f-doc-rec','f-correo-rec','f-tel-rec','f-cargo','f-centro'].forEach(function(id) {
    var campo = document.getElementById(id);
    if (campo) campo.value = '';
  });
  renderUserMenu();
  document.getElementById('login-screen').classList.remove('hide');
  var lp = document.getElementById('login-pass');
  if (lp) lp.value = '';
  var lu = document.getElementById('login-user');
  if (lu) lu.value = '';
    toast('Sesión cerrada correctamente', 'info');
}

function abrirSeguimientoEnlazado() {
  var params = new URLSearchParams(window.location.search);
  var radicado = params.get('seguimiento');
  if (!radicado || !loggedIn || !currentUser || !rolPuede(currentUser.rol, 'seg')) return;
  var boton = document.getElementById('seg-item');
  var campo = document.getElementById('seg-q');
  if (!boton || !campo) return;
  campo.value = radicado;
  goTab('seguimiento', boton);
  cargarSeg();
}

function togglePass() {
  var inp = document.getElementById('login-pass');
  var icon = document.getElementById('pass-toggle-icon');
  if (!inp || !icon) return;
  var show = inp.type === 'password';
  inp.type = show ? 'text' : 'password';
  icon.textContent = show ? 'visibility_off' : 'visibility';
  inp.focus();
}
(function() {
  var btns = document.querySelectorAll('.btn-ripple');
  for (var i = 0; i < btns.length; i++) {
    btns[i].addEventListener('click', function(e) {
      var r = this.getBoundingClientRect();
      var d = Math.max(r.width, r.height);
      var ink = document.createElement('span');
      ink.className = 'ripple-ink';
      ink.style.width = ink.style.height = d + 'px';
      ink.style.left = (e.clientX - r.left - d / 2) + 'px';
      ink.style.top = (e.clientY - r.top - d / 2) + 'px';
      this.appendChild(ink);
      setTimeout(function() { ink.remove(); }, 600);
    });
  }
})();
function toggleUserMenu() {
  var m = document.getElementById('user-menu');
  var w = document.querySelector('.user-menu-wrap');
  if (!m) return;
  var open = m.classList.toggle('open');
  if (w) w.classList.toggle('open', open);
  var t = document.getElementById('user-menu-trigger');
  if (t) t.setAttribute('aria-expanded', open ? 'true' : 'false');
}
function closeUserMenu() {
  var m = document.getElementById('user-menu');
  var w = document.querySelector('.user-menu-wrap');
  if (m) m.classList.remove('open');
  if (w) w.classList.remove('open');
  var t = document.getElementById('user-menu-trigger');
  if (t) t.setAttribute('aria-expanded', 'false');
}
document.addEventListener('click', function(e) {
  var w = document.querySelector('.user-menu-wrap');
  if (w && !w.contains(e.target)) closeUserMenu();
});
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') closeUserMenu();
});

function openProfile() {
  var u = currentUser || { nombre: '—', usuario: '—', rol: '—', linea_producto: '', empresa: 'INAPEL' };
  var lineaLbl = u.linea_producto ? u.linea_producto : 'No aplica';
  oModal('Mi perfil',
    '<div class="form-grid">' +
    '<div class="field full"><label>Nombre</label><input type="text" value="' + u.nombre + '" disabled></div>' +
    '<div class="field"><label>Usuario</label><input type="text" value="' + u.usuario + '" disabled></div>' +
    '<div class="field"><label>Rol</label><input type="text" value="' + u.rol.replace(/_/g, ' ') + '" disabled></div>' +
    '<div class="field"><label>Línea de producto</label><input type="text" value="' + lineaLbl + '" disabled></div>' +
    '<div class="field"><label>Empresa</label><input type="text" value="' + u.empresa + '" disabled></div>' +
    '</div>' +
    '<div class="action-row" style="margin-top:18px">' +
    '<button class="btn btn-primary" onclick="cModal()">Cerrar</button>' +
    '</div>');
}
function cerrarSesion() {
  confirmar('Cerrar sesión', '¿Estás seguro de que deseas cerrar la sesión?', '🔒', logout);
}
renderUserMenu();

// Restaurar sesión activa al recargar la página
(function() {
  fetch('/api/sesion', { cache: 'no-store' })
  .then(function(r) { return r.json(); })
  .then(function(d) {
    if (!d.ok || !d.usuario) return;
    currentUser = d.usuario;
    adminMode = currentUser.rol === 'ADMIN';
    loggedIn = true;
    if (rolPuede(currentUser.rol, 'bd')) activarModulo('bd');
    if (rolPuede(currentUser.rol, 'dash')) activarModulo('dash');
    if (rolPuede(currentUser.rol, 'seg')) activarModulo('seg');
    if (rolPuede(currentUser.rol, 'us')) activarModulo('us');
    document.getElementById('login-screen').classList.add('hide');
    renderUserMenu();
    cargarDatosRecepcion();
    abrirSeguimientoEnlazado();
  })
  .catch(function() {});
})();

// ── AUTH ────────────────────────────────────────────────────────────────
function activarModulo(tipo) {
  if (tipo === 'bd') {
    bdAuth = true;
    document.getElementById('gate-bd').style.display = 'none';
    document.getElementById('con-bd').style.display = 'block';
    renderDB();
  } else if (tipo === 'dash') {
    dashAuth = true;
    document.getElementById('gate-dash').style.display = 'none';
    document.getElementById('con-dash').style.display = 'block';
    cargarDashboard();
    iniciarDashboardAuto();
  } else if (tipo === 'us') {
    usuAuth = true;
    document.getElementById('con-us').style.display = 'block';
  } else {
    segAuth = true;
    document.getElementById('gate-seg').style.display = 'none';
    document.getElementById('con-seg').style.display = 'block';
  }
}
function abrir(tipo) {
  activarModulo(tipo);
}
function cerrar(tipo) {
  if (tipo === 'bd') {
    bdAuth = false;
    document.getElementById('gate-bd').style.display = 'block';
    document.getElementById('con-bd').style.display = 'none';
    document.getElementById('p-bd').value = '';
  } else if (tipo === 'dash') {
    dashAuth = false;
    document.getElementById('gate-dash').style.display = 'block';
    document.getElementById('con-dash').style.display = 'none';
    document.getElementById('p-dash').value = '';
    if (dashboardInterval) { clearInterval(dashboardInterval); dashboardInterval = null; }
  } else if (tipo === 'us') {
    usuAuth = false;
    document.getElementById('con-us').style.display = 'none';
  } else {
    segAuth = false;
    document.getElementById('gate-seg').style.display = 'block';
    document.getElementById('con-seg').style.display = 'none';
    document.getElementById('seg-con').innerHTML = '';
    document.getElementById('p-seg').value = '';
  }
}
