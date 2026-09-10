# Referencias y Recursos — Sesión 6
## Agentes de IA · Seminario · Semana 3, Sesión 6

---

## 🔧 Documentación oficial

| Recurso | URL | Para qué sirve |
|---|---|---|
| Railway Docs | https://docs.railway.app | Documentación completa de Railway |
| Railway Deploy | https://docs.railway.app/guides/deployments | Cómo hacer despliegues |
| Railway Variables | https://docs.railway.app/guides/variables | Configurar variables de entorno |
| Railway Logs | https://docs.railway.app/guides/logs | Leer logs en producción |
| GitHub Docs | https://docs.github.com/repositories | Crear y gestionar repositorios |
| Git Cheat Sheet | https://education.github.com/git-cheat-sheet-education.pdf | Comandos Git de referencia |

---

## 📄 Lectura recomendada

### Buenas prácticas en producción
> **The Twelve-Factor App** — Heroku  
> Link: https://12factor.net/es/  
> **Qué leer**: Factor III (Configuración), Factor IV (Backing services), Factor VII (Port binding).  
> Son exactamente los principios que aplicamos: .env para config, APIs como servicios, Puerto por variable de entorno.

---

## 💡 Comandos Git para el despliegue

```bash
# ── Configuración inicial (solo una vez) ─────────────────
git config --global user.name "Tu Nombre"
git config --global user.email "tu@email.com"

# ── Inicializar repositorio local ────────────────────────
git init
git add .
git commit -m "feat: agente IA inicial con FastAPI"

# ── Conectar con GitHub ───────────────────────────────────
git remote add origin https://github.com/tu-usuario/tu-repo.git
git branch -M main
git push -u origin main

# ── Actualizar después de cambios ────────────────────────
git add .
git commit -m "feat: descripción del cambio"
git push

# ── Ver estado del repositorio ───────────────────────────
git status
git log --oneline -5

# ── Verificar que .env no se subió ───────────────────────
git ls-files | grep ".env"
# Si devuelve .env → ejecuta: git rm --cached .env
```

---

## 🧠 Glosario — Sesión 6

| Término | Definición simple |
|---|---|
| **Railway** | Plataforma cloud que despliega aplicaciones desde GitHub automáticamente |
| **Procfile** | Archivo que le dice a Railway cómo arrancar tu aplicación |
| **railway.toml** | Configuración detallada del despliegue en Railway |
| **CI/CD** | Continuous Integration / Continuous Deployment — cada push a GitHub actualiza el servidor automáticamente |
| **Variables de entorno** | Configuración sensible (API Keys) almacenada en el servidor, no en el código |
| **.gitignore** | Archivo que lista qué NO subir a GitHub (como .env) |
| **Health check** | Endpoint que Railway llama para saber si el servicio está vivo |
| **Deploy** | El proceso de publicar una versión del código en producción |
| **Logs** | Registro de eventos del servidor — clave para depurar errores en producción |
| **$PORT** | Variable de entorno que Railway asigna automáticamente — el servidor debe escuchar en este puerto |
| **Dominio** | La URL pública de tu servicio en Railway (xxx.railway.app) |

---

## 🗂️ Flujo completo de despliegue

```
Tu código (local)
      ↓
git push → GitHub
      ↓
Railway detecta el push
      ↓
Railway instala requirements.txt
      ↓
Railway ejecuta el Procfile
      ↓
Servidor corriendo en Railway
      ↓
URL pública disponible
      ↓
Health check → /health → OK
      ↓
¡Agente en producción! 🎉
```

---

*¡Felicitaciones por completar el seminario!*
