// ── DASHBOARD ────────────────────────────────────────────────────────────
function cargarDashboard() {
  fetch("/api/dashboard")
  .then(function(r){ return r.json(); })
  .then(function(d) {
    try {
      if (document.getElementById("total")) document.getElementById("total").innerHTML = d.total;
      if (document.getElementById("abiertas")) document.getElementById("abiertas").innerHTML =
        (d.estados["Recibido"]||0) + (d.estados["Radicado"]||0) + (d.estados["En revisión"]||0) + (d.estados["En investigación"]||0);
      if (document.getElementById("cerradas")) document.getElementById("cerradas").innerHTML = d.estados["Cerrado"]||0;
      if (document.getElementById("alta")) document.getElementById("alta").innerHTML = d.prioridades["Alta"]||0;
      if (chartEstados) chartEstados.destroy();
      chartEstados = new Chart(document.getElementById("grafEstados").getContext("2d"), {
        type: "bar",
        data: { labels: Object.keys(d.estados), datasets: [{ label: "PQR", data: Object.values(d.estados), backgroundColor: "#1F5EAC" }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
      });
      if (chartTipos) chartTipos.destroy();
      chartTipos = new Chart(document.getElementById("grafTipos").getContext("2d"), {
        type: "doughnut",
        data: {
          labels: Object.keys(d.tipos),
          datasets: [{ data: Object.values(d.tipos), backgroundColor: ["#001E40","#1F5EAC","#f37021","#22c55e"] }]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } } }
      });
    } catch(e) { console.error("ERROR DASHBOARD:", e); }
  });
}

function iniciarDashboardAuto() {
  if (dashboardInterval) clearInterval(dashboardInterval);
  dashboardInterval = setInterval(function() {
    var panel = document.getElementById('panel-dashboard');
    if (panel && panel.classList.contains('on') && dashAuth) cargarDashboard();
  }, 30000);
}

// ── URGENT BADGE ───────────────────────────────────────────────────────
function actualizarUrgentes() {
  var urg = db.filter(function(p) {
    return dias(p.fechaRec || p.savedAt) > 7 &&
           ['Cerrado','No procede'].indexOf(p.estado) === -1;
  }).length;
  var badge = document.getElementById('urg-badge');
  if (badge) {
    badge.textContent = urg;
    badge.style.display = urg ? 'inline' : 'none';
  }
}
document.addEventListener('dbUpdated', function() { actualizarUrgentes(); });

function badgeCls(estado) {
  switch (estado) {
    case "Recibido": return "badge bs-rec";
    case "Radicado": return "badge bs-rad";
    case "En revisión": return "badge bs-rev";
    case "En investigación": return "badge bs-inv";
    case "Pendiente de información":
    case "Pendiente de decisión": return "badge bs-pen";
    case "Acción en proceso": return "badge bs-acc";
    case "Respuesta enviada": return "badge bs-res";
    case "Cerrado": return "badge bs-cer";
    case "No procede": return "badge bs-nop";
    default: return "badge bs-rec";
  }
}
function timerCls(dias) {
  dias = Number(dias) || 0;
  if (dias <= 5)  return "timer tok";
  if (dias <= 15) return "timer twn";
  return "timer tbd";
}

// ── RENDER DB ───────────────────────────────────────────────────────────
var dbExcel = null;
function cargarBDExcel() {
  return fetch("/api/pqr/todos")
    .then(function(r) { return r.json(); })
    .then(function(lista) { dbExcel = lista || []; });
}
function renderDB() {
  if (!bdAuth) return;
  if (!dbExcel) { cargarBDExcel().then(function() { renderDB(); }); return; }
  var q   = (document.getElementById('db-q').value || '').toLowerCase();
  var est = document.getElementById('db-est').value || '';
  var desde = document.getElementById('db-desde').value;
  var hasta = document.getElementById('db-hasta').value;
  var data = dbExcel.filter(function(p) {
    var f = p.fechaRec || (p.savedAt || '').slice(0,10);
    var cumpleFecha = true;
    if (desde && f < desde) cumpleFecha = false;
    if (hasta && f > hasta) cumpleFecha = false;
    return cumpleFecha &&
           (!q || (p.radicado||'').toLowerCase().indexOf(q) > -1 || (p.cliente||'').toLowerCase().indexOf(q) > -1) &&
           (!est || p.estado === est);
  });
  var total = dbExcel.length;
  var abier = dbExcel.filter(function(p) { return ['Cerrado','No procede'].indexOf(p.estado) === -1; }).length;
  var urgen = dbExcel.filter(function(p) { return dias(p.savedAt) > 7 && ['Cerrado','No procede'].indexOf(p.estado) === -1; }).length;
  var cerr  = dbExcel.filter(function(p) { return p.estado === 'Cerrado'; }).length;
  var puedeEditar = currentUser && (currentUser.rol === 'ADMIN' || currentUser.rol === 'LIDER_CALIDAD');
  document.getElementById('sg').innerHTML =
    sc('Total PQR', total, '#eaf1fb', '#1F5EAC', 'registros totales', 'M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z M14 2L14 8 20 8') +
    sc('Abiertos', abier, '#dbeafe', '#001E40', 'en trámite activo', 'M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z') +
    sc('Urgentes +7d', urgen, '#fee2e2', '#ba1a1a', 'requieren atención', 'M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z M12 9L12 13 M12 17L12.01 17') +
    sc('Cerrados', cerr, '#dcfce7', '#22c55e', 'resueltos', 'M20 6L9 17 4 12');
  var tbody = document.getElementById('db-tb');
  tbody.innerHTML = '';
  document.getElementById('db-empty').style.display = data.length ? 'none' : 'block';
  data.forEach(function(p) {
    var d = dias(p.fechaRec);
    var tr = document.createElement('tr');
    tr.innerHTML =
      '<td><span class="rad-cell">' + esc(p.radicado) + '</span></td>' +
      '<td>' + esc(p.fechaRec || p.savedAt.slice(0,10)) + '</td>' +
      '<td><span class="timer ' + timerCls(d) + '">' + d + 'd</span></td>' +
      '<td style="max-width:150px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + esc(p.cliente||'—') + '</td>' +
      '<td>' + esc(p.tipoSol||'—') + '</td>' +
      '<td><span class="' + badgeCls(p.estado) + '">' + esc(p.estado) + '</span></td>' +
      '<td>' + (p.prioridad ? '<span class="' + priCls(p.prioridad) + '">' + esc(p.prioridad) + '</span>' : '—') + '</td>' +
      '<td style="text-align:center;white-space:nowrap">' +
        (puedeEditar ? '<button class="btn btn-xs btn-icon" title="Cambiar estado" onclick="mEstado(\'' + p.radicado + '\')" style="margin-right:4px">✏️</button>' : '') +
        '<button class="btn btn-xs btn-icon" title="Ver detalle" onclick="mDetalle(\'' + p.radicado + '\')" style="margin-right:4px">👁️</button>' +
        (puedeEditar ? '<button class="btn-del" title="Eliminar" onclick="mEliminar(\'' + p.radicado + '\')">🗑️</button>' : '') +
      '</td>';
    tbody.appendChild(tr);
  });
}

function sc(lbl, val, bg, stroke, sub, path) {
  return '<div class="stat-card"><div class="stat-top"><span class="stat-label">' + lbl + '</span>' +
    '<div class="stat-icon" style="background:' + bg + '">' +
    '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="' + stroke + '" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="' + path + '"/></svg>' +
    '</div></div><div class="stat-value">' + val + '</div><div class="stat-sub">' + sub + '</div></div>';
}

// ── ELIMINAR PQR ────────────────────────────────────────────────────────
function mEliminar(rad) {
  oModal('Eliminar registro · ' + rad,
    '<div style="display:flex;flex-direction:column;align-items:center;text-align:center;padding:6px 0 20px">' +
    '<div style="width:54px;height:54px;border-radius:50%;background:var(--error-bg);display:flex;align-items:center;justify-content:center;margin-bottom:16px">' +
    '<span class="material-symbols-outlined" style="font-size:27px;color:var(--error)">delete</span></div>' +
    '<p style="font-size:15px;font-weight:600;margin-bottom:6px;color:var(--on-surface)">¿Está seguro de eliminar este registro?</p>' +
    '<p style="font-size:13px;color:var(--on-surface-variant);max-width:340px;line-height:1.55">Esta acción eliminará toda la información relacionada con este PQR y no podrá deshacerse.</p></div>' +
    '<div style="display:flex;gap:9px;justify-content:flex-end">' +
    '<button class="btn" onclick="cModal()">Cancelar</button>' +
    '<button class="btn btn-danger" onclick="ejecutarEliminar(\'' + rad + '\')">🗑 Eliminar</button></div>');
}

function ejecutarEliminar(rad) {
  fetch('/api/pqr/' + encodeURIComponent(rad), { method: 'DELETE' })
  .then(function(r) {
    return r.json().then(function(d) { return { ok: r.ok, data: d }; });
  })
  .then(function(res) {
    cModal();
    if (res.ok) {
      dbExcel = dbExcel.filter(function(x) { return x.radicado !== rad; });
      db = db.filter(function(x) { return x.radicado !== rad; });
      guardarDatos();
      renderDB();
      toast('Registro eliminado correctamente.', 'success');
    } else {
      toast(res.data.mensaje || 'No fue posible eliminar el registro.', 'error');
    }
  })
  .catch(function(err) {
    console.error(err);
    cModal();
    toast('No fue posible eliminar el registro.', 'error');
  });
}

// ── EXPORT CSV ──────────────────────────────────────────────────────────
function expCSV() {
  if (!db.length) { alert('No hay datos para exportar.'); return; }
  var hdrs = ['Radicado','Fecha guardado','Fecha recepción','Hora','Quien recibe','Cargo','Ciudad','Dpto','Centro','Medio','Tipo solicitud','Cliente','NIT','Contacto','Tel','Email','Descripción','Productos','Tipo evidencia','N° evidencias','Expectativa','Utilizado','Estado','Prioridad'];
  var rows = db.map(function(p) {
    return [
      p.radicado, p.savedAt, p.fechaRec, p.horaRec, p.quienRecibe, p.cargo,
      p.ciudadRec, p.dptoRec, p.centro, p.medio + (p.otroMedio ? ': '+p.otroMedio : ''),
      p.tipoSol, p.cliente, p.nit, p.contacto, p.tel, p.email,
      '"' + (p.desc||'').replace(/"/g,'""') + '"',
       p.productos ? p.productos.map(function(x) {
         return [x.linea, x.referencia_siesa || x.referencia || x.ref, x.detalle_presentacion, x.producto,
            x.unidad, x.lote, x.fechaEmp, x.cant, x.tipoDoc, x.numDoc]
           .filter(function(valor) { return String(valor || '').trim(); })
           .join(' | ');
       }).join('; ') : '',
      p.tipoEvid, p.numEvid, p.expectativa, p.utilizado, p.estado, p.prioridad
    ];
  });
  var csv = [hdrs.join(',')].concat(rows.map(function(r) { return r.join(','); })).join('\n');
  var a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' }));
  a.download = 'INAPEL_PQR_' + new Date().toISOString().slice(0,10) + '.csv';
  a.click();
}
