# Excel Lex Bot

Our institution decides to try Amazon Lex in teaching, research and health care. However, most users are non-technical users such as English Teachers and Therapist but we don’t have enough developers to support them from the development to the long term update their Chat Bot. It is possible to teach them build Chat Bot in Amazon Lex Console, although it is already very user friendly for developers. However, most of them know how to use Microsoft Excel and we start build project “ExcelLexBot” that let them use Excel to create Chatbot with minimum effort for developers.
ExcelLexBot is a serverless applications using AWS SAM (https://github.com/awslabs/serverless-application-model) that converts Excel file (xlsx) with predefined format into Amazon Lex Chat Bot.

Build an Amazon Lex Chatbot with Microsoft Excel


https://aws.amazon.com/blogs/machine-learning/build-an-amazon-lex-chatbot-with-microsoft-excel/


Microsoft Excel を使った Amazon Lex チャットボットの構築


https://aws.amazon.com/jp/blogs/news/build-an-amazon-lex-chatbot-with-microsoft-excel/


借助 Microsoft Excel 构建 Amazon Lex 聊天机器人


https://aws.amazon.com/cn/blogs/china/build-an-amazon-lex-chatbot-with-microsoft-excel/

## Deployment with AWS Serverless Application Repository
Search "ExcelLexBot" and deploy it with one click!

## Deployment has been updated!

It needs to AWS SAM deploy.

Install the latest AWS SAM CLI in Cloud9

git clone https://github.com/wongcyrus/ExcelLexBot

cd ExcelLexBot

./setup.sh

sudo ./get_layer_packages.sh

./deployment.sh


## userId overriding logic 
If you put userId in session, it will use the userId in session and save to DynamoDB.




