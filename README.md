# Face Privacy Toolkit / Kit de Privacidad Facial

[English](#english) | [Español](#español)

---

## English

### What it is
A small, privacy-focused Python toolkit for working with portrait images **you own**. It helps you inspect/remove metadata, redact faces/regions, compare local images by visual similarity, and generate manual reverse-image search links. It also includes a local web interface.

### What it is NOT
- No social media account lookup.
- No biometric identification or face recognition against online profiles.
- No scraping of social networks.
- No automatic person matching.

This design is intentional to reduce misuse (doxxing, stalking, non-consensual surveillance).

### Features
- **EXIF inspect/clean**: view metadata and export a clean copy.
- **Redact**: blur/pixelate manual regions; optional automatic face detection with OpenCV.
- **Local perceptual hash compare**: find similar/duplicate images in local folders.
- **Manual reverse-image links**: generate links to Google Lens/Bing/Yandex/TinEye for images you own/control.
- **Local web UI**: simple HTML interface served by Python.

### Install
```bash
git clone https://github.com/BENDER35/face-privacy-toolkit.git
cd face-privacy-toolkit
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Optional for auto face detection:
pip install opencv-python-headless
```

### CLI Usage
```bash
# Show EXIF
python3 face_privacy.py exif photo.jpg

# Remove EXIF
python3 face_privacy.py exif photo.jpg --clean --output photo.clean.jpg

# Redact manual region x,y,w,h
python3 face_privacy.py redact photo.jpg --region 120,80,140,140 --output photo.redacted.jpg

# Auto-detect faces (optional opencv)
python3 face_privacy.py redact photo.jpg --auto --output photo.redacted.jpg

# Compare local similarity
python3 face_privacy.py hash ./my_photos --compare photo.jpg --limit 20

# Manual reverse-image links
python3 face_privacy.py search-links photo.jpg --public-url "https://example.com/photo.jpg"
```

### Web UI
```bash
python3 web_app.py
# Open http://127.0.0.1:8000
```
The web UI runs locally and processes images on your machine. Do not expose it to the public internet without authentication.

### Development
```bash
python3 -m py_compile face_privacy.py web_app.py
```

### License
MIT. See [LICENSE](LICENSE).

---

## Español

### Qué es
Un pequeño kit en Python, enfocado en privacidad, para trabajar con imágenes tipo retrato **de tu propiedad**. Permite inspeccionar/eliminar metadatos, redactar caras/regiones, comparar similitud visual en archivos locales y generar enlaces de búsqueda inversa manual. Incluye una interfaz web local.

### Qué NO es
- No busca cuentas de redes sociales.
- No identifica personas ni hace reconocimiento biométrico contra perfiles online.
- No hace scraping de redes sociales.
- No realiza emparejamiento automático de personas.

Este diseño es intencional para reducir usos indebidos (doxeo, acoso, vigilancia sin consentimiento).

### Funciones
- **Inspeccionar/limpiar EXIF**: ver metadatos y exportar copia limpia.
- **Redactar**: difuminar/pixelar regiones manuales; detección automática opcional con OpenCV.
- **Comparación local por hash perceptual**: encontrar imágenes similares/duplicadas en carpetas locales.
- **Enlaces manuales de búsqueda inversa**: genera enlaces a Google Lens/Bing/Yandex/TinEye para imágenes que controlas.
- **Interfaz web local**: HTML simple servido por Python.

### Instalación
```bash
git clone https://github.com/BENDER35/face-privacy-toolkit.git
cd face-privacy-toolkit
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Opcional para detección automática:
pip install opencv-python-headless
```

### Uso CLI
```bash
python3 face_privacy.py exif foto.jpg
python3 face_privacy.py exif foto.jpg --clean --output foto.limpia.jpg
python3 face_privacy.py redact foto.jpg --region 120,80,140,140 --output foto.redactada.jpg
python3 face_privacy.py redact foto.jpg --auto --output foto.redactada.jpg
python3 face_privacy.py hash ./mis_fotos --compare foto.jpg --limit 20
python3 face_privacy.py search-links foto.jpg --public-url "https://ejemplo.com/foto.jpg"
```

### Interfaz web
```bash
python3 web_app.py
# Abrir http://127.0.0.1:8000
```
La interfaz web se ejecuta localmente y procesa imágenes en tu máquina. No la expongas a Internet sin autenticación.

### Licencia
MIT. Ver [LICENSE](LICENSE).
