from .ExcelConverterBase import ExcelConverterBase


class SlotJsonConverter(ExcelConverterBase):
    def __init__(self, workbook_path_name, lexjson_dir):
        super(SlotJsonConverter, self).__init__(workbook_path_name, lexjson_dir)

    def _generate_intent_slot_json(self, sheet_name: str):
        worksheet = self._get_worksheet(sheet_name)
        data = {
            "description": "B1",
            "valueSelectionStrategy": "B2",
        }
        data = self.populate_simple_cell_data(sheet_name, data)

        slots = self._get_variable_length_column_data(2, 3, worksheet)
        data["enumerationValues"] = slots

        self._save_json_template('slotType.json', sheet_name, data)

    def generate_json(self):
        list(map(self._generate_intent_slot_json, self.slot_types))
