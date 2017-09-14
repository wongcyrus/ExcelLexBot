import json

from .ExcelJsonConverterBase import ExcelJsonConverterBase


class BotJsonConverter(ExcelJsonConverterBase):
    def __init__(self, workbook, lexjson_dir):
        super(BotJsonConverter, self).__init__(workbook, lexjson_dir)

    def _generate_bot_json(self, sheet_name: str):
        data = {
            "description": "B1",
            "abortStatement": "B2",
            "clarificationPrompt": "B3"
        }
        data = self._get_single_value_cell_data(sheet_name, data)
        data["intents"] = [json.dumps(elem) for elem in self.worksheets if
                           elem.endswith("Intend")]
        self._save_json_template('bot.json', sheet_name, data)

    def generate_json(self):
        list(map(self._generate_bot_json, self.bots))
