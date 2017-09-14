import json
import os

import boto3
import time

from converter.BotJsonConverter import BotJsonConverter
from converter.IntendJsonConverter import IntendJsonConverter
from converter.IntendSlotJsonConverter import IntendSlotJsonConverter


class BotBuilder:
    def __init__(self, workbook, output_dir, lambda_arn_prefix):
        self.intendSlotJConverter = IntendSlotJsonConverter(workbook, output_dir)
        self.intendConverter = IntendJsonConverter(workbook, output_dir, lambda_arn_prefix)
        self.botJConverter = BotJsonConverter(workbook, output_dir)
        self.output_dir = output_dir
        self.lambda_arn_prefix = lambda_arn_prefix
        self.client = boto3.client('lex-models', region_name='us-east-1')

    def __build_lex_component(self, name: str, func):
        with open(os.path.join(self.output_dir, name + ".json"), 'r') as f:
            data = json.load(f)
        print(data)
        response = func(**data)
        print(response)

    @staticmethod
    def __delete_lex_component(name: str, func):
        try:
            response = func(name=name)
            print(response)
        except Exception as e:
            print("Cannot Delete" + name)
            print(e)

    def deploy_bot(self):
        list(map((lambda x: self.__build_lex_component(x, self.client.put_slot_type)), self.botJConverter.slot_types))
        time.sleep(2)
        list(map((lambda x: self.__build_lex_component(x, self.client.put_intent)), self.botJConverter.intends))
        time.sleep(5)
        list(map((lambda x: self.__build_lex_component(x, self.client.put_bot)), self.botJConverter.bots))

    def generate_json(self):
        self.intendSlotJConverter.generate_json()
        self.intendConverter.generate_json()
        self.botJConverter.generate_json()

    def undeploy_bot(self):
        list(map((lambda x: self.__delete_lex_component(x, self.client.delete_bot)), self.botJConverter.bots))
        time.sleep(10)
        list(map((lambda x: self.__delete_lex_component(x, self.client.delete_intent)), self.botJConverter.intends))
        time.sleep(5)
        list(map((lambda x: self.__delete_lex_component(x, self.client.delete_slot_type)),
                 self.botJConverter.slot_types))


if __name__ == "__main__":
    # bot_builder = BotBuilder(os.path.join(os.getcwd(), "playground", "OrderFlowersChatbot.xlsx"),
    #                          os.path.join(os.getcwd(), "output"))
    # bot_builder.deploy_bot()

    bot_builder1 = BotBuilder(os.path.join("../playground", "MakeAppointmentChatBot.xlsx"),
                              os.path.join("../", "output"), " arn:aws:lambda:us-east-1:894598711988:function:")
    bot_builder1.generate_json()
    # bot_builder1.deploy_bot()
    # time.sleep(10)
    # bot_builder1.undeploy_bot()

    # bot_builder.undeploy_bot()
