# Church Management (cdb_management)

Módulo de Odoo para administrar la información de miembros de una iglesia (CASA DE BENDICION).

## Características

- **Gestión de Miembros**: Extensión de `res.partner` con campos específicos para la iglesia.
- **Datos Personales**: Género, nivel académico, estatus ocupacional, ocupación, estado civil y edad calculada.
- **Datos de Iglesia**: Estado de bautismo, fecha de bautizo, fecha de ingreso a CDB.
- **Organización**: Sectores, Ministerios y Roles.
- **Familiares**: Conexión con otros miembros o registro de nombres de familiares no miembros.
- **Vistas Dedicadas**: Vistas de lista y formulario personalizadas para miembros de la iglesia.

## Instalación

1. Asegúrese de que la carpeta `cdb_management` esté en su ruta de `addons`.
2. Actualice la lista de aplicaciones en Odoo.
3. Instale el módulo "Church Management (CDB)".

## Configuración

Vaya a **Iglesia > Configuración** para dar de alta:
- Sectores
- Ministerios
- Roles

## Uso

Acceda a **Iglesia > Miembros** para gestionar los registros de la congregación. Los campos de dirección utilizan el estándar de Odoo.
