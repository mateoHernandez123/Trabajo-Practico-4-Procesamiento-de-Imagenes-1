# Trabajo Práctico 4 — Procesamiento de Imágenes I

**Materia:** Procesamiento de Imágenes I  
**Integrantes:** Mateo Hernandez, Felipe Lucero  
**Repositorio sugerido en GitHub:** `Trabajo-Practico-4-Procesamiento-de-Imagenes-1`

Este trabajo implementa un pipeline en Python: histograma y rango dinámico, estadísticos (media, desvío, moda, entropía), decisión de expansión de histograma según entropía, preprocesamiento y filtros, segmentación del racimo principal en HSV con morfología y relleno de huecos, y visualización en **falso color**.

---

## Cómo ejecutar

```bash
pip install -r requirements.txt
python tp_integrador.py
```

Instrucciones detalladas (venv, Windows/Linux): [docs/Readme.md](docs/Readme.md).  
Respuestas y justificaciones de la consigna: [docs/doc.md](docs/doc.md).

---

## Imagen de entrada

Escena elegida para aplicar todos los conceptos: racimo de uvas con follaje e iluminación natural.

![Imagen de entrada — escena de uvas](imagenes/imagen_uvas.jpg)

**Uso en el código:** se carga en RGB desde `imagenes/imagen_uvas.jpg` y es la base de histogramas, estadísticos y segmentación.

---

## Resultados visuales (qué muestra cada una y qué técnica justifica)

### 1. Histogramas RGB — imagen original

![Histogramas RGB de la imagen original](resultados/histograma_original.png)

**Qué es:** frecuencia de niveles 0–255 en R, G y B (líneas verticales P2–P98 = rango efectivo).  
**Qué justifica:** ver reparto de intensidades, picos (hojas, sombras, reflejos) y si el rango dinámico está concentrado o repartido.

---

### 2. Histogramas RGB — imagen de trabajo

![Histogramas RGB de la imagen de trabajo](resultados/histograma_trabajo.png)

**Qué es:** mismos histogramas tras la **decisión por entropía** (expansión por percentiles solo si algún canal tiene entropía bajo el umbral; si no, la imagen de trabajo coincide con la original).  
**Qué justifica:** comparar con el paso anterior y fundamentar si hizo falta estirar contraste global.

---

### 3. Imagen de trabajo guardada (JPG)

![Imagen de trabajo en disco](resultados/imagen_uvas_trabajo.jpg)

**Qué es:** la imagen que alimenta filtros y segmentación (original o expandida).  
**Qué justifica:** traza reproducible del dato intermedio entre análisis y preprocesamiento.

---

### 4. Preprocesamiento y filtros (mediana + unsharp mask)

![Pipeline: trabajo, mediana 3×3, unsharp mask](resultados/pipeline_filtros.png)

**Qué es:** izquierda imagen de trabajo; centro **filtro de mediana 3×3** por canal (reduce ruido en sombras); derecha **unsharp mask** (realce suave de bordes).  
**Qué justifica:** la consigna pide filtros acordes al histograma/rango; acá se prioriza denoise + realce sin ecualización agresiva.

---

### 5. Canales H, S, V (espacio HSV)

![Canales HSV como imágenes](resultados/canales_hsv.png)

**Qué es:** tono (H), saturación (S) y valor (V) tras convertir desde RGB.  
**Qué justifica:** por qué segmentamos en **HSV** (el morado del racimo se separa mejor del verde de las hojas que en un solo canal en gris).

---

### 6. Histogramas de H, S y V

![Histogramas de los canales HSV](resultados/histograma_hsv.png)

**Qué es:** distribución de valores en cada canal HSV.  
**Qué justifica:** apoyar la elección de **umbrales por intervalos** en H, S y V para las uvas.

---

### 7. Resumen de segmentación y falso color

![Máscara, extracción, resaltado, falso color y nota Otsu](resultados/segmentacion_resumen.png)

**Qué es:** panel con imagen filtrada, **máscara binaria** (mayor componente conexa), objeto sobre negro, resaltado con fondo atenuado, **falso color inferno** y valor de **Otsu** en luminancia como referencia.  
**Qué justifica:** umbralización por color + morfología (**cierre**, apertura leve) + **relleno de huecos** (`binary_fill_holes`) para incluir sombras internas del racimo; Otsu documenta un umbral global clásico aunque el método principal sea HSV.

---

### 8. Objeto segmentado (fondo negro)

![Racimo extraído sobre fondo negro](resultados/objeto_extraido.jpg)

**Qué es:** solo los píxeles dentro de la máscara final.  
**Qué justifica:** resultado binario / segmentación del **objeto de mayor presencia** (mayor componente conexa del color elegido).

---

### 9. Falso color sobre el objeto

![Falso color inferno en el racimo](resultados/objeto_falso_color.jpg)

**Qué es:** fondo en gris atenuado; dentro de la máscara, color según luminancia con colormap **`inferno`**.  
**Qué justifica:** la consigna pide **falso color** para que el objeto resalte; `inferno` es perceptualmente uniforme y legible.

---

## Estructura del proyecto

| Ruta | Contenido |
|------|-----------|
| `tp_integrador.py` | Código del pipeline |
| `requirements.txt` | Dependencias |
| `imagenes/imagen_uvas.jpg` | Entrada |
| `resultados/` | Figuras y JPG generados al ejecutar el script |
| `docs/Readme.md` | Instalación y ejecución |
| `docs/doc.md` | Informe / respuestas a la consigna |

---

## Subir a GitHub (crear el repo `Trabajo-Practico-4-Procesamiento-de-Imagenes-1`)

1. En GitHub: **New repository** → nombre `Trabajo-Practico-4-Procesamiento-de-Imagenes-1` → sin README si ya tenés uno local.
2. En la carpeta del proyecto (ya renombrada si seguiste el paso de carpeta):

```bash
git init
git add .
git commit -m "TP4: pipeline de procesamiento de imagenes (uvas)"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/Trabajo-Practico-4-Procesamiento-de-Imagenes-1.git
git push -u origin main
```

Si usás **GitHub CLI** (`gh`) autenticado:

```bash
gh repo create Trabajo-Practico-4-Procesamiento-de-Imagenes-1 --private --source=. --remote=origin --push
```

*(Ajustá `--public` o `--private` según la cátedra.)*

**Nota:** las imágenes de `resultados/` deben estar **commiteadas** para que se vean en el README en GitHub; si no las subís, los enlaces `![](resultados/...)` quedarán rotos hasta volver a generarlas y hacer push.
