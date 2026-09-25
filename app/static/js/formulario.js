// ── FORM STEPS ────────────────────────────────────────────────────────────
var currentStep = 1;
function goStep(n) {
  if (n < 1 || n > 5 || n === currentStep) return;
  if (n > currentStep) {
    var invalido = validarRangoPasos(currentStep, n);
    if (invalido !== null) {
      if (invalido === currentStep) {
        ocultarAlertaPasos();
        window.scrollTo({top: document.getElementById('form-progress').offsetTop - 80, behavior:'smooth'});
        return;
      }
      goStep(invalido);
      return;
    }
  }
  document.querySelectorAll('.form-step').forEach(function(s){ s.classList.remove('on'); });
  document.querySelectorAll('.progress-step').forEach(function(s){ s.classList.remove('on'); });
  document.querySelectorAll('.progress-line').forEach(function(l){ l.classList.remove('on'); });
  document.querySelector('.form-step[data-step="' + n + '"]').classList.add('on');
  document.querySelector('.progress-step[data-step="' + n + '"]').classList.add('on');
  for (var i = 1; i < n; i++) {
    var ps = document.querySelector('.progress-step[data-step="' + i + '"]');
    if (ps) ps.classList.add('done');
    var pl = document.querySelectorAll('.progress-line')[i-1];
    if (pl) pl.classList.add('done');
  }
  for (var i = n; i <= 5; i++) {
    var ps = document.querySelector('.progress-step[data-step="' + i + '"]');
    if (ps) ps.classList.remove('done');
    var pl = document.querySelectorAll('.progress-line')[i-1];
    if (pl && i > 1) pl.classList.remove('done');
  }
  currentStep = n;
  window.scrollTo({top: document.getElementById('form-progress').offsetTop - 80, behavior:'smooth'});
}
function nextStep(n) { goStep(n); }
function prevStep(n) { goStep(n); }

// ── VALIDACIÓN DE PASOS ──────────────────────────────────────────────────
function marcarCampo(campo, mensaje) {
  if (!campo) return;
  campo.classList.add('error');
  if (campo.parentElement) {
    var aviso = campo.parentElement.querySelector('small[data-step-err]');
    if (aviso) {
      aviso.textContent = mensaje;
    } else {
      aviso = document.createElement('small');
      aviso.setAttribute('data-step-err', '1');
      aviso.style.cssText = 'display:block;font-size:11.5px;color:var(--error);margin-top:4px;font-weight:500';
      aviso.textContent = mensaje;
      campo.parentElement.appendChild(aviso);
    }
  }
}

function quitarErrorCampo(campo) {
  if (!campo) return;
  campo.classList.remove('error');
  if (campo.parentElement) {
    var aviso = campo.parentElement.querySelector('small[data-step-err]');
    if (aviso) aviso.remove();
  }
}

function ocultarAlertaPasos() {
  var errores = document.querySelectorAll('.form-step input.error, .form-step select.error, .form-step textarea.error');
  var alerta = document.getElementById('step-alert');
  if (alerta) alerta.style.display = errores.length ? 'block' : 'none';
}

function validarPaso(n) {
  var paso = document.querySelector('.form-step[data-step="' + n + '"]');
  if (!paso) return true;
  var ok = true;
  paso.querySelectorAll('.field.required input, .field.required select, .field.required textarea').forEach(function(campo) {
    var valor = (campo.value || '').trim();
    if (!valor) {
      marcarCampo(campo, campo.tagName === 'SELECT' ? 'Debe seleccionar una opción.' : 'Este campo es obligatorio.');
      ok = false;
    } else {
      quitarErrorCampo(campo);
    }
  });
  paso.querySelectorAll('input[type="email"]').forEach(function(campo) {
    var valor = (campo.value || '').trim();
    if (valor && !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(valor)) {
      marcarCampo(campo, 'Debe ingresar un correo válido.');
      ok = false;
    } else {
      quitarErrorCampo(campo);
    }
  });
  ocultarAlertaPasos();
  return ok;
}

function validarRangoPasos(desde, hasta) {
  for (var s = desde; s < hasta; s++) {
    if (!validarPaso(s)) return s;
  }
  return null;
}

document.addEventListener('input', function(e) {
  var t = e.target;
  if (t && t.closest && t.closest('.form-step')) {
    quitarErrorCampo(t);
    ocultarAlertaPasos();
  }
});
document.addEventListener('change', function(e) {
  var t = e.target;
  if (t && t.closest && t.closest('.form-step')) {
    quitarErrorCampo(t);
    ocultarAlertaPasos();
  }
});

// ── TABLA PRODUCTOS ────────────────────────────────────────────────────
function addRow() {
  var tbody = document.getElementById('prod-tbody');
  var row = tbody.rows[0].cloneNode(true);
  row.querySelectorAll('input, textarea').forEach(function(i) { i.value = ''; });
  row.querySelectorAll('select').forEach(function(s) {
    if (s.classList.contains('prod-linea')) s.value = '';
    else if (s.classList.contains('catalog-choice')) {
      s.innerHTML = '';
      s.style.display = 'none';
    } else {
      s.selectedIndex = 0;
    }
  });
  row.querySelectorAll('.catalog-message').forEach(function(m) { m.textContent = ''; });
  limpiarCatalogoFila(row);
  var tipoDocumento = row.querySelector('.prod-tipo-doc');
  if (tipoDocumento) tipoDocumento.value = 'Factura de venta';
  row._catalogoProducto = null;
  row._catalogoOpciones = [];
  tbody.appendChild(row);
}
function rmRow(btn) {
  var tbody = document.getElementById('prod-tbody');
  if (tbody.rows.length > 1) btn.closest('tr').remove();
}
function catalogoFila(elemento) {
  return elemento && elemento.closest ? elemento.closest('#prod-tbody tr') : null;
}
function catalogoMensaje(row, texto) {
  var mensaje = row && row.querySelector('.catalog-message');
  if (mensaje) mensaje.textContent = texto || '';
}
function limpiarCatalogoFila(row) {
  if (!row) return;
  row._catalogoSolicitud = (row._catalogoSolicitud || 0) + 1;
  row._catalogoProducto = null;
  row._catalogoOpciones = [];
  var choice = row.querySelector('.catalog-choice');
  if (choice) {
    choice.innerHTML = '';
    choice.style.display = 'none';
    choice.value = '';
  }
  row.querySelectorAll('.catalog-field').forEach(function(campo) { campo.value = ''; });
  var unidad = row.querySelector('.catalog-unidad');
  if (unidad) {
    unidad.disabled = true;
    unidad.readOnly = true;
    unidad.placeholder = 'Catálogo';
  }
  catalogoMensaje(row, '');
}
function aplicarCatalogoFila(row, producto) {
  if (!row || !producto) return;
  row._catalogoProducto = producto;
  var valores = {
    '.catalog-producto': producto.producto || '',
    '.catalog-detalle': producto.detalle_presentacion || '',
    '.catalog-unidad': producto.unidad || ''
  };
  Object.keys(valores).forEach(function(selector) {
    var campo = row.querySelector(selector);
    if (campo) campo.value = valores[selector];
  });
  var unidad = row.querySelector('.catalog-unidad');
  var unidadCatalogo = String(producto.unidad || '').trim();
  if (unidad) {
    unidad.disabled = Boolean(unidadCatalogo);
    unidad.readOnly = Boolean(unidadCatalogo);
    unidad.placeholder = unidadCatalogo ? 'Catálogo' : 'Diligenciar unidad';
  }
  var choice = row.querySelector('.catalog-choice');
  if (choice) {
    choice.innerHTML = '';
    choice.style.display = 'none';
  }
  catalogoMensaje(row, '');
}
function mostrarOpcionesCatalogo(row, productos) {
  var choice = row.querySelector('.catalog-choice');
  if (!choice) return;
  row._catalogoOpciones = productos || [];
  choice.innerHTML = '';
  var inicial = document.createElement('option');
  inicial.value = '';
  inicial.textContent = 'Seleccione una coincidencia...';
  choice.appendChild(inicial);
  row._catalogoOpciones.forEach(function(producto, indice) {
    var opcion = document.createElement('option');
    opcion.value = String(indice);
    opcion.textContent = [producto.producto, producto.detalle_presentacion]
      .filter(function(valor) { return String(valor || '').trim(); })
      .join(' · ') || producto.referencia_siesa;
    choice.appendChild(opcion);
  });
  choice.value = '';
  choice.style.display = 'block';
  catalogoMensaje(row, 'Seleccione una coincidencia.');
}
function seleccionarCatalogo(select) {
  var row = catalogoFila(select);
  var indice = select.value === '' ? -1 : Number(select.value);
  if (!row || indice < 0 || !row._catalogoOpciones[indice]) {
    limpiarCatalogoFila(row);
    return;
  }
  aplicarCatalogoFila(row, row._catalogoOpciones[indice]);
}
function consultarCatalogoFila(row) {
  if (!row) return;
  var lineaCampo = row.querySelector('.prod-linea');
  var referenciaCampo = row.querySelector('.prod-ref');
  var linea = lineaCampo ? lineaCampo.value : '';
  var referencia = referenciaCampo ? referenciaCampo.value.trim() : '';
  if (!linea || !referencia) return;

  var solicitud = (row._catalogoSolicitud || 0) + 1;
  row._catalogoSolicitud = solicitud;
  fetch('/api/catalogo/productos?linea=' + encodeURIComponent(linea) + '&referencia_siesa=' + encodeURIComponent(referencia), { cache: 'no-store' })
    .then(function(respuesta) { return respuesta.json(); })
    .then(function(data) {
      if (row._catalogoSolicitud !== solicitud) return;
      limpiarCatalogoFila(row);
      if (!data.ok) {
        catalogoMensaje(row, data.mensaje || 'No fue posible consultar el catálogo.');
      } else if (!data.productos || !data.productos.length) {
        catalogoMensaje(row, 'Referencia no encontrada en el catálogo.');
      } else if (data.productos.length === 1) {
        aplicarCatalogoFila(row, data.productos[0]);
      } else {
        mostrarOpcionesCatalogo(row, data.productos);
      }
    })
    .catch(function(error) {
      if (row._catalogoSolicitud !== solicitud) return;
      console.error('Error consultando catálogo:', error);
      limpiarCatalogoFila(row);
      catalogoMensaje(row, 'No fue posible consultar el catálogo.');
    });
}
function programarConsultaCatalogo(row) {
  if (!row) return;
  clearTimeout(row._catalogoTimer);
  limpiarCatalogoFila(row);
  var referencia = row.querySelector('.prod-ref');
  if (!referencia || referencia.value.trim().length < 2 || !row.querySelector('.prod-linea').value) return;
  row._catalogoTimer = setTimeout(function() { consultarCatalogoFila(row); }, 350);
}
function catalogoReferenciaCambio(input) {
  programarConsultaCatalogo(catalogoFila(input));
}
function catalogoLineaCambio(select) {
  programarConsultaCatalogo(catalogoFila(select));
}
function showFiles() {
  var files = document.getElementById('f-files').files;
  var list = document.getElementById('file-list');
  list.innerHTML = '';
  for (var i = 0; i < files.length; i++) {
    var li = document.createElement('li');
    li.innerHTML = '<span class="material-symbols-outlined" style="font-size:16px;color:var(--blue)">description</span> ' + files[i].name + ' <span style="color:var(--on-surface-variant);margin-left:auto">' + (files[i].size/1024).toFixed(1) + ' KB</span>';
    list.appendChild(li);
  }
}
function getProds() {
  return Array.from(document.querySelectorAll('#prod-tbody tr')).map(function(r) {
    var valor = function(selector) {
      var campo = r.querySelector(selector);
      return campo ? String(campo.value || '').trim() : '';
    };
    var referencia = valor('.prod-ref');
    return {
      linea: valor('.prod-linea'),
      referencia_siesa: referencia,
      detalle_presentacion: valor('.catalog-detalle'),
      producto: valor('.catalog-producto'),
      unidad: valor('.catalog-unidad'),
      lote: valor('.prod-lote'),
      fechaEmp: valor('.prod-fecha'),
      cant: valor('.prod-cantidad'),
      tipoDoc: 'Factura de venta',
      numDoc: valor('.prod-num-doc')
    };
  }).filter(function(p) { return p.referencia_siesa || p.producto || p.lote || p.cant || p.numDoc; });
}
function validarProductosCatalogo() {
  var valido = true;
  document.querySelectorAll('#prod-tbody tr').forEach(function(row) {
    var referencia = row.querySelector('.prod-ref');
    var linea = row.querySelector('.prod-linea');
    var tieneDatos = ['.prod-ref', '.prod-lote', '.prod-fecha', '.prod-cantidad', '.prod-num-doc']
      .some(function(selector) {
        var campo = row.querySelector(selector);
        return campo && String(campo.value || '').trim();
      });
    if (!tieneDatos) return;
    if (!linea || !linea.value || !referencia || !referencia.value.trim() || !row._catalogoProducto) {
      valido = false;
    }
  });
  if (!valido) {
    msg('msg-form', 'Complete la línea y seleccione una referencia válida del catálogo para cada producto.', 'error');
  }
  return valido;
}

// ── GUARDAR PQR ────────────────────────────────────────────────────────
function msjRegistro(rad, data) {
  var base = '&#10003; PQR registrada correctamente.<br><br><strong>Radicado:</strong> ' + rad;
  if (data && data.email_enviado) {
    base += '<br><br>Se envió una confirmación al correo registrado.';
  } else if (data && data.email_estado === 'no_enviado') {
    base += '<br><br>&#9888; No fue posible enviar el correo de confirmación.';
  } else if (data && data.email_estado === 'sin_correo') {
    base += '<br><br>&#8505; La PQR fue registrada correctamente, pero no tiene un correo electrónico registrado para enviar la confirmación.';
  } else if (data && data.email_estado === 'correo_invalido') {
    base += '<br><br>&#9888; No fue posible enviar el correo de confirmación (el correo del cliente no es válido).';
  }
  return base;
}
function toastEmailEstado(data) {
  if (!data) return;
  if (data.email_enviado) {
    toast("Correo de confirmación enviado al cliente", "success", 6000);
  } else if (data.email_estado === 'sin_correo') {
    toast("La PQR no tiene correo registrado: no se envió confirmación", "info", 6000);
  } else {
    toast("No se pudo enviar el correo de confirmación al cliente", "error", 6000);
  }
}
function toastCalidadEstado(data) {
  if (!data) return;
  if (data.notificacion_calidad_enviada) {
    toast("Se notificó a Calidad por correo", "success", 6000);
  } else {
    toast("No se pudo notificar a Calidad por correo" + (data.notificacion_calidad_mensaje ? " (" + data.notificacion_calidad_mensaje + ")" : ""), "error", 6000);
  }
}
function guardar() {
  var req = [
    {id:'f-fecha', label:'Fecha de recepción'},
    {id:'f-recibe', label:'Nombre de quien recibe'},
    {id:'f-medio', label:'Medio de recepción'},
    {id:'f-tipo', label:'Tipo de solicitud'},
    {id:'f-cliente', label:'Nombre del cliente'}
  ];
  var ok = true;
  req.forEach(function(r) {
    var el = document.getElementById(r.id);
    if (!el || !el.value.trim()) {
      if (el) { el.classList.add('error'); }
      ok = false;
    } else {
      if (el) el.classList.remove('error');
    }
  });
  if (!ok) {
    msg('msg-form', 'Complete los campos obligatorios marcados con *.', 'error');
    return;
  }
  if (!validarProductosCatalogo()) return;
  var btnRadicar = document.getElementById('btn-radicar');
  if (btnRadicar && btnRadicar.disabled) return;
  if (btnRadicar) loadBtn(btnRadicar, true);
  var now = new Date();
  var pqr = {
    fechaRec: document.getElementById('f-fecha').value,
    horaRec: document.getElementById('f-hora').value,
    quienRecibe: document.getElementById('f-recibe').value,
    documentoReceptor: document.getElementById('f-doc-rec').value,
    correoReceptor: document.getElementById('f-correo-rec').value,
    telefonoReceptor: document.getElementById('f-tel-rec').value,
    cargo: document.getElementById('f-cargo').value,
    centro: document.getElementById('f-centro').value,
    cargoReceptor: document.getElementById('f-cargo').value,
    areaReceptor: document.getElementById('f-centro').value,
    ciudadRec: document.getElementById('f-ciudad-r').value,
    dptoRec: document.getElementById('f-dpto-r').value,
    medio: document.getElementById('f-medio').value,
    otroMedio: document.getElementById('f-otro-m').value,
    tipoSol: document.getElementById('f-tipo').value,
    cliente: document.getElementById('f-cliente').value,
    nit: document.getElementById('f-nit').value,
    contacto: document.getElementById('f-contacto').value,
    dir: document.getElementById('f-dir').value,
    ciudadCli: document.getElementById('f-ciudad-c').value,
    dptoCli: document.getElementById('f-dpto-c').value,
    tel: document.getElementById('f-tel').value,
    whatsapp: document.getElementById('f-wa').value,
    email: document.getElementById('f-email').value,
    desc: document.getElementById('f-desc').value,
    productos: getProds(),
    tipoEvid: document.getElementById('f-tip-ev').value,
    numEvid: document.getElementById('f-num-ev').value,
    otroEvid: document.getElementById('f-otro-ev-txt').value,
    infoAd: document.getElementById('f-info-ad').value,
    expectativa: document.getElementById('f-exp').value,
    utilizado: document.getElementById('f-util').value,
    prioridad: document.getElementById('f-pri').value
  };

  fetch("/api/pqr", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(pqr) })
  .then(function(response) { return response.json(); })
  .then(function(data) {
    if (!data.ok) { msg('msg-form', 'Error al guardar en el servidor.', 'error'); if (btnRadicar) loadBtn(btnRadicar, false); return; }
    var rad = data.radicado;
    pqr.radicado = rad;
    pqr.savedAt = now.toISOString();
    pqr.estado = 'Recibido';
    pqr.historial = [{ estado: 'Recibido', fecha: now.toISOString() }];
    db.push(pqr);
    guardarDatos();
    dbExcel = null;
    var archivos = document.getElementById("f-files").files;
    if (archivos.length > 0) {
      var formData = new FormData();
      formData.append("radicado", rad);
      formData.append("tipo", document.getElementById("f-tip-ev").value);
      for (var i = 0; i < archivos.length; i++) formData.append("archivos", archivos[i]);
      fetch("/api/evidencias", { method: "POST", body: formData })
      .then(function(r) { return r.json(); })
      .then(function(res) {
        document.getElementById('rad-num').textContent = rad.replace(/-/g, ' · ');
        if (res.ok) {
          msg('msg-form', msjRegistro(rad, data) + '<br><br>Las evidencias fueron cargadas exitosamente.', 'success');
          toast("PQR " + rad + " registrado con evidencias", "success", 5000);
        } else {
          msg('msg-form', msjRegistro(rad, data) + '<br><br>&#9888; PQR registrado, pero las evidencias no se pudieron cargar: ' + (res.mensaje || 'error desconocido') + '.', 'error');
          toast("PQR " + rad + " registrado, pero fallaron las evidencias: " + (res.mensaje || 'error desconocido'), "error", 6000);
        }
        toastEmailEstado(data);
        toastCalidadEstado(data);
        if (btnRadicar) loadBtn(btnRadicar, false);
        setTimeout(limpiar, 5000);
      })
      .catch(function(err) {
        console.error("Error adjuntos:", err);
        toast("PQR " + rad + " registrado, pero hubo un error de conexión al subir las evidencias", "error", 6000);
        toastEmailEstado(data);
        toastCalidadEstado(data);
        if (btnRadicar) loadBtn(btnRadicar, false);
        setTimeout(limpiar, 5000);
      });
    } else {
      document.getElementById('rad-num').textContent = rad.replace(/-/g, ' · ');
      msg('msg-form', msjRegistro(rad, data), 'success');
      toast("PQR " + rad + " registrado exitosamente", "success", 5000);
      toastEmailEstado(data);
      toastCalidadEstado(data);
      if (btnRadicar) loadBtn(btnRadicar, false);
      setTimeout(limpiar, 5000);
    }
  })
  .catch(function(error) {
    console.error(error);
    toast("Error de conexión con el servidor", "error");
    msg('msg-form', 'Error de conexión con el servidor.', 'error');
    if (btnRadicar) loadBtn(btnRadicar, false);
  });
}

// ── LIMPIAR ─────────────────────────────────────────────────────────────
function limpiar() {
  var ids = ['f-fecha','f-hora','f-ciudad-r','f-dpto-r',
             'f-cliente','f-nit','f-contacto','f-dir','f-ciudad-c','f-dpto-c','f-tel',
             'f-wa','f-email','f-desc','f-num-ev','f-info-ad','f-otro-m','f-otro-ev-txt'];
  ids.forEach(function(id) {
    var el = document.getElementById(id);
    if (el) { el.value = ''; el.classList.remove('error'); }
  });
  var sels = ['f-medio','f-tipo','f-tip-ev','f-exp','f-util','f-pri'];
  sels.forEach(function(id) {
    var el = document.getElementById(id);
    if (el) { el.value = ''; el.classList.remove('error'); }
  });
  document.getElementById('f-otro-medio').style.display = 'none';
  document.getElementById('f-otro-ev').style.display = 'none';
  document.getElementById('file-list').innerHTML = '';
  document.getElementById('f-files').value = '';
  var tbody = document.getElementById('prod-tbody');
  while (tbody.rows.length > 1) tbody.deleteRow(1);
  tbody.rows[0].querySelectorAll('input, textarea').forEach(function(i) { i.value = ''; });
  tbody.rows[0].querySelectorAll('select').forEach(function(s) {
    if (s.classList.contains('prod-linea')) s.value = '';
    else if (s.classList.contains('catalog-choice')) {
      s.innerHTML = '';
      s.style.display = 'none';
    } else {
      s.selectedIndex = 0;
    }
  });
  var tipoDocumento = tbody.rows[0].querySelector('.prod-tipo-doc');
  if (tipoDocumento) tipoDocumento.value = 'Factura de venta';
  tbody.rows[0]._catalogoProducto = null;
  tbody.rows[0]._catalogoOpciones = [];
  tbody.rows[0]._catalogoSolicitud = 0;
  var unidadCatalogo = tbody.rows[0].querySelector('.catalog-unidad');
  if (unidadCatalogo) {
    unidadCatalogo.disabled = true;
    unidadCatalogo.readOnly = true;
    unidadCatalogo.placeholder = 'Catálogo';
  }
  catalogoMensaje(tbody.rows[0], '');
  document.getElementById('rad-num').textContent = 'PQR · 2026 · XXXX';
  document.getElementById('msg-form').innerHTML = '';
  document.querySelectorAll('small[data-step-err]').forEach(function(el) { el.remove(); });
  var stepAlerta = document.getElementById('step-alert');
  if (stepAlerta) stepAlerta.style.display = 'none';
  var now = new Date();
  document.getElementById('f-fecha').value = now.toLocaleDateString('en-CA'); // fecha local (no UTC)
  document.getElementById('f-hora').value = now.toTimeString().slice(0, 5);
}
