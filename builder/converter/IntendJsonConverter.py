import json
from json import JSONDecoder

from .ExcelJsonConverterBase import ExcelJsonConverterBase


class IntendJsonConverter(ExcelJsonConverterBase):
    def __init__(self, workbook, lexjson_dir, lambda_arn_prefix):
        super(IntendJsonConverter, self).__init__(workbook, lexjson_dir)
        self.lambda_arn_prefix = lambda_arn_prefix

    def _generate_intent_json(self, sheet_name: str):
        worksheet = self.wb[sheet_name]
        data = {
            "description": "B1",
            "maxAttempts": "B2",
            "confirmationPrompt": "B3",
            "rejectionStatement": "B4",
            "fulfillmentActivity": "B5",
            "dialogCodeHook": "B6"
        }
        data = self._get_single_value_cell_data(sheet_name, data)

        sample_utterances = self._get_variable_length_row_data(2, 7, worksheet)
        data["sampleUtterances"] = sample_utterances

        slot_start_row = 10
        slots = self._get_variable_length_column_data(1, slot_start_row, worksheet)

        def get_slot_row_dict(r: int):
            slots_column = ["name", "description", "content", "slotType", "slotConstraint", "priority",
                            "sampleUtterances", "row"]
            slot_cell_data = [worksheet.cell(row=r + slot_start_row, column=i).value for i in range(1, 8)]
            slot_cell_data.append(r + slot_start_row)

            content = slot_cell_data[2]
            if "\n" in content:
                slot_cell_data[2] = content.split('\n')
            else:
                slot_cell_data[2] = [content]
            print(slot_cell_data[2])

            return dict(zip(slots_column, slot_cell_data))

        slots = list(map(get_slot_row_dict, range(0, len(slots))))
        data["slots"] = slots

        def get_slot(slot: dict):
            slot_data = {
                "slotType": slot["slotType"],
                "name": slot["name"],
                "slotConstraint": slot["slotConstraint"],
                "valueElicitationPrompt": {
                    "maxAttempts": int(JSONDecoder().decode(data["maxAttempts"])),
                    "messages": list(map(lambda x: {"content": x, "contentType": "PlainText"}, slot["content"]))
                },
                "priority": slot["priority"],
                "description": slot["description"]
            }

            if slot["sampleUtterances"] is not None:
                slot_sample_utterances = self._get_variable_length_column_data(7, slot["row"], worksheet)
                slot_data["sampleUtterances"] = list(map(JSONDecoder().decode, slot_sample_utterances))
            if not slot["slotType"].startswith('AMAZON.'):
                slot_data["slotTypeVersion"] = "$LATEST"

            return slot_data

        data["slots"] = json.dumps(list(map(get_slot, slots)))

        data["dialogCodeHook"] = None if data["dialogCodeHook"] == "\"\"" \
            else data["dialogCodeHook"][:1] + self.lambda_arn_prefix + data["dialogCodeHook"][1:]

        data["fulfillmentActivity"] = data["fulfillmentActivity"] if data["fulfillmentActivity"] == "\"ReturnIntent\"" \
            else data["fulfillmentActivity"][:1] + self.lambda_arn_prefix + data["fulfillmentActivity"][1:]

        self._save_json_template('intent.json', sheet_name, data)

    def generate_json(self):
        list(map(self._generate_intent_json, self.intends))
