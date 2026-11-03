# -*- coding: utf-8 -*-
from odoo import models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def to_json(self):
        values = super().to_json()
        return self._alku_fix_cfdi_values(values)

    def _alku_fix_cfdi_values(self, values):
        """Post-process the dict built by nomina_cfdi_ee ``to_json`` (hr_payroll.py ~1431).

        (a) IT Admin 19 sends ``nomina12['TotalOtrosPagos']`` only when the total is > 0.
            If OtrosPagos exists and the total is None, write the sum of Importe ('0.00').
        (b) ``FechaInicioRelLaboral`` and ``Antiguedad`` use ``contract_id.date_start``, which in v19
            is max(date_version, contract_date_start): a new version would restart the seniority.
            Use ``contract_date_start`` instead, with the same week formula as IT Admin.
        """
        self.ensure_one()
        nomina = values.get('nomina12')
        if not isinstance(nomina, dict):
            return values
        otros_pagos = values.get('OtrosPagos')
        if otros_pagos and nomina.get('TotalOtrosPagos') is None:
            total = sum(float(line.get('Importe') or 0.0) for line in (otros_pagos.get('conceptos') or []))
            nomina['TotalOtrosPagos'] = self.set_decimals(round(total, 2), 2)
        receptor = nomina.get('Receptor')
        start = self.contract_id.contract_date_start
        if isinstance(receptor, dict) and receptor.get('FechaInicioRelLaboral') and start and self.date_to:
            receptor['FechaInicioRelLaboral'] = start.strftime(DEFAULT_SERVER_DATE_FORMAT)
            receptor['Antiguedad'] = 'P%dW' % int(((self.date_to - start).days + 1) / 7)
        return values
