# Traspaso: nómina México en Odoo (lo aprendido en la demo Mobi v20)

**Para usar en la siguiente conversación** (repo Odoo 19 + módulo de nómina de IT Admin). Adjunta este archivo con `@docs/traspaso-nomina-mx.md` al empezar.

- **Autor:** Pedro Ibarra (Alku) con Claude
- **Periodo:** 2 de noviembre de 2026
- **Detalle completo:** `docs/nomina-demo-reporte.md` (reporte de pruebas, hallazgos y guion de demo)

---

## 1. Contexto de la demo

| Dato | Valor |
|---|---|
| Instancia | `https://lparra-alku-demo-mobi.odoo.com` (odoo.sh, **Odoo 20.0+e**) |
| Base | `lparra-alku-demo-mobi-main-39934591` · empresa "Mobi Muebles (demo)" |
| Acceso API | JSON-2 (`/json/2/<modelo>/<método>`, header `Authorization: bearer`) con la llave de `~/Downloads/_credenciales.json`. Nunca se imprime la llave |
| Repo | `lparra-alku/Demo-Mobi`, rama `prueba-nomina-reportes` (commits `f7aad70`, `9dae66c`). La cuenta NorthWestDev **no** tiene acceso; Pedro sube desde GitHub Desktop |
| ⚠️ Vigencia | La base es de **prueba en odoo.sh y se borra el 14 de noviembre de 2026**, sin respaldo |

**Enfoque acordado:** todo lo más nativo posible (config → Studio/vistas → acciones de servidor → módulo). Cero módulos instalados por nosotros.

---

## 2. Qué se hizo (en orden)

1. Contabilidad instalada; analítica por **región y ciudad** con asientos de ejemplo.
2. Nómina, Empleados, Ausencias, Asistencias y Reclutamiento instalados. 12 empleados con datos fiscales ficticios (RFC, CURP, NSS, CP, CLABE con dígito verificador válido).
3. Plan de nómina por fases y pruebas de **todos los flujos nativos**: octubre y noviembre mensual, incidencias, prestaciones, Infonavit/Fonacot, deducciones recurrentes, aumento masivo, corrección de recibo, aguinaldo, reclutamiento → contrato, pólizas con analítica, CSV de banco y **timbrado CFDI 1.2** en el PAC de pruebas.
4. Estructuras y reglas nuevas, solo con configuración:
   - Horas extra P019, dobles/triples por semana.
   - Finiquito y Liquidación.
   - PTU (con parámetro "PTU a repartir").
   - Asimilados a salarios (tipo de estructura propio, régimen 09).
5. Traducción al español de reglas, tipos de entrada, conceptos SAT, categorías y estructuras.
6. Cambio a **quincenal** desde el 1 de diciembre y ejercicio **Q23/2026** con 4 lotes en paralelo: ordinaria, asimilados, aguinaldo y finiquito. Validados, pagados y timbrados desde el kanban de lotes.
7. **Reportes estilo IT Admin sin módulo:**
   - "Listado de nómina (Excel)" y "Recibos de nómina (PDF)" como acciones de servidor + botones en el menú ⋮ del lote.
   - "Lista de raya" (tabla dinámica en Nómina → Reportes).
8. **Clave SAT en el nombre de las reglas** (`P001 · Sueldo base`, `D002 · ISR`…) y columna "Concepto SAT" en las listas. **Los códigos internos no se tocaron.**

---

## 3. Hallazgos que aplican a cualquier implementación de nómina MX

### Localización nativa (v20) — bugs y huecos
| # | Hallazgo | Cómo se resolvió |
|---|---|---|
| 1 | Tras actualizar odoo.sh, la nómina deja de calcular ("No rule parameter l10n_mx_min_wage_days_per_month") | Actualizar el módulo `l10n_mx_hr_payroll` |
| 2 | El tipo "Public holiday" no tiene categoría BASIC: el feriado no se paga | Agregar BASIC al tipo de entrada |
| 3 | La lista nativa de feriados trae 12 de diciembre y Jueves/Viernes Santo (no obligatorios en la LFT) | Revisar con cada cliente |
| 4 | Sin regla de horas extra (P019) | Regla nueva por configuración |
| 5 | La **prima vacacional** viene en 0% en todos los contratos | Capturar 0.25 (fracción) |
| 6 | El **ISR de aguinaldo y de prima vacacional** retiene de menos en quincenal (toma el sueldo por periodo como mensual) | Fórmula: salario diario × 30.4 (reglas `noupdate`) |
| 7 | El **CFDI del aguinaldo solo declara la parte gravada**. Si todo es exento, el SAT lo rechaza (CFDI40166) | Regla informativa "Aguinaldo (exento)" con concepto P02_2 |
| 8 | Faltan los conceptos exentos P19_2, P02_2, P03_2, P22_2 y P25_2 | Se crearon (mismo `sat_code`, `is_taxable` falso) |
| 9 | La plantilla CFDI no tiene los nodos **HorasExtra** (NOM84) ni **SeparacionIndemnizacion** (NOM37), y manda **RegistroPatronal** en asimilados (NOM43) | **Pendiente: requiere módulo** |
| 10 | 15 conceptos SAT con nombre de más de 100 caracteres (el SAT los rechaza) | Acortar el nombre (se corrigió O999) |
| 11 | Traducciones engañosas: "Allowance" → "Subsidio"; prima vacacional traducida como "aguinaldo" | Corregidas |
| 12 | Odoo deja cancelar un recibo con UUID sin cancelar el CFDI en el SAT | Regla operativa: primero el SAT |

### Operación
- **Quincenal:** periodicidad "2 semanas / Quincenal" (`bi-weekly`, 15 días). El **sueldo del contrato es por periodo**: en quincenal se captura la mitad.
- Las **versiones nuevas del contrato** (aumento masivo o `create_version`) **no copian Infonavit ni Fonacot**. El aumento masivo tampoco copia el domicilio. Hay que revisarlo en cada cambio.
- La tasa del aumento masivo y el % de Infonavit van como **fracción** vía API (0.05 = 5%).
- **Datos que exige el timbrado desde el alta:** CP y estado del domicilio, número de empleado, tipo de contrato (clave SAT), CLABE válida (una sola cuenta por empleado) y registro patronal en la empresa.
- **Un lote con un recibo cancelado adentro no cierra:** hay que sacarlo del lote.
- Odoo no retimbra un recibo que ya tiene UUID.
- La **PTU** se recalcula con las nóminas pagadas del año. Cada nómina nueva cambia el reparto hasta que se cierra el ejercicio.
- **No renombrar códigos de reglas:** las fórmulas se llaman entre sí por código (341 referencias, 55 códigos) y `BASIC`, `GROSS` y `NET` son fijos para Odoo. La clave SAT va en el **concepto** o en el **nombre**.

### Técnica (acciones de servidor y vistas)
- `safe_eval` **no permite closures** (error `MAKE_CELL`): nada de lambdas ni comprensiones que usen variables locales dentro de un `def`. Usar ciclos.
- Excel sin librerías: **SpreadsheetML 2003** en `ir.attachment.raw` + `act_url`. Excel puede avisar que el formato no coincide; un `.xlsx` real requiere módulo con `xlsxwriter`.
- Botones en el kanban del lote: heredar `hr.payrun.blank.kanban.card` (template "menu"). Un `invisible` con un campo que la tarjeta no carga **esconde el botón**.
- Favoritos con `pivot_*` no siempre respetan el contexto. Es mejor una acción de ventana propia con `pivot_row_groupby` y `pivot_column_groupby`.
- Las líneas de recibo toman el **nombre de la regla al vuelo**: renombrar la regla cambia también los recibos ya pagados.
- Borrar por API lo bloquea el clasificador de seguridad. Usar **cancelar o archivar**.

---

## 4. Lo que se construyó (para reutilizar)

| Pieza | Dónde | Notas |
|---|---|---|
| Listado de nómina (Excel) | `odoo_config/nomina_reportes/listado_nomina.py` → acción de servidor id 1084 | Agrupado por departamento, columnas de conceptos dinámicas (por concepto SAT), exento/gravado, otros pagos, deducciones, neto, patronales, efectivo/especie, subtotales y gran total |
| Recibos de nómina (PDF) | `odoo_config/nomina_reportes/recibos_pdf.py` → acción id 1085 | Usa el reporte CFDI nativo si todo está timbrado |
| Botones en el lote | vista `alku.hr.payslip.run.kanban.listado` (id 2924) | Menú ⋮ de la tarjeta, junto a "Diario de nómina" |
| Lista de raya | acción de ventana 1082 + menú Nómina → Reportes | Empleados × reglas |
| Columna Concepto SAT | vistas `alku.hr.payroll.structure.form.concepto_sat` y `alku.hr.salary.rule.list.concepto_sat` | |
| Estructuras nuevas | Finiquito (4), Liquidación (5), PTU (6), Asimilados (7) | Fórmulas en Python dentro de cada regla; **las debe revisar el developer Sr.** |

**Smoke test del listado:** en los 5 lotes, por empleado, percepciones + otros pagos − deducciones = neto, y el gran total = neto del lote (al centavo).

---

## 5. Referencia: el "Listado de nómina" de IT Admin

Se tomó como modelo el archivo `Listado_de_nomina.xls` exportado del módulo de IT Admin (contiene datos reales de un cliente; **no se copió al repo**). Estructura:

- **Una fila por recibo**, agrupadas por **departamento** con fila de título, "Total Departamento" y al final "Gran Total".
- **33 columnas:**
  - Identificación: Cod, Empleado, Días pagados.
  - Percepciones: sueldo base, séptimo día, prima vacacional (exento/gravado, captura y total), compensaciones, préstamo, interés.
  - Totales de percepciones: exento, gravado y total.
  - Otros pagos: subsidio al empleo, ISR por subsidio no correspondido, total otros pagos.
  - Deducciones: ISR, ajuste ISR, ajuste subsidio causado, IMSS, crédito Infonavit, total deducciones.
  - Netos: sueldo neto en efectivo, sueldo neto, "Excedente administrativos (NO TIMBRA)".
  - Patronales: IMSS patronal, SAR, cesantía y vejez, Infonavit patronal, **impuesto sobre nómina**.
  - Cierre: total efectivo, total especie.

---

## 6. Para la nueva conversación (Odoo 19 + IT Admin)

**Diferencia clave:** el módulo de IT Admin **reemplaza** la nómina nativa de México (sus propias tablas CFDI, reglas, estructuras, "Procesamiento de nómina" y reportes). Casi todos los parches de la sección 3 eran para cubrir huecos de la localización nativa. Con IT Admin hay que **validar** que esos casos los resuelva su módulo, no repetirlos.

**Checklist sugerido para probar IT Admin en v19** (los mismos casos que fallaron o costaron trabajo en v20):
1. **Timbrado** de horas extra (nodo HorasExtra), liquidación (SeparacionIndemnizacion) y asimilados (sin registro patronal).
2. **Aguinaldo** con parte exenta en el XML, incluido un empleado de nuevo ingreso 100% exento.
3. **ISR de aguinaldo y prima vacacional en quincenal** (art. 174 RLISR).
4. **Prima vacacional** en aniversario y en finiquito.
5. **PTU:** reparto 50/50, exclusión de directores, tope y eventuales con menos de 60 días.
6. **Finiquito vs. liquidación:** prima de antigüedad con tope de 2 salarios mínimos y exención de 90 UMA por año.
7. **Cambios de contrato:** que Infonavit, Fonacot y domicilio no se pierdan.
8. **Varias nóminas en el mismo periodo** (ordinaria + extraordinaria) y timbrado en lote.
9. **Reportes:** listado de nómina, recibos PDF, acumulados, ISN y SUA/IDSE si los trae.
10. **Contabilidad:** póliza por lote con analítica.

**Reglas de trabajo que siguen igual:**
- Nunca en `main`.
- Configuración antes que código.
- Consensuar antes de desarrollar.
- Smoke test y reporte breve al final.
- No instalar ni mezclar la nómina nativa de Odoo con la de IT Admin en la misma base sin revisarlo: pueden chocar los modelos de recibo y CFDI.
- **Verificar al inicio:** en v19 confirmar si la API es XML-RPC o JSON-2 y qué versión exacta del módulo de IT Admin se instala.

**Pendientes que se quedan en Mobi v20:**
- Módulo de CFDI (nodos HorasExtra y SeparacionIndemnizacion, sin registro patronal en asimilados).
- Regla de ISN.
- Recibo de Andrés duplicado (id 38).
- Respaldar o convertir la base antes del 14 de noviembre.
- Subir el commit `9dae66c`.
