# TP 4 — Procesamiento de Imágenes I (guía de ejecución)

**Materia:** Procesamiento de Imágenes I  
**Integrantes:** Mateo Hernandez, Felipe Lucero  
**Repositorio:** [github.com/mateoHernandez123/Trabajo-Practico-4-Procesamiento-de-Imagenes-1](https://github.com/mateoHernandez123/Trabajo-Practico-4-Procesamiento-de-Imagenes-1)

**Imagen por defecto:** `imagenes/imagen_uvas.jpg` (racimo de uvas con follaje).

En la raíz del proyecto, **[README.md](../README.md)** resume el pipeline, la estructura y las **figuras de resultados** para verlas en GitHub sin abrir cada archivo.

## Estructura del proyecto

| Carpeta / archivo   | Contenido                                                            |
| ------------------- | -------------------------------------------------------------------- |
| `README.md`         | Vista general del TP, figuras embebidas y enlaces a esta guía y al informe |
| `tp_integrador.py`  | Código principal (ejecutar desde la raíz del proyecto)               |
| `requirements.txt`  | Dependencias: `numpy`, `matplotlib`, `Pillow`, `scipy`               |
| `imagenes/`         | Entrada (`imagen_uvas.jpg` o la que indique `IMAGE_PATH` en el script) |
| `resultados/`       | Salidas PNG/JPG (la carpeta se crea al ejecutar si no existe)         |
| `docs/doc.md`       | Respuestas y justificaciones de la consigna                        |
| `docs/Readme.md`    | Este archivo                                                         |
| `.gitignore`        | `venv/`, bytecode, cachés e ignorados de IDE                         |

## Objetivo

Un solo script (`tp_integrador.py`) calcula histograma y rango dinámico (absoluto y P2–P98), estadísticos por canal (media, desvío, moda, entropía), decide si aplica expansión de histograma según entropía, aplica preprocesamiento (mediana + unsharp mask), segmenta en **HSV** el objeto de mayor área (racimo) y genera **falso color** (`inferno`) para que el objeto resalte del fondo.

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

**Windows (Git Bash),** desde la raíz del proyecto:

```bash
source venv/Scripts/activate
pip install -r requirements.txt
python tp_integrador.py
```

La imagen de entrada por defecto es **`imagenes/imagen_uvas.jpg`**. Para otra foto, ajusta `IMAGE_PATH` (y si hace falta `IMAGES_DIR`) al inicio de `tp_integrador.py`, o reemplaza el archivo manteniendo la misma ruta.

## Salidas generadas (`resultados/`)

| Archivo                    | Descripción                                                          |
| -------------------------- | -------------------------------------------------------------------- |
| `histograma_original.png`  | Histogramas RGB de la imagen original                                |
| `histograma_trabajo.png`   | Histogramas RGB de la imagen de trabajo (tras decisión de expansión) |
| `comparacion.png`          | Solo si se aplica expansión: original vs expandida e histogramas     |
| `imagen_uvas_trabajo.jpg`  | Imagen de trabajo guardada en disco                                  |
| `pipeline_filtros.png`     | Imagen de trabajo (post decisión de expansión), mediana 3×3, unsharp mask |
| `canales_hsv.png`          | Visualización de H, S, V                                             |
| `histograma_hsv.png`       | Histogramas de H, S, V                                               |
| `segmentacion_resumen.png` | Entrada a segmentación (post filtros), máscara, extracción, resaltado, falso color y nota Otsu |
| `objeto_extraido.jpg`      | Objeto segmentado sobre fondo negro                                  |
| `objeto_falso_color.jpg`   | Falso color (`inferno`) en el objeto, fondo atenuado                 |

## Documentación de respuestas a la consigna

Las justificaciones teóricas y las respuestas a las preguntas del enunciado están en **`docs/doc.md`**.

## Estructura del código

- `load_image`, `compute_histogram`, `effective_range`, `channel_stats`: análisis por canal.
- `histogram_expansion`: estiramiento lineal usando percentiles P2–P98.
- `plot_comparison`: guarda `comparacion.png` solo cuando la expansión se aplica (`needs_expansion`).
- `median_denoise_rgb`, `unsharp_mask_rgb`: preprocesamiento y realce.
- `rgb_to_hsv`, `build_grape_mask_hsv`: segmentación por intervalos en HSV + morfología + **componente conexa de mayor área** + `binary_fill_holes`.
- `otsu_threshold` / `rgb_to_gray`: Otsu sobre luminancia BT.601 como **referencia** en consola y en el panel de texto del resumen.
- `false_color_object`: colormap `inferno` sobre luminancia dentro de la máscara; fondo en gris atenuado.

Si la consola de Windows muestra caracteres raros en los `print`, puede configurarse UTF-8 en la terminal o ignorarse: los resultados gráficos y los JPG/PNG son correctos.
