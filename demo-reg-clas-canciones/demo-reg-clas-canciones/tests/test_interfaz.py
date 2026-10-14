"""Pruebas de la interfaz web. Se omiten si Streamlit no está instalado (pip install -r requirements-ui.txt).

    pytest -q
"""

import warnings
from pathlib import Path

import pytest

warnings.filterwarnings("ignore", category=DeprecationWarning)
pytest.importorskip("streamlit")
pytest.importorskip("plotly")
from streamlit.testing.v1 import AppTest  # noqa: E402

from src.app.esquemas import Cancion  # noqa: E402
from src.app.main import predecir_filas  # noqa: E402
from src.artefacto import cargar  # noqa: E402
from src.interfaz import contribuciones, fuera_de_rango, medidor_html  # noqa: E402
from src.variables import FILA_EJEMPLO, GENEROS, cargar_canciones  # noqa: E402

APP = str(Path(__file__).resolve().parent.parent / "app_streamlit.py")


def abrir() -> AppTest:
    return AppTest.from_file(APP, default_timeout=60).run()


def de_la_pagina(at: AppTest) -> dict:
    return at.session_state["ultima_prediccion"]


def de_la_api(**cambios) -> dict:
    return predecir_filas(cargar(), [Cancion(**{**FILA_EJEMPLO, **cambios})])[0].model_dump()


def test_arranca_sin_errores():
    at = abrir()
    assert not at.exception
    assert not at.error


def test_coincide_con_la_api():
    assert de_la_pagina(abrir()) == de_la_api()


def test_la_duracion_cambia_la_prediccion_como_en_la_api():
    """El servicio no puede dejar la duración al cuadrado en 0: una canción de 6 min no es igual a una de 3,5."""
    at = abrir()
    base = de_la_pagina(at)
    at.slider(key="duracion").set_value(6.0).run()
    larga = de_la_pagina(at)
    assert larga != base
    assert larga == de_la_api(duracion_min=6.0)


def test_cada_genero_del_selector_existe_y_da_una_prediccion_distinta():
    at = abrir()
    assert len(at.selectbox(key="genero").options) == len(GENEROS)
    resultados = set()
    for g in GENEROS:
        at.selectbox(key="genero").select(g).run()
        resultados.add(de_la_pagina(at)["popularidad_esperada"])
    assert len(resultados) == len(GENEROS)


def test_colaboracion_y_tempo_se_pueden_editar():
    at = abrir()
    sin = de_la_pagina(at)
    at.toggle(key="colaboracion").set_value(False).run()
    assert de_la_pagina(at)["popularidad_esperada"] < sin["popularidad_esperada"]
    at.slider(key="tempo").set_value(170).run()
    assert de_la_pagina(at) == de_la_api(colaboracion=0, tempo=170.0)


def test_el_texto_del_usuario_se_escapa():
    at = abrir()
    at.text_input(key="titulo").set_value("<img src=x onerror=alert(1)>").run()
    assert not at.exception
    html_pagina = " ".join(m.value for m in at.markdown)
    assert "<img src=x" not in html_pagina
    assert "&lt;img" in html_pagina


def test_los_aportes_suman_la_prediccion():
    modelo, datos = cargar(), cargar_canciones()
    for fila in (FILA_EJEMPLO, {**FILA_EJEMPLO, "duracion_min": 6.0, "genero": "indie", "colaboracion": 0}):
        base, aportes = contribuciones(modelo, fila, datos)
        esperado = predecir_filas(modelo, [Cancion(**fila)])[0].popularidad_esperada
        assert base + sum(aportes.values()) == pytest.approx(esperado, abs=0.06)


def test_aviso_de_valores_fuera_del_rango_de_entrenamiento():
    datos = cargar_canciones()
    assert fuera_de_rango(FILA_EJEMPLO, datos) == []
    assert fuera_de_rango({**FILA_EJEMPLO, "tempo": 240.0, "duracion_min": 9.0}, datos) == ["tempo", "duración"]


def test_medidor_no_incluye_texto_del_usuario_y_marca_la_decision():
    html = medidor_html(84.8, 65, True, "84,8", "de 100", "Popularidad esperada", "detalle", "zona", margen=5.75,
                        leyenda_rango="rango")
    assert "Promocionar" in html and "No promocionar" not in html
    assert "rotate(62.6deg)" in html  # -90 + 1,8 x 84,8 = 62,64
    assert "No promocionar" in medidor_html(5, 65, False, "5,0", "de 100", "r", "d", "z")
