# Restaurant Analytics — Laboratorio Semana 2

**Asignatura:** Data Analytics (Código: 43390860)
**Profesor:** Ing. Elias Buitrago Bolívar, MSc.
**Tema:** Perfil del analista, modelo relacional y trabajo reproducible
**Autores:** Juan Felipe Garavito Feo , Juan Fernando Fonseca Martinez y Cristian Andres Villamil Castellanos

---

## 1. Objetivo

Actuar como *Business Data Analyst* de una cadena de restaurantes que mantiene sus datos de productos, clientes y ventas en archivos independientes. El objetivo es **consolidar** estas fuentes, **validar** las relaciones entre ellas y construir **indicadores de ingresos, frecuencia de compra y recurrencia de clientes** que permitan a la gerencia comparar el desempeño entre dos semanas de operación y tomar decisiones informadas sobre el menú y la fidelización.

> **Alcance y limitación declarada:** los datos disponibles contienen precios de venta, pero **no** incluyen costos, cantidades ni descuentos. Por lo tanto, este análisis reporta **ingresos, frecuencia y recurrencia**, y en ningún punto afirma rentabilidad, utilidad o margen, ya que esas métricas no pueden calcularse con la información disponible.

---

## 2. Estructura del repositorio

```text
lab-restaurant-analytics/
│
├── data/
│   ├── Restaurant-Foods.csv          # Catálogo de productos y precios
│   ├── Restaurant-Week1-Sales.csv    # Ventas semana 1
│   └── Restaurant-Week2-Sales.csv    # Ventas semana 2
│                                       (Restaurant-Customers.csv excluido, ver sección 6)
├── lab_Sem2_DA_20261.ipynb           # Notebook ejecutado con evidencia del proceso
├── One-Page Executive Report.docx    # Informe ejecutivo para el dueño del restaurante
├── .gitignore
└── README.md
```

---

## 3. Datos y modelo relacional

| Archivo | Contenido | Clave |
|---|---|---|
| `Restaurant-Foods.csv` | Catálogo de productos y precio unitario | `Food ID` (única) |
| `Restaurant-Customers.csv` | Identificador, nombre, género, empresa y ocupación del cliente | `ID` (única) |
| `Restaurant-Week1-Sales.csv` | Registros de venta, semana 1 | `Customer ID`, `Food ID` (foráneas) |
| `Restaurant-Week2-Sales.csv` | Registros de venta, semana 2 | `Customer ID`, `Food ID` (foráneas) |

**Relación entre tablas:**

```text
CUSTOMERS (1) ────< SALES >──── (1) FOODS
    ID                                Food ID
```

- Un cliente puede aparecer en muchos registros de venta (`1 : N`).
- Un producto puede aparecer en muchos registros de venta (`1 : N`).
- Cada registro de venta referencia exactamente un cliente y un producto (`N : 1` en ambos sentidos).

Antes de unir las tablas, el notebook valida que `Food ID` e `ID` sean claves únicas en sus tablas de origen, y que todo `Food ID` y `Customer ID` presente en las ventas exista en su tabla de referencia (`.isin()`). Solo tras superar estas validaciones se realiza el `merge`, usando `validate='many_to_one'` para garantizar que cada unión sea consistente con el modelo relacional descrito.

---

## 4. Metodología

1. **Carga y unificación**: se cargan los 4 archivos y se concatenan las ventas de ambas semanas en una sola tabla (`all_sales`), agregando una columna `Semana` para poder comparar.
2. **Validación de integridad**: verificación de unicidad de claves primarias y de existencia de todas las claves foráneas antes de cualquier unión (evita registros huérfanos o duplicados silenciosos).
3. **Consolidación**: `merge` de `all_sales` con `foods` y `customers`, controlado con `validate='many_to_one'`, produciendo `full_report` (una fila por registro de venta, enriquecida con producto, precio y ocupación del cliente).
4. **Construcción de indicadores (KPIs)** con Pandas: ingresos totales, ingresos y registros por semana, ingreso promedio por registro, frecuencia de compra e ingresos por producto, recurrencia de clientes entre semanas, e ingresos agregados por ocupación.
5. **Verificación cruzada con SQL**: se replica el resumen semanal mediante una consulta SQL sobre una base SQLite temporal, comprobando que Pandas y SQL devuelven el mismo resultado.
6. **Visualización**: se generan gráficos de desempeño del menú, comparación semanal y recurrencia de clientes, insumo directo del informe ejecutivo.

---

## 5. Principales hallazgos

| Indicador | Resultado |
|---|---|
| Ingresos totales (2 semanas) | **$3,886.56** |
| Ingresos semana 1 / semana 2 | $1,962.68 / $1,923.88 (**-2.0%**) |
| Registros de venta por semana | 250 / 250 (sin cambio) |
| Ingreso promedio por registro | $7.85 → $7.70 |
| Producto con mayor frecuencia | **Drink** (59 registros, $103.25 en ingresos) |
| Producto con mayores ingresos | **Steak** ($1,249.50, 50 registros) |
| Clientes únicos semana 1 | 221 |
| Clientes recurrentes (compraron en ambas semanas) | 46 |
| **Tasa de recurrencia** | **20.8%** |
| Ocupaciones con mayor gasto agregado | Compensation Analyst, Sales Representative, Marketing Manager, Cost Accountant, Assistant Media Planner |

**Interpretación clave:** el producto más vendido (por frecuencia) no es el que más ingresos genera. Esto confirma que frecuencia e ingresos son indicadores complementarios y no intercambiables: uno mide tráfico/popularidad, el otro mide aporte económico directo, condicionado por el precio unitario del producto.

Con solo dos semanas de datos, las variaciones observadas (ingresos, recurrencia) se describen como asociaciones, **no se les atribuye causalidad**.

---

## 6. Privacidad de los datos

Este repositorio es **público** para permitir su revisión académica, por lo que se excluyó deliberadamente el archivo `Restaurant-Customers.csv` mediante `.gitignore`, ya que contiene nombres reales de clientes. El análisis de perfil de consumo (sección de ocupación) se realizó únicamente sobre variables **agregadas** (suma de ingresos por categoría ocupacional), sin exponer ni referenciar clientes individuales en ningún resultado, tabla o gráfico del notebook ni del informe ejecutivo.

Para reproducir el análisis completo de forma local, el archivo de clientes debe solicitarse directamente al equipo o utilizar una copia propia con la misma estructura de columnas (`ID`, `First Name`, `Last Name`, `Gender`, `Company`, `Occupation`).

---

## 7. Instrucciones de ejecución

### Opción A — Google Colab (recomendada)
1. Abrir [colab.research.google.com](https://colab.research.google.com) y subir `lab_Sem2_DA_20261.ipynb`.
2. En la primera celda, ejecutar:
```python
   from google.colab import files
   uploaded = files.upload()
```
   y seleccionar los 4 archivos CSV.
3. Ejecutar todas las celdas (**Entorno de ejecución → Ejecutar todas**).

### Opción B — Local (Jupyter / VS Code)
1. Clonar el repositorio:
```bash
   git clone https://github.com/TU-USUARIO/lab-restaurant-analytics.git
```
2. Copiar los CSV de `data/` a la raíz del proyecto (junto al notebook), o ajustar las rutas de lectura en el código.
3. Instalar dependencias:
```bash
   pip install pandas matplotlib jupyter ipykernel
```
4. Abrir `lab_Sem2_DA_20261.ipynb` y ejecutar todas las celdas en orden, de la primera a la última, sin modificaciones manuales.

> **Criterio de reproducibilidad:** el notebook debe poder ejecutarse de principio a fin sin errores ni intervención manual del código (salvo la carga inicial de archivos en Colab).

---

## 8. Entregables

- `lab_Sem2_DA_20261.ipynb` — notebook ejecutado, con validaciones de datos, indicadores en Pandas y SQL, y visualizaciones como evidencia del proceso.
- `One-Page Executive Report.docx` — informe ejecutivo de una página dirigido al dueño del restaurante, con hallazgos, gráficos y recomendaciones, sin código ni tecnicismos.
- `README.md` — este documento.
