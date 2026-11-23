# Guide / Guía didáctica

[English](#english-guide) | [Español](#guía-en-español)

---

## English Guide

### 1. Purpose
This project teaches safe, privacy-respecting image handling:
- inspect and remove hidden metadata (EXIF),
- redact faces/areas before sharing,
- find similar local copies,
- generate manual reverse-search links for images you own.

It intentionally does **not** identify people or search social media accounts.

### 2. Prerequisites
- Python 3.10+ (tested with 3.15)
- pip
- Optional: `opencv-python-headless` for automatic face detection

### 3. Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Lesson: EXIF metadata
Photos may contain camera model, date, and sometimes GPS coordinates.

```bash
python3 face_privacy.py exif photo.jpg
python3 face_privacy.py exif photo.jpg --clean --output photo.clean.jpg
```

Check the clean file before sharing publicly.

### 5. Lesson: Redaction
Manual region redaction (x,y,width,height):
```bash
python3 face_privacy.py redact photo.jpg --region 100,60,120,120 --output photo.redacted.jpg
```

Automatic face detection (optional dependency):
```bash
pip install opencv-python-headless
python3 face_privacy.py redact photo.jpg --auto --output photo.redacted.jpg
```

Always visually verify the output; automatic detection can miss faces.

### 6. Lesson: Local similarity
Perceptual hashes help find near-duplicates in your own archive:
```bash
python3 face_privacy.py hash ./photos --compare photo.jpg --threshold 10
```
Lower Hamming distance means more similar. This is not identity recognition.

### 7. Lesson: Manual reverse image search
For images you own and control, you can generate links:
```bash
python3 face_privacy.py search-links photo.jpg --public-url "https://your-site/photo.jpg"
```
Open the links manually. Do not use this to identify or track other people.

### 8. Web interface
```bash
python3 web_app.py
```
Open `http://127.0.0.1:8000`. The UI performs local processing only.

### 9. Ethics and legal notes
- Process only images you own or have permission to process.
- Get consent before sharing or processing identifiable images of others.
- Biometric identification and scraping can be illegal or restricted depending on jurisdiction/platform terms.

---

## Guía en Español

### 1. Propósito
Este proyecto enseña manejo seguro y respetuoso de imágenes:
- inspeccionar y eliminar metadatos ocultos (EXIF),
- redactar caras/zonas antes de compartir,
- encontrar copias similares en local,
- generar enlaces manuales de búsqueda inversa para imágenes que controlas.

Intencionalmente **no** identifica personas ni busca cuentas en redes sociales.

### 2. Requisitos
- Python 3.10+ (probado con 3.15)
- pip
- Opcional: `opencv-python-headless` para detección automática de caras

### 3. Instalación
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Lección: Metadatos EXIF
Las fotos pueden contener modelo de cámara, fecha y a veces coordenadas GPS.

```bash
python3 face_privacy.py exif foto.jpg
python3 face_privacy.py exif foto.jpg --clean --output foto.limpia.jpg
```

Revisa el archivo limpio antes de compartirlo.

### 5. Lección: Redacción
Redacción manual por región (x,y,ancho,alto):
```bash
python3 face_privacy.py redact foto.jpg --region 100,60,120,120 --output foto.redactada.jpg
```

Detección automática (dependencia opcional):
```bash
pip install opencv-python-headless
python3 face_privacy.py redact foto.jpg --auto --output foto.redactada.jpg
```

Verifica siempre el resultado; la detección automática puede fallar.

### 6. Lección: Similitud local
Los hashes perceptuales ayudan a encontrar casi-duplicados en tu archivo:
```bash
python3 face_privacy.py hash ./fotos --compare foto.jpg --threshold 10
```
Menor distancia de Hamming = más similar. No es reconocimiento de identidad.

### 7. Lección: Búsqueda inversa manual
Para imágenes propias que controlas:
```bash
python3 face_privacy.py search-links foto.jpg --public-url "https://tu-sitio/foto.jpg"
```
Abre los enlaces manualmente. No uses esto para identificar o rastrear a otras personas.

### 8. Interfaz web
```bash
python3 web_app.py
```
Abre `http://127.0.0.1:8000`. La UI procesa localmente.

### 9. Ética y legalidad
- Procesa solo imágenes propias o con permiso.
- Obtén consentimiento antes de procesar/compartir imágenes identificables de otras personas.
- La identificación biométrica y el scraping pueden ser ilegales o estar restringidos según jurisdicción y términos de plataforma.
