import os
import sys
from flask import Flask, request, abort
import psycopg2
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    MessageAction, QuickReply, QuickReplyButton,
    FollowEvent,UnfollowEvent,
    PostbackEvent,PostbackAction,
    URIAction,ButtonsTemplate,TemplateSendMessage,
    DatetimePickerAction,
)
####
# DBとのコネクション
conn = psycopg2.connect(
    '''
    dbname=d6i155n1m3pt0j
    host=ec2-174-129-253-174.compute-1.amazonaws.com
    user=mlvfguyntpxyof
    password=f23c619df387a333b4b08cb7d97aa54622307fefc534e9727e4081eec8fa76b4
    '''
)
conn.autocommit = True

#表名,列名を定義
TRANSACTION_TABLE = "TRANSACTION_TABLE"
C_TRANSACTIONID = "transactionid"
C_USERID = "userid"
C_QUESTION_TYPE = "questiontype"
C_AT_DATETIME="at_datetime"
C_ANSWER = "answer"

QUESTION_TYPE=[
    "start",
    "question_NM",
    "question_NF",
    "attend_date",
    "confirm",
]
ANSWER ={
    "start":{
        "引っ越し手続き":"moving",
        "住民票発行":"issueResidentCart",
        "マイナンバーカードの発行":"issueMyNumberCard"
    }

}

#以下、Flask web app
app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = os.environ['LINE_CHANNEL_ACCESS_TOKEN']
CHANNEL_SECRET = os.environ['LINE_CHANNEL_SECRET']

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

#以下、処理

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    #https://developers.line.biz/console/channel/1653365219/basic/
    #LINEコンソールのwebhook URL のエラー回避用.
    if event.reply_token == "00000000000000000000000000000000":
        return 

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text)
    )


@handler.add(PostbackEvent)
def handle_postback(event):
    rt = event.reply_token
    user_id = event.source.user_id
    question,answer = event.postback.data.split(':') #':'で文字列を分解し、[questionType,answer]　で分ける。
    

    if(question==QUESTION_TYPE[0]):#type:start
        if(answer==ANSWER[question]["引っ越し手続き"]): #answer:moving
            sql = f"""
                INSERT INTO {TRANSACTION_TABLE}({C_USERID},{C_QUESTION_TYPE},{C_AT_DATETIME},{C_ANSWER})
                VALUES('{user_id}','{question}', CURRENT_TIMESTAMP, '{answer}');
            """

            with conn.cursor() as cur:
                cur.execute(sql)

            message = TemplateSendMessage(
                alt_text='Buttons template',
                template=ButtonsTemplate(
                title='いつ転居なされる予定ですか？',
                text='以下よりご選択ください。',
                actions=[
                    DatetimePickerAction(
                        label='転居予定日の選択',
                        data=f"question_NM:{question}0",
                        mode="datetime",
                    )
                ])
            )
            #返信
            line_bot_api.reply_message(rt,messages=message)

        elif(answer==ANSWER[question]["住民票発行"]): #answer:issueResidentCart
            #未定
            return
        elif(answer[1]==ANSWER[question]["マイナンバーカードの発行"]): #answer:issueMyNumber
            #未定
            return

@handler.add(FollowEvent)
def handle_follow(event):
    reply_token = event.reply_token
    userID = event.source.user_id

    #ボタンテンプレートメッセージを作成
    buttons_template_message = TemplateSendMessage(
        alt_text='Buttons template',
        template=ButtonsTemplate(
        title='目的選択',
        text='自分の目的に合うものをご選択ください。',
        actions=[
            PostbackAction(
                label='引っ越し手続き',
                data='start:moving'
            ),
            PostbackAction(
                label='住民票発行',
                data='start:issueResidentCard'
            ),
            PostbackAction(
                label='マイナンバーカード発行',
                data='start:issueMyNumberCard'
            )
        ])
    )

    line_bot_api.reply_message(reply_token, messages=buttons_template_message)

    # sql = f"""
    # INSERT INTO {TABLE_NAME}({C_USERID},{C_USERID},{C_QUESTION_TYPE},{C_AT_DATETIME})
    # VALUES ('{userID}','{}');
    # """
    # with conn.cursor() as cur:
    #     cur.execute(sql)

# @handler.add(UnfollowEvent):
#     #DBからアンフォローしたユーザのトランザクションデータを全て削除。


if __name__ == "__main__":
    app.run()