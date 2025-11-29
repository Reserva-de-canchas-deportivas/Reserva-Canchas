# Reserva-Canchas

## Seguridad Transversal (HU-006)

Esta versión incorpora autenticación JWT RS256, control de acceso por roles y API Keys obligatorias para integraciones externas.

- **JWT RS256**: los tokens se firman con la clave privada ubicada en `keys/private.pem` (o variables `PRIVATE_KEY/ PUBLIC_KEY`). La verificación usa la clave pública y se valida `exp`, `jti` y `type` (`access`/`refresh`).
- **Roles**: se soportan los roles `cliente`, `personal` y `admin`. Los endpoints marcan sus permisos con el decorador `@require_role(...)`. Ejemplos:
  - `/api/v1/usuarios/perfil` ⇒ solo `admin`.
  - CRUD de sedes/canchas/tarifario ⇒ `admin`/`personal` (consultas admiten todos los roles).
  - `/api/v1/disponibilidad` ⇒ todos los roles autenticados.
- **API Keys**: las rutas SOAP (`/soap/*`) exigen `X-Api-Key`. Se siembra una llave demo `DEMO-INTEGRACION-2024-KEY` (hash persistido en BD). Cada intento exitoso y fallido queda registrado en `security_audit_logs`.
- **Auditoría**: cualquier validación (tokens, roles, API Keys) genera eventos en la tabla `security_audit_logs` con ip, agente y motivo.
- **Usuarios semilla**:
  - `admin@example.com` / `admin123` (rol `admin`)
  - `blocked@example.com` / `blocked123` (rol `cliente`, estado `bloqueado`)

### Casos de prueba sugeridos
1. Token válido ⇒ acceder a `/api/v1/usuarios/perfil` con `Authorization: Bearer <token>` desde login del admin. Debe responder 200 con el rol.
2. Token expirado ⇒ manipular `exp` (o esperar) y reintentar ⇒ 401 `TOKEN_EXPIRED`.
3. Usuario sin rol requerido ⇒ iniciar sesión con un `cliente` activo (crear mediante seed o repositorio) y llamar `/api/v1/usuarios/perfil` ⇒ 403 `FORBIDDEN`.
4. API Key inexistente ⇒ llamar algún `/soap/*` sin `X-Api-Key` o con valor aleatorio ⇒ 401 `INVALID_API_KEY`.
5. Token manipulado ⇒ alterar un caracter del JWT ⇒ 401 `SIGNATURE_INVALID`.

La respuesta estándar de error para seguridad es:

```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Token inválido o ausente"
  }
}
```

# Resolución de Precio (HU-017)

- **Endpoint:** `GET /api/v1/tarifario/resolver?fecha=YYYY-MM-DD&hora_inicio=HH:MM&hora_fin=HH:MM&sede_id=...&cancha_id?=...`
- **Lógica:** se normaliza la fecha/hora con la zona horaria de la sede, se intenta primero la tarifa específica de la cancha y, si no existe, la general de la sede. Si no hay ninguna, se retorna `404 SIN_TARIFA`.
- **Cache:** las respuestas se almacenan en memoria por 5 minutos (TTL configurable en código) para evitar recalcular precios repetidos.
- **Respuesta exitosa:**
  ```json
  {
    "mensaje": "Tarifa resuelta",
    "data": {
      "origen": "cancha",
      "tarifa_id": "uuid",
      "moneda": "COP",
      "precio_por_bloque": 150000
    },
    "success": true
  }
  ```
- **Errores controlados:**
  - `404 SIN_TARIFA` → no existe tarifa aplicable (detalles incluyen día/hora).
  - `500 ZONA_HORARIA_INVALIDA` → la sede tiene TZ inválida.
  - `422 VALIDATION_ERROR` → fecha/hora con formato incorrecto (los parámetros requeridos ya son validados por FastAPI si faltan).

### Casos de prueba HU-017
1. **Tarifa de cancha:** enviar `cancha_id` con una tarifa específica → `origen="cancha"`.
2. **Tarifa de sede:** omitir `cancha_id` o usar una sin tarifa → `origen="sede"`.
3. **Sin tarifa:** usar horario fuera de franjas -> 404 con `SIN_TARIFA`.
4. **Zona horaria inválida:** configura `sede.zona_horaria` a un valor erróneo y consulta → 500 controlado.
5. **Validación:** omite parámetros obligatorios → FastAPI responde 422.

# Pre-reserva HOLD (HU-019)

```
POST /api/v1/reservas
Authorization: Bearer <token cliente/personal/admin>
{
  "sede_id": "...",
  "cancha_id": "...",
  "fecha": "2025-07-31",
  "hora_inicio": "18:00",
  "hora_fin": "19:00",
  "clave_idempotencia": "HOLD-CLIENTE-123"
}
```

- Calcula el precio reutilizando HU-017 y crea un registro en `estado="hold"` con `vence_hold = now + HOLD_TTL_MINUTES` (10 min por defecto).
- Si se repite la misma `clave_idempotencia`, responde 200 con la misma `reserva_id` (idempotente).
- Aplica validación de solape (hold/pending/confirmed + buffer), horario de apertura y estado de la cancha.
- Respuestas de error clave: `RESERVA_SOLAPADA`, `FUERA_DE_APERTURA`, `CANCHA_NO_RESERVABLE`.

# Confirmar Reserva (HU-020)

```
POST /api/v1/reservas/{reserva_id}/confirmar
Authorization: Bearer <token cliente/personal/admin>
{
  "clave_idempotencia": "CONFIRM-123"  // opcional
}
```

```powershell
# Login
$login = Invoke-RestMethod -Method Post `
    -Uri http://localhost:8000/api/v1/auth/login `
    -Body '{"correo":"admin@example.com","contrasena":"admin123"}' `
    -ContentType "application/json"
$headers = @{ Authorization = "Bearer $($login.data.access_token)" }

# IDs demo
$sedes = Invoke-RestMethod -Method Get -Uri http://localhost:8000/api/v1/sedes/ -Headers $headers
$sedeId = $sedes.data.sedes[0].sede_id
$canchas = Invoke-RestMethod -Method Get -Uri "http://localhost:8000/api/v1/sedes/$sedeId/canchas/" -Headers $headers
$canchaId = $canchas.data.canchas[0].cancha_id

# Crear HOLD (>24h)
$holdBody = @{
    sede_id = $sedeId
    cancha_id = $canchaId
    fecha = "2025-07-31"
    hora_inicio = "18:00"
    hora_fin = "19:00"
    clave_idempotencia = "HOLD-001"
} | ConvertTo-Json -Compress
$holdResponse = Invoke-RestMethod -Method Post `
    -Uri http://localhost:8000/api/v1/reservas `
    -Headers $headers -ContentType "application/json" `
    -Body $holdBody
$reservaId = $holdResponse.data.reserva_id

# Confirmar
Invoke-RestMethod -Method Post `
    -Uri "http://localhost:8000/api/v1/reservas/$reservaId/confirmar" `
    -Headers $headers -ContentType "application/json" `
    -Body '{ "clave_idempotencia": "CONFIRM-001" }'

# Cancelar e idempotencia
$cancelBody = @{
    motivo = "Cliente no asistirá"
    clave_idempotencia = "CANCEL-001"
} | ConvertTo-Json -Compress
Invoke-RestMethod -Method Post `
    -Uri "http://localhost:8000/api/v1/reservas/$reservaId/cancelar" `
    -Headers $headers -ContentType "application/json" `
    -Body $cancelBody
Invoke-RestMethod -Method Post `
    -Uri "http://localhost:8000/api/v1/reservas/$reservaId/cancelar" `
    -Headers $headers -ContentType "application/json" `
    -Body $cancelBody

# Alternativa sin body JSON: ?motivo=...&clave_idempotencia=...
Invoke-RestMethod -Method Post `
    -Uri "http://localhost:8000/api/v1/reservas/$reservaId/cancelar?motivo=Cliente%20no%20asistira&clave_idempotencia=CANCEL-QUERY"` `
    -Headers $headers
```

# Comandos GIT
# Comandos GIT

### Conceptos Clave

- **Repositorio**: Directorio que contiene el proyecto y su historial de versiones
- **Commit**: Instantánea de los cambios realizados en el proyecto
- **Branch**: Línea independiente de desarrollo
- **Merge**: Proceso de combinar cambios de diferentes ramas
- **Remote**: Versión del repositorio alojada en un servidor remoto


## Comandos Básicos de Git

### Inicialización y Clonado

```bash
# Inicializar un nuevo repositorio
git init

# Clonar un repositorio existente
git clone https://github.com/usuario/repositorio.git

# Clonar con un nombre específico
git clone https://github.com/usuario/repositorio.git mi-proyecto
```

### Seguimiento de Cambios

```bash
# Ver estado del repositorio
git status

# Agregar archivos al staging area
git add archivo.txt
git add .                    # Agregar todos los archivos
git add *.js                 # Agregar archivos por patrón

# Confirmar cambios
git commit -m "Mensaje descriptivo del commit"
git commit -am "Agregar y confirmar archivos modificados"

# Ver historial de commits
git log
git log --oneline           # Formato compacto
git log --graph             # Mostrar gráfico de ramas
```

### Información y Diferencias

```bash
# Ver diferencias no confirmadas
git diff

# Ver diferencias en staging area
git diff --cached

# Ver diferencias entre commits
git diff commit1 commit2

# Mostrar información de un commit específico
git show commit-hash
```

### Deshacer Cambios

```bash
# Deshacer cambios en working directory
git checkout -- archivo.txt

# Quitar archivo del staging area
git reset HEAD archivo.txt

# Deshacer último commit (mantener cambios)
git reset --soft HEAD~1

# Deshacer último commit (eliminar cambios)
git reset --hard HEAD~1
```

> **⚠️ Advertencia**: `git reset --hard` elimina permanentemente los cambios no confirmados.

---

## Trabajo con Ramas

### Gestión de Ramas

```bash
# Listar ramas locales
git branch

# Listar todas las ramas (locales y remotas)
git branch -a

# Crear nueva rama
git branch nueva-funcionalidad

# Cambiar a una rama
git checkout nueva-funcionalidad

# Crear y cambiar a nueva rama
git checkout -b nueva-funcionalidad

# Cambiar a rama (comando moderno)
git switch nueva-funcionalidad

# Crear y cambiar a nueva rama (comando moderno)
git switch -c nueva-funcionalidad
```

### Fusión de Ramas

```bash
# Fusionar rama en la rama actual
git merge nombre-rama

# Fusión con mensaje personalizado
git merge nombre-rama -m "Mensaje de merge"

# Fusión sin fast-forward
git merge --no-ff nombre-rama

# Eliminar rama local
git branch -d nombre-rama

# Eliminar rama forzadamente
git branch -D nombre-rama
```

### Rebase

```bash
# Rebase interactivo
git rebase -i HEAD~3

# Rebase sobre otra rama
git rebase development

# Continuar rebase después de resolver conflictos
git rebase --continue

# Abortar rebase
git rebase --abort
```

> **Nota**: Usa rebase para mantener un historial lineal y limpio, pero evítalo en ramas compartidas.

---
*-*-*-*-*-*-**/*/*/*/*/*/*/
## GitHub: Comandos Remotos
### Sincronización con Repositorio Remoto

```bash
# Subir cambios al repositorio remoto
git push origin development
# Subir nueva rama al remoto
git push -u origin nueva-funcionalidad

# Subir todas las ramas
git push --all origin

# Subir tags
git push --tags origin

# Forzar push (usar con precaución)
git push --force origin development
```

### Obtener Cambios del Remoto

```bash
# Obtener cambios sin fusionar
git fetch origin

# Obtener y fusionar cambios
git pull origin development

# Pull con rebase
git pull --rebase origin development

# Establecer rama upstream
git branch --set-upstream-to=origin/development development
```


---

## Solución de Conflictos

### Identificar y Resolver Conflictos

```bash
# Ver archivos con conflictos
git status

# Ver diferencias de conflictos
git diff

# Resolver conflictos manualmente y confirmar
git add archivo-resuelto.txt
git commit -m "Resolver conflicto en archivo-resuelto.txt"

# Usar herramienta de merge
git mergetool
```

## Buenas Prácticas y Recomendaciones

### Estructura de Commits

```bash
# Formato recomendado para mensajes de commit
git commit -m "tipo: descripción breve

Explicación detallada del cambio (opcional)

Resolves #123"

# Ejemplos de tipos comunes:
# feat: nueva funcionalidad
# fix: corrección de bug
# docs: cambios en documentación
# style: cambios de formato
# refactor: refactorización de código
# test: agregar o modificar tests
```

### Flujo de Trabajo Recomendado

```bash
# 1. Actualizar rama principal
git checkout development
git pull origin development

# 2. Crear rama para nueva funcionalidad
git checkout -b feature/descripcion-funcionalidad

# 3. Hacer commits frecuentes y descriptivos
git add .
git commit -m "feat: implementar validación de formulario"

# 4. Mantener rama actualizada
git checkout development
git pull origin development
git checkout feature/descripcion-funcionalidad
git rebase development

# 5. Subir cambios
git push -u origin feature/descripcion-funcionalidad

# 6. Crear Pull Request en GitHub
# 7. Después de aprobación, fusionar y limpiar
git checkout development
git pull origin development
git branch -d feature/descripcion-funcionalidad
```

### Comandos de Limpieza

```bash
# Limpiar archivos no rastreados
git clean -n                # Vista previa
git clean -f                # Ejecutar limpieza

# Limpiar ramas fusionadas
git branch --merged | grep -v development | xargs -n 1 git branch -d

# Limpiar referencias remotas obsoletas
git remote prune origin
```

### Configuración Avanzada

```bash
# Configurar autopush para branches
git config --global push.default current

# Configurar rebase por defecto para pull
git config --global pull.rebase true

# Configurar colores
git config --global color.ui auto

# Configurar .gitignore global
git config --global core.excludesfile ~/.gitignore_global
```

### Herramientas Útiles

```bash
# Buscar texto en historial
git log -S "texto-a-buscar"

# Encontrar quién modificó una línea
git blame archivo.txt

# Buscar commit que introdujo un bug
git bisect start
git bisect bad              # Commit con bug
git bisect good commit-hash # Commit sin bug

# Guardar cambios temporalmente
git stash
git stash pop
git stash list
git stash apply stash@{0}
```
