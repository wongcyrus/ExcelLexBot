import json
import os
import string
from abc import abstractmethod

from jinja2 import Environment, FileSystemLoader
from openpyxl import load_workbook


class ExcelJsonConverterBase(object):
    def __init__(self, workbook, lexjson_dir):
        dir_path = os.path.dirname(os.path.abspath(__file__))
        self.data = []
        self.templateDir = os.path.join(dir_path, "template")
        self.outputDir = lexjson_dir
        if workbook is not None:
            self.wb = load_workbook(workbook)
            self.worksheets = self.wb.get_sheet_names()
        else:
            self.wb = None
            files = os.listdir(os.path.join(dir_path, lexjson_dir))
            self.worksheets = [os.path.splitext(os.path.basename(fn))[0] for fn in files]
        self.intends = [elem for elem in self.worksheets if elem.endswith("Intend")]
        self.slot_types = [elem for elem in self.worksheets if elem.endswith("Types")]
        self.bots = [elem for elem in self.worksheets if elem.endswith("Bot")]
        print(vars(self))

    def _render(self, filename: str, data: dict) -> str:
        j2_env = Environment(loader=FileSystemLoader(self.templateDir), trim_blocks=True)
        template = j2_env.get_template(filename).render(**data)
        template = str.encode(template, 'utf-8')
        template = template.decode('unicode_escape').encode('ascii', 'ignore')
        return json.dumps(json.loads(template), indent=4)

    def _save_json_template(self, template_filename: str, save_filename: str, data: dict):
        with open(os.path.join(self.outputDir, save_filename + '.json'), "w+", encoding='utf8') as text_file:
            print(self._render(template_filename, data), file=text_file)

    @staticmethod
    def _get_cell_value(worksheet, address):
        val = str(worksheet[address].value)
        if not val.isdigit():
            return json.dumps(val)
        return val

    def _get_variable_length_column_data(self, column: int, start_row: int, worksheet):
        data = []
        i = start_row
        column = string.ascii_uppercase[column - 1]
        while worksheet[column + str(i)].value is not None and worksheet[column + str(i)].value:
            data.append(self._get_cell_value(worksheet, column + str(i)))
            i = i + 1
        return data

    def _get_variable_length_row_data(self, column: int, row: int, worksheet):
        data = []
        i = column
        column = string.ascii_uppercase[i - 1]
        while worksheet[column + str(row)].value is not None and worksheet[column + str(row)].value:
            data.append(self._get_cell_value(worksheet, column + str(row)))
            i = i + 1
            column = string.ascii_uppercase[i - 1]
        return data

    def _get_single_value_cell_data(self, sheet_name: str, data: dict):
        worksheet = self.wb[sheet_name]
        data = dict(map(lambda item: (item[0], self._get_cell_value(worksheet, item[1])), data.items()))
        data["name"] = json.dumps(sheet_name)
        return data

    @abstractmethod
    def generate_json(self):
        pass
