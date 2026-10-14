"""Lógica de la interfaz web que no depende de Streamlit, para poder probarla por separado.

La página (app_streamlit.py) solo dibuja: los números, el medidor y la explicación de la
predicción se calculan aquí. Todo lo que sale de este módulo son números o HTML construido
con números; el texto que escribe la persona (título, artista) nunca entra al medidor.
"""

import math

import numpy as np
import pandas as pd

from src.variables import ANIO_CORTE

ETIQUETA_GENERO = {
    "pop": "Pop",
    "urbano": "Urbano",
    "rock": "Rock",
    "electronica": "Electrónica",
    "indie": "Indie",
}

ETIQUETA_VARIABLE = {
    "bailabilidad": "Bailabilidad",
    "energia": "Energía",
    "valencia": "Valencia",
    "acustica": "Acústica",
    "tempo": "Tempo",
    "duracion_min": "Duración",
    "duracion_c2": "Duración",  # la derivada y la original se presentan juntas
    "volumen_db": "Volumen",
    "anio": "Año",
    "colaboracion": "Colaboración",
}

# Variables numéricas cuyo rango de entrenamiento se avisa si la persona se sale de él.
# El año no entra: toda canción nueva es posterior al entrenamiento y se avisa aparte.
VARIABLES_CON_AVISO = {
    "bailabilidad": "bailabilidad",
    "energia": "energía",
    "valencia": "valencia",
    "acustica": "acústica",
    "tempo": "tempo",
    "duracion_min": "duración",
    "volumen_db": "volumen",
}


def num(valor: float, decimales: int = 1) -> str:
    """Número con coma decimal: 84.8 -> '84,8'."""
    return f"{valor:.{decimales}f}".replace(".", ",")


def limpio(valor: float) -> str:
    """Número sin ceros sobrantes y con coma decimal: 65.0 -> '65', 0.27 -> '0,27'."""
    return f"{valor:g}".replace(".", ",")


def fuera_de_rango(fila: dict, datos: pd.DataFrame) -> list[str]:
    """Nombres de las variables que la persona puso fuera del rango visto en entrenamiento."""
    ent = datos[datos["anio"] < ANIO_CORTE]
    fuera = []
    for columna, nombre in VARIABLES_CON_AVISO.items():
        if columna in fila and not ent[columna].min() <= fila[columna] <= ent[columna].max():
            fuera.append(nombre)
    return fuera


def contribuciones(modelo: dict, fila: dict, datos: pd.DataFrame):
    """Cuántos puntos suma o resta cada variable respecto a una canción promedio del entrenamiento.

    Solo aplica a regresiones lineales. Devuelve (base, aportes) con la identidad exacta
    predicción = base + suma(aportes), o None si el modelo no es lineal o no se puede descomponer.
    Los aportes son asociaciones del modelo, no efectos causales.
    """
    pipeline, ficha = modelo["pipeline"], modelo["ficha"]
    estimador = pipeline[-1]
    if ficha["tarea"] != "regresion" or not hasattr(estimador, "coef_") or len(pipeline) < 2:
        return None
    try:
        X = pd.DataFrame([fila])[modelo["columnas_entrada"]]
        z = np.ravel(pipeline[:-1].transform(X))
        nombres = [n.split("__", 1)[-1] for n in pipeline[-2].get_feature_names_out()]
        coef = np.ravel(estimador.coef_)
        if not len(z) == len(coef) == len(nombres):
            return None
        proporcion = datos[datos["anio"] < ANIO_CORTE]["genero"].value_counts(normalize=True)
        base = float(np.ravel(estimador.intercept_)[0])
        aportes: dict[str, float] = {}
        for nombre, zj, cj in zip(nombres, z, coef):
            if nombre.startswith("genero_"):
                # Referencia del género: la mezcla de géneros del entrenamiento.
                pj = float(proporcion.get(nombre[len("genero_"):], 0.0))
                base += pj * cj
                aporte, clave = (zj - pj) * cj, "Género"
            else:
                aporte, clave = zj * cj, ETIQUETA_VARIABLE.get(nombre, nombre)
            aportes[clave] = aportes.get(clave, 0.0) + float(aporte)
        return base, aportes
    except Exception:  # un pipeline propio con otra estructura simplemente no se descompone
        return None


# --- Medidor ----------------------------------------------------------------------------
# Geometría del dial: un semicírculo de 0 a 100 centrado en (CX, CY).
CX, CY, R = 210, 214, 150
RADIO_CARA = R + 58

CSS_MEDIDOR = """
.vu { max-width: 520px; color: var(--tinta); font-family: 'Archivo', system-ui, sans-serif; }
.vu svg { display: block; width: 100%; height: auto; }
.vu .vu-num { font: 600 13px 'Archivo', system-ui, sans-serif; fill: var(--tinta); }
.vu .vu-rotulo { font: 500 12px 'Archivo', system-ui, sans-serif; fill: #4A5B76; }
.vu .vu-lectura { display: flex; align-items: baseline; gap: 6px 22px; flex-wrap: wrap; margin-top: 10px; }
.vu .vu-cifra { font-size: 64px; font-weight: 800; line-height: 1; font-variation-settings: 'wdth' 118; }
.vu .vu-cifra small { font-size: 18px; font-weight: 600; margin-left: 6px; color: #4A5B76; }
.vu .vu-veredicto { font-size: 28px; font-weight: 800; font-variation-settings: 'wdth' 118; }
.vu .vu-detalle { margin: 8px 0 0; font-size: 16px; line-height: 1.5; color: #2B3A55; }
.vu .vu-leyenda { margin: 14px 0 10px; display: flex; gap: 8px 24px; flex-wrap: wrap; font-size: 14px; color: #2B3A55; }
.vu .vu-leyenda span { white-space: nowrap; }
.vu .vu-leyenda i { display: inline-block; width: 22px; height: 7px; margin-right: 8px; vertical-align: middle; }
"""


def _punto(radio: float, valor: float) -> tuple[float, float]:
    angulo = math.radians(-90 + 1.8 * valor)
    return CX + radio * math.sin(angulo), CY - radio * math.cos(angulo)


def _arco(radio: float, desde: float, hasta: float) -> str:
    x0, y0 = _punto(radio, desde)
    x1, y1 = _punto(radio, hasta)
    grande = 1 if (hasta - desde) * 1.8 > 180 else 0
    return f"M {x0:.1f} {y0:.1f} A {radio} {radio} 0 {grande} 1 {x1:.1f} {y1:.1f}"


def medidor_html(
    valor: float,
    corte: float,
    promocionar: bool,
    cifra: str,
    unidad: str,
    rotulo: str,
    detalle: str,
    leyenda_zona: str,
    margen: float | None = None,
    leyenda_rango: str | None = None,
    color_ok: str = "#0E7C7B",
    color_no: str = "#B23A48",
    color_rango: str = "#E8A200",
) -> str:
    """Medidor tipo VU con la aguja en `valor`, la zona de promoción desde `corte` y, si hay
    `margen`, el rango esperado. Todos los valores van en la escala 0 a 100."""
    pos = max(0.0, min(100.0, valor))
    color = color_ok if promocionar else color_no
    angulo = -90 + 1.8 * pos

    marcas = []
    for v in range(0, 101, 5):
        mayor = v % 10 == 0
        x0, y0 = _punto(R + 4, v)
        x1, y1 = _punto(R + (16 if mayor else 10), v)
        marcas.append(
            f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" '
            f'stroke="#14213D" stroke-width="{2 if mayor else 1}"/>'
        )
        if v % 20 == 0:
            xt, yt = _punto(R + 34, v)
            marcas.append(f'<text x="{xt:.1f}" y="{yt + 5:.1f}" text-anchor="middle" class="vu-num">{v}</text>')

    corte_pos = max(0.0, min(100.0, corte))
    xa, ya = _punto(R - 26, corte_pos)
    xb, yb = _punto(R + 18, corte_pos)

    rango_svg = ""
    if margen is not None:
        r0, r1 = max(0.0, valor - margen), min(100.0, valor + margen)
        if r1 > r0:
            rango_svg = f'<path d="{_arco(R - 26, r0, r1)}" fill="none" stroke="{color_rango}" stroke-width="8"/>'

    cara = (
        f"M {CX - RADIO_CARA} {CY} A {RADIO_CARA} {RADIO_CARA} 0 0 1 {CX + RADIO_CARA} {CY} "
        f"L {CX + RADIO_CARA} {CY + 30} L {CX - RADIO_CARA} {CY + 30} Z"
    )
    leyenda = f'<span><i style="background:{color_ok}"></i>{leyenda_zona}</span>'
    if margen is not None and leyenda_rango:
        leyenda += f'<span><i style="background:{color_rango}"></i>{leyenda_rango}</span>'

    animacion = (
        f"<style>{CSS_MEDIDOR}"
        f".vu .vu-aguja {{ transform-origin: {CX}px {CY}px; transform: rotate({angulo:.1f}deg); "
        f"animation: vu-oscila .9s cubic-bezier(.22,1.25,.36,1) both; }}"
        f"@keyframes vu-oscila {{ from {{ transform: rotate(-90deg); }} to {{ transform: rotate({angulo:.1f}deg); }} }}"
        f"@media (prefers-reduced-motion: reduce) {{ .vu .vu-aguja {{ animation: none; }} }}"
        f"</style>"
    )

    return (
        f'{animacion}<div class="vu">'
        f'<svg viewBox="0 0 420 256" role="img" aria-label="Medidor: {cifra} {unidad}">'
        f'<defs><radialGradient id="vu-luz" cx="50%" cy="100%" r="75%">'
        f'<stop offset="0%" stop-color="#FFE7A3"/><stop offset="55%" stop-color="#FCF3DA"/>'
        f'<stop offset="100%" stop-color="#F4F7FA"/></radialGradient></defs>'
        f'<path d="{cara}" fill="url(#vu-luz)" stroke="#14213D" stroke-width="3" stroke-linejoin="round"/>'
        f'<path d="{_arco(R - 6, 0, 100)}" fill="none" stroke="#B8C4CF" stroke-width="10"/>'
        f'<path d="{_arco(R - 6, corte_pos, 100)}" fill="none" stroke="{color_ok}" stroke-width="10"/>'
        f"{rango_svg}{''.join(marcas)}"
        f'<line x1="{xa:.1f}" y1="{ya:.1f}" x2="{xb:.1f}" y2="{yb:.1f}" stroke="{color_ok}" stroke-width="4"/>'
        f'<text x="{CX}" y="{CY + 24}" text-anchor="middle" class="vu-rotulo">{rotulo}</text>'
        f'<g class="vu-aguja"><line x1="{CX}" y1="{CY + 16}" x2="{CX}" y2="{CY - (R - 4)}" '
        f'stroke="#14213D" stroke-width="3.5" stroke-linecap="round"/></g>'
        f'<circle cx="{CX}" cy="{CY}" r="10" fill="#14213D"/><circle cx="{CX}" cy="{CY}" r="3.5" fill="#F4F7FA"/>'
        f"</svg>"
        f'<div class="vu-lectura"><div class="vu-cifra">{cifra}<small>{unidad}</small></div>'
        f'<div class="vu-veredicto" style="color:{color}">{"Promocionar" if promocionar else "No promocionar"}</div></div>'
        f'<p class="vu-detalle">{detalle}</p>'
        f'<div class="vu-leyenda">{leyenda}</div></div>'
    )
