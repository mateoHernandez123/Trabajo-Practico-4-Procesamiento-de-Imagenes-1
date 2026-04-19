# TP 4 — Procesamiento de Imágenes I (guía de ejecución)

**Integrantes:** Mateo Hernandez, Felipe Lucero  
**Imagen utilizada:** `imagenes/imagen_uvas.jpg` (racimo de uvas en viñedo)

En la raíz del proyecto, el archivo **[README.md](../README.md)** resume el trabajo e incluye **todas las figuras** para verlas en GitHub sin abrir cada archivo.

## Estructura del proyecto

| Carpeta / archivo  | Contenido                                                            |
| ------------------ | -------------------------------------------------------------------- |
| `tp_integrador.py` | Código principal (ejecutar desde la raíz del proyecto)               |
| `requirements.txt` | Dependencias Python                                                  |
| `imagenes/`        | Imagen de entrada (`imagen_uvas.jpg`)                                |
| `resultados/`      | Figuras y JPG generados al ejecutar el script (se crea si no existe) |
| `docs/doc.md`      | Respuestas y justificaciones de la consigna                          |
| `docs/Readme.md`   | Este archivo                                                         |

## Objetivo

Script único que calcula histograma y rango dinámico, estadísticos (media, desvío, moda, entropía), decide si aplica expansión de histograma según la entropía, aplica preprocesamiento y filtros, segmenta el objeto de mayor presencia en la escena (racimo principal) y genera una visualización en **falso color** para que el objeto resalte del fondo.

## Requisitos

- Python 3.10 o superior (probado con 3.11)
- Dependencias en `requirements.txt` (en la raíz del proyecto)

## Instalación y ejecución

Abrir una terminal en la **carpeta raíz** del proyecto (donde está `tp_integrador.py`):

```bash
python -m venv venv
```

**Windows (cmd):**

```bat
venv\Scripts\activate
pip install -r requirements.txt
python tp_integrador.py
```

**Windows (PowerShell):**

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python tp_integrador.py
```

**Linux / macOS:**

```bash
source venv/bin/activate
pip install -r requirements.txt
python tp_integrador.py
```

La imagen de entrada debe ser **`imagenes/imagen_uvas.jpg`**. Para usar otra foto, reemplazar ese archivo o cambiar `IMAGE_PATH` en `tp_integrador.py`.

## Salidas generadas (`resultados/`)

| Archivo                    | Descripción                                                          |
| -------------------------- | -------------------------------------------------------------------- |
| `histograma_original.png`  | Histogramas RGB de la imagen original                                |
| `histograma_trabajo.png`   | Histogramas RGB de la imagen de trabajo (tras decisión de expansión) |
| `comparacion.png`          | Solo si se aplica expansión: original vs expandida e histogramas     |
| `imagen_uvas_trabajo.jpg`  | Imagen de trabajo guardada en disco                                  |
| `pipeline_filtros.png`     | Tras expansión (o original), mediana 3×3, unsharp mask               |
| `canales_hsv.png`          | Visualización de H, S, V                                             |
| `histograma_hsv.png`       | Histogramas de H, S, V                                               |
| `segmentacion_resumen.png` | Máscara, extracción, resaltado, falso color y nota de Otsu           |
| `objeto_extraido.jpg`      | Objeto segmentado sobre fondo negro                                  |
| `objeto_falso_color.jpg`   | Falso color (`inferno`) en el objeto, fondo atenuado                 |

## Documentación de respuestas a la consigna

Las justificaciones teóricas y las respuestas a las preguntas del enunciado están en **`docs/doc.md`**.

## Estructura del código

- `load_image`, `compute_histogram`, `effective_range`, `channel_stats`: análisis por canal.
- `histogram_expansion`: estiramiento lineal usando percentiles P2–P98.
- `median_denoise_rgb`, `unsharp_mask_rgb`: preprocesamiento y realce.
- `rgb_to_hsv`, `build_grape_mask_hsv`: segmentación por intervalos en HSV + morfología + **componente conexa de mayor área**.
- `otsu_threshold`: umbral de Otsu en luminancia como **referencia** comparativa en consigna e informe.
- `false_color_object`: colormap `inferno` sobre intensidad local dentro de la máscara.

Si la consola de Windows muestra caracteres raros en los `print`, puede configurarse UTF-8 en la terminal o ignorarse: los resultados gráficos y los JPG/PNG son correctos.
