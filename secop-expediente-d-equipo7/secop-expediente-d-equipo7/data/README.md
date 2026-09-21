# Datos

| Archivo | Contenido | Origen |
|---|---|---|
| `secop_recorte.csv` | 50.000 contratos de SECOP II, Distrito Capital de Bogotá, firmados entre 2024-01-01 y 2025-12-31 | Dataset `jbjy-vk9h` (datos.gov.co), preparado por el profesor |
| `secop_adiciones.csv` | 50.000 registros de la tabla de adiciones de SECOP II, sin filtro territorial | Dataset `cb9c-h8sn` (datos.gov.co), preparado por el profesor |
| `metadata_extraccion.json` | Consulta y fecha de extracción de los contratos | Generado en la descarga |
| `metadata_adiciones.json` | Fecha de extracción y tope de la tabla de adiciones | Generado en la descarga |

## Advertencias
- El recorte de contratos está **truncado**: 50.000 de 567.075 contratos disponibles; el criterio de selección no está documentado.
- La tabla de adiciones **no trae montos**, no está filtrada por territorio y solo llega hasta 2024-09-09. Solo 114 contratos del recorte tienen algún registro en ella (ver el notebook, sección «Relacionar contratos y adiciones»).
- `secop_recorte.csv` pesa unos 85 MB: GitHub lo acepta (límite de 100 MB por archivo) pero muestra una advertencia por superar los 50 MB. Si prefieren no versionarlo, agréguenlo a `.gitignore` y documenten cómo obtenerlo.
