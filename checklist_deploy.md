# Checklist de Despliegue — Sesión 6
## Verifica estos 12 puntos antes de hacer push a Railway

---

## ✅ ANTES DE SUBIR A GITHUB

- [ ] **1. `.env` en `.gitignore`**
  El archivo `.gitignore` existe y contiene `.env`. Verifica con `git status` que `.env` no aparece como archivo a subir.

- [ ] **2. Sin claves en el código**
  Ningún archivo `.py` tiene claves API escritas directamente (`gsk_...`, contraseñas, tokens). Todo viene de `os.getenv()`.

- [ ] **3. `requirements.txt` actualizado**
  Todas las librerías que usa el proyecto están en `requirements.txt` con versiones fijas.

- [ ] **4. El servidor corre local sin errores**
  Ejecuta `uvicorn main:app --reload` y verifica que `/health` responde `{"status": "ok"}`.

- [ ] **5. Todos los endpoints funcionan**
  Corre `python 02_probar_api.py` o prueba desde Swagger en `localhost:8000/docs`.

---

## ✅ ARCHIVOS DE DESPLIEGUE PRESENTES

- [ ] **6. `Procfile` existe**
  Contiene: `web: uvicorn main:app --host 0.0.0.0 --port $PORT`

- [ ] **7. `railway.toml` existe**
  Con `healthcheckPath = "/health"` configurado.

- [ ] **8. `requirements.txt` en la raíz del proyecto**
  Railway lo busca en la raíz — no en subcarpetas.

---

## ✅ EN RAILWAY (antes de hacer deploy)

- [ ] **9. Variables de entorno configuradas**
  En Railway → tu proyecto → Variables, agrega:
  - `GROQ_API_KEY` con tu clave real
  - `AGENT_NAME` y `AGENT_ROLE`
  - `LLM_PROVIDER=groq`
  - `OPENWEATHER_API_KEY` si usas clima

- [ ] **10. Repositorio vinculado**
  Railway está conectado al repositorio correcto de GitHub.

---

## ✅ DESPUÉS DEL DEPLOY

- [ ] **11. URL pública responde**
  Visita `https://tu-proyecto.railway.app/health` y verifica `{"status": "ok"}`.

- [ ] **12. Swagger accesible en producción**
  Visita `https://tu-proyecto.railway.app/docs` y prueba POST /chat desde el navegador.

---

## 🚨 Errores frecuentes y soluciones

| Error en logs | Causa | Solución |
|---|---|---|
| `ModuleNotFoundError` | Falta librería en requirements.txt | Agregar la librería y hacer push |
| `GROQ_API_KEY not found` | Variable no configurada en Railway | Agregar en Railway → Variables |
| `Port already in use` | Puerto fijo en el código | Usar `$PORT` en el Procfile |
| `Build failed` | Error de sintaxis en Python | Revisar el log de build en Railway |
| `Health check failed` | `/health` no responde en 30s | Revisar logs del servicio en Railway |
| `Application failed to respond` | Error al iniciar el agente | Ver logs → buscar el error al importar |
