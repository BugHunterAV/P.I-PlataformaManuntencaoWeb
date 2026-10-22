import warnings
from io import BytesIO
from unittest import TestCase

from openpyxl import load_workbook

from .utils.excel_exporter import ExportadorExcel


class ExportadorExcelTests(TestCase):
    def test_long_title_is_truncated_to_valid_sheet_name(self):
        titulo = 'Dashboard — KPIs por Equipamento'

        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter('always')
            response = ExportadorExcel().exportar('dashboard', titulo, [], [])

        workbook = load_workbook(BytesIO(response.content))

        self.assertEqual(workbook.active.title, titulo[:31])
        self.assertEqual(caught_warnings, [])
