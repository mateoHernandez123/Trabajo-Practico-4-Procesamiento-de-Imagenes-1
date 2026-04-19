# Documentación — TP Integrador (respuestas y justificaciones)

**Materia:** Procesamiento de Imágenes I  
**Integrantes:** Mateo Hernandez, Felipe Lucero  
**Imagen:** `imagenes/imagen_uvas.jpg` — racimo de uvas moradas con follaje verde e iluminación natural.

**Carpetas:** el código lee desde `imagenes/` y escribe todas las figuras y JPG en `resultados/`.

---

## 1. Histograma

Se calcula un histograma de **256 bins** en el rango [0, 255] para cada canal (R, G, B) y también para H, S, V tras la conversión. El histograma describe la frecuencia de cada nivel de intensidad y permite ver si la imagen usa bien el rango dinámico, si hay picos (cielo, hojas, sombras) y si conviene estirar contraste o trabajar en otro espacio de color.

**Salidas:** `resultados/histograma_original.png`, `resultados/histograma_trabajo.png`, `resultados/histograma_hsv.png`.

---

## 2. Rango dinámico

Se reportan dos nociones complementarias:

1. **Rango absoluto:** `max − min` del canal en toda la imagen. En `imagen_uvas.jpg` los tres canales alcanzan 0 y 255, por lo que el rango absoluto es **255** en R, G y B (típico cuando hay zonas casi negras y reflejos o cielo casi saturados).
2. **Rango efectivo (P2–P98):** descarta una fracción pequeña de outliers en colas del histograma. Valores orientativos obtenidos al ejecutar el script: **231** (R), **238** (G), **233** (B). Un rango efectivo alto indica que la escena ya reparte niveles en una banda ancha; sirve para decidir si el estiramiento global aportará mucho o no.

---

## 3. Estadísticos: media, desvío, moda y entropía

Por cada canal se calcula:

- **Media:** brillo promedio.
- **Desvío estándar:** dispersión de intensidades (textura y contraste local/global).
- **Moda:** nivel más frecuente (picos del histograma).
- **Entropía de Shannon** (base 2, bits): mide la dispersión de la distribución de niveles. Valores cercanos a **8** (máximo teórico para 8 bits) indican que muchos niveles aparecen con frecuencia no trivial.

**Ejemplo de salida de consola (misma corrida):**

| Canal | Media  | Desvío | Moda | Entropía |
| ----- | ------ | ------ | ---- | -------- |
| R     | 115.66 | 55.42  | 123  | 7.7155   |
| G     | 130.37 | 67.25  | 255  | 7.9036   |
| B     | 83.18  | 65.16  | 0    | 7.5619   |

La **moda en B en 0** refleja píxeles muy oscuros o dominancia de azul bajo en sombras; la **moda en G en 255** está ligada a hojas y zonas muy claras.

---

## 4. Entropía y expansión de histograma

**Criterio implementado:** si algún canal tiene entropía **estrictamente menor** a un umbral (`7.0`, configurable), se aplica **expansión lineal** por canal usando los percentiles **P2** y **P98** como rango a mapear a [0, 255] (recorte con `clip`).

En esta imagen, los tres canales superan el umbral (entropías ~7.56–7.90), es decir, la distribución ya es bastante “llena” en términos de niveles utilizados. Por tanto la decisión del programa es **no aplicar expansión**, para no amplificar ruido sin un beneficio claro de contraste global.

Si en otra imagen la entropía fuera baja (histograma muy concentrado), la expansión ayudaría a separar mejor tonos cercanos.

---

## 5. Preprocesamiento (¿es necesario? Justificación)

Sí, de forma **moderada**:

1. **Filtro de mediana 3×3** por canal: reduce ruido tipo **sal y pimienta** y outliers puntuales, frecuentes en sombras entre uvas y en transiciones fuerte borde–fondo. La mediana preserva mejor los bordes que un promedio simple.
2. **Unsharp mask** (I + k·(I − Gauss(I))): tras suavizar con la mediana, se recupera nitidez percibida en hojas y contorno del racimo sin usar un realce tan agresivo como una máscara de altas frecuencias muy amplia.

**Salida:** `resultados/pipeline_filtros.png`.

---

## 6. Filtros según histograma y rango dinámico

- Con **rango efectivo medio ~234 niveles** (P2–P98 en RGB), el contraste global ya es alto: no se priorizó ecualización global ni CLAHE en esta versión, para evitar cambios de tono no deseados en follaje.
- Se priorizó **reducción de ruido** + **realce suave**, alineado con una escena natural con sombras profundas y brillos especulares.

---

## 7. Umbralización y objeto de mayor presencia

**Método principal (justificado para esta imagen):**

1. Conversión a **HSV** (implementación PIL: H, S, V en 0–255).
2. **Umbralización por intervalos** en H, S y V acorde al tono púrpura/violeta de las uvas; los rangos incluyen **sombras internas** (valor V bajo entre bayas y saturación S algo menor en lo oscuro).
3. **Morfología:** primero **cierre** (dilatación–erosión) para unir fragmentos del racimo; una **apertura** leve para quitar ruido puntual en el exterior.
4. **Componente conexa de mayor área:** se queda el blob principal (racimo del medio).
5. **`binary_fill_holes`:** rellena agujeros rodeados por el racimo (efecto “queso gruyere” por sombras que antes quedaban fuera del umbral).
6. **Cierre final** suave para consolidar el borde.

**Referencia adicional:** se calcula el umbral de **Otsu** sobre la **luminancia** (gris ITU-R BT.601) y se muestra en consola y en el panel de texto de `resultados/segmentacion_resumen.png` (en una corrida típica, **T ≈ 117**). Otsu global no está optimizado para separar “uvas vs hojas” cuando ambas clases no forman un histograma bimodal limpio; por eso el pipeline de entrega usa **color + mayor componente** como decisión principal, coherente con la consigna que permite trabajar en color.

**Salidas:** `resultados/segmentacion_resumen.png`, `resultados/objeto_extraido.jpg`.

---

## 8. Falso color

Dentro de la máscara del objeto, cada píxel se colorea según su **luminancia** normalizada usando el colormap **`inferno`** de Matplotlib. El fondo se muestra en **gris atenuado** (factor 0.45 sobre la luminancia) para que el objeto **contraste fuerte** en tonos amarillo–naranja–violeta sobre un entorno casi neutro. `inferno` es perceptualmente uniforme y evita el arcoíris confuso de mapas clásicos tipo `jet`.

**Salida:** `resultados/objeto_falso_color.jpg`.

---

## 9. ¿Escala de grises o color para la segmentación?

Para **esta** imagen se usa **color (HSV)** porque el objetivo morado está **separado cromáticamente** del verde de las hojas; en escala de grises muchos píxeles de uva y de hoja pueden caer en luminancias parecidas, mezclando clases. Si la escena fuera casi monocromática, convendría gris + Otsu o umbral adaptativo local.

---

## 10. ¿Por qué HSV y no solo RGB?

En RGB, el “morado” es una combinación no trivial de R y B; en **HSV** el **tono H** agrupa los matices en un solo canal y **S** separa colores puros de grises, lo que simplifica reglas del tipo “H en arco púrpura, S suficiente, V acotado para evitar negros puros o reflejos extremos”. Alternativas válidas: **CIELAB** (a*, b*) para ser más robusto a sombras si se calibran bien los rangos.

---

## Pregunta A — Automatización de rangos de color para segmentación

Una estrategia práctica es un pipeline en varias capas:

1. **Muestreo semiautomático:** el usuario encierra una región del objeto; se acumulan píxeles en HSV o LAB y se estiman **percentiles robustos** (p. ej. 5–95) de H, S, V para fijar intervalos sin tocar constantes a mano.
2. **Modas en histograma cromático:** detectar picos en histogramas de H (o de ángulo en a*, b*) con suavizado previo; cada pico candidato se etiqueta y se asocia al blob de mayor área.
3. **Clustering:** k-means o GMM en (H, S) o (a*, b*) con k pequeño; luego se elige el cluster cuya máscara tenga **mayor área** o mayor solapamiento con un box inicial.
4. **Backprojection:** histograma modelo del objeto proyectado sobre la imagen completa (OpenCV), útil si hay buena muestra.
5. **Métodos gráficos:** GrabCut / graph cuts con semillas automáticas desde un detector de saliency (más pesado computacionalmente).

En todos los casos conviene cerrar con **morfología** y **componente conexa mayor** para alinearse con “objeto de mayor presencia”.

---

## Pregunta B — Automatización de umbralización para segmentación binaria

Opciones clásicas:

1. **Otsu** sobre la imagen o canal que mejor separe fondo/objeto (a veces no es el gris estándar sino **S** o **V** o `B−G`).
2. Si Otsu global falla por iluminación no uniforme: **umbral adaptativo** (Sauvola, Niblack) sobre ventanas locales.
3. **Método de triángulo** o **Li** cuando el histograma tiene una cola larga y un pico dominante.
4. Tras binarizar: **etiquetado de componentes conexas** y quedarse con la región de **mayor área** (o la que maximice un criterio: centralidad, compacidad, solapamiento con detección previa de color).

Para escenas naturales multiclase, a menudo se combina **umbral automático** + **filtro por área** + **validación por color medio** dentro de cada componente.

---