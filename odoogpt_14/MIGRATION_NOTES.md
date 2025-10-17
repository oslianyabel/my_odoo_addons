# Notas de Migración - OdooGPT de Odoo 17 a Odoo 14

## Cambios Realizados

### 1. Manifest (__manifest__.py)
- ✅ Versión actualizada de `17.0.0.0.1` a `14.0.0.0.1`
- ✅ Cambio de sistema de assets: en Odoo 14 no existe `assets`, se usa `qweb` para templates XML
- ✅ Agregadas las vistas XML (`main_menu.xml`, `odoogpt_table.xml`) a la sección `data`

### 2. JavaScript (list_controller.js)
- ✅ Migrado de módulos ES6 (@odoo-module) a sistema odoo.define()
- ✅ Reemplazado `patch()` por `include()`
- ✅ Adaptado el método `renderButtons` para vincular eventos en Odoo 14
- ✅ Cambiado el método RPC de servicios a `_rpc()`
- ✅ Actualizado acceso al contexto: `this.initialState.context` en lugar de `this.model.rootParams`

### 3. Plantillas XML (list_controller.xml)
- ✅ Cambiado de herencia OWL (`t-inherit-mode="extension"`) a QWeb clásico (`t-extend`)
- ✅ Reemplazado `t-on-click` por botón sin evento directo (manejado en JS)
- ✅ Cambiado `xpath` con `hasclass()` por `t-jquery` con selectores CSS

### 4. Modelos Python

#### discuss_channel.py
- ✅ Renombrado de `discuss.channel` a `mail.channel` (nombre correcto en Odoo 14)
- ✅ Cambiado campo `is_chat` a `channel_type == 'chat'`
- ✅ Cambiado tipo de campo `view_data` de `Json` a `Text` (mayor compatibilidad)

#### mail_message.py
- ✅ Actualizadas todas las referencias de `discuss.channel` a `mail.channel`

#### res_partner.py
- ✅ Actualizado modelo de canal de `discuss.channel` a `mail.channel`
- ✅ Agregado `json.dumps()` para serializar params antes de guardar en campo Text
- ✅ Agregado contexto `mail_create_nosubscribe=True` para creación de canales
- ✅ Agregado campo `public: 'private'` para canales privados en Odoo 14

#### res_users.xml
- ✅ Cambiado sintaxis de `Command.link()` a tupla `(4, ref())` compatible con Odoo 14

### 5. Seguridad (ir.model.access.csv)
- ✅ Agregados permisos de acceso para el modelo `odoogpt.table`

### 6. Models __init__.py
- ✅ Agregada importación del modelo `odoogpt_table`

## Diferencias Clave entre Odoo 14 y Odoo 17

### Framework JavaScript
- **Odoo 14**: Usa RequireJS con `odoo.define()`
- **Odoo 17**: Usa módulos ES6 con `@odoo-module`

### Sistema de Mensajería
- **Odoo 14**: Modelo `mail.channel` con `channel_type`
- **Odoo 17**: Modelo `discuss.channel` con campos diferentes

### Assets
- **Odoo 14**: Usa `qweb` para templates, JS incluido directamente
- **Odoo 17**: Sistema de assets más avanzado con bundles específicos

### OWL (Odoo Web Library)
- **Odoo 14**: OWL 1.x con QWeb clásico
- **Odoo 17**: OWL 2.x con componentes modernos

### Campos de Base de Datos
- **Odoo 14**: No todos los tipos de campos modernos (ej. Json) están disponibles
- **Odoo 17**: Tipos de campos más ricos (Json, etc.)

## Dependencias Externas

Las siguientes dependencias Python deben estar instaladas:
```bash
pip install openai python-dotenv psycopg2-binary phonenumbers flanker markdown2 markupsafe "PyPDF2<2.0" python-docx openpyxl
```

**IMPORTANTE**: 
- **PyPDF2**: Debe ser versión 1.x (< 2.0) para compatibilidad con Odoo 14. La versión recomendada es 1.28.6.
  - Odoo 14 usa `PyPDF2.filters` que no existe en versiones 2.x o superiores
  - El módulo usa `PdfFileReader` y `extractText()` (API de versión 1.x)
- Verificar compatibilidad con Python 3.6-3.8 que son las versiones soportadas por Odoo 14.

## API de OpenAI

El módulo usa la nueva API de OpenAI con:
- Clients síncronos y asíncronos (`OpenAI`, `AsyncOpenAI`)
- Modelos GPT-4 y GPT-5 (según enumeraciones)
- Sistema de `responses.create()` que parece ser una API personalizada o más reciente

**ADVERTENCIA**: Verificar que la versión de la librería `openai` instalada sea compatible con Odoo 14 (Python 3.6-3.8).

## Módulo queue_job

El módulo depende de `queue_job` que debe estar instalado en Odoo 14:
```bash
# Instalar desde OCA
# https://github.com/OCA/queue/tree/14.0
```

## Pasos de Instalación

1. Asegurarse de tener Python 3.6-3.8
2. Instalar dependencias Python listadas arriba
3. Instalar el módulo `queue_job` para Odoo 14
4. Copiar el módulo a `extra_addons/`
5. Actualizar lista de aplicaciones en Odoo
6. Instalar el módulo OdooGPT
7. Configurar la variable de entorno `OPENAI_API_KEY` en archivo `.env`

## Posibles Problemas y Soluciones

### Problema: Error al crear canales
**Solución**: Verificar que los usuarios y partners de OdooGPT estén correctamente creados con los datos XML.

### Problema: JavaScript no se carga
**Solución**: Limpiar assets de Odoo con modo desarrollador activado o regenerar assets.

### Problema: Botón OdooGPT no aparece
**Solución**: Verificar que el template QWeb esté correctamente cargado en la sección `qweb` del manifest.

### Problema: Incompatibilidad con librería OpenAI
**Solución**: Usar una versión compatible de la librería `openai` con Python 3.6-3.8. Puede ser necesario downgrade.

### Problema: async/await en contexto de Odoo
**Solución**: El código usa `asyncio` y `async/await`. Verificar que funcione correctamente en el contexto de workers de Odoo 14.

## Archivos Modificados

- `__manifest__.py`
- `static/src/views/list/list_controller.js`
- `static/src/views/list/list_controller.xml`
- `models/discuss_channel.py`
- `models/mail_message.py` (+ compatibilidad PyPDF2 1.x)
- `models/res_partner.py`
- `models/__init__.py`
- `models/enumerations.py` (type hints Python 3.8)
- `models/completions.py` (type hints Python 3.8)
- `models/utils.py` (type hints Python 3.8)
- `data/res_users.xml`
- `security/ir.model.access.csv`

## Testing Recomendado

1. ✅ Verificar que el módulo se instala sin errores
2. ✅ Probar creación de canal con OdooGPT
3. ✅ Enviar mensaje y verificar respuesta del bot
4. ✅ Verificar que los jobs asíncronos funcionen correctamente
5. ✅ Probar adjuntos (PDF, DOCX, XLSX)
6. ✅ Verificar herramientas de integración con Odoo (crear partners, pedidos, etc.)

## Fecha de Migración
2025-01-17

## Autor de la Migración
Migración automatizada con asistencia IA
