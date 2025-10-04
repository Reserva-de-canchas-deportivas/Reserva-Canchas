# Reserva-Canchas
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
