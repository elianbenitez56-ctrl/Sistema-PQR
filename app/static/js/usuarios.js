// ── GESTIÓN DE USUARIOS ─────────────────────────────────────────────────
var usuariosCache = null;

function crearUsuarioModal() {
  oModal('Agregar usuario',
    '<div class="form-section">Datos personales</div>' +
    '<div class="form-grid">' +
      '<div class="field full"><label for="nu-nombre">Nombre completo</label>' +
        '<input type="text" id="nu-nombre" placeholder="Nombre completo del usuario" autocomplete="off"></div>' +
      '<div class="field"><label for="nu-documento">Documento</label>' +
        '<input type="text" id="nu-documento" placeholder="Número de identificación" autocomplete="off"></div>' +
      '<div class="field"><label for="nu-correo">Correo electrónico</label>' +
        '<input type="email" id="nu-correo" placeholder="usuario@empresa.com" autocomplete="off"></div>' +
      '<div class="field"><label for="nu-telefono">Teléfono</label>' +
        '<input type="tel" id="nu-telefono" placeholder="310 123 4567" autocomplete="off"></div>' +
    '</div>' +
    '<div class="form-section">Datos de acceso</div>' +
    '<div class="form-grid">' +
      '<div class="field"><label for="nu-usuario">Usuario</label>' +
        '<input type="text" id="nu-usuario" placeholder="Nombre de usuario" autocomplete="off"></div>' +
      '<div class="field"><label for="nu-pass">Contraseña</label>' +
        '<input type="password" id="nu-pass" placeholder="Mínimo 6 caracteres" autocomplete="new-password"></div>' +
      '<div class="field"><label for="nu-pass2">Confirmar contraseña</label>' +
        '<input type="password" id="nu-pass2" placeholder="Confirmar contraseña" autocomplete="new-password"></div>' +
    '</div>' +
    '<div class="form-section">Configuración</div>' +
    '<div class="form-grid">' +
      '<div class="field"><label for="nu-rol">Rol</label>' +
        '<select id="nu-rol" onchange="toggleLineaRol()">' +
          '<option value="VENDEDOR">VENDEDOR</option>' +
          '<option value="LIDER_CALIDAD">LÍDER DE CALIDAD</option>' +
          '<option value="LIDER_COMERCIAL">LÍDER COMERCIAL</option>' +
          '<option value="COORDINADORA COMERCIAL">COORDINADORA COMERCIAL</option>' +
          '<option value="DIRECTORA COMERCIAL">DIRECTORA COMERCIAL</option>' +
          '<option value="COMERCIAL">COMERCIAL</option>' +
          '<option value="DIRECTOR DE PRODUCCION">DIRECTOR DE PRODUCCION</option>' +
          '<option value="ADMIN">ADMIN</option>' +
        '</select></div>' +
      '<div class="field"><label for="nu-linea">Línea de producto</label>' +
        '<select id="nu-linea"><option value="INAPEL">INAPEL</option><option value="TOROFIL">TOROFIL</option></select></div>' +
      '<div class="field"><label for="nu-empresa">Empresa</label>' +
        '<select id="nu-empresa"><option value="INAPEL">INAPEL</option><option value="TOROFIL">TOROFIL</option><option value="OTRA">OTRA</option></select></div>' +
      '<div class="field"><label for="nu-estado">Estado</label>' +
        '<select id="nu-estado"><option value="1">Activo</option><option value="0">Inactivo</option></select></div>' +
    '</div>' +
    '<p id="nu-err" class="gate-error" role="alert" style="min-height:16px"></p>' +
    '<div class="action-row">' +
      '<button class="btn" onclick="cModal()">Cancelar</button>' +
      '<button class="btn btn-primary" onclick="guardarNuevoUsuario()">Crear usuario</button>' +
    '</div>');
  setTimeout(function() {
    var inp = document.getElementById('nu-nombre');
    if (inp) inp.focus();
  }, 100);
}

function toggleLineaRol() {
  var rol = document.getElementById('nu-rol');
  var linea = document.getElementById('nu-linea');
  if (!rol || !linea) return;
  var f = linea.closest('.field');
  if (f) f.style.display = rol.value === 'VENDEDOR' ? '' : 'none';
}

function guardarNuevoUsuario() {
  var nombre = document.getElementById('nu-nombre').value.trim();
  var documento = document.getElementById('nu-documento').value.trim();
  var correo = document.getElementById('nu-correo').value.trim();
  var telefono = document.getElementById('nu-telefono').value.trim();
  var usuario = document.getElementById('nu-usuario').value.trim();
  var rol = document.getElementById('nu-rol').value;
  var linea = document.getElementById('nu-linea').value;
  var empresa = document.getElementById('nu-empresa').value;
  var estado = document.getElementById('nu-estado').value;
  var pass = document.getElementById('nu-pass').value;
  var pass2 = document.getElementById('nu-pass2').value;
  var err = document.getElementById('nu-err');

  if (!nombre || !usuario || !pass) { err.textContent = 'Nombre, usuario y contraseña son obligatorios.'; return; }
  if (pass !== pass2) { err.textContent = 'Las contraseñas no coinciden.'; return; }
  if (pass.length < 6) { err.textContent = 'La contraseña debe tener al menos 6 caracteres.'; return; }
  if (!/^[A-Za-z0-9._@-]+$/.test(usuario)) { err.textContent = 'El usuario solo puede contener letras, números y los símbolos . _ @ -'; return; }
  if (usuario.length < 3) { err.textContent = 'El usuario debe tener al menos 3 caracteres.'; return; }
  if (documento && !/^\d+$/.test(documento)) { err.textContent = 'El documento solo puede contener números.'; return; }
  if (correo && !/^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$/.test(correo)) { err.textContent = 'Ingrese un correo electrónico válido.'; return; }
  var telDigit = telefono.replace(/\D/g, '');
  if (telefono && (telDigit.length < 7 || telDigit.length > 10)) { err.textContent = 'El teléfono debe tener entre 7 y 10 dígitos.'; return; }

  var body = { nombre: nombre, documento: documento, correo: correo, telefono: telefono, usuario: usuario, contrasena: pass, rol: rol, linea_producto: linea, empresa: empresa, activo: estado === '1' };

  fetch('/api/usuarios', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  })
  .then(function(r) {
    return r.json().then(function(d) { return { status: r.status, data: d }; });
  })
  .then(function(res) {
    if (!res.data.ok) {
      err.textContent = res.data.mensaje || 'No fue posible crear el usuario.';
      return;
    }
    cModal();
    toast('Usuario creado correctamente.', 'success');
    usuariosCache = null;
    renderUsuarios();
  })
  .catch(function(e) {
    console.error(e);
    err.textContent = 'Error de conexión con el servidor.';
  });
}

function renderUsuarios() {
  if (!usuAuth) return;
  if (!usuariosCache) {
    cargarUsuarios().then(renderUsuarios);
    return;
  }
  var q = (document.getElementById('us-q').value || '').toLowerCase();
  var data = usuariosCache.filter(function(u) {
    if (!q) return true;
    return (u.nombre || '').toLowerCase().indexOf(q) > -1
        || (u.usuario || '').toLowerCase().indexOf(q) > -1
        || (u.documento || '').toLowerCase().indexOf(q) > -1
        || (u.correo || '').toLowerCase().indexOf(q) > -1
        || fmtTel(u.telefono).toLowerCase().indexOf(q) > -1;
  });
  var tbody = document.getElementById('us-tb');
  var empty = document.getElementById('us-empty');
  if (!tbody || !empty) return;
  tbody.innerHTML = '';
  empty.style.display = data.length ? 'none' : 'block';
  var puedeEditar = currentUser && currentUser.rol === 'ADMIN';
  data.forEach(function(u) {
    var tr = document.createElement('tr');
    tr.innerHTML =
      '<td>' + (u.nombre || '—') + '</td>' +
      '<td>' + (u.documento || '—') + '</td>' +
      '<td><span style="font-family:\'Courier New\',monospace;font-weight:600">' + u.usuario + '</span></td>' +
      '<td><span class="cell-email" title="' + (u.correo || '') + '">' + (u.correo || '—') + '</span></td>' +
      '<td>' + fmtTel(u.telefono) + '</td>' +
      '<td>' + String(u.rol || '').replace(/_/g, ' ') + '</td>' +
      '<td>' + (u.linea_producto || '—') + '</td>' +
      '<td><span class="' + (u.activo ? 'badge bs-cer' : 'badge bs-nop') + '">' + (u.activo ? 'Activo' : 'Inactivo') + '</span></td>' +
      '<td style="text-align:center">' +
        (puedeEditar ? '<button class="btn btn-xs" title="Editar usuario" onclick="editarUsuario(' + u.id + ')">✏️ Editar</button> ' : '') +
        '<button class="btn btn-xs" onclick="editarCredenciales(' + u.id + ')">Editar credenciales</button> ' +
        '<button class="btn btn-xs btn-danger" title="Eliminar usuario" onclick="mEliminarUsuario(' + u.id + ')">🗑 Eliminar</button>' +
      '</td>';
    tbody.appendChild(tr);
  });
}

function fmtTel(t) {
  if (!t) return '—';
  var d = String(t).replace(/\D/g, '');
  return d.length === 10 ? d.slice(0,3) + ' ' + d.slice(3,6) + ' ' + d.slice(6) : d;
}

function cargarUsuarios() {
  return fetch('/api/usuarios', { cache: 'no-store' })
    .then(function(r) { return r.json(); })
    .then(function(d) {
      usuariosCache = d.ok ? (d.usuarios || []) : [];
    })
    .catch(function(err) {
      console.error(err);
      usuariosCache = [];
    });
}

function editarCredenciales(uid) {
  if (!usuariosCache) return;
  var u = null;
  for (var i = 0; i < usuariosCache.length; i++) {
    if (usuariosCache[i].id === uid) { u = usuariosCache[i]; break; }
  }
  if (!u) return;
  if (u.rol === 'ADMIN' && currentUser && currentUser.rol === 'LIDER_CALIDAD') {
    toast('No puede modificar las credenciales de usuarios administradores.', 'error');
    return;
  }
  var nombre = u.nombre || 'Usuario';
  oModal('Editar credenciales',
    '<div style="margin-bottom:14px;padding:10px 12px;background:var(--surface-dim);border-radius:8px">' +
      '<div style="font-size:11px;color:var(--on-surface-variant)">Usuario seleccionado</div>' +
      '<div style="font-size:14px;font-weight:600">' + nombre + ' · <span style="font-family:\'Courier New\',monospace">' + u.usuario + '</span></div>' +
    '</div>' +
    '<div class="form-grid">' +
      '<div class="field full"><label for="uc-usuario">Nuevo usuario</label>' +
        '<input type="text" id="uc-usuario" value="' + u.usuario + '" placeholder="Nombre de usuario" autocomplete="off">' +
        '<small style="color:var(--on-surface-variant)">El usuario actual se conserva si no se cambia.</small></div>' +
      '<div class="field"><label for="uc-pass">Nueva contraseña</label>' +
        '<input type="password" id="uc-pass" placeholder="Nueva contraseña" autocomplete="new-password"></div>' +
      '<div class="field"><label for="uc-pass2">Confirmar contraseña</label>' +
        '<input type="password" id="uc-pass2" placeholder="Confirmar contraseña" autocomplete="new-password"></div>' +
    '</div>' +
    '<p id="uc-err" class="gate-error" role="alert" style="min-height:16px"></p>' +
    '<div class="action-row">' +
      '<button class="btn" onclick="cModal()">Cancelar</button>' +
      '<button class="btn btn-primary" onclick="guardarCredenciales(' + u.id + ')">Guardar cambios</button>' +
    '</div>');
  setTimeout(function() {
    var inp = document.getElementById('uc-usuario');
    if (inp) { inp.focus(); inp.select(); }
  }, 100);
}

function guardarCredenciales(uid) {
  var usuario = document.getElementById('uc-usuario').value.trim();
  var pass = document.getElementById('uc-pass').value;
  var pass2 = document.getElementById('uc-pass2').value;
  var err = document.getElementById('uc-err');
  if (pass !== pass2) { err.textContent = 'Las contraseñas no coinciden.'; return; }
  if (!usuario && !pass) { err.textContent = 'Ingrese un nuevo usuario o una nueva contraseña.'; return; }
  var body = { usuario: usuario, contrasena: pass };
  fetch('/api/usuarios/' + uid + '/credenciales', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  })
  .then(function(r) {
    return r.json().then(function(d) { return { status: r.status, data: d }; });
  })
  .then(function(res) {
    if (!res.data.ok) {
      err.textContent = res.data.mensaje || 'No fue posible guardar los cambios.';
      return;
    }
    cModal();
    toast(res.data.mensaje || 'Credenciales actualizadas correctamente.', 'success');
    usuariosCache = null;
    renderUsuarios();
  })
  .catch(function(e) {
    console.error(e);
    err.textContent = 'Error de conexión con el servidor.';
  });
}

// ── ELIMINAR USUARIO ────────────────────────────────────────────────────
function mEliminarUsuario(uid) {
  if (!usuariosCache) return;
  var u = null;
  for (var i = 0; i < usuariosCache.length; i++) {
    if (usuariosCache[i].id === uid) { u = usuariosCache[i]; break; }
  }
  if (!u) return;
  var rolTxt = String(u.rol || '').replace(/_/g, ' ');
  oModal('Eliminar usuario',
    '<div style="display:flex;flex-direction:column;align-items:center;text-align:center;padding:6px 0 20px">' +
    '<div style="width:54px;height:54px;border-radius:50%;background:var(--error-bg);display:flex;align-items:center;justify-content:center;margin-bottom:16px">' +
    '<span class="material-symbols-outlined" style="font-size:27px;color:var(--error)">delete</span></div>' +
    '<p style="font-size:15px;font-weight:600;margin-bottom:6px;color:var(--on-surface)">¿Está seguro de eliminar este usuario?</p>' +
    '<p style="font-size:13px;color:var(--on-surface-variant);max-width:340px;line-height:1.55;margin-bottom:12px">Esta acción eliminará el acceso del usuario al sistema y no podrá deshacerse.</p>' +
    '<div style="width:100%;max-width:300px;background:var(--surface-dim);border:1px solid var(--outline-soft);border-radius:10px;padding:12px 14px;text-align:left;font-size:13px">' +
      '<div style="display:flex;justify-content:space-between;gap:10px;padding:3px 0"><span style="color:var(--on-surface-variant)">Nombre</span><strong>' + (u.nombre || '—') + '</strong></div>' +
      '<div style="display:flex;justify-content:space-between;gap:10px;padding:3px 0"><span style="color:var(--on-surface-variant)">Rol</span><strong>' + rolTxt + '</strong></div>' +
      '<div style="display:flex;justify-content:space-between;gap:10px;padding:3px 0"><span style="color:var(--on-surface-variant)">Usuario</span><strong style="font-family:\'Courier New\',monospace">' + (u.usuario || '—') + '</strong></div>' +
    '</div></div>' +
    '<div style="display:flex;gap:9px;justify-content:flex-end">' +
    '<button class="btn" onclick="cModal()">Cancelar</button>' +
    '<button class="btn btn-danger" onclick="eliminarUsuario(' + u.id + ')">🗑 Eliminar usuario</button></div>');
}

function eliminarUsuario(uid) {
  fetch('/api/usuarios/' + uid, { method: 'DELETE' })
  .then(function(r) {
    return r.json().then(function(d) { return { status: r.status, data: d }; });
  })
  .then(function(res) {
    cModal();
    if (res.data.ok) {
      toast(res.data.mensaje || 'Usuario eliminado correctamente.', 'success');
      usuariosCache = null;
      renderUsuarios();
    } else {
      toast(res.data.mensaje || 'No fue posible eliminar el usuario.', 'error');
    }
  })
  .catch(function(e) {
    console.error(e);
    cModal();
    toast('Error de conexión con el servidor. No fue posible eliminar el usuario.', 'error');
  });
}

// ── EDITAR USUARIO (ADMIN) ──────────────────────────────────────────────
function editarUsuario(uid) {
  if (!usuariosCache) return;
  if (currentUser && currentUser.rol !== 'ADMIN') {
    toast('No tiene permisos para editar usuarios.', 'error');
    return;
  }
  var u = null;
  for (var i = 0; i < usuariosCache.length; i++) {
    if (usuariosCache[i].id === uid) { u = usuariosCache[i]; break; }
  }
  if (!u) return;
  var lineaVisible = u.rol === 'VENDEDOR' ? '' : 'none';
  oModal('Editar usuario',
    '<div style="margin-bottom:6px;padding:10px 12px;background:var(--surface-dim);border-radius:8px">' +
      '<div style="font-size:11px;color:var(--on-surface-variant)">Usuario seleccionado</div>' +
      '<div style="font-size:14px;font-weight:600">' + (u.nombre || 'Usuario') + ' · <span style="font-family:\'Courier New\',monospace">' + u.usuario + '</span></div>' +
    '</div>' +
    '<div class="form-section">Datos personales</div>' +
    '<div class="form-grid">' +
      '<div class="field full"><label for="ue-nombre">Nombre completo</label>' +
        '<input type="text" id="ue-nombre" value="' + u.nombre + '" autocomplete="off"></div>' +
      '<div class="field"><label for="ue-documento">Documento</label>' +
        '<input type="text" id="ue-documento" value="' + (u.documento || '') + '" placeholder="Número de identificación" autocomplete="off"></div>' +
      '<div class="field"><label for="ue-correo">Correo electrónico</label>' +
        '<input type="email" id="ue-correo" value="' + (u.correo || '') + '" placeholder="usuario@empresa.com" autocomplete="off"></div>' +
      '<div class="field"><label for="ue-telefono">Teléfono</label>' +
        '<input type="tel" id="ue-telefono" value="' + (u.telefono || '') + '" placeholder="310 123 4567" autocomplete="off"></div>' +
    '</div>' +
    '<div class="form-section">Datos de acceso</div>' +
    '<div class="form-grid">' +
      '<div class="field full"><label for="ue-usuario">Usuario</label>' +
        '<input type="text" id="ue-usuario" value="' + u.usuario + '" autocomplete="off"></div>' +
    '</div>' +
    '<div class="form-section">Configuración</div>' +
    '<div class="form-grid">' +
      '<div class="field"><label for="ue-rol">Rol</label>' +
        '<select id="ue-rol" onchange="toggleLineaRolEdit()">' +
          '<option value="VENDEDOR"' + (u.rol === 'VENDEDOR' ? ' selected' : '') + '>VENDEDOR</option>' +
          '<option value="LIDER_CALIDAD"' + (u.rol === 'LIDER_CALIDAD' ? ' selected' : '') + '>LÍDER DE CALIDAD</option>' +
          '<option value="LIDER_COMERCIAL"' + (u.rol === 'LIDER_COMERCIAL' ? ' selected' : '') + '>LÍDER COMERCIAL</option>' +
          '<option value="COORDINADORA COMERCIAL"' + (u.rol === 'COORDINADORA COMERCIAL' ? ' selected' : '') + '>COORDINADORA COMERCIAL</option>' +
          '<option value="DIRECTORA COMERCIAL"' + (u.rol === 'DIRECTORA COMERCIAL' ? ' selected' : '') + '>DIRECTORA COMERCIAL</option>' +
          '<option value="COMERCIAL"' + (u.rol === 'COMERCIAL' ? ' selected' : '') + '>COMERCIAL</option>' +
          '<option value="DIRECTOR DE PRODUCCION"' + (u.rol === 'DIRECTOR DE PRODUCCION' ? ' selected' : '') + '>DIRECTOR DE PRODUCCION</option>' +
          '<option value="ADMIN"' + (u.rol === 'ADMIN' ? ' selected' : '') + '>ADMIN</option>' +
        '</select></div>' +
      '<div class="field" id="ue-linea-field" style="display:' + lineaVisible + '"><label for="ue-linea">Línea de producto</label>' +
        '<select id="ue-linea">' +
          '<option value="INAPEL"' + (u.linea_producto === 'INAPEL' ? ' selected' : '') + '>INAPEL</option>' +
          '<option value="TOROFIL"' + (u.linea_producto === 'TOROFIL' ? ' selected' : '') + '>TOROFIL</option>' +
        '</select></div>' +
      '<div class="field"><label for="ue-estado">Estado</label>' +
        '<select id="ue-estado">' +
          '<option value="1"' + (u.activo ? ' selected' : '') + '>Activo</option>' +
          '<option value="0"' + (!u.activo ? ' selected' : '') + '>Inactivo</option>' +
        '</select></div>' +
    '</div>' +
    '<p id="ue-err" class="gate-error" role="alert" style="min-height:16px"></p>' +
    '<div class="action-row">' +
      '<button class="btn" onclick="cModal()">Cancelar</button>' +
      '<button class="btn btn-primary" onclick="guardarUsuarioEditado(' + u.id + ')">Guardar cambios</button>' +
    '</div>');
  setTimeout(function() {
    var inp = document.getElementById('ue-nombre');
    if (inp) inp.focus();
  }, 100);
}

function toggleLineaRolEdit() {
  var rol = document.getElementById('ue-rol');
  var f = document.getElementById('ue-linea-field');
  if (!rol || !f) return;
  f.style.display = rol.value === 'VENDEDOR' ? '' : 'none';
}

function guardarUsuarioEditado(uid) {
  var nombre = document.getElementById('ue-nombre').value.trim();
  var documento = document.getElementById('ue-documento').value.trim();
  var correo = document.getElementById('ue-correo').value.trim();
  var telefono = document.getElementById('ue-telefono').value.trim();
  var usuario = document.getElementById('ue-usuario').value.trim();
  var rol = document.getElementById('ue-rol').value;
  var linea = document.getElementById('ue-linea').value;
  var estado = document.getElementById('ue-estado').value;
  var err = document.getElementById('ue-err');

  if (!nombre) { err.textContent = 'El nombre es obligatorio.'; return; }
  if (!usuario) { err.textContent = 'El nombre de usuario es obligatorio.'; return; }
  if (!/^[A-Za-z0-9._@-]+$/.test(usuario)) { err.textContent = 'El usuario solo puede contener letras, números y los símbolos . _ @ -'; return; }
  if (usuario.length < 3) { err.textContent = 'El usuario debe tener al menos 3 caracteres.'; return; }
  if (documento && !/^\d+$/.test(documento)) { err.textContent = 'El documento solo puede contener números.'; return; }
  if (correo && !/^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$/.test(correo)) { err.textContent = 'Ingrese un correo electrónico válido.'; return; }
  var telDigit = telefono.replace(/\D/g, '');
  if (telefono && (telDigit.length < 7 || telDigit.length > 10)) { err.textContent = 'El teléfono debe tener entre 7 y 10 dígitos.'; return; }

  var body = { nombre: nombre, documento: documento, correo: correo, telefono: telefono, usuario: usuario, rol: rol, linea_producto: rol === 'VENDEDOR' ? linea : '', activo: estado === '1' };

  fetch('/api/usuarios/' + uid, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  })
  .then(function(r) {
    return r.json().then(function(d) { return { status: r.status, data: d }; });
  })
  .then(function(res) {
    if (!res.data.ok) {
      err.textContent = res.data.mensaje || 'No fue posible guardar los cambios.';
      return;
    }
    cModal();
    toast(res.data.mensaje || 'Usuario actualizado correctamente.', 'success');
    usuariosCache = null;
    renderUsuarios();
  })
  .catch(function(e) {
    console.error(e);
    err.textContent = 'Error de conexión con el servidor.';
  });
}
