# -*- coding: utf-8 -*-
{
    'name': 'Alku - Correcciones CFDI nómina IT Admin (v19)',
    'version': '19.0.1.1.0',
    'summary': 'TotalOtrosPagos y antigüedad del CFDI de nómina de IT Admin en Odoo 19',
    'description': """
Correcciones al CFDI de nómina de IT Admin (nomina_cfdi_ee 19.1.6) sin tocar su código:

* TotalOtrosPagos: IT Admin 19 solo lo manda si el total es > 0. La regla O001 siempre
  genera el OtroPago 002 con importe 0, y el SAT rechaza el XML sin el total.
* FechaInicioRelLaboral y Antigüedad: se toman de la fecha de ingreso del contrato
  (contract_date_start), no de la versión vigente, para que un cambio de salario no
  reinicie la antigüedad.
* Botón "Crear Polizas" visible en cuanto el lote tiene recibos (IT Admin lo oculta hasta
  que todos están confirmados; la acción ya confirma los borradores por sí sola).

Misma corrección que alku_li_nomina (S31) de Limpieza Inteligente.
""",
    'author': 'Alku',
    'category': 'Human Resources/Payroll',
    'depends': ['nomina_cfdi_ee', 'om_hr_payroll_account_ee'],
    'data': [
        'views/hr_payslip_run_views.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}
