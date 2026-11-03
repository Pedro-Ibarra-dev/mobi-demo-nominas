# Nómina IT Admin en Odoo 19: reporte de pruebas y guion de demo (Mobi Muebles)

- **Instancia:** `https://pedro-ibarra-dev-mobi-demo-nominas.odoo.com` (odoo.sh, Production, Odoo 19.0+e)
- **Repo / rama:** `Pedro-Ibarra-dev/mobi-demo-nominas`, `main` = `prueba-nomina-itadmin`
- **Fecha:** 2 de noviembre de 2026 · Pedro Ibarra (Alku) con Claude
- ⚠️ El proyecto odoo.sh está en **prueba de 29 días** (código de partner): si no se cambia la activación, se borra solo (~1 de diciembre de 2026).

---

## 1. Qué se instaló

| Capa | Módulos |
|---|---|
| Nómina IT Admin (copiados de `AlkuMX/SAS`) | `om_hr_payroll` 19.1.0, `nomina_cfdi_ee` 19.1.6, `nomina_cfdi_extras_ee` 19.1.2, `om_hr_payroll_account_ee` 19.1.2, `report_xlsx` (OCA), `l10n_mx_sat_sync_itadmin_ee` 19.1.7 |
| Corrección propia | `alku_nomina_itadmin_fix` 19.0.1.0.0 (TotalOtrosPagos y antigüedad del CFDI; igual a la S31 de LimpiezaI) |
| Nativos | Contabilidad + localización MX (CFDI 4.0, reportes), Empleados, Ausencias, Asistencias, Reclutamiento, Habilidades, Evaluaciones, Gastos, Presupuestos, Activos, Ventas, Compras (además quedaron Inventario y Fabricación, sin datos) |
| **No** instalado | `hr_payroll` / `l10n_mx_hr_payroll` (nómina nativa): choca con `om_hr_payroll` |

Idioma: español (México) para el usuario admin; zona horaria America/Mazatlan.

---

## 2. Configuración que IT Admin NO trae y hubo que cargar

1. **Reglas, estructuras, categorías y tablas:** la instalación deja 0 reglas. Se cargó el paquete del proveedor (`Belpa/Reglas salariales`: 166 reglas, 8 estructuras, 9 categorías, tablas 2024) por API con `load`, en el orden de sus instrucciones.
2. **TABLAS 2026 (quincenal):** UMA 117.31, SM 315.04, UMI 100.81, ISR mensual y anual 2026, ISR quincenal = mensual × 15/30.4, subsidio 535.65 con límite 11,492.66, antigüedades LFT 2023 (1-50 años), meses y bimestres 2026, ISN 3%. Cuentas patronales para la póliza IMSS.
3. **Registro patronal** `E1234567101` (Clase III), **configuración "Quincenal"**, serie `NOM`, "CFDI MX" activo, PAC Finkok en modo pruebas, póliza "Por nómina" con una línea por empleado (para que la analítica por región/ciudad salga exacta).
4. **Permisos:** el admin no trae los grupos de nómina; se le asignaron (Nómina MX, Payroll manager).

---

## 3. Errores de IT Admin encontrados y corregidos (todo con respaldo en el scratchpad)

| # | Regla / pieza | Problema | Corrección |
|---|---|---|---|
| 1 | 49 reglas | Usan `contract.<campo>` y en v19 esos campos viven en el empleado (fondo_ahorro, infonavit_*, prestamo_fonacot, periodicidad_pago, antiguedad_anos, bonos...) → truenan | `contract.X` → `employee.X`; `env['hr.contract'].antiguedad_to` → `employee.antiguedad_to` |
| 2 | SUB, ISR, ISR2, ISR3, O005/7/8, D060/62 | El tope de subsidio compara el ingreso **quincenal** contra el límite **mensual** → todos recibían subsidio | Comparar el gravado mensualizado (`grabado_sub`) |
| 3 | ISR2 de asimilados | Aplica la tarifa mensual al pago quincenal (ISR de 620 en vez de 990) | Mensualiza y regresa al periodo |
| 4 | Estructura Asimilado | Paga `contract.wage` (sueldo mensual completo) en categoría no gravable → ISR 0 | Regla nueva **P046** (clave SAT 046) = sueldo diario × días |
| 5 | ISR art. 174 (aguinaldo, PTU, ISR3) | Busca el renglón de la tarifa del sueldo con el ingreso *más* la extraordinaria → ISR inflado al cambiar de renglón | Usar `grabado_mensual2` |
| 6 | Fondo de ahorro P041 | La empresa aporta 30% y descuenta 7.5% | 7.5% (igual a D068) |
| 7 | D010 Pensión alimenticia | Truena si no hay descuentos periódicos o si no hay P001 (PTU/aguinaldo) | Base segura: P001 o TPER − ISR − descuentos calculados |
| 8 | Estructura ordinaria | Le faltan pensión, Fonacot, fondo de ahorro, horas triples, festivo laborado y comisiones | Se agregaron |
| 9 | Finiquito | El asistente busca una estructura "Liquidación - Ordinario" que no existe; con la ordinaria no paga aguinaldo ni prima vacacional | Estructura nueva **FINIQ** (ordinaria + reglas de liquidación) |
| 10 | "Comprobación viáticos" | El código busca el nombre literal "Comprobación Viaticos" | Renombrada |
| 11 | CFDI `TotalOtrosPagos` | Solo se manda si > 0; O001 genera OtroPago en 0 → el SAT rechaza **todos** los recibos | Módulo `alku_nomina_itadmin_fix` |
| 12 | CFDI antigüedad | Una versión nueva del contrato (cambio de salario) reinicia FechaInicioRelLaboral | Mismo módulo: usa `contract_date_start` |
| 13 | Préstamos | Si el préstamo arranca el día 16 genera 2 cuotas en la misma quincena | Capturar inicio = cierre de quincena |
| 14 | PTU | El botón "Calcular reparto" escribe campos inexistentes (truena); el monto se captura por empleado (entrada PTU) | Reparto calculado por fuera (script); pendiente acción de servidor |
| 15 | Pensionado | Estructura vacía de fábrica | No aplica en Mobi |

**Todas las reglas parchadas deben pasar por revisión del developer Sr. antes de usarse con un cliente.**

---

## 4. Prueba por estructura salarial

| Estructura | Caso | Resultado |
|---|---|---|
| Sueldos ordinaria (Q21) | 11 empleados, Ramón ingresa el día 3 | ✅ ISR y subsidio verificados a mano (Ramón 360.35 − 264.30 = 96.05; Luis 584.60), IMSS obrero por ramo (Luis 176.72) |
| Sueldos ordinaria con incidencias (Q22) | Falta, incapacidad RT y EG, vacaciones + prima, 20 h extra (18 dobles + 2 triples), festivo laborado, prima dominical, bono, comisión 9,500, Infonavit % y cuota fija, Fonacot, pensión 20%, vales, fondo de ahorro, préstamo | ✅ todos calculan |
| Asimilados | Sofía, 9,000 por quincena | ✅ ISR 990.65, neto 8,009.35, sin IMSS ni subsidio |
| Aguinaldo | Lote del 1-ene al 31-dic (el periodo del lote define los días) | ✅ 15 días, exento 30 UMA (3,519.30), Ramón proporcional (59 días), ISR art. 174 |
| PTU 2025 | Reparto 250,000 (50% días / 50% salario), excluye director y < 60 días | ✅ exento 15 UMA (1,759.65), ISR art. 174 (Luis 3,586.67) |
| Finiquito (renuncia) | José Manuel, 15-dic | ✅ días, vacaciones 13.68 d, aguinaldo 14.34 d, prima vac., Fonacot pendiente → neto 17,012.64 |
| Liquidación (despido) | Andrés, simulación | ✅ indemnización 90 d + 20 d/año (96,111.93), prima de antigüedad topada a 2 SM, exento 90 UMA/año |
| Entrega / Comprobación de viáticos | Jorge, 8,000 | ✅ OtroPago 003 en la entrega; exento + D003 en la comprobación (neto 0) |
| Pensionado | — | ⚪ sin reglas de fábrica |

---

## 5. Lo que quedó en la base (datos ficticios)

**Empleados (12):** Ricardo Salazar (Director), Laura Beltrán y Diana Félix (Administración), Jorge Castañeda, Mariana Treviño y Andrés Navarro (Ventas), Héctor Valenzuela, Luis Armenta y José Manuel Leyva (Producción, JM dado de baja 15-dic), Karla Osuna (RH), Ramón Quiñónez (Almacén, alta 3-nov desde Reclutamiento), Sofía Ramírez (asimilados). RFC, CURP, NSS y CLABE con dígito verificador válido; organigrama con jefes; analítica por región y ciudad.

**Nómina:** ver tabla de lotes en la sección 7. Incidencias IT Admin: cambio de salario de Luis (+5% desde 1-dic, versión nueva del contrato) y baja de José Manuel. Créditos Infonavit (Héctor 20%, Luis cuota fija), Fonacot, préstamo de Diana (4 quincenas), viáticos 0001.

**Empleados (apps nativas):** habilidades (ebanistería, software, seguridad, inglés), currículum, 4 evaluaciones (1 hecha, 2 en curso, 1 nueva), 4 gastos aprobados con analítica, reclutamiento de Almacenista con 5 candidatos, vacaciones LFT asignadas, solicitud de Jorge por aprobar, festivos 16-nov y 25-dic, una semana de asistencias.

**Contabilidad:** 6 clientes y 7 proveedores, 14 facturas de venta (sep-nov) con analítica región/ciudad, 14 facturas de compra (oct-nov), 17 pagos, 12 pólizas de nómina publicadas + dispersión bancaria de cada una, entero de retenciones de octubre, 5 movimientos bancarios sin conciliar (para conciliar en vivo), 2 presupuestos 2026 por región (nómina y ventas), router CNC como activo (depreciación 10 años).

---

## 6. Pendientes

1. **Timbrado (se deja así, 3-nov):** CSD de pruebas EKU9003173C9 cargado (.cer + .key) y Finkok en ambiente de pruebas. El XML ya pasa sello, estructura, emisor y RFC/nombre del receptor; el SAT de pruebas rechaza el CP del receptor (CFDI40147) con los 13 RFC de personas físicas de la lista pública de Facturama, así que no hay recibos timbrados. Para cerrarlo se necesita la lista de RFC de pruebas vigente de soporte de Finkok.
   - El XML confirma `alku_nomina_itadmin_fix`: `TotalOtrosPagos="0.00"` y `Antigüedad` desde la fecha de ingreso.
   - Para timbrar en pruebas, la compañía debe llamarse "ESCUELA KEMPER URGATE" (IT Admin manda `company.name` en mayúsculas como nombre del emisor).
   - Se asignó clave SAT a 9 reglas que bloqueaban el timbrado: 390 Préstamo, 391 Interés del préstamo, D089, D011, D014 y D040 → 004 Otros; D019 → 011 FONACOT; D092 → 010 Vivienda; P013 Gratificación → 038 Otros ingresos por salarios.
   - Quedaron en la base, para reintentar: el empleado 999 "INGRID XODAR JIMENEZ" (RFC de pruebas) y el lote borrador "Prueba de timbrado SAT". No forman parte del guion.
2. Póliza IMSS patronal (asistente de IT Admin) y reporte de ISN: probar en vivo.
3. Acción de servidor para el reparto de PTU (reemplazar el botón roto).
4. Revisión del developer Sr. de: reglas parchadas, estructura FINIQ y `alku_nomina_itadmin_fix`.
5. Definir la activación del proyecto odoo.sh antes de que venza la prueba.

---

## 7. Lotes en la base

| Lote | Estado | Recibos | Percepciones | Deducciones | Neto | Póliza |
|---|---|---|---|---|---|---|
| Aguinaldo 2026 | Cerrado | 10 | 116,971.42 | 21,072.40 | 95,899.02 | NOM/2026/12/0003 |
| PTU 2025 · pago mayo 2026 | Cerrado | 9 | 250,000.01 | 50,651.05 | 199,348.96 | NOM/2026/05/0001 |
| Q19/2026 · Ordinaria · 1a quincena octubre | Cerrado | 10 | 128,742.93 | 31,605.02 | 97,137.91 | NOM/2026/10/0001 |
| Q19/2026 · Asimilados · 1a quincena octubre | Cerrado | 1 | 9,000.00 | 990.65 | 8,009.35 | NOM/2026/10/0002 |
| Q20/2026 · Ordinaria · 2a quincena octubre | Cerrado | 10 | 128,742.93 | 31,605.02 | 97,137.91 | NOM/2026/10/0003 |
| Q20/2026 · Asimilados · 2a quincena octubre | Cerrado | 1 | 9,000.00 | 990.65 | 8,009.35 | NOM/2026/10/0004 |
| Q21/2026 · Ordinaria · 1a quincena noviembre | Cerrado | 11 | 133,382.93 | 31,812.65 | 101,570.28 | NOM/2026/11/0001 |
| Q21/2026 · Asimilados · 1a quincena noviembre | Cerrado | 1 | 9,000.00 | 990.65 | 8,009.35 | NOM/2026/11/0002 |
| Q22/2026 · Ordinaria · 2a quincena noviembre | Cerrado | 11 | 143,341.31 | 33,609.69 | 109,731.62 | NOM/2026/11/0003 |
| Q22/2026 · Asimilados · 2a quincena noviembre | Cerrado | 1 | 9,000.00 | 990.65 | 8,009.35 | NOM/2026/11/0004 |
| Finiquito · José Manuel Leyva (renuncia 15-dic) | Cerrado | 1 | 19,816.76 | 2,804.12 | 17,012.64 | NOM/2026/12/0002 |
| Simulación liquidación · Andrés Navarro (no aplicar) | Borrador | 2 | 148,432.23 | 11,906.20 | 136,526.03 | — |
| Q23/2026 · Ordinaria · 1a quincena diciembre | Borrador | 10 | 128,380.38 | 31,217.87 | 97,162.51 | — |
| Q23/2026 · Asimilados · 1a quincena diciembre | Borrador | 1 | 9,000.00 | 990.65 | 8,009.35 | — |

Cada lote cerrado tiene su póliza publicada (NOM) y su dispersión bancaria. Los recibos de viáticos de Jorge (entrega y comprobación) están confirmados fuera de lote.

---

## 8. Guion de la demo (~40 min) — "Un mes en Mobi Muebles con IT Admin"

1. **Reclutamiento → empleado.** Puesto *Almacenista*: embudo con 5 candidatos; Ramón en *Contrato firmado* → su ficha. *"Del candidato al empleado sin recapturar."*
2. **Expediente (Empleados).** Luis Armenta: datos fiscales (RFC, CURP, NSS, CP SAT, CLABE), régimen y contrato SAT, registro patronal, Infonavit cuota fija, Fonacot, pensión 20%, habilidades y currículum. Historial de versiones (aumento 5% del 1-dic). Organigrama.
3. **Incidencias IT Admin (Nómina → Incidencias).** Cambio de salario de Luis (SDI recalculado) y baja de José Manuel: *"esto es lo que alimenta el IDSE"*.
4. **Ausencias.** Calendario de noviembre: falta de Andrés, incapacidades de Héctor (RT) y José Manuel (EG), vacaciones de Karla; festivo 16-nov. **En vivo:** aprobar las vacaciones de Jorge (21-24 dic).
5. **Horas extra y prima dominical.** Nómina → Horas extras: 20 h de Luis en modo *Automático* → 18 dobles + 2 triples. Prima dominical de Mariana. Asistencias de la semana 30-nov.
6. **Procesamiento Q22 (2a quincena noviembre).** Abrir 3 recibos: Luis (horas, Infonavit, Fonacot, pensión), Héctor (incapacidad RT, Infonavit 20% SBC, fondo de ahorro, vales), Karla (vacaciones + prima). Pestaña de totales: exento/gravado, ISR, subsidio, IMSS obrero.
7. **En vivo: Q23 (1a quincena diciembre, borrador).** Recalcular, ver el sueldo nuevo de Luis y el préstamo de Diana (3/4), **Confirmar** → **Crear póliza**.
8. **Contabilidad de la nómina.** Póliza NOM con cuentas 601/216/205/210 por empleado y analítica región/ciudad. **Contabilidad → Reportes → Analítico**: costo de nómina por región junto a las ventas por región. **Presupuestos**: nómina y ventas 2026 por región (presupuesto vs real).
9. **Asimilados.** Sofía: régimen 09, contrato 09, sin IMSS ni subsidio, ISR quincenal.
10. **Extraordinarias.** Aguinaldo 2026 (15 días, exento 30 UMA, Ramón proporcional), PTU 2025 (reparto 50/50, exento 15 UMA, director excluido), finiquito de José Manuel y la simulación de liquidación de Andrés (indemnización 90 + 20 días/año, prima de antigüedad topada).
11. **Viáticos.** Nómina → Viáticos → 0001 de Jorge: entrega y comprobación con sus recibos (OtroPago 003 / exento + D003).
12. **Reportes IT Admin.** Listado de nómina (Excel), acumulados, recibo PDF, póliza IMSS patronal.
13. **Contabilidad general (músculo).** Facturas de venta con CFDI y analítica, cuentas por cobrar (4 pendientes), **conciliación bancaria en vivo** (3 SPEI de clientes, comisión, CFE), gastos de empleados → registrar y reembolsar, activo CNC con su tabla de depreciación, reportes de estado de resultados por analítica.

### Qué no prometer todavía
- **Timbrado:** se muestra hasta "listo para timbrar"; el timbrado real se valida con el CSD y empleados del primer cliente (pendiente 1).
- **PTU automática:** hoy el reparto se captura; la automatización es desarrollo/acción de servidor.
- **SUA/IDSE y dispersión con layout bancario:** IT Admin trae las incidencias; los archivos dependen del banco/configuración.
