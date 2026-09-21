# TRZ QUALITY SYSTEM
## Propuesta de Arquitectura, Estructura y Plan de Implementación
**INAPEL / Marfil Escolar y Oficinas S.A.S.**

---

## 1. Principios rectores

Antes de la estructura, cinco decisiones que gobiernan todo lo demás:

1. **Evolución, no reescritura.** El módulo de Muestreo Diario ya funciona en producción con datos reales de seis plantas. TRZ Quality System no lo reemplaza de golpe: lo absorbe como el primer módulo maduro dentro de una arquitectura nueva, y los demás módulos (Laboratorio, Trazabilidad, No Conformidades, PQR, Auditorías) se construyen *al lado*, compartiendo la misma base.
2. **Monorepo modular, no monolito.** Una sola aplicación React, pero organizada por dominio funcional, no por tipo de archivo. Cada módulo es casi un mini-paquete con sus propias páginas, hooks y servicios.
3. **Design system antes que pantallas.** Los tokens de color, tipografía, espaciado y componentes base (Card, Table, Button, Dialog, Sidebar) se construyen una sola vez y se consumen en todos los módulos. Esto es lo que da la sensación "SAP QM / Ignition" en vez de "app hecha a mano".
4. **Firestore por colecciones desacopladas con trazabilidad cruzada.** Cada módulo tiene sus colecciones, pero comparten claves comunes (lote, planta, referencia, usuario) para que la trazabilidad pueda atravesar módulos sin duplicar datos.
5. **Permisos a nivel de módulo y de acción**, no solo de página — un Analista puede *ver* Laboratorio pero no *liberar* un lote; un Supervisor puede *cerrar* una no conformidad pero no *eliminarla*.

---

## 2. Arquitectura general (capas)

```
┌─────────────────────────────────────────────┐
│  UI Layer            → pages/ + layouts/     │
│  Componentes reutilizables → components/     │
├─────────────────────────────────────────────┤
│  Lógica de aplicación → hooks/ + contexts/    │
├─────────────────────────────────────────────┤
│  Servicios de dominio → services/            │
│  (un servicio por entidad: muestreo, ensayo, │
│   lote, noConformidad, pqr, auditoria...)    │
├─────────────────────────────────────────────┤
│  Acceso a datos       → firebase/            │
│  (Firestore, Auth, Storage, reglas)          │
├─────────────────────────────────────────────┤
│  Utilidades transversales → utils/           │
│  (exportExcel, formatDate, permisos, etc.)   │
└─────────────────────────────────────────────┘
```

La regla clave: **una página nunca llama a Firestore directamente**. Siempre pasa por un `service`. Esto es lo que permite que mañana cambies de Firestore a otra base de datos, o que un mismo servicio sirva a la app web y a un futuro dashboard de BI, sin tocar las pantallas.

---

## 3. Estructura de carpetas propuesta

```
trz-quality-system/
├── src/
│   ├── app/                      # Bootstrap: rutas, providers globales
│   │   ├── App.jsx
│   │   ├── routes.jsx
│   │   └── providers.jsx
│   │
│   ├── layouts/
│   │   ├── MainLayout.jsx        # Sidebar + Header + contenido
│   │   ├── AuthLayout.jsx        # Layout de login
│   │   └── components/
│   │       ├── Sidebar.jsx
│   │       ├── Header.jsx
│   │       └── MobileNav.jsx
│   │
│   ├── modules/                  # Un dominio por carpeta
│   │   ├── dashboard/
│   │   │   ├── pages/
│   │   │   ├── components/
│   │   │   └── hooks/
│   │   ├── muestreo/             # Migración del módulo actual
│   │   │   ├── pages/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   └── services/
│   │   ├── laboratorio/
│   │   │   ├── pages/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   └── services/
│   │   ├── produccion/
│   │   ├── trazabilidad/
│   │   ├── no-conformidades/
│   │   ├── pqr/
│   │   ├── auditorias/
│   │   ├── documentos/
│   │   ├── configuracion/
│   │   └── usuarios/
│   │
│   ├── components/               # Componentes 100% genéricos (design system)
│   │   ├── ui/
│   │   │   ├── Button.jsx
│   │   │   ├── Card.jsx
│   │   │   ├── Table.jsx
│   │   │   ├── Dialog.jsx
│   │   │   ├── Badge.jsx
│   │   │   ├── Tabs.jsx
│   │   │   └── Charts/
│   │   └── feedback/
│   │       ├── Toast.jsx
│   │       └── EmptyState.jsx
│   │
│   ├── hooks/                    # Hooks transversales (no de un módulo)
│   │   ├── useAuth.js
│   │   ├── usePermisos.js
│   │   └── useResponsive.js
│   │
│   ├── contexts/
│   │   ├── AuthContext.jsx
│   │   ├── PlantaContext.jsx
│   │   └── ThemeContext.jsx      # Modo oscuro
│   │
│   ├── services/                 # Un servicio = una colección/entidad
│   │   ├── muestreoService.js
│   │   ├── laboratorioService.js
│   │   ├── loteService.js
│   │   ├── noConformidadService.js
│   │   ├── pqrService.js
│   │   ├── auditoriaService.js
│   │   └── usuarioService.js
│   │
│   ├── firebase/
│   │   ├── config.js
│   │   ├── auth.js
│   │   ├── firestore.js
│   │   └── storage.js
│   │
│   ├── utils/
│   │   ├── excelExport.js        # ExcelJS centralizado
│   │   ├── formatters.js
│   │   ├── permisos.js
│   │   └── constants.js          # Catálogos: plantas, familias, roles
│   │
│   └── styles/
│       ├── tokens.css            # Variables de la paleta corporativa
│       └── globals.css
│
├── public/
└── firestore.rules
```

**Por qué `modules/` y no `pages/` a secas:** con 11 módulos y crecimiento de años, todo en una carpeta `pages/` se vuelve inmanejable. Agrupar por módulo significa que cuando trabajes en Laboratorio, todo lo relevante está en una sola carpeta — y cuando el sistema crezca, un módulo se puede incluso extraer a un paquete independiente sin tocar el resto.

---

## 4. Mapa de módulos

| Módulo | Estado | Colecciones Firestore clave | Roles con acceso |
|---|---|---|---|
| **Dashboard** | Nuevo (agrega datos de los demás) | — (lee de otros) | Todos (vista filtrada por rol) |
| **Muestreo** | Migrar el actual, mejorar UI | `sesiones`, `muestras`, `resultados` | Analista, Supervisor, Coordinador, Director, Admin |
| **Laboratorio** | Nuevo | `ensayos`, `fichasTecnicas`, `certificados`, `equipos`, `calibraciones`, `reactivos` | Laboratorista, Coordinador, Director, Admin |
| **Producción** | Nuevo | `ordenes`, `lotes`, `procesos` | Supervisor, Coordinador, Director, Admin |
| **Trazabilidad** | Nuevo (consulta transversal) | — (consulta cruzada por `loteId`) | Todos (solo lectura salvo Admin) |
| **No Conformidades** | Nuevo | `noConformidades`, `accionesCorrectivas` | Todos los roles pueden crear; cierre: Coordinador+ |
| **PQR** | Nuevo | `pqr` | Coordinador, Director, Admin, Consulta (lectura) |
| **Auditorías** | Nuevo | `auditorias`, `hallazgos`, `planesAccion` | Director, Admin |
| **Documentos** | Nuevo | `documentos` (metadata; archivos en Storage) | Todos (lectura), Admin (escritura) |
| **Configuración** | Ampliar el panel admin actual | `catalogos` (plantas, familias, referencias, ensayos) | Admin |
| **Usuarios** | Ampliar el actual | `usuarios`, `roles` | Admin |

**El eje que conecta todo es `loteId` / `referenciaId`.** Trazabilidad no es una colección propia: es una vista que, dado un lote, consulta `sesiones` (muestreo), `ensayos` (laboratorio), `ordenes` (producción) y `noConformidades` asociadas, y arma la historia completa. Esto evita duplicar información y mantiene una sola fuente de verdad por entidad.

---

## 5. Sistema de diseño (resumen)

- **Tokens de color** definidos una vez en `styles/tokens.css` como variables CSS, mapeados a la paleta dada (`--color-primary: #0F4C81`, etc.) y consumidos por Tailwind vía `tailwind.config.js` (`theme.extend.colors`). Esto es lo que permite activar modo oscuro cambiando solo los valores de las variables, sin tocar componentes.
- **Componentes base** (`components/ui/`) se construyen una sola vez: `Card`, `Table` (con paginación y export), `Badge` de estado (cumple / no cumple / en revisión, con los colores verde/naranja/rojo definidos), `Dialog`, `Tabs`, envoltorios de gráficas.
- **Layout responsive:** `MainLayout` decide con un hook (`useResponsive`) si renderiza `Sidebar` fijo (desktop) o `MobileNav` tipo hamburguesa (mobile), sin duplicar lógica de negocio.

---

## 6. Plan de implementación por fases

La prioridad es que **el módulo de Muestreo Diario nunca deje de funcionar** mientras se construye alrededor de él.

### Fase 0 — Cimientos (sin tocar funcionalidad existente)
- Crear el nuevo esqueleto de carpetas (`app/`, `layouts/`, `components/ui/`, `styles/tokens.css`).
- Definir los tokens de color y componentes base genéricos.
- Configurar Tailwind con la paleta corporativa.
- No se mueve todavía ningún código del módulo actual.

### Fase 1 — Migración del Muestreo actual a la nueva arquitectura
- Mover el módulo actual a `modules/muestreo/` sin cambiar su lógica, solo su ubicación y sus imports.
- Reemplazar sus componentes de UI ad-hoc por los componentes reutilizables de `components/ui/`.
- Aplicar el nuevo `MainLayout` (sidebar + header) sobre las pantallas existentes.
- Verificar en campo que ninguna funcionalidad se perdió (login, roles, sesiones, export Excel, historial).

### Fase 2 — Rediseño visual completo
- Aplicar el sistema de diseño a todas las pantallas migradas.
- Implementar el Dashboard central con los KPIs iniciales que ya existen en Muestreo (cumplimiento, rechazo, reproceso).
- Dejar preparado (aunque no activado) el modo oscuro.

### Fase 3 — Módulo de Laboratorio
- Modelar `fichasTecnicas` por producto y `ensayos` configurables (tipo, unidad, rango de aceptación).
- Construir flujo recepción → registro → ensayos → resultados → liberación → certificado.
- Conectar resultados de laboratorio al mismo `loteId` que usa Producción/Muestreo.
- Añadir gráficas de tendencia y cartas de control (SPC) como una segunda iteración dentro de esta fase.

### Fase 4 — Trazabilidad
- Construir la vista de consulta cruzada por lote/materia prima/proveedor/cliente, apoyada en los datos que ya existen en Muestreo y Laboratorio.
- Esta fase es relativamente rápida si las fases 1–3 mantuvieron `loteId` consistente en todas las colecciones.

### Fase 5 — No Conformidades, PQR y Auditorías
- Estos tres módulos comparten patrón (registro → clasificación → responsable → seguimiento → cierre), así que conviene construir un componente de "flujo de seguimiento" reutilizable y luego especializarlo para cada uno.

### Fase 6 — Documentos, Configuración avanzada y Usuarios/Permisos finos
- Repositorio de documentos controlados (procedimientos, formatos) con control de versión básico.
- Ampliar el panel de administración actual con gestión de catálogos por módulo y matriz de permisos por rol y acción (no solo por página).

### Fase 7 — Endurecimiento y escalado
- Revisión de reglas de seguridad de Firestore por rol.
- Optimización de consultas (índices compuestos) ahora que hay varios módulos consultando por `loteId`/`planta`/`fecha`.
- Preparación para que el sistema pueda ofrecerse como producto a otras plantas o incluso otras empresas (multi-tenant, si eso llega a plantearse más adelante).

---

## 7. Riesgos a vigilar

- **Migrar el Muestreo actual demasiado rápido** es el mayor riesgo: es el único módulo con datos reales en producción. La Fase 1 debe hacerse con el módulo en paralelo (rama separada, pruebas con datos reales) antes de reemplazar el actual.
- **Colecciones desalineadas entre módulos** (por ejemplo, que Laboratorio use `lote` como string y Producción use `loteId` como referencia) rompería la Trazabilidad. Vale la pena fijar ahora una convención única de claves antes de construir Laboratorio.
- **Permisos por rol** crecen rápido en complejidad con 7 roles × 11 módulos. Conviene modelarlos como una matriz de datos (no como `if` repartidos en el código) desde la Fase 0.

---

**Siguiente paso sugerido:** confirmar la Fase 0 y 1 (cimientos + migración de Muestreo) como punto de partida concreto, ya que es lo que garantiza que no se pierde nada de lo que ya funciona antes de construir lo nuevo.
