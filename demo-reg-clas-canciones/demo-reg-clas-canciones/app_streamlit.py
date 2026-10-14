"""Interfaz web del servicio de predicción de canciones (Streamlit).

    pip install -r requirements-ui.txt
    streamlit run app_streamlit.py          # http://localhost:8501

La página no tiene reglas propias: carga models/modelo.pkl con src.artefacto.cargar y decide con
la misma función que la API (src.app.main.predecir_filas), así que lo que se ve aquí coincide con
lo que responde POST /predecir. Sirve para el modelo del sprint 1 (regresión) y para el del
sprint 2 (clasificación): cambiar de modelo es reemplazar el .pkl.
"""

import html

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from pydantic import ValidationError

from src.app.esquemas import Cancion
from src.app.main import predecir_filas
from src.artefacto import RUTA_MODELO, cargar
from src.interfaz import (
    ETIQUETA_GENERO,
    contribuciones,
    fuera_de_rango,
    limpio,
    medidor_html,
    num,
)
from src.variables import ANIO_CORTE, FILA_EJEMPLO, GENEROS, cargar_canciones

TINTA, PANEL, LINEA = "#14213D", "#F7FAFC", "#B8C4CF"
TURQUESA, LADRILLO, AMBAR = "#0E7C7B", "#B23A48", "#E8A200"
COLOR_GENERO = {
    "pop": "#3A6EA5",
    "urbano": "#E8A200",
    "rock": "#7B4B94",
    "electronica": "#0E7C7B",
    "indie": "#8795A5",
}

st.set_page_config(page_title="Promoción de lanzamientos", page_icon="🎚️", layout="wide")

# El tema (colores base de widgets y fondo) vive en .streamlit/config.toml; aquí solo la tipografía.
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@100..125,500..900&display=swap');
:root { --tinta: #14213D; --turquesa: #0E7C7B; --ladrillo: #B23A48; --ambar: #E8A200; }
.block-container { padding-top: 2.6rem; max-width: 1180px; }
[data-testid="stHeading"] h1, [data-testid="stHeading"] h2, [data-testid="stHeading"] h3 {
    font-family: 'Archivo', system-ui, sans-serif; font-variation-settings: 'wdth' 118; color: var(--tinta);
}
[data-testid="stHeading"] h1 { font-weight: 800; font-size: 2.6rem; letter-spacing: -0.015em; line-height: 1.1; }
[data-testid="stHeading"] h3 { font-weight: 700; font-size: 1.15rem; margin-top: .6rem; }
.entradilla { font-size: 1.1rem; max-width: 46rem; margin: .2rem 0 1.4rem; color: #2B3A55; }
.cancion { font-size: 1.05rem; margin: 0 0 .4rem; color: #2B3A55; }
.cancion b { color: var(--tinta); }
.nota { border-left: 4px solid var(--ambar); padding: .15rem 0 .15rem .9rem; margin: .9rem 0; color: #2B3A55; font-size: .98rem; }
.nota.alerta { border-left-color: var(--ladrillo); }
button[data-baseweb="tab"] p { font-weight: 600; font-size: 1.02rem; }
</style>
""",
    unsafe_allow_html=True,
)


# --- Carga del modelo y de los datos --------------------------------------------------------
@st.cache_resource(show_spinner="Cargando el modelo…")
def cargar_modelo(marca_de_tiempo: float) -> dict:
    """La marca de tiempo del archivo invalida la caché cuando se reemplaza el .pkl."""
    return cargar(RUTA_MODELO)


@st.cache_data(show_spinner=False)
def cargar_datos() -> pd.DataFrame | None:
    try:
        return cargar_canciones()
    except FileNotFoundError:
        return None


if not RUTA_MODELO.exists():
    st.error(
        f"No hay un modelo en `{RUTA_MODELO.name}`. Entrénalo con `python -m src.entrenar_regresion` "
        "y recarga esta página."
    )
    st.stop()

try:
    modelo = cargar_modelo(RUTA_MODELO.stat().st_mtime)
except Exception as error:  # archivo dañado, ficha incompleta o versión incompatible
    st.error(f"No se pudo cargar el modelo: {error}")
    st.stop()

ficha = modelo["ficha"]
es_clasificacion = ficha["tarea"] == "clasificacion"
datos = cargar_datos()

st.title("¿Conviene promocionar esta canción?")
st.markdown(
    '<p class="entradilla">Describe la canción antes de publicarla. El modelo estima qué tan bien le irá '
    "y recomienda si vale la pena invertir en promoción.</p>",
    unsafe_allow_html=True,
)

tab_prediccion, tab_catalogo, tab_modelo = st.tabs(["Predicción", "Catálogo", "Modelo"])


def estilo(fig: go.Figure, alto: int, leyenda: bool = False) -> go.Figure:
    fig.update_layout(
        height=alto,
        margin=dict(l=8, r=36, t=16, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=PANEL,
        font=dict(family="'Source Sans 3', 'Source Sans Pro', system-ui, sans-serif", color=TINTA, size=13),
        separators=",.",
        showlegend=leyenda,
        legend=dict(orientation="h", y=1.14, x=0),
    )
    fig.update_xaxes(gridcolor="#DDE4EA", zeroline=False, linecolor=LINEA)
    fig.update_yaxes(gridcolor="#DDE4EA", zeroline=False, linecolor=LINEA)
    return fig


# --- Predicción -----------------------------------------------------------------------------
with tab_prediccion:
    col_form, col_res = st.columns([5, 6], gap="large")

    with col_form:
        st.subheader("La canción")
        titulo = st.text_input("Título", "Midnight Pulse", max_chars=60, key="titulo")
        artista = st.text_input("Artista", "Artista Demo", max_chars=60, key="artista")
        c1, c2 = st.columns(2)
        genero = c1.selectbox(
            "Género",
            GENEROS,
            index=GENEROS.index(FILA_EJEMPLO["genero"]),
            format_func=lambda g: ETIQUETA_GENERO.get(g, g.title()),
            key="genero",
        )
        anio = c2.number_input("Año de lanzamiento", 1990, 2035, FILA_EJEMPLO["anio"], step=1, key="anio")
        colaboracion = st.toggle("Es una colaboración", value=bool(FILA_EJEMPLO["colaboracion"]), key="colaboracion")

        st.subheader("Cómo suena")
        bailabilidad = st.slider("Bailabilidad", 0.0, 1.0, FILA_EJEMPLO["bailabilidad"], 0.01, key="bailabilidad")
        energia = st.slider("Energía", 0.0, 1.0, FILA_EJEMPLO["energia"], 0.01, key="energia")
        valencia = st.slider("Valencia (qué tan alegre suena)", 0.0, 1.0, FILA_EJEMPLO["valencia"], 0.01, key="valencia")
        acustica = st.slider("Acústica", 0.0, 1.0, FILA_EJEMPLO["acustica"], 0.01, key="acustica")

        st.subheader("Producción")
        tempo = st.slider("Tempo (pulsos por minuto)", 50, 210, int(FILA_EJEMPLO["tempo"]), key="tempo")
        duracion = st.slider("Duración (minutos)", 1.0, 7.0, FILA_EJEMPLO["duracion_min"], 0.1, key="duracion")
        volumen = st.slider("Volumen (dB)", -25.0, 0.0, FILA_EJEMPLO["volumen_db"], 0.5, key="volumen")

    entrada = {
        "bailabilidad": bailabilidad,
        "energia": energia,
        "valencia": valencia,
        "acustica": acustica,
        "tempo": float(tempo),
        "duracion_min": duracion,
        "volumen_db": volumen,
        "anio": int(anio),
        "colaboracion": int(colaboracion),
        "genero": genero,
    }
    try:
        pred = predecir_filas(modelo, [Cancion(**entrada)])[0]
    except ValidationError as error:
        st.error(f"La canción no cumple el formato del servicio: {error.errors()[0]['msg']}")
        st.stop()
    st.session_state["ultima_prediccion"] = pred.model_dump()

    with col_res:
        st.markdown(
            f'<p class="cancion"><b>{html.escape(titulo)}</b> de {html.escape(artista)}, '
            f"{ETIQUETA_GENERO.get(genero, genero.title()).lower()}, {int(anio)}</p>",
            unsafe_allow_html=True,
        )

        if es_clasificacion:
            valor, corte = pred.probabilidad_hit * 100, pred.umbral * 100
            medidor = medidor_html(
                valor=valor,
                corte=corte,
                promocionar=pred.promocionar,
                cifra=num(valor, 1),
                unidad="%",
                rotulo="Probabilidad de hit",
                detalle=(
                    f"La probabilidad de que sea un hit {'alcanza' if pred.promocionar else 'queda por debajo de'} "
                    f"el umbral de {limpio(corte)} %."
                ),
                leyenda_zona=f"Zona de promoción: desde {limpio(corte)} %",
            )
        else:
            mae = float(ficha["desempeno"]["mae"])
            valor, corte = pred.popularidad_esperada, pred.corte_promocion
            detalle = (
                f"La popularidad esperada {'alcanza' if pred.promocionar else 'queda por debajo de'} "
                f"el corte de {limpio(corte)}, con un error típico de ±{limpio(mae)} puntos."
            )
            if not 0 <= valor <= 100:
                detalle += " Queda fuera de la escala 0 a 100: el modelo lineal no conoce esos límites."
            medidor = medidor_html(
                valor=valor,
                corte=corte,
                promocionar=pred.promocionar,
                cifra=num(valor, 1),
                unidad="de 100",
                rotulo="Popularidad esperada",
                detalle=detalle,
                leyenda_zona=f"Zona de promoción: desde {limpio(corte)}",
                margen=mae,
                leyenda_rango=f"Rango esperado: {num(pred.rango[0])} a {num(pred.rango[1])}",
            )
        st.markdown(medidor, unsafe_allow_html=True)

        if datos is not None and not es_clasificacion:
            por_debajo = (datos["popularidad"] < valor).mean() * 100
            st.caption(
                f"Superaría al {num(por_debajo, 0)} % de las {len(datos):,} canciones del catálogo "
                f"({datos['anio'].min()} a {datos['anio'].max()}).".replace(",", ".")
            )

        if datos is not None:
            avisos = fuera_de_rango(entrada, datos)
            if avisos:
                st.markdown(
                    f'<div class="nota alerta">Fuera del rango de entrenamiento: {", ".join(avisos)}. '
                    "La predicción es menos fiable con esos valores.</div>",
                    unsafe_allow_html=True,
                )
            if entrada["anio"] >= ANIO_CORTE:
                st.markdown(
                    f'<div class="nota">El modelo se entrenó con canciones de 1995 a {ANIO_CORTE - 1}. '
                    f"Para {entrada['anio']} extrapola la tendencia por año.</div>",
                    unsafe_allow_html=True,
                )

    # Explicación de la predicción (solo regresión lineal)
    descomposicion = contribuciones(modelo, entrada, datos) if datos is not None else None
    if descomposicion:
        base, aportes = descomposicion
        with col_res:
            st.subheader("Qué empuja la predicción")
            st.caption(
                f"Una canción promedio del entrenamiento obtiene {num(base)}. Cada barra muestra cuántos puntos "
                "suma o resta esta canción respecto a ese promedio. Son asociaciones, no causas."
            )
            orden = sorted(aportes.items(), key=lambda par: abs(par[1]))
            fig_aportes = go.Figure(
                go.Bar(
                    x=[v for _, v in orden],
                    y=[k for k, _ in orden],
                    orientation="h",
                    marker_color=[TURQUESA if v >= 0 else LADRILLO for _, v in orden],
                    text=[f"{v:+.1f}".replace(".", ",") for _, v in orden],
                    textposition="outside",
                    cliponaxis=False,
                    hovertemplate="%{y}: %{x:+.2f} puntos<extra></extra>",
                )
            )
            fig_aportes.update_xaxes(zeroline=True, zerolinecolor=TINTA, zerolinewidth=1.5)
            st.plotly_chart(estilo(fig_aportes, 38 * len(orden) + 50), width="stretch", key="grafica_aportes")



# --- Catálogo -------------------------------------------------------------------------------
with tab_catalogo:
    if datos is None:
        st.info("No se encontró data/canciones.csv, así que no hay catálogo para comparar.")
    else:
        marca = dict(symbol="star", size=18, color=TINTA, line=dict(color="#FFFFFF", width=2))
        valor_pop = None if es_clasificacion else pred.popularidad_esperada

        st.subheader("Dónde cae frente a las demás canciones")
        fig_hist = go.Figure(go.Histogram(x=datos["popularidad"], nbinsx=30, marker_color=LINEA, name="Canciones"))
        if es_clasificacion:
            fig_hist.add_vline(x=70, line_color=TINTA, line_dash="dash", annotation_text="Desde 70 es hit")
        else:
            fig_hist.add_vline(x=pred.corte_promocion, line_color=TURQUESA, line_dash="dash",
                               annotation_text="Corte de promoción", annotation_position="top left")
            fig_hist.add_vline(x=valor_pop, line_color=TURQUESA if pred.promocionar else LADRILLO, line_width=4,
                               annotation_text="Esta canción", annotation_position="top right")
        fig_hist.update_xaxes(title="Popularidad (0 a 100)")
        fig_hist.update_yaxes(title="Canciones")
        st.plotly_chart(estilo(fig_hist, 330), width="stretch", key="grafica_hist")

        izq, der = st.columns(2, gap="large")
        with izq:
            st.subheader("Popularidad media por año")
            por_anio = datos.groupby("anio")["popularidad"].mean().reset_index()
            fig_anio = go.Figure(go.Scatter(x=por_anio["anio"], y=por_anio["popularidad"], mode="lines+markers",
                                            line=dict(color=TINTA, width=2.5), marker=dict(size=6), name="Media del catálogo"))
            ultimo = max(int(datos["anio"].max()), int(entrada["anio"]))
            fig_anio.add_vrect(x0=ANIO_CORTE - 0.5, x1=int(datos["anio"].max()) + 0.5, fillcolor=AMBAR, opacity=0.15,
                               line_width=0, annotation_text="Periodo de prueba", annotation_position="bottom left")
            if valor_pop is not None:
                fig_anio.add_trace(go.Scatter(x=[entrada["anio"]], y=[valor_pop], mode="markers", marker=marca,
                                              name="Esta canción"))
            fig_anio.update_xaxes(title="Año de lanzamiento", range=[1994, ultimo + 1])
            fig_anio.update_yaxes(title="Popularidad media")
            st.plotly_chart(estilo(fig_anio, 340, leyenda=True), width="stretch", key="grafica_anio")
        with der:
            st.subheader("Bailabilidad y popularidad")
            fig_disp = go.Figure()
            for g in GENEROS:
                sub = datos[datos["genero"] == g]
                fig_disp.add_trace(go.Scatter(x=sub["bailabilidad"], y=sub["popularidad"], mode="markers",
                                              name=ETIQUETA_GENERO.get(g, g.title()),
                                              marker=dict(size=6, opacity=0.55, color=COLOR_GENERO.get(g, LINEA))))
            if valor_pop is not None:
                fig_disp.add_trace(go.Scatter(x=[entrada["bailabilidad"]], y=[valor_pop], mode="markers", marker=marca,
                                              name="Esta canción"))
            fig_disp.update_xaxes(title="Bailabilidad")
            fig_disp.update_yaxes(title="Popularidad")
            st.plotly_chart(estilo(fig_disp, 340, leyenda=True), width="stretch", key="grafica_disp")


# --- Modelo ---------------------------------------------------------------------------------
ETIQUETA_METRICA = {"mae": "MAE", "rmse": "RMSE", "r2": "R²", "sesgo": "Sesgo", "costo": "Costo",
                    "precision": "Precisión", "recall": "Recall"}

with tab_modelo:
    st.subheader("Qué modelo responde")
    st.markdown(f"**{ficha['nombre']}**, entrenado el {ficha.get('fecha', 'sin fecha')}.")
    st.write(f"Predice: {ficha['objetivo']}. Momento de la decisión: {ficha['momento_prediccion']}.")
    st.caption("Esta página decide con el mismo código que la API (`POST /predecir`), así que ambas coinciden.")

    st.subheader("Qué tan bien lo hace")
    desempeno = ficha["desempeno"]
    escalares = {k: v for k, v in desempeno.items() if isinstance(v, (int, float))}
    columnas = st.columns(max(len(escalares), 1))
    for col, (clave, valor_m) in zip(columnas, escalares.items()):
        col.metric(ETIQUETA_METRICA.get(clave, clave.capitalize()), num(float(valor_m), 3 if abs(float(valor_m)) < 1 else 2))
    matriz = desempeno.get("matriz_confusion")
    if isinstance(matriz, dict):
        st.caption("Matriz de confusión en la prueba: cuántas canciones cayeron en cada caso.")
        st.dataframe(
            pd.DataFrame(
                [[matriz["tn"], matriz["fp"]], [matriz["fn"], matriz["tp"]]],
                index=["Real: no hit", "Real: hit"],
                columns=["Predicho: no hit", "Predicho: hit"],
            ),
            width="stretch",
        )
    base_ref = ficha["linea_base"]
    if isinstance(base_ref, dict):
        medidas = ", ".join(
            f"{ETIQUETA_METRICA.get(k, k.capitalize())} {num(float(v), 2)}" for k, v in base_ref.items() if k != "descripcion"
        )
        st.write(f"Línea base: {base_ref.get('descripcion', 'sin descripción')}, {medidas}.")
    else:
        st.write(f"Línea base: {base_ref}.")
    prueba = ficha.get("prueba")
    if isinstance(prueba, dict):
        st.caption(f"Medido con {prueba.get('n', '?')} canciones de {prueba.get('periodo', '?')}, que el modelo no vio al entrenar.")

    st.subheader("Cómo se decide")
    decision = ficha["decision"]
    st.write(decision.get("regla", "").capitalize())
    costos = decision.get("costos")
    if isinstance(costos, dict):
        st.write(
            f"Costos de equivocarse: un hit que no se promociona cuesta {costos.get('falso_negativo')}; "
            f"una promoción que no rinde cuesta {costos.get('falso_positivo')}."
        )
    if decision.get("nota"):
        st.caption(decision["nota"].capitalize())

    excluidas = ficha["variables_excluidas"]
    st.subheader("Variables que no se usan")
    if isinstance(excluidas, dict):
        for nombre, motivo in excluidas.items():
            st.markdown(f"- `{nombre}`: {motivo}.")
    else:
        st.markdown("\n".join(f"- `{nombre}`" for nombre in excluidas))

    por_genero = ficha.get("por_genero")
    if por_genero:
        st.subheader("El error no se reparte igual")
        tabla = pd.DataFrame(por_genero).T
        tabla.index = [ETIQUETA_GENERO.get(g, g.title()) for g in tabla.index]
        tabla = tabla.sort_values(tabla.columns[0], ascending=False)
        tabla.columns = [ETIQUETA_METRICA.get(c, c.capitalize()) for c in tabla.columns]
        st.dataframe(tabla.map(lambda v: num(float(v), 2)), width="stretch")

    descartadas = ficha.get("variantes_descartadas")
    if descartadas:
        with st.expander("Variantes que se probaron y se descartaron"):
            for nombre, motivo in descartadas.items():
                st.markdown(f"- **{nombre}**: {motivo}.")
    if ficha.get("limites"):
        st.caption(f"Límites: {ficha['limites']}.")
