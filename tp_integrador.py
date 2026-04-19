"""
TP 4 - Procesamiento de Imágenes I
Integrantes: Mateo Hernandez, Felipe Lucero

Imagen: imagenes/imagen_uvas.jpg (racimo de uvas)

Contenido del pipeline:
  - Histograma y rango dinámico (absoluto y efectivo P2–P98)
  - Estadísticos por canal: media, desvío, moda, entropía
  - Decisión de expansión de histograma según entropía
  - Preprocesamiento y filtros espaciales según análisis del histograma
  - Segmentación por rangos en HSV + morfología + componente conexa mayor
  - Falso color sobre el objeto segmentado
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from scipy import stats
from scipy.ndimage import (
    binary_closing,
    binary_fill_holes,
    binary_opening,
    gaussian_filter,
    label,
    median_filter,
)

# -----------------------------------------------------------------------------
# Rutas y constantes
# -----------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
IMAGES_DIR = SCRIPT_DIR / "imagenes"
OUTPUT_DIR = SCRIPT_DIR / "resultados"
IMAGE_PATH = IMAGES_DIR / "imagen_uvas.jpg"

CHANNEL_NAMES = ["Rojo (R)", "Verde (G)", "Azul (B)"]
CHANNEL_COLORS = ["red", "green", "blue"]

# Entropía máxima teórica 8 bits: log2(256) = 8.0
MAX_ENTROPY_8BIT = 8.0
ENTROPY_THRESHOLD = 7.0

# Segmentación HSV (PIL: H,S,V en 0–255). Rangos amplios para uvas + sombras internas
# (entre bayas V cae fuerte; S también baja en zonas muy oscuras).
H_MIN, H_MAX = 145, 225
S_MIN = 14
V_MIN, V_MAX = 4, 220


# -----------------------------------------------------------------------------
# Carga y utilidades de histograma / estadísticos
# -----------------------------------------------------------------------------


def load_image(path: Path) -> np.ndarray:
    img = Image.open(path).convert("RGB")
    data = np.array(img)
    print(f"Imagen cargada: {path}")
    print(f"  Shape: {data.shape}  (alto x ancho x canales)")
    print(f"  Dtype: {data.dtype}")
    return data


def compute_histogram(channel: np.ndarray) -> np.ndarray:
    hist, _ = np.histogram(channel.ravel(), bins=256, range=(0, 256))
    return hist


def effective_range(channel: np.ndarray, percentile_low: float = 2, percentile_high: float = 98):
    flat = channel.ravel()
    p_low = int(np.percentile(flat, percentile_low))
    p_high = int(np.percentile(flat, percentile_high))
    return p_low, p_high


def channel_stats(channel: np.ndarray) -> dict:
    flat = channel.ravel()

    mean = float(np.mean(flat))
    std = float(np.std(flat))
    mode_result = stats.mode(flat, keepdims=True)
    mode_val = int(mode_result.mode[0])

    hist = compute_histogram(channel)
    total = hist.sum()
    if total == 0:
        entropy = 0.0
    else:
        prob = hist.astype(np.float64) / total
        prob_nonzero = prob[prob > 0]
        entropy = float(-np.sum(prob_nonzero * np.log2(prob_nonzero)))

    vmin, vmax = int(flat.min()), int(flat.max())
    dynamic_range = vmax - vmin

    eff_min, eff_max = effective_range(channel)
    eff_range = eff_max - eff_min

    return {
        "min": vmin,
        "max": vmax,
        "rango_dinamico": dynamic_range,
        "eff_min": eff_min,
        "eff_max": eff_max,
        "rango_efectivo": eff_range,
        "media": mean,
        "desvio": std,
        "moda": mode_val,
        "entropia": entropy,
    }


def histogram_expansion(channel: np.ndarray) -> np.ndarray:
    eff_min, eff_max = effective_range(channel)
    if eff_max == eff_min:
        return np.zeros_like(channel)
    expanded = (channel.astype(np.float64) - eff_min) / (eff_max - eff_min) * 255.0
    return np.clip(expanded, 0, 255).astype(np.uint8)


def rgb_to_gray(rgb: np.ndarray) -> np.ndarray:
    r = rgb[:, :, 0].astype(np.float64)
    g = rgb[:, :, 1].astype(np.float64)
    b = rgb[:, :, 2].astype(np.float64)
    y = 0.299 * r + 0.587 * g + 0.114 * b
    return np.clip(y, 0, 255).astype(np.uint8)


def otsu_threshold(gray: np.ndarray) -> int:
    """Umbral de Otsu (0–255) para uint8."""
    hist, _ = np.histogram(gray.ravel(), bins=256, range=(0, 256))
    hist = hist.astype(np.float64)
    total = gray.size
    if total == 0:
        return 0
    prob = hist / total
    omega = np.cumsum(prob)
    mu = np.cumsum(prob * np.arange(256))
    mu_t = mu[-1]
    denom = omega * (1.0 - omega)
    denom[denom == 0] = np.nan
    sigma_b_sq = (mu_t * omega - mu) ** 2 / denom
    return int(np.nanargmax(sigma_b_sq))


def largest_connected_component(mask: np.ndarray) -> np.ndarray:
    """Devuelve máscara booleana con solo la componente conexa de mayor área."""
    labeled, num = label(mask.astype(bool))
    if num == 0:
        return np.zeros_like(mask, dtype=bool)
    counts = np.bincount(labeled.ravel())
    # índice 0 = fondo
    largest_label = int(np.argmax(counts[1:]) + 1)
    return labeled == largest_label


def median_denoise_rgb(image: np.ndarray, size: int = 3) -> np.ndarray:
    out = np.empty_like(image)
    for c in range(3):
        out[:, :, c] = median_filter(image[:, :, c], size=size)
    return out


def unsharp_mask_rgb(image: np.ndarray, sigma: float = 1.2, amount: float = 0.35) -> np.ndarray:
    """Realce suave: I_out = I + amount * (I - Gauss(I))."""
    base = image.astype(np.float64)
    blurred = np.stack([gaussian_filter(base[:, :, c], sigma=sigma) for c in range(3)], axis=2)
    sharp = base + amount * (base - blurred)
    return np.clip(sharp, 0, 255).astype(np.uint8)


def rgb_to_hsv(image_rgb: np.ndarray) -> np.ndarray:
    img_pil = Image.fromarray(image_rgb, "RGB")
    img_hsv = img_pil.convert("HSV")
    return np.array(img_hsv)


def build_grape_mask_hsv(hsv: np.ndarray) -> np.ndarray:
    """
    Umbralización por intervalos en HSV + morfología + mayor componente conexa.
    Se prioriza un racimo compacto: cierre para unir la superficie, luego la mayor
    componente, relleno de agujeros internos (sombras entre uvas) y cierre final.
    """
    h_channel = hsv[:, :, 0]
    s_channel = hsv[:, :, 1]
    v_channel = hsv[:, :, 2]
    mask_h = (h_channel >= H_MIN) & (h_channel <= H_MAX)
    mask_s = s_channel >= S_MIN
    mask_v = (v_channel >= V_MIN) & (v_channel <= V_MAX)
    mask = mask_h & mask_s & mask_v

    struct3 = np.ones((3, 3), dtype=bool)
    struct5 = np.ones((5, 5), dtype=bool)

    # Cierre primero: une fragmentos del racimo antes de abrir (el opening fuerte
    # borraba puentes finos entre bayas y dejaba agujeros tipo "queso gruyere").
    mask = binary_closing(mask, structure=struct3, iterations=5)
    mask = binary_closing(mask, structure=struct5, iterations=1)
    mask = binary_opening(mask, structure=struct3, iterations=1)

    mask = largest_connected_component(mask)

    # Rellena huecos totalmente rodeados por el racimo (sombras internas).
    mask = binary_fill_holes(mask)

    mask = binary_closing(mask, structure=struct3, iterations=2)
    return mask


def false_color_object(rgb: np.ndarray, mask: np.ndarray, intensity: np.ndarray, cmap_name: str = "inferno"):
    """
    Fondo atenuado en escala de grises; objeto con falso color según intensidad local.
    `intensity` suele ser luminancia 0–255 (uint8).
    """
    cmap = plt.colormaps[cmap_name]
    gray = rgb_to_gray(rgb).astype(np.float64) / 255.0
    out = np.zeros_like(rgb, dtype=np.float64)
    for c in range(3):
        out[:, :, c] = gray * 255.0 * 0.45
    t = (intensity.astype(np.float64) / 255.0).clip(0, 1)
    rgba = cmap(t)
    for c in range(3):
        ch = out[:, :, c]
        ch[mask] = rgba[:, :, c][mask] * 255.0
        out[:, :, c] = ch
    return np.clip(out, 0, 255).astype(np.uint8)


def print_stats_table(all_stats: list[dict]):
    header = (
        f"{'Canal':<12} {'Min':>4} {'Max':>4} {'Rango':>6} "
        f"{'EffMin':>7} {'EffMax':>7} {'RgEfec':>7} "
        f"{'Media':>8} {'Desvío':>8} {'Moda':>5} {'Entropía':>9}"
    )
    sep = "-" * len(header)
    print(sep)
    print(header)
    print(sep)
    for name, s in zip(CHANNEL_NAMES, all_stats):
        print(
            f"{name:<12} {s['min']:>4} {s['max']:>4} {s['rango_dinamico']:>6} "
            f"{s['eff_min']:>7} {s['eff_max']:>7} {s['rango_efectivo']:>7} "
            f"{s['media']:>8.2f} {s['desvio']:>8.2f} {s['moda']:>5} {s['entropia']:>9.4f}"
        )
    print(sep)


def plot_histograms(image: np.ndarray, title: str, filename: str, show_effective: bool = True):
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    fig.suptitle(title, fontsize=14, fontweight="bold")

    for i, (ax, name, color) in enumerate(zip(axes, CHANNEL_NAMES, CHANNEL_COLORS)):
        channel = image[:, :, i]
        hist = compute_histogram(channel)
        ax.bar(range(256), hist, color=color, alpha=0.7, width=1.0)

        if show_effective:
            eff_min, eff_max = effective_range(channel)
            ax.axvline(eff_min, color="black", linestyle="--", linewidth=1.2, label=f"P2={eff_min}")
            ax.axvline(eff_max, color="black", linestyle="--", linewidth=1.2, label=f"P98={eff_max}")
            ax.legend(fontsize=8)

        ax.set_title(name)
        ax.set_xlabel("Nivel")
        ax.set_ylabel("Frecuencia")
        ax.set_xlim([0, 255])

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / filename, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Histograma guardado en: resultados/{filename}")


def plot_comparison(original: np.ndarray, expanded: np.ndarray, filename: str = "comparacion.png"):
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle("Comparación: Original vs Expandida", fontsize=14, fontweight="bold")

    axes[0, 0].imshow(original)
    axes[0, 0].set_title("Imagen original")
    axes[0, 0].axis("off")

    axes[0, 1].imshow(expanded)
    axes[0, 1].set_title("Imagen expandida")
    axes[0, 1].axis("off")

    for i, color in enumerate(CHANNEL_COLORS):
        hist_orig = compute_histogram(original[:, :, i])
        hist_exp = compute_histogram(expanded[:, :, i])
        axes[1, 0].plot(hist_orig, color=color, alpha=0.7, label=CHANNEL_NAMES[i])
        axes[1, 1].plot(hist_exp, color=color, alpha=0.7, label=CHANNEL_NAMES[i])

    axes[1, 0].set_title("Histograma original")
    axes[1, 0].set_xlabel("Nivel")
    axes[1, 0].set_ylabel("Frecuencia")
    axes[1, 0].legend()
    axes[1, 0].set_xlim([0, 255])

    axes[1, 1].set_title("Histograma expandido")
    axes[1, 1].set_xlabel("Nivel")
    axes[1, 1].set_ylabel("Frecuencia")
    axes[1, 1].legend()
    axes[1, 1].set_xlim([0, 255])

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / filename, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Comparacion guardada en: resultados/{filename}")


def plot_hsv_overview(hsv: np.ndarray):
    hsv_names = ["Tono (H)", "Saturación (S)", "Valor (V)"]
    cmaps = ["hsv", "gray", "gray"]

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    fig.suptitle("Canales HSV", fontsize=14, fontweight="bold")

    for ax, name, cmap, i in zip(axes, hsv_names, cmaps, range(3)):
        ax.imshow(hsv[:, :, i], cmap=cmap)
        ax.set_title(name)
        ax.axis("off")

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "canales_hsv.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  Canales HSV guardados en: resultados/canales_hsv.png")

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    fig.suptitle("Histogramas HSV", fontsize=14, fontweight="bold")
    colors = ["purple", "orange", "gray"]
    for ax, name, color, i in zip(axes, hsv_names, colors, range(3)):
        hist = compute_histogram(hsv[:, :, i])
        ax.bar(range(256), hist, color=color, alpha=0.7, width=1.0)
        ax.set_title(name)
        ax.set_xlabel("Valor")
        ax.set_ylabel("Frecuencia")
        ax.set_xlim([0, 255])

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "histograma_hsv.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  Histogramas HSV guardados en: resultados/histograma_hsv.png")


def plot_segmentation_summary(
    image_rgb: np.ndarray,
    mask: np.ndarray,
    grapes_only: np.ndarray,
    highlighted: np.ndarray,
    false_color: np.ndarray,
    otsu_t: int,
    filename: str = "segmentacion_resumen.png",
):
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    fig.suptitle("Segmentación, objeto dominante y falso color", fontsize=14, fontweight="bold")

    axes[0, 0].imshow(image_rgb)
    axes[0, 0].set_title("Imagen de trabajo (RGB)")
    axes[0, 0].axis("off")

    axes[0, 1].imshow(mask, cmap="gray")
    axes[0, 1].set_title("Máscara binaria (mayor componente)")
    axes[0, 1].axis("off")

    axes[0, 2].imshow(grapes_only)
    axes[0, 2].set_title("Objeto sobre fondo negro")
    axes[0, 2].axis("off")

    axes[1, 0].imshow(highlighted)
    axes[1, 0].set_title("Resaltado sobre original (fondo x0.35)")
    axes[1, 0].axis("off")

    axes[1, 1].imshow(false_color)
    axes[1, 1].set_title("Falso color (inferno) en el objeto")
    axes[1, 1].axis("off")

    axes[1, 2].axis("off")
    axes[1, 2].text(
        0.05,
        0.55,
        f"Referencia Otsu (luminancia):\nT = {otsu_t}\n\n"
        "Mascara: HSV + cierre\n"
        "morfologico + mayor\n"
        "componente + relleno\n"
        "de huecos internos.",
        fontsize=12,
        verticalalignment="center",
        fontfamily="monospace",
        transform=axes[1, 2].transAxes,
    )

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / filename, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Resumen de segmentacion guardado en: resultados/{filename}")


def plot_filtering_step(original: np.ndarray, denoised: np.ndarray, sharpened: np.ndarray):
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    fig.suptitle("Preprocesamiento y filtrado", fontsize=14, fontweight="bold")
    for ax, im, title in zip(
        axes,
        [original, denoised, sharpened],
        ["Tras expansion (o original)", "Mediana 3x3", "Unsharp mask"],
    ):
        ax.imshow(im)
        ax.set_title(title)
        ax.axis("off")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "pipeline_filtros.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  Figura de filtros guardada en: resultados/pipeline_filtros.png")


def main():
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not IMAGE_PATH.is_file():
        raise FileNotFoundError(f"No se encuentra la imagen: {IMAGE_PATH}")

    print("=" * 60)
    print("PUNTO 1: Carga de imagen RGB")
    print("=" * 60)
    image = load_image(IMAGE_PATH)

    print("\n" + "=" * 60)
    print("PUNTO 2 y 3: Histograma y rango dinámico")
    print("=" * 60)

    all_stats = []
    for i, name in enumerate(CHANNEL_NAMES):
        s = channel_stats(image[:, :, i])
        all_stats.append(s)
        print(f"  {name}: min={s['min']}, max={s['max']} -> rango absoluto = {s['rango_dinamico']}")
        print(f"          rango efectivo (P2-P98): [{s['eff_min']}, {s['eff_max']}] -> {s['rango_efectivo']}")

    plot_histograms(image, "Histogramas - imagen original", "histograma_original.png")

    print("\n" + "=" * 60)
    print("PUNTO 4: Estadísticos por canal")
    print("=" * 60)
    print_stats_table(all_stats)

    print("\n" + "=" * 60)
    print("PUNTO 5: Entropía y expansión de histograma")
    print("=" * 60)

    needs_expansion = any(s["entropia"] < ENTROPY_THRESHOLD for s in all_stats)

    for name, s in zip(CHANNEL_NAMES, all_stats):
        ratio = s["entropia"] / MAX_ENTROPY_8BIT * 100
        low = s["entropia"] < ENTROPY_THRESHOLD
        status = "por debajo del umbral" if low else "alta / reparto más uniforme"
        print(f"  {name}: H = {s['entropia']:.4f} ({ratio:.1f}% del maximo {MAX_ENTROPY_8BIT}) - {status}")

    if needs_expansion:
        print("\n  Decision: al menos un canal con entropia claramente por debajo del maximo teorico.")
        print("  Se aplica expansion lineal por percentiles (P2-P98) canal a canal.")
        expanded = np.stack([histogram_expansion(image[:, :, i]) for i in range(3)], axis=2)
    else:
        print("\n  Decision: la entropia ya es alta en todos los canales; la expansion no es imprescindible.")
        print("  Se mantiene la imagen original para no amplificar ruido sin beneficio claro.")
        expanded = image.copy()

    print("\n  Estadisticos de la imagen de trabajo (post decision de expansion):")
    work_stats = [channel_stats(expanded[:, :, i]) for i in range(3)]
    print_stats_table(work_stats)

    plot_histograms(expanded, "Histogramas - imagen de trabajo", "histograma_trabajo.png")
    if needs_expansion:
        plot_comparison(image, expanded)

    Image.fromarray(expanded).save(OUTPUT_DIR / "imagen_uvas_trabajo.jpg", quality=95)
    print("\n  Imagen de trabajo guardada en: resultados/imagen_uvas_trabajo.jpg")

    print("\n" + "=" * 60)
    print("Preprocesamiento y filtros (según histograma / rango)")
    print("=" * 60)

    eff_ranges = [channel_stats(expanded[:, :, i])["rango_efectivo"] for i in range(3)]
    mean_eff = float(np.mean(eff_ranges))
    print(f"  Rango efectivo medio (P2-P98) en RGB: {mean_eff:.1f} niveles")

    denoised = median_denoise_rgb(expanded, size=3)
    sharpened = unsharp_mask_rgb(denoised, sigma=1.2, amount=0.35)
    print("  Mediana 3x3: reduce ruido tipo sal-pimienta en sombras entre bayas.")
    print("  Unsharp mask: recupera bordes suavizados sin exagerar (amount moderado).")
    plot_filtering_step(expanded, denoised, sharpened)

    print("\n" + "=" * 60)
    print("HSV, segmentación y objeto de mayor presencia")
    print("=" * 60)

    hsv = rgb_to_hsv(sharpened)
    print(f"  Forma HSV: {hsv.shape}")
    plot_hsv_overview(hsv)

    mask = build_grape_mask_hsv(hsv)

    gray_work = rgb_to_gray(sharpened)
    t_otsu = otsu_threshold(gray_work)
    print(f"  Umbral Otsu (luminancia, referencia): T = {t_otsu}")

    pixels_total = mask.size
    pixels_obj = int(np.sum(mask))
    print(f"\n  Umbrales HSV: H en [{H_MIN},{H_MAX}], S>={S_MIN}, V en [{V_MIN},{V_MAX}]")
    print(f"  Tras morfologia y mayor componente conexa: {pixels_obj:,} pixeles ({pixels_obj / pixels_total * 100:.1f}%)")

    grapes_only = sharpened.copy()
    grapes_only[~mask] = 0

    highlighted = sharpened.copy()
    dim = 0.35
    highlighted_f = highlighted.astype(np.float64)
    highlighted_f[~mask] *= dim
    highlighted = np.clip(highlighted_f, 0, 255).astype(np.uint8)

    false_rgb = false_color_object(sharpened, mask, gray_work, cmap_name="inferno")

    plot_segmentation_summary(sharpened, mask, grapes_only, highlighted, false_rgb, t_otsu)

    Image.fromarray(grapes_only).save(OUTPUT_DIR / "objeto_extraido.jpg", quality=95)
    Image.fromarray(false_rgb).save(OUTPUT_DIR / "objeto_falso_color.jpg", quality=95)
    print("  Guardado: resultados/objeto_extraido.jpg, resultados/objeto_falso_color.jpg")

    print("\n" + "=" * 60)
    print("TP Integrador: ejecucion completada.")
    print("=" * 60)


if __name__ == "__main__":
    main()
