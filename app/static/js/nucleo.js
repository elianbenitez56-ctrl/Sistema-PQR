// ── CONSTANTS ─────────────────────────────────────────────────────────
var STORE_KEY = 'inapel_pqr_v4';
var db = [];
var seguimientoActual = null;
var bdAuth = false;
var segAuth = false;
var dashAuth = false;
var usuAuth = false;
var editRad = null;
var SEARCH_KEY = 'inapel_search_v1';
var dashboardInterval = null;
var chartEstados = null;
var chartTipos = null;

function cargarDatos() {
  try { db = JSON.parse(localStorage.getItem(STORE_KEY) || '[]'); } catch(e) { db = []; }
}
function guardarDatos() {
  try {
    localStorage.setItem(STORE_KEY, JSON.stringify(db));
  } catch (e) {
    // La PQR ya se guarda en el servidor; localStorage es solo persistencia auxiliar.
    console.warn('No fue posible actualizar el almacenamiento local:', e);
  }
  actualizarUrgentes();
  document.dispatchEvent(new Event('dbUpdated'));
}
cargarDatos();

// ── NAVEGACIÓN ──────────────────────────────────────────────────────────
function goTab(name, btn) {
  var rol = rolActual();
  var modTipo = name === 'basedatos' ? 'bd' : name === 'seguimiento' ? 'seg' : name === 'dashboard' ? 'dash' : name === 'usuarios' ? 'us' : null;
  if (modTipo && !rolPuede(rol, modTipo)) {
    toast('No tiene permisos para acceder a esta sección.', 'error');
    return;
  }
  var prev = document.querySelector('.panel.on');
  if (prev && prev.id === 'panel-consultar' && name !== 'consultar') resetConsulta();
  document.querySelectorAll('.panel').forEach(function(p){ p.classList.remove('on'); });
  document.querySelectorAll('.nav-item').forEach(function(b){ b.classList.remove('on'); });
  document.getElementById('panel-' + name).classList.add('on');
  btn.classList.add('on');
  var titles = { formulario:'Nuevo PQR', consultar:'Consultar', basedatos:'Base de datos', seguimiento:'Seguimiento', dashboard:'Dashboard', usuarios:'Gestión de usuarios' };
  var sub = document.getElementById('page-title-sub');
  if (sub) sub.textContent = titles[name] || 'Sistema de Gestión PQR';
  if (name === 'basedatos' && bdAuth) renderDB();
  if (name === 'formulario' && loggedIn) cargarDatosRecepcion();
  if (name === 'usuarios' && usuAuth) setTimeout(renderUsuarios, 50);
  if (name === 'dashboard' && dashAuth) {
    setTimeout(function(){ cargarDashboard(); iniciarDashboardAuto(); }, 200);
  }
  var ev = null;
  try {
    ev = new CustomEvent('sectionchange', { detail: { from: prev ? prev.id.replace('panel-', '') : null, to: name } });
  } catch (e) { ev = null; }
  if (ev) document.dispatchEvent(ev);
  if (name === 'consultar') resetConsulta();
  if (window.innerWidth <= 600) closeSidebar();
}

// ── HELPERS ────────────────────────────────────────────────────────────
function tog(selId, val, wrapId) {
  document.getElementById(wrapId).style.display =
    document.getElementById(selId).value === val ? 'block' : 'none';
}
function dias(fecha) {
  if (!fecha) return 0;
  var f = new Date(fecha);
  if (isNaN(f.getTime())) {
    var partes = fecha.split("/");
    if (partes.length === 3) f = new Date(partes[2], partes[1] - 1, partes[0]);
  }
  return Math.floor((new Date() - f) / 86400000);
}
function priCls(p) {
  return p === 'Alta' ? 'badge bp-alt' : p === 'Media' ? 'badge bp-med' : p === 'Baja' ? 'badge bp-baj' : '';
}
function msg(id, html, tipo) {
  var el = document.getElementById(id);
  if (!el) return;
  el.innerHTML = '<div class="alert alert-' + tipo + '" style="margin-top:10px">' + html + '</div>';
  if (tipo === 'success') setTimeout(function() { el.innerHTML = ''; }, 6000);
}

// ── TOAST ────────────────────────────────────────────────────────────────
function toast(html, tipo, duracion) {
  tipo = tipo || 'success';
  duracion = duracion || 4000;
  var c = document.getElementById('toast-container');
  var t = document.createElement('div');
  t.className = 'toast ' + tipo;
  t.setAttribute('role', 'alert');
  var ico = tipo === 'success' ? '&#10003;' : tipo === 'error' ? '&#9888;' : '&#8505;';
  t.innerHTML = '<span style="font-size:16px;flex-shrink:0;margin-top:1px">' + ico + '</span><span>' + html + '</span>';
  c.appendChild(t);
  setTimeout(function() {
    t.classList.add('toast-out');
    setTimeout(function() { t.remove(); }, 300);
  }, duracion);
}

// ── CONFIRM ──────────────────────────────────────────────────────────────
var _confirmCb = null;
function confirmar(title, msg, icono, cb) {
  document.getElementById('confirm-title').textContent = title;
  document.getElementById('confirm-msg').textContent = msg;
  document.getElementById('confirm-icon').textContent = icono || '&#9888;';
  document.getElementById('confirm-modal').classList.add('open');
  _confirmCb = cb;
}
function cConfirm() {
  document.getElementById('confirm-modal').classList.remove('open');
  _confirmCb = null;
}
document.getElementById('confirm-yes').addEventListener('click', function() {
  var cb = _confirmCb;
  cConfirm();
  if (cb) cb();
});

// ── LOADING ──────────────────────────────────────────────────────────────
function loadBtn(btn, loading) {
  if (loading) {
    btn._txt = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spin"></span> Cargando...';
  } else {
    btn.disabled = false;
    if (btn._txt) btn.innerHTML = btn._txt;
  }
}

// ── MODAL ───────────────────────────────────────────────────────────────
function oModal(title, html) {
  document.getElementById('m-title').textContent = title;
  document.getElementById('m-body').innerHTML = html;
  document.getElementById('modal').classList.add('open');
}
function cModal() { document.getElementById('modal').classList.remove('open'); }

function mEstado(rad) {
  editRad = rad;
  var p = (dbExcel !== null ? dbExcel : db).filter(function(x) { return x.radicado === rad; })[0];
  var opts = ['Recibido','Radicado','En revisión','En investigación','Pendiente de información','Pendiente de decisión','Acción en proceso','Respuesta enviada','Cerrado','No procede'];
  var sel = opts.map(function(o) { return '<option' + (p && p.estado === o ? ' selected' : '') + '>' + o + '</option>'; }).join('');
  oModal('Cambiar estado · ' + rad,
    '<div style="margin-bottom:14px"><div style="font-size:11px;color:var(--on-surface-variant);margin-bottom:3px">Cliente</div>' +
    '<div style="font-size:14px;font-weight:500">' + (p ? p.cliente : '—') + '</div></div>' +
    '<div class="field" style="margin-bottom:18px"><label>Nuevo estado</label><select id="m-est">' + sel + '</select></div>' +
    '<div style="display:flex;gap:9px;justify-content:flex-end">' +
    '<button class="btn" onclick="cModal()">Cancelar</button>' +
    '<button class="btn btn-primary" onclick="aplicarEst()">✓ Guardar cambio</button></div>');
}

function aplicarEst() {
  var nuevoEstado = document.getElementById('m-est').value;
  confirmar("Cambiar estado", "¿Estás seguro de cambiar el estado a «" + nuevoEstado + "»?", "🔄", function() {
    fetch("/api/cambiar_estado", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ radicado: editRad, estado: nuevoEstado }) })
    .then(function(r) { return r.json(); })
    .then(function(res) {
      if (!res.ok) { toast(res.mensaje || "Error al actualizar el estado", "error"); return; }
      var p = db.filter(function(x) { return x.radicado === editRad; })[0];
      if (p) {
        p.estado = nuevoEstado;
        if (!p.historial) p.historial = [];
        p.historial.push({ estado: nuevoEstado, fecha: new Date().toISOString() });
        guardarDatos();
      }
      if (dbExcel) {
        var x = dbExcel.filter(function(v) { return v.radicado === editRad; })[0];
        if (x) x.estado = nuevoEstado;
      }
      renderDB();
      cModal();
      toast("Estado actualizado a «" + nuevoEstado + "»", "success");
    })
    .catch(function(err) { console.error(err); toast("Error al actualizar el estado", "error"); });
  });
}

function mDetalle(rad) {
  var p = (dbExcel !== null ? dbExcel : db).filter(function(x) { return x.radicado === rad; })[0];
  if (!p) return;
  var d = dias(p.savedAt);
  var states = ['Recibido','Radicado','En revisión','En investigación','Acción en proceso','Respuesta enviada','Cerrado'];
  var idx = Math.max(states.indexOf(p.estado), 0);
  var pct = Math.round((idx + 1) / states.length * 100);
   var prods = p.productos && p.productos.length
     ? p.productos.map(function(x) {
          var referencia = x.referencia_siesa || x.referencia || x.ref || '—';
          var nombreProducto = x.producto || x.detalle_presentacion || '—';
          return '<div style="font-size:12px;padding:5px 9px;background:var(--surface-dim);border-radius:6px;margin-bottom:3px">' +
               '<strong>' + nombreProducto + '</strong> · Línea: ' + (x.linea||'—') + ' · Detalle: ' + (x.detalle_presentacion||'—') + ' · REFERENCIA SIESA: ' + referencia + ' · Lote: ' + (x.lote||'—') + ' · ' + (x.cant||'—') + ' ' + (x.unidad||'') + '</div>';
      }).join('')
    : '<p style="font-size:13px;color:var(--on-surface-variant)">Sin productos</p>';
  var hist = (p.historial || [{estado:p.estado, fecha:p.savedAt}]).map(function(h){
    return '<div class="timeline-item">' +
           '<div class="timeline-dot"></div>' +
           '<div><div class="timeline-state">' + h.estado + '</div>' +
           '<div class="timeline-date">' + h.fecha + ' - ' + (h.hora || '') + '</div></div></div>';
  }).join('');
  oModal('Detalle · ' + rad,
    '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px">' +
    '<span style="font-family:Courier New,monospace;font-size:16px;font-weight:700;color:var(--navy)">' + p.radicado + '</span>' +
    '<span class="' + badgeCls(p.estado) + '">' + p.estado + '</span></div>' +
    '<div class="progress-bar"><div class="progress-track"><div class="progress-fill" style="width:' + pct + '%"></div></div>' +
    '<div class="progress-labels"><span>Recibido</span><span>Investigación</span><span>Cerrado</span></div></div>' +
    '<div class="result-card" style="border-color:var(--outline-soft);padding:16px;margin-top:0">' +
    '<div class="detail-grid">' +
    dd('Cliente', p.cliente) + dd('Tipo', p.tipoSol) +
    dd('Fecha recepción', p.fechaRec) + dd('Días', '<span class="timer ' + timerCls(d) + '">' + d + ' días</span>') +
    dd('Prioridad', p.prioridad ? '<span class="' + priCls(p.prioridad) + '">' + p.prioridad + '</span>' : '—') +
    dd('Expectativa', p.expectativa) + '</div></div>' +
    '<div style="margin-bottom:12px"><div class="detail-label" style="margin-bottom:5px">Productos</div>' + prods + '</div>' +
    '<div style="margin-bottom:12px"><div class="detail-label" style="margin-bottom:5px">Descripción</div>' +
    '<p style="font-size:13px;color:var(--on-surface);line-height:1.6;background:var(--surface-dim);padding:9px 12px;border-radius:7px">' + (p.desc||'—') + '</p></div>' +
    '<div><div class="detail-label" style="margin-bottom:6px">Historial de estados</div><div class="timeline">' + hist + '</div></div>' +
    '<div style="margin-top:18px;text-align:right"><button class="btn" onclick="cModal()">Cerrar</button></div>');
}
function dd(label, val) {
  return '<div><div class="detail-label">' + label + '</div><div class="detail-value">' + (val||'—') + '</div></div>';
}
