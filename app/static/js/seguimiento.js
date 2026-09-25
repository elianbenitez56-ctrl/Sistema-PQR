// ── SEGUIMIENTO ─────────────────────────────────────────────────────────
var CATEGORIAS_HERRAMIENTA = [
  {
    titulo: '🔎 Herramientas de inspección',
    opciones: ['Inspección visual', 'Ensayos de laboratorio', 'Comparación muestra patrón', 'Checklist de inspección']
  },
  {
    titulo: '📊 Herramientas de análisis',
    opciones: ['5 ¿Por qué?', 'Diagrama Ishikawa', 'Análisis Pareto']
  }
];

function obtenerHerramientasSeleccionadas() {
  var checks = document.querySelectorAll('input[name="herramientas[]"]:checked');
  var valores = [];
  for (var i = 0; i < checks.length; i++) valores.push(checks[i].value);
  return valores;
}

function construirHerramientasHtml(seleccionadas) {
  return CATEGORIAS_HERRAMIENTA.map(function(categoria, indiceCategoria) {
    var opciones = categoria.opciones.map(function(opcion, indiceOpcion) {
      var id = 'herramienta-' + indiceCategoria + '-' + indiceOpcion;
      var checked = seleccionadas.indexOf(opcion) > -1 ? ' checked' : '';
      return '<label class="herramienta-option">' +
        '<input type="checkbox" id="' + id + '" name="herramientas[]" value="' + opcion + '"' + checked + '>' +
        '<span>' + opcion + '</span></label>';
    }).join('');
    return '<div class="herramienta-categoria">' +
      '<div class="herramienta-categoria-titulo">' + categoria.titulo + '</div>' +
      '<div class="herramienta-grid">' + opciones + '</div></div>';
  }).join('');
}

function configurarPermisosSeguimiento() {
  var rol = currentUser ? currentUser.rol : '';
  var puedeCalidad = rol === 'ADMIN' || rol === 'LIDER_CALIDAD';
  var puedeComercial = rol === 'ADMIN' || rol === 'LIDER_COMERCIAL'
    || rol === 'COORDINADORA COMERCIAL' || rol === 'DIRECTORA COMERCIAL' || rol === 'COMERCIAL';
  var camposCalidad = ['si-resp', 'si-cargo', 'si-causa', 'si-deptos', 'si-txt-calidad'];
  var herramientas = document.querySelectorAll('input[name="herramientas[]"]');
  for (var i = 0; i < herramientas.length; i++) camposCalidad.push(herramientas[i].id);
  var camposComercial = ['si-acc', 'si-notif', 'si-fresp', 'si-cierre', 'si-fcierre', 'si-txt'];

  function aplicarBloqueo(ids, editable) {
    ids.forEach(function(id) {
      var campo = document.getElementById(id);
      if (!campo) return;
      if (campo.tagName === 'SELECT' || campo.type === 'checkbox') {
        campo.disabled = !editable;
      } else {
        campo.readOnly = !editable;
      }
      campo.setAttribute('aria-readonly', editable ? 'false' : 'true');
      campo.title = editable ? '' : 'Información de solo lectura';
      campo.style.backgroundColor = editable ? '' : 'var(--surface-dim)';
      campo.style.cursor = editable ? '' : 'not-allowed';
    });
  }

  aplicarBloqueo(camposCalidad, puedeCalidad);
  aplicarBloqueo(camposComercial, puedeComercial);

  var botonCalidad = document.getElementById('seg-btn-calidad');
  var botonComercial = document.getElementById('seg-btn-comercial');
  if (botonCalidad) botonCalidad.style.display = puedeCalidad ? '' : 'none';
  if (botonComercial) botonComercial.style.display = puedeComercial ? '' : 'none';
}

async function cargarSeg() {
  var rad = document.getElementById("seg-q").value.trim().toUpperCase();
  var btn = document.querySelector('#panel-seguimiento .btn-primary');
  var div = document.getElementById("seg-con");
  if (!rad) { toast("Ingrese un número de radicado.", "error", 3000); return; }
  loadBtn(btn, true);
  div.innerHTML = '<div style="text-align:center;padding:38px;color:var(--on-surface-variant)"><span class="spin-dark"></span> Cargando PQR...</div>';
  try {
    var respuesta = await fetch("/api/consultar/" + rad);
    if (!respuesta.ok) {
      div.innerHTML = '<div class="alert alert-error">No se encontró el radicado <strong>' + esc(rad) + '</strong>.</div>';
      toast("Radicado no encontrado", "error", 4000);
      return;
    }
     var p = await respuesta.json();
     toast("PQR cargado exitosamente", "success", 3000);
     var inv = p.investigacion || {};
     var calidadCompletada = inv.calidad_estado === 'completada';
     var comercialCompletada = inv.comercial_estado === 'completada';
     var herramientas = Array.isArray(inv.herramientas) && inv.herramientas.length
       ? inv.herramientas.slice()
        : (inv.herr ? [inv.herr] : [CATEGORIAS_HERRAMIENTA[1].opciones[0]]);
     var prodRows = p.productos && p.productos.length
        ? p.productos.map(function(x) {
            return '<tr><td style="padding:7px 11px;border-bottom:1px solid var(--outline-soft)">' + esc(x.linea||'—') + '</td>' +
                    '<td style="padding:7px 11px;border-bottom:1px solid var(--outline-soft)">' + esc(x.referencia_siesa || x.referencia || x.ref || '—') + '</td>' +
                    '<td style="padding:7px 11px;border-bottom:1px solid var(--outline-soft)">' + esc(x.producto||'—') + '</td>' +
                    '<td style="padding:7px 11px;border-bottom:1px solid var(--outline-soft)">' + esc(x.detalle_presentacion||'—') + '</td>' +
                 '<td style="padding:7px 11px;border-bottom:1px solid var(--outline-soft)">' + esc(x.lote||'—') + '</td>' +
                 '<td style="padding:7px 11px;border-bottom:1px solid var(--outline-soft)">' + esc(x.cant||'—') + ' ' + esc(x.unidad||'') + '</td>' +
                 '<td style="padding:7px 11px;border-bottom:1px solid var(--outline-soft)">' + esc(x.tipoDoc||'—') + ' ' + esc(x.numDoc||'') + '</td></tr>';
        }).join('')
       : '<tr><td colspan="7" style="padding:10px;color:var(--on-surface-variant);text-align:center">Sin productos</td></tr>';
     var mkSel = function(id, opts, val) {
       return '<select id="' + id + '">' + opts.map(function(o) {
         return '<option' + (val === o ? ' selected' : '') + '>' + o + '</option>';
       }).join('') + '</select>';
     };
     div.innerHTML =
      '<div class="card">' +
      '<div class="card-header"><div class="card-icon"><span class="material-symbols-outlined mat-icon">info</span></div>' +
      '<h3>PQR · ' + p.radicado + '</h3><span class="' + badgeCls(p.estado) + '" style="margin-left:auto">' + p.estado + '</span></div>' +
      '<div class="card-body">' +
      '<div class="form-grid" style="margin-bottom:14px">' +
      '<div><div class="detail-label">Cliente</div><div style="font-size:14px;font-weight:500">' + esc(p.cliente||'—') + '</div></div>' +
      '<div><div class="detail-label">Tipo de solicitud</div><div style="font-size:13px">' + esc(p.tipoSol||'—') + '</div></div></div>' +
      '<div class="detail-label" style="margin-bottom:5px">Descripción</div>' +
      '<p style="font-size:13px;color:var(--on-surface);line-height:1.6;background:var(--surface-dim);padding:9px 13px;border-radius:7px;margin-bottom:14px">' + esc(p.desc||'—') + '</p>' +
      '<div class="detail-label" style="margin-bottom:6px">Productos involucrados</div>' +
      '<table style="width:100%;border-collapse:collapse;font-size:13px;background:var(--surface-container-lowest);border:1px solid var(--outline-soft);border-radius:var(--radius-md);overflow:hidden">' +
         '<thead><tr style="background:var(--navy)"><th style="padding:7px 11px;color:#fff;font-size:10.5px;text-align:left;font-weight:600">Línea</th>' +
         '<th style="padding:7px 11px;color:#fff;font-size:10.5px;text-align:left;font-weight:600">REFERENCIA SIESA</th>' +
         '<th style="padding:7px 11px;color:#fff;font-size:10.5px;text-align:left;font-weight:600">Producto</th>' +
         '<th style="padding:7px 11px;color:#fff;font-size:10.5px;text-align:left;font-weight:600">Detalle / presentación</th>' +
      '<th style="padding:7px 11px;color:#fff;font-size:10.5px;text-align:left;font-weight:600">Lote/OP</th>' +
      '<th style="padding:7px 11px;color:#fff;font-size:10.5px;text-align:left;font-weight:600">Cantidad</th>' +
      '<th style="padding:7px 11px;color:#fff;font-size:10.5px;text-align:left;font-weight:600">Documento</th></tr></thead>' +
       '<tbody>' + prodRows + '</tbody></table>' +
       '</div></div>' +

       '<div class="card"><div class="card-body">' +
       '<div class="detail-label" style="margin-bottom:10px">Estado de gestión</div>' +
       '<div style="display:flex;gap:10px;flex-wrap:wrap" id="seg-estados">' +
       '<span id="seg-estado-calidad" class="badge ' + (calidadCompletada ? 'bs-acc' : 'bs-rev') + '">' + (calidadCompletada ? '🟢' : '🟡') + ' Calidad — ' + (calidadCompletada ? 'Completada' : 'Pendiente') + '</span>' +
       '<span id="seg-estado-comercial" class="badge ' + (comercialCompletada ? 'bs-acc' : 'bs-rev') + '">' + (comercialCompletada ? '🟢' : '🟡') + ' Comercial — ' + (comercialCompletada ? 'Completada' : 'Pendiente') + '</span>' +
       '</div></div></div>' +

       '<div class="card">' +
       '<div class="card-header"><div class="card-icon"><span class="material-symbols-outlined mat-icon">troubleshoot</span></div><h3>Investigación y análisis de causas</h3><span style="margin-left:auto;color:var(--on-surface-variant);font-size:11px;font-weight:700">CALIDAD</span></div>' +
       '<div class="card-body">' +
       '<div class="form-grid">' +
       '<div class="field"><label>Responsable de investigación</label><input type="text" id="si-resp" value="' + esc(inv.resp||'') + '"></div>' +
       '<div class="field"><label>Cargo</label><input type="text" id="si-cargo" value="' + esc(inv.cargo||'') + '"></div>' +
       '<div class="field"><label>Asignación de causa</label>' + mkSel('si-causa',['Materias primas','Máquina o equipo','Mano de obra','Medición/Inspección','Diseño del producto','Empaque','Transporte','Almacenamiento','Proveedor','Cliente (Uso inadecuado)'],inv.causa) + '</div>' +
        '<div class="field full"><label>Herramientas utilizadas</label>' + construirHerramientasHtml(herramientas) + '</div>' +
       '<div class="field full"><label>Departamentos involucrados</label><input type="text" id="si-deptos" value="' + esc(inv.deptos||'') + '" placeholder="Ej: Calidad, Logística, Producción"></div>' +
        '<div class="field full"><label>Respuesta detallada al cliente</label>' +
        '<textarea id="si-txt-calidad" name="respuesta_calidad" rows="6" placeholder="Redacte aquí la respuesta detallada para el cliente...">' + esc(inv.respuesta_calidad||'') + '</textarea></div>' +
        '<div class="action-row"><button id="seg-btn-calidad" class="btn btn-primary" onclick="guardarSeg(\'' + p.radicado + '\', \'calidad\')">💾 Guardar investigación</button></div>' +
        '</div></div></div>' +
       '<div class="card">' +
       '<div class="card-header"><div class="card-icon"><span class="material-symbols-outlined mat-icon">business_center</span></div><h3>Gestión comercial</h3><span style="margin-left:auto;color:var(--on-surface-variant);font-size:11px;font-weight:700">COMERCIAL</span></div>' +
       '<div class="card-body">' +
       '<div class="form-grid">' +
       '<div class="field"><label>Acciones tomadas</label>' + mkSel('si-acc',['Reposición','Retrabajo','Nota crédito','Capacitación','Acción correctiva','Acción preventiva','Mejora del proceso'],inv.acc) + '</div>' +
       '<div class="field"><label>Notificación al cliente</label>' + mkSel('si-notif',['Sí','No'],inv.notif) + '</div>' +
       '<div class="field"><label>Fecha de respuesta</label><input type="date" id="si-fresp" value="' + (inv.fResp||'') + '"></div>' +
      '<div class="field"><label>Cierre del PQR</label>' + mkSel('si-cierre',['No','Sí'],inv.cierre) + '</div>' +
      '<div class="field"><label>Fecha de cierre</label><input type="date" id="si-fcierre" value="' + (inv.fCierre||'') + '"></div>' +
      '<div class="field full"><label>Respuesta detallada al cliente</label>' +
        '<textarea id="si-txt" name="respuesta_comercial" rows="6" placeholder="Redacte el análisis de causa raíz y la respuesta completa para el cliente...">' + esc(inv.respuesta_comercial||'') + '</textarea></div>' +
      '</div>' +
      '<div class="action-row">' +
      '<button class="btn btn-success" onclick="expSeg(\'' + p.radicado + '\')">⬇ Descargar respuesta</button>' +
       '<button id="seg-btn-comercial" class="btn btn-primary" onclick="guardarSeg(\'' + p.radicado + '\', \'comercial\')">💾 Guardar gestión comercial</button>' +
      '</div>' +
       '<div id="seg-msg"></div>' +
       '</div></div>';
      configurarPermisosSeguimiento();
     loadBtn(btn, false);
  } catch(err) {
    console.error(err);
    loadBtn(btn, false);
    toast("Error al cargar PQR", "error", 4000);
    div.innerHTML = '<div class="alert alert-error">' + err + '</div>';
  }
}

async function guardarSeg(rad, seccion) {
  var btn = document.getElementById(seccion === 'comercial' ? 'seg-btn-comercial' : 'seg-btn-calidad');
  loadBtn(btn, true);
  var p = { radicado: rad, investigacion: {} };
  var respuestaCalidad = document.getElementById('si-txt-calidad').value;
  var respuestaComercial = document.getElementById('si-txt').value;
  p.investigacion = {
    resp: document.getElementById('si-resp').value,
    cargo: document.getElementById('si-cargo').value,
    causa: document.getElementById('si-causa').value,
    herramientas: obtenerHerramientasSeleccionadas(),
    deptos: document.getElementById('si-deptos').value,
    acc: document.getElementById('si-acc').value,
    notif: document.getElementById('si-notif').value,
    fResp: document.getElementById('si-fresp').value,
    cierre: document.getElementById('si-cierre').value,
    fCierre: document.getElementById('si-fcierre').value,
    respuesta_calidad: respuestaCalidad,
    respuesta_comercial: respuestaComercial
  };
  var rolSeg = currentUser ? currentUser.rol : '';
  var camposObligatorios = seccion === 'comercial'
    ? [
        ['acc', 'Acciones tomadas'],
        ['notif', 'Notificación al cliente'],
        ['fResp', 'Fecha de respuesta'],
        ['cierre', 'Cierre del PQR'],
        ['fCierre', 'Fecha de cierre'],
        ['respuesta_comercial', 'Respuesta detallada al cliente']
      ]
    : [
        ['resp', 'Responsable de investigación'],
        ['cargo', 'Cargo'],
        ['causa', 'Asignación de causa'],
        ['herramientas', 'Herramienta utilizada'],
        ['deptos', 'Departamentos involucrados']
      ];
  var camposFaltantes = camposObligatorios.filter(function(campo) {
    return !String(p.investigacion[campo[0]] || '').trim();
  }).map(function(campo) { return campo[1]; });
  if (camposFaltantes.length) {
    var mensajeFaltantes = 'Complete los campos obligatorios: ' + camposFaltantes.join(', ') + '.';
    loadBtn(btn, false);
    msg('seg-msg', mensajeFaltantes, 'error');
    toast(mensajeFaltantes, 'error', 5000);
    return;
  }
  p.estado = p.investigacion.cierre === "Sí" ? "Cerrado" : "En investigación";
  var datosSeccion = seccion === 'comercial'
    ? {
        radicado: p.radicado,
        acc: p.investigacion.acc,
        notif: p.investigacion.notif,
        fResp: p.investigacion.fResp,
        cierre: p.investigacion.cierre,
        fCierre: p.investigacion.fCierre,
        respuesta_comercial: p.investigacion.respuesta_comercial
      }
    : {
        radicado: p.radicado,
        resp: p.investigacion.resp,
        cargo: p.investigacion.cargo,
        causa: p.investigacion.causa,
        herramientas: p.investigacion.herramientas,
        deptos: p.investigacion.deptos,
        respuesta_calidad: p.investigacion.respuesta_calidad
      };
  try {
    var respuesta = await fetch("/api/seguimiento/" + seccion, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(datosSeccion)
    });
    var resultado = await respuesta.json();
    loadBtn(btn, false);
    if (resultado.ok) {
      var calidadStatus = document.getElementById('seg-estado-calidad');
      var comercialStatus = document.getElementById('seg-estado-comercial');
      if (calidadStatus && resultado.calidad_estado) {
        var calidadLista = resultado.calidad_estado === 'completada';
        calidadStatus.className = 'badge ' + (calidadLista ? 'bs-acc' : 'bs-rev');
        calidadStatus.textContent = (calidadLista ? '🟢' : '🟡') + ' Calidad — ' + (calidadLista ? 'Completada' : 'Pendiente');
      }
      if (comercialStatus && resultado.comercial_estado) {
        var comercialLista = resultado.comercial_estado === 'completada';
        comercialStatus.className = 'badge ' + (comercialLista ? 'bs-acc' : 'bs-rev');
        comercialStatus.textContent = (comercialLista ? '🟢' : '🟡') + ' Comercial — ' + (comercialLista ? 'Completada' : 'Pendiente');
      }
      var mensajeExito = seccion === 'comercial'
        ? 'Gestión comercial guardada correctamente.'
        : 'Información de Calidad guardada correctamente.';
      if (resultado.notificacion_comercial_intentada) {
        if (resultado.notificacion_comercial_enviada) {
          mensajeExito += ' Se notificó a Comercial por correo.';
        } else {
          mensajeExito += ' ⚠ No se pudo notificar a Comercial por correo (' + (resultado.notificacion_mensaje || 'error desconocido') + '). Se reintentará al guardar de nuevo.';
        }
      }
      var avisoFallido = resultado.notificacion_comercial_intentada && !resultado.notificacion_comercial_enviada;
      toast(mensajeExito, avisoFallido ? "error" : "success");
      msg("seg-msg", (avisoFallido ? "⚠ " : "✅ ") + mensajeExito, avisoFallido ? "error" : "success");
    } else {
      toast("Error al guardar la investigación", "error");
      msg("seg-msg", "Error al guardar la investigación", "error");
    }
  } catch (e) {
    console.error(e);
    loadBtn(btn, false);
    toast("Error de conexión con el servidor", "error");
    msg("seg-msg", "Error de conexión con el servidor", "error");
  }
}

function expSeg(rad) {
  var p = seguimientoActual && seguimientoActual.radicado === rad
    ? seguimientoActual
    : (dbExcel !== null ? dbExcel : db).filter(function(x) { return x.radicado === rad; })[0];
  if (!p) { toast('PQR no encontrado.', 'error'); return; }
  var inv = p.investigacion || {};
  var texto = function(valor, defecto) {
    var valorTexto = String(valor || '').trim();
    return valorTexto ? esc(valorTexto).replace(/\r?\n/g, '<br>') : (defecto || 'No registrado');
  };
  var valor = function(dato, defecto) {
    return esc(String(dato || '').trim() || (defecto || 'No registrado'));
  };
  var respuestaCalidad = document.getElementById('si-txt-calidad')
    ? document.getElementById('si-txt-calidad').value
    : (inv.respuesta_calidad || '');
  var respuestaComercial = document.getElementById('si-txt')
    ? document.getElementById('si-txt').value
    : (inv.respuesta_comercial || '');
  var herramientas = Array.isArray(inv.herramientas) ? inv.herramientas : (inv.herr ? [inv.herr] : []);
  var herramientasHtml = CATEGORIAS_HERRAMIENTA.map(function(categoria, indice) {
    var seleccionadas = categoria.opciones.filter(function(opcion) {
      return herramientas.indexOf(opcion) > -1;
    });
    if (!seleccionadas.length) return '';
    return '<div class="tool-group"><div class="tool-group-title">' +
      esc(indice === 0 ? 'Herramientas de inspección' : 'Herramientas de análisis') + '</div>' +
      '<ul>' + seleccionadas.map(function(opcion) { return '<li>' + esc(opcion) + '</li>'; }).join('') + '</ul></div>';
  }).join('') || '<div class="empty">No registrado</div>';
   var prods = p.productos && p.productos.length
     ? p.productos.map(function(x) {
         var documento = [x.tipoDoc || '', x.numDoc || ''].join(' ').trim();
         return '<tr><td>' + valor(x.linea, '-') + '</td>' +
           '<td>' + valor(x.producto, '-') + '</td>' +
           '<td>' + valor(x.detalle_presentacion, '-') + '</td>' +
            '<td>' + valor(x.referencia_siesa || x.referencia || x.ref, '-') + '</td>' +
           '<td>' + valor(x.lote, '-') + '</td>' +
           '<td>' + valor(x.cant, '-') + '</td>' +
           '<td>' + valor(x.unidad, '-') + '</td>' +
           '<td>' + valor(documento, '-') + '</td></tr>';
       }).join('')
     : '<tr><td colspan="8" class="empty">No registrado</td></tr>';
   var generado = new Date().toLocaleDateString('es-CO');
   var logo = window.location.origin + '/static/img/logo_inapel.png';
   var seguimientoUrl = window.location.origin + '/?seguimiento=' + encodeURIComponent(rad);
  var html = '<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>Informe de Gestión de PQR - ' + esc(rad) + '</title>' +
    '<style>' +
    '@page{size:A4;margin:18mm 14mm 20mm}' +
    '*{box-sizing:border-box}' +
    'html,body{margin:0;padding:0;background:#eef3f8;color:#182638;font-family:Arial,"Segoe UI",sans-serif;font-size:11px;line-height:1.45}' +
    '.report{max-width:900px;margin:24px auto;background:#fff;padding:30px 34px 55px;box-shadow:0 5px 24px rgba(0,30,64,.12)}' +
    '.report-header{display:flex;align-items:center;gap:16px;border-bottom:3px solid #1f5eac;padding-bottom:18px}' +
    '.logo{width:58px;height:58px;object-fit:contain;flex:0 0 auto}' +
    '.brand{font-size:19px;font-weight:700;color:#00325e;letter-spacing:.04em}' +
    '.brand span{display:block;font-size:10px;color:#65758a;font-weight:500;letter-spacing:.03em;margin-top:3px}' +
    '.header-meta{margin-left:auto;text-align:right;color:#65758a;font-size:10px}' +
    '.document-title{margin:24px 0 5px;color:#00325e;font-size:22px;letter-spacing:.04em}' +
    '.radicado{display:inline-block;margin-top:5px;padding:8px 14px;border-radius:6px;background:#eaf2fb;color:#00325e;font:700 17px "Courier New",monospace;letter-spacing:.05em}' +
    '.section{margin-top:25px;break-inside:avoid}' +
    '.section-title{display:flex;align-items:center;gap:9px;margin:0 0 10px;padding-bottom:6px;border-bottom:1px solid #cdd9e6;color:#00325e;font-size:15px;break-after:avoid}' +
    '.section-title:before{content:"";display:block;width:4px;height:19px;border-radius:3px;background:#1f5eac}' +
    '.info-table,.data-table{width:100%;border-collapse:collapse;table-layout:fixed}' +
    '.info-table td{width:25%;padding:8px 10px;border:1px solid #dce4ed;vertical-align:top;overflow-wrap:anywhere}' +
    '.info-table .label{background:#f3f6fa;color:#63748a;font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.06em}' +
     '.info-table .value{font-weight:600;color:#203449}' +
     '.back-link{display:inline-flex;align-items:center;gap:6px;margin-top:18px;color:#1f5eac;text-decoration:none;font-size:11px;font-weight:700;letter-spacing:.02em}' +
     '.back-link:hover{text-decoration:underline}' +
    '.text-block{padding:13px 15px;border:1px solid #dce4ed;border-left:4px solid #1f5eac;border-radius:5px;background:#f8fafc;white-space:normal;overflow-wrap:anywhere;word-break:break-word}' +
    '.data-table{font-size:10px;word-break:break-word}' +
    '.data-table th{padding:8px 7px;background:#00325e;color:#fff;text-align:left;font-size:9px;text-transform:uppercase;letter-spacing:.04em}' +
    '.data-table td{padding:8px 7px;border:1px solid #dce4ed;vertical-align:top;overflow-wrap:anywhere}' +
    '.data-table tbody tr:nth-child(even) td{background:#f8fafc}' +
    'thead{display:table-header-group}' +
    '.two-col{display:grid;grid-template-columns:1fr 1fr;gap:10px}' +
    '.detail{padding:9px 11px;border:1px solid #dce4ed;border-radius:5px;background:#fbfcfe;overflow-wrap:anywhere}' +
    '.detail b{display:block;margin-bottom:3px;color:#63748a;font-size:9px;text-transform:uppercase;letter-spacing:.05em}' +
    '.tool-group{margin:8px 0;padding:10px 12px;border:1px solid #dce4ed;border-radius:5px;background:#fbfcfe}' +
    '.tool-group-title{color:#00325e;font-weight:700;margin-bottom:5px}' +
    '.tool-group ul{margin:0;padding-left:19px}' +
    '.tool-group li{margin:2px 0}' +
    '.empty{color:#738397;font-style:italic;text-align:center;padding:10px}' +
    '.document-footer{position:fixed;left:14mm;right:14mm;bottom:7mm;display:flex;justify-content:space-between;border-top:1px solid #dce4ed;padding-top:5px;color:#738397;font-size:9px;background:#fff}' +
    '.page-number:after{content:"Página " counter(page) " de " counter(pages)}' +
    '.avoid-break{break-inside:avoid;page-break-inside:avoid}' +
     '@media print{html,body{background:#fff}.report{max-width:none;margin:0;padding:0 0 15mm;box-shadow:none}.back-link{color:#1f5eac;text-decoration:underline}.document-footer{position:fixed;background:#fff}.section{break-inside:auto}.section-title,.avoid-break{break-inside:avoid;page-break-inside:avoid}.data-table tr{break-inside:avoid;page-break-inside:avoid}}' +
    '@media screen and (max-width:700px){.report{margin:0;padding:20px 18px 55px}.report-header{align-items:flex-start}.header-meta{font-size:9px}.two-col{grid-template-columns:1fr}.info-table{font-size:10px}.info-table td{width:50%;display:table-cell}.document-footer{left:18px;right:18px}}' +
    '</style></head><body>' +
    '<main class="report">' +
     '<header class="report-header"><img class="logo" src="' + esc(logo, true) + '" alt="INAPEL"><div class="brand">INAPEL<span>Sistema de Gestión de PQR</span></div><div class="header-meta">Fecha de generación<br><b>' + esc(generado) + '</b></div></header>' +
     '<a class="back-link" href="' + esc(seguimientoUrl) + '">← VOLVER AL SEGUIMIENTO</a>' +
     '<h1 class="document-title">INFORME DE GESTIÓN DE PQR</h1><div class="radicado">' + esc(rad) + '</div>' +
    '<section class="section"><h2 class="section-title">1. Información general</h2><table class="info-table"><tr><td class="label">Radicado</td><td class="value">' + valor(p.radicado, '-') + '</td><td class="label">Cliente</td><td class="value">' + valor(p.cliente, '-') + '</td></tr><tr><td class="label">Tipo de solicitud</td><td class="value">' + valor(p.tipoSol, '-') + '</td><td class="label">Fecha</td><td class="value">' + valor(p.fechaRec, '-') + '</td></tr><tr><td class="label">Estado</td><td class="value">' + valor(p.estado, '-') + '</td><td class="label">Prioridad</td><td class="value">' + valor(p.prioridad, '-') + '</td></tr></table></section>' +
    '<section class="section"><h2 class="section-title">2. Descripción del caso</h2><div class="text-block">' + texto(p.desc, 'No registrado') + '</div></section>' +
     '<section class="section"><h2 class="section-title">3. Productos involucrados</h2><table class="data-table"><thead><tr><th>Línea</th><th>Producto</th><th>Detalle / presentación</th><th>Referencia</th><th>Lote/OP</th><th>Cantidad</th><th>Unidad</th><th>Documento</th></tr></thead><tbody>' + prods + '</tbody></table></section>' +
    '<section class="section"><h2 class="section-title">4. Investigación y análisis</h2><div class="two-col"><div class="detail"><b>Responsable de investigación</b>' + valor(inv.resp, '-') + '</div><div class="detail"><b>Cargo</b>' + valor(inv.cargo, '-') + '</div><div class="detail"><b>Causa asignada</b>' + valor(inv.causa, '-') + '</div><div class="detail"><b>Departamentos involucrados</b>' + valor(inv.deptos, '-') + '</div></div><div class="detail" style="margin-top:10px"><b>Herramientas utilizadas</b>' + herramientasHtml + '</div></section>' +
    '<section class="section"><h2 class="section-title">5. Resultado de la investigación</h2><div class="detail"><b>Respuesta detallada de Calidad</b><div class="text-block" style="margin-top:7px">' + texto(respuestaCalidad, 'No registrado') + '</div></div></section>' +
    '<section class="section"><h2 class="section-title">6. Gestión comercial</h2><table class="info-table"><tr><td class="label">Acciones tomadas</td><td class="value">' + valor(inv.acc, '-') + '</td><td class="label">Notificación al cliente</td><td class="value">' + valor(inv.notif, '-') + '</td></tr><tr><td class="label">Fecha de respuesta</td><td class="value">' + valor(inv.fResp, '-') + '</td><td class="label">Fecha de cierre</td><td class="value">' + valor(inv.fCierre, '-') + '</td></tr><tr><td class="label">Estado de cierre</td><td class="value" colspan="3">' + valor(inv.cierre, '-') + '</td></tr></table></section>' +
    '<section class="section"><h2 class="section-title">7. Respuesta al cliente</h2><div class="text-block">' + texto(respuestaComercial, 'No registrado') + '</div></section>' +
    '</main><footer class="document-footer"><span>INAPEL · Sistema de Gestión de PQR</span><span>Documento generado automáticamente</span><span class="page-number"></span></footer>' +
    '</body></html>';
  var w = window.open();
  if (w) {
    w.document.write(html);
    w.document.close();
  }
}
