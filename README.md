# Tutor Oposiciones - Técnico Especialista (Opción Terapeuta) CARM

Aplicación Streamlit personal para preparar la oposición al Cuerpo de
Técnicos Especialistas, opción Terapeuta, de la Comunidad Autónoma de la
Región de Murcia. Usa la API gratuita de Google Gemini.

## Uso local

```bash
pip install -r requirements.txt
streamlit run app.py
```

Requiere un archivo `.streamlit/secrets.toml` con:

```toml
GOOGLE_API_KEY = "tu-clave-de-gemini"
```
