// ── RECENT SEARCHES (solo en memoria: se limpian al salir de CONSULTAR) ─
var _RECENT_SEARCHES = [];
function getRecentSearches() { return _RECENT_SEARCHES.slice(); }
function addRecentSearch(val) {
  _RECENT_SEARCHES = _RECENT_SEARCHES.filter(function(s) { return s !== val; });
  _RECENT_SEARCHES.unshift(val);
  if (_RECENT_SEARCHES.length > 5) _RECENT_SEARCHES = _RECENT_SEARCHES.slice(0, 5);
  renderRecentSearches();
}
function renderRecentSearches() {
  var list = getRecentSearches();
  var el = document.getElementById('rs-list');
  if (!el) return;
  if (!list.length) { el.parentElement.classList.remove('show'); return; }
  el.innerHTML = list.map(function(s) {
    return '<div class="search-item" onclick="setSearch(\'' + s + '\')">' +
           '<span class="material-symbols-outlined" style="font-size:16px">history</span>' + s +
           '<span class="search-del" onclick="event.stopPropagation();removeSearch(\'' + s + '\')">✕</span></div>';
  }).join('');
  el.parentElement.classList.add('show');
}
function setSearch(val) {
  document.getElementById('c-rad').value = val;
  document.getElementById('rs-drop').classList.remove('show');
  consultar();
}
function removeSearch(val) {
  _RECENT_SEARCHES = _RECENT_SEARCHES.filter(function(s) { return s !== val; });
  renderRecentSearches();
}
document.addEventListener('click', function(e) {
  var drop = document.getElementById('rs-drop');
  if (drop && !e.target.closest('.search-wrap')) drop.classList.remove('show');
});

window.addEventListener('resize', function() {
  if (window.innerWidth > 600) {
    var s = document.getElementById('sidebar');
    var o = document.getElementById('sidebar-overlay');
    var h = document.getElementById('hamburger');
    s.classList.remove('open');
    o.classList.remove('open');
    h.classList.remove('open');
    h.setAttribute('aria-label', 'Abrir menú');
    document.body.style.overflow = '';
  }
});

// ── CONSULTAR ───────────────────────────────────────────────────────────
var _CONSULTA_STATE_KEYS = ['resultadoActual','consultaActual','ultimoResultado','currentPQR','searchState','cacheConsulta'];
function resetConsulta() {
  var rad = document.getElementById('c-rad');
  if (rad) { rad.value = ''; rad.blur(); }
  var list = document.getElementById('rs-list');
  if (list) list.innerHTML = '';
  var drop = document.getElementById('rs-drop');
  if (drop) drop.classList.remove('show');
  var res = document.getElementById('c-res');
  if (res) res.innerHTML = '';
  _RECENT_SEARCHES = [];
  try { localStorage.removeItem(SEARCH_KEY); } catch (e) {}
  var btn = document.querySelector('#panel-consultar .btn-primary');
  if (btn) loadBtn(btn, false);
  _CONSULTA_STATE_KEYS.forEach(function(k) {
    try { window[k] = null; } catch (e) {}
  });
}
document.addEventListener('sectionchange', function(e) {
  var d = (e && e.detail) || {};
  if (d.from === 'consultar' || d.to === 'consultar') resetConsulta();
});
async function consultar() {
  var rad = document.getElementById("c-rad").value.trim();
  var btn = document.querySelector('#panel-consultar .btn-primary');
  if (!rad) { toast("Ingrese un número de radicado.", "error", 3000); document.getElementById("c-rad").focus(); return; }
  loadBtn(btn, true);
  document.getElementById("c-res").innerHTML = '<div style="text-align:center;padding:28px;color:var(--on-surface-variant)"><span class="spin-dark"></span> Consultando...</div>';
  try {
    var respuesta = await fetch("/api/consultar/" + encodeURIComponent(rad));
    if (!respuesta.ok) {
      var mensajeErr = "PQR no encontrado";
      try {
        var er = await respuesta.json();
        if (er && er.error) mensajeErr = er.error;
      } catch (e) {}
      throw new Error(mensajeErr);
    }
      var p = await respuesta.json();
      seguimientoActual = p;
    renderConsulta(p);
    addRecentSearch(rad);
    toast("PQR encontrado correctamente", "success", 3000);
  } catch (error) {
    console.error(error);
    document.getElementById("c-res").innerHTML = '<div class="alert alert-error">' + error.message + '</div>';
    toast(error.message || "Error al consultar", "error", 4000);
  } finally { loadBtn(btn, false); }
}

function renderConsulta(p) {
  var inv = p.investigacion || {};
  var div = document.getElementById('c-res');
  var d = dias(p.savedAt);
  var states = ['Recibido','Radicado','En revisión','En investigación','Acción en proceso','Respuesta enviada','Cerrado'];
  var idx = Math.max(states.indexOf(p.estado), 0);
  var pct = Math.round((idx + 1) / states.length * 100);
  var hist = (p.historial || [{ estado: p.estado, fecha: p.fechaRec, hora: p.horaRec }]).map(function(h) {
    return '<div class="timeline-item">' +
           '<div class="timeline-dot"></div>' +
           '<div><div class="timeline-state">' + esc(h.estado) + '</div>' +
           '<div class="timeline-date">' + esc(h.fecha) + ' - ' + esc(h.hora || '') + '</div></div></div>';
  }).join('');
  var prodRows = p.productos && p.productos.length
    ? p.productos.map(function(x) {
        return '<tr>' +
           '<td style="padding:7px 10px;border-bottom:1px solid var(--outline-soft)">' + esc(x.linea || '—') + '</td>' +
           '<td style="padding:7px 10px;border-bottom:1px solid var(--outline-soft)">' + esc(x.referencia_siesa || x.referencia || x.ref || '—') + '</td>' +
           '<td style="padding:7px 10px;border-bottom:1px solid var(--outline-soft)">' + esc(x.producto || '—') + '</td>' +
           '<td style="padding:7px 10px;border-bottom:1px solid var(--outline-soft)">' + esc(x.detalle_presentacion || '—') + '</td>' +
          '<td style="padding:7px 10px;border-bottom:1px solid var(--outline-soft)">' + esc(x.lote || '—') + '</td>' +
          '<td style="padding:7px 10px;border-bottom:1px solid var(--outline-soft)">' + esc(x.cant || '—') + ' ' + esc(x.unidad || '') + '</td>' +
          '<td style="padding:7px 10px;border-bottom:1px solid var(--outline-soft)">' + esc(x.tipoDoc || '—') + ' ' + esc(x.numDoc || '') + '</td>' +
          '</tr>';
      }).join('')
      : '<tr><td colspan="7" style="padding:10px;color:var(--on-surface-variant);text-align:center">Sin productos</td></tr>';
  var productosHtml =
    '<div style="margin-top:18px;border-top:1px solid var(--outline-soft);padding-top:14px">' +
    '<div class="detail-label" style="margin-bottom:6px">Productos involucrados</div>' +
    '<div class="table-wrap"><table class="table-pqr" style="min-width:620px;font-size:12px">' +
      '<thead><tr><th>Línea</th><th>REFERENCIA SIESA</th><th>Producto</th><th>Detalle / presentación</th><th>Lote / OP</th><th>Cantidad</th><th>Documento</th></tr></thead>' +
    '<tbody>' + prodRows + '</tbody></table></div></div>';
  var evidenciasHtml = '';
  if (p.adjuntos && p.adjuntos.length) {
    var evidRows = p.adjuntos.map(function(a) {
      return '<li style="padding:4px 0"><a href="/api/evidencias/' + encodeURIComponent(a.id) + '" target="_blank" rel="noopener">' +
        esc(a.nombre || 'Archivo') + '</a>' + (a.tipo ? ' <span style="color:var(--on-surface-variant)">(' + esc(a.tipo) + ')</span>' : '') + '</li>';
    }).join('');
    evidenciasHtml =
      '<div style="margin-top:18px;border-top:1px solid var(--outline-soft);padding-top:14px">' +
      '<div class="detail-label" style="margin-bottom:6px">Evidencias adjuntas</div>' +
      '<ul style="margin:0;padding-left:18px;font-size:13px">' + evidRows + '</ul></div>';
  }
  div.innerHTML =
    '<div class="result-card">' +
    '<div class="result-top"><span class="result-rad">' + esc(p.radicado) + '</span><span class="' + badgeCls(p.estado) + '">' + esc(p.estado) + '</span></div>' +
    '<div class="progress-bar"><div class="progress-track"><div class="progress-fill" style="width:' + pct + '%"></div></div>' +
    '<div class="progress-labels"><span>Recibido</span><span>En revisión</span><span>Cerrado</span></div></div>' +
    '<div class="detail-grid">' +
    dd('Cliente', esc(p.cliente)) + dd('Tipo de solicitud', esc(p.tipoSol)) +
    (p.vendedor ? dd('Vendedor', esc(p.vendedor)) : '') +
    (p.linea ? dd('Línea de producto', esc(p.linea)) : '') +
    dd('Fecha de recepción', esc(p.fechaRec)) + dd('Días en trámite', '<span class="timer ' + timerCls(d) + '">' + d + ' días</span>') +
    dd('Prioridad', p.prioridad ? '<span class="' + priCls(p.prioridad) + '">' + esc(p.prioridad) + '</span>' : '—') +
    dd('Expectativa del cliente', esc(p.expectativa)) +
    '</div>' +
    productosHtml +
    '<div style="border-top:1px solid var(--outline-soft);padding-top:12px">' +
    '<div class="detail-label" style="margin-bottom:7px">Historial de estados</div>' +
    '<div class="timeline">' + hist + '</div></div>' +

    evidenciasHtml +

    '<div style="margin-top:25px;border-top:1px solid var(--outline-soft);padding-top:18px">' +
    '<div class="inv-card">' +
    '<div class="inv-header">' +
    '<span class="material-symbols-outlined" style="font-size:22px">description</span>' +
    '<span>Resultados de la investigación</span></div>' +
    '<div class="inv-wrap"><table class="inv-table">' +
    '<tr><td class="inv-label">Asignación de la causa</td><td class="inv-val">' + esc(inv.causa || 'Pendiente') + '</td>' +
    '<td class="inv-label">Máquina o Equipo</td><td class="inv-val">Pendiente</td></tr>' +
    '<tr><td class="inv-label">Departamentos involucrados</td><td class="inv-val">' + esc(inv.deptos || 'Pendiente') + '</td>' +
    '<td class="inv-label">Herramienta utilizada</td><td class="inv-val">' + ((inv.herramientas && inv.herramientas.length) ? esc(inv.herramientas.join(', ')) : 'Pendiente') + '</td></tr>' +
    '<tr><td class="inv-label">Acción Correctiva</td><td class="inv-val">' + esc(inv.acc || 'Pendiente') + '</td>' +
    '<td class="inv-label">Notificación al cliente</td><td class="inv-val">' + esc(inv.notif || 'Pendiente') + '</td></tr>' +
    '<tr><td class="inv-label">Fecha de respuesta</td><td class="inv-val">' + esc(inv.fResp || '-') + '</td>' +
    '<td class="inv-label">Fecha de cierre</td><td class="inv-val">' + esc(inv.fCierre || '-') + '</td></tr>' +
    '<tr><td class="inv-label">Cierre del PQR</td><td class="inv-val" colspan="3">' + esc(inv.cierre || 'No') + '</td></tr>' +
    '</table></div></div>' +

    '<div style="margin-top:20px">' +
    '<div class="detail-label" style="margin-bottom:12px;font-size:16px;font-weight:700;color:var(--navy)">Respuesta al cliente</div>' +
     '<div class="response-box">' + esc(inv.respuesta_comercial || 'La investigación aún se encuentra en proceso.') + '</div></div>' +
    '</div></div>';
}
