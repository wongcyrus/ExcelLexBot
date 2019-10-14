import sys
sys.path.append("/opt/")
import json

from .ExcelConverterBase import ExcelConverterBase


class BotJsonConverter(ExcelConverterBase):
    def __init__(self, workbook_path_name, lexjson_dir):
        super(BotJsonConverter, self).__init__(workbook_path_name, lexjson_dir)

    def _generate_bot_json(self, sheet_name: str):
        data = {
            "description": "B1",
            "abortStatement": "B2",
            "clarificationPrompt": "B3"
        }
        data = self.populate_simple_cell_data(sheet_name, data)
        data["intents"] = [json.dumps(elem) for elem in self.intents]

        data["clarificationPrompt"] = self.none_string_to_none(
            data["clarificationPrompt"])
        self._save_json_template('bot.json', sheet_name, data)

    def generate_json(self):
        list(map(self._generate_bot_json, self.bots))
