# Business Data Analytics — Applied Lab 2
## Risk Management & OSH Analytics (CRISP-DM) — Semana 4

**Asignatura:** Data Analytics (43390860)
**Profesor:** Ing. Elias Buitrago Bolivar, MSc.
**Integrantes:** Juan Garavito, Juan Fonseca, Cristian Villamil

---

## 1. Contexto de negocio

Un conglomerado de 150 empresas está alarmado por el aumento en los reportes de accidentes laborales. Este laboratorio aplica la metodología **CRISP-DM** para consolidar tres fuentes de datos dispersas, identificar patrones de riesgo laboral (jornada, capacitación, sector, sistema de gestión SST) y proponer una regla de negocio preventiva accionable.

## 2. Estructura del repositorio

```
.
├── lab_Sem4_DA_20262_resuelto.ipynb   # Notebook resuelto y ejecutado (Colab/Jupyter)
├── data/
│   ├── trabajadores.csv               # Perfil, cargo, jornada y antigüedad del personal
│   ├── empresas.csv                   # Sector económico y sistema de gestión SST
│   └── accidentes.csv                 # Registro histórico de incidentes
├── imagenes/
│   ├── chart_base.png                 # Gráficos base: jornada, capacitación, top 5 sectores
│   ├── chart_extra.png                # Exploración autónoma: antigüedad, sistema gestión, nivel educativo
│   └── chart_heatmap.png              # Cruce jornada x capacitación
├── reporte/
│   └── Executive_Report_Riesgos_Laborales.pdf   # One-page executive report (entregable final)
├── requirements.txt
└── README.md
```

## 3. Metodología aplicada (mapeo CRISP-DM)

| Fase CRISP-DM | Actividad realizada |
|---|---|
| **Business Understanding** | Definición del problema: reducir accidentalidad laboral mediante identificación de factores de riesgo. |
| **Data Understanding** | Carga y exploración de `trabajadores.csv` (3.000 registros), `empresas.csv` (150 registros) y `accidentes.csv` (1.067 eventos). |
| **Data Preparation** | *Triple join*: `trabajadores` ↔ `empresas` (por `id_empresa`) y luego ↔ `accidentes` mediante `left join` (por `id_trabajador`), preservando a quienes no tuvieron accidentes. Se derivó la variable binaria `incidente`. |
| **Modeling (descriptivo)** | Visualizaciones comparativas de tasa de accidentalidad por jornada, capacitación, sector, antigüedad, sistema de gestión y nivel educativo. |
| **Evaluation** | Interpretación de negocio de cada gráfico, incluyendo el hallazgo de causalidad inversa en la variable capacitación. |
| **Deployment** | Regla de negocio ERP propuesta para generar alertas automáticas de intervención SST. |

## 4. Principales hallazgos

- **Tasa global de accidentalidad:** 35.57% (1.067 / 3.000 trabajadores).
- **Jornada más peligrosa:** nocturna (44.96%), vs. diurna (32.26%) y mixta (34.49%).
- **Capacitación:** el grupo "capacitado" muestra una tasa mayor (41.67% vs. 31.03%). Se interpreta como **causalidad inversa** — se capacita más a los perfiles ya expuestos a mayor riesgo — no como que la capacitación sea contraproducente.
- **Sectores más críticos:** minería (49.59%) y construcción (48.62%).
- **Sistema de gestión SST (hallazgo autónomo):** el factor de mayor poder explicativo. Empresas sin sistema: 57.62% vs. con sistema: 31.10% (brecha de 26.5 puntos porcentuales).
- **Antigüedad:** mayor riesgo en los primeros 3 años (38.4%), decreciente con la experiencia.
- **Nivel educativo:** sin diferencias relevantes (31%–37%).

## 5. Recomendación ERP (regla de negocio)

> **SI** `jornada = 'nocturna'` **Y** `sector_economico ∈ {minería, construcción}` **Y** `sistema_gestion = 0`
> **ENTONCES** generar automáticamente una **alerta de intervención prioritaria SST**: activación obligatoria del sistema de gestión, refuerzo de capacitación certificada por turno nocturno y auditoría de campo en máximo 30 días.

## 6. Cómo ejecutar

```bash
pip install -r requirements.txt
jupyter notebook lab_Sem4_DA_20262_resuelto.ipynb
```

O ábrelo directamente en Google Colab, subiendo la carpeta `data/` a la misma sesión (o montando el repo desde GitHub).

## 7. Entregable

El informe ejecutivo de una página (`reporte/Executive_Report_Riesgos_Laborales.pdf`) resume el diagnóstico, los hallazgos y la recomendación ERP, listo para presentación a dirección.
