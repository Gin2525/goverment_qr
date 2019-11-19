import os
import sys
from flask import *
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
    "question_n", #n は 1から nは小文字
    "attend_date",
    "confirm",
]
ANSWER ={
    "start":{
        "引越し手続き":"moving",
        "住民票発行":"issueResidentCard",
        "マイナンバーカードの発行":"issueMyNumberCard"
    },
    "question_n":{
        "引越し手続き_質問1":"moving_1",
        "引越し手続き_質問2":"moving_2",
        "引越し手続き_質問3":"moving_3"
    },

}
I_SQL = f"""
            INSERT INTO {TRANSACTION_TABLE}({C_USERID},{C_QUESTION_TYPE},{C_AT_DATETIME},{C_ANSWER})
            VALUES('*u', '*q', CURRENT_TIMESTAMP, '*a');
        """

#以下、Flask web app
app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = "lFl6Qfb1LlSds5DSMSnt1e2dc+o5DnymdAEWECCEnCMgLw0PiFVJ9ny3hs1tes5fOtE+gG6P7fxJd42bfRnMaR/h2LB/oj5SBLmG/Ah51CTykpdIxr+W/nBuP0HYKC18f1k5+i5qvd6JXQTl7AHmBQdB04t89/1O/w1cDnyilFU="#os.environ['LINE_CHANNEL_ACCESS_TOKEN']
CHANNEL_SECRET = "5ab046b03214bd09c3162a124a3ad784"#os.environ['LINE_CHANNEL_SECRET']

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
    
    if event.message.text=="最初から" or event.message.text == "さいしょから":
        user_id = event.source.user_id
        #DBからこれまでのトランザクションを削除
        sql = f"DELETE FROM {TRANSACTION_TABLE} WHERE {C_USERID}='{user_id}'"
        with conn.cursor() as cur:
            cur.execute(sql)

        #ボタンテンプレートメッセージを作成
        buttons_template_message = TemplateSendMessage(
            alt_text='Buttons template',
            template=ButtonsTemplate(
            title='目的選択',
            text='自分の目的に合うものをご選択ください。',
            actions=[
                PostbackAction(
                    label='引越し手続き(転出届)',
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
        line_bot_api.reply_message(event.reply_token, messages=buttons_template_message)

    else: #その他のメッセージがきた場合。
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="最初から選び直したいときは\n「最初から」or「さいしょから」\nと入力してください。")
        )

@handler.add(PostbackEvent)
def handle_postback(event):
    rt = event.reply_token
    user_id = event.source.user_id
    print(f"debug log -> {event.postback.data}")
    question,answer = event.postback.data.split(':') #':'で文字列を分解し、[questionType,answer]　で分ける。
    
    #type:start
    if(question==QUESTION_TYPE[0]):
        if(answer==ANSWER[question]["引越し手続き"]): #answer:moving
            sql = I_SQL.replace("*u",user_id).replace("*q",answer).replace("*a",answer) #どちらにもstartのインスタンスが入る。

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
                        data=f"question_n:{answer}_1",
                        mode="date",
                    )
                ])
            )
            #返信
            line_bot_api.reply_message(rt,messages=message)

        elif(answer==ANSWER[question]["住民票発行"]): #answer:issueResidentCart
            #未定
            print("debug:entered 住民票発行")
            line_bot_api.reply_message(rt,TextSendMessage(text="続きは開発中です"))

        elif(answer==ANSWER[question]["マイナンバーカードの発行"]): #answer:issueMyNumber
            print("debug:entered マイナンバーカードの発行")
            #未定
            line_bot_api.reply_message(rt,TextSendMessage(text="続きは開発中です"))
    
    #type:question_n
    if(question==QUESTION_TYPE[1]):
        #answer:moving_1
        if(answer==ANSWER[question]["引越し手続き_質問1"]):
            print("debug:entered 引越し手続き_質問1")

            sql = I_SQL.replace("*u",user_id).replace("*q",answer).replace("*a",event.postback.params["date"]) #answerは分かりにくいが、moving_1を格納しないといけないのでこうなる。
            with conn.cursor() as cur:
                cur.execute(sql)

            message = TemplateSendMessage(
                alt_text='Buttons template',
                template=ButtonsTemplate(
                title='お引越し先のご住所をお伝えください。',
                text='以下よりご入力ください。',
                actions=[
                    URIAction(
                        label='住所を入力',
                        uri='line://app/1653526331-jJQZGQGJ',
                        data="question_n:moving_2"
                    )
                ])
            )
            #返信
            line_bot_api.reply_message(rt,messages=message)
        
        #answer:moving_3
        elif(answer==ANSWER[question]["引越し手続き_質問3"]):
            line_bot_api.reply_message(rt,TextSendMessage(text="ここは開発中。。。"))

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
                label='引越し手続き(転出届け)',
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

#LIFF
@app.route("/enter_address",methods=["GET","POST"])
def display_liff():
    return render_template("enter_address.html")

#moving_2のハンドラ
@app.route("/recieve_address",methods=["POST"])
def recieve_liff():
    ##受け取った情報をDBに格納。
    user_id = request.form["user_id"]
    answer = request.form["answer"]
    zipcode = request.form["zipcode"]
    street_address = request.form["streetAddress"]
    address = request.form["address"]
    fullAddress = f"{zipcode} {street_address} {address}"

    sql = I_SQL.replace("*u",user_id).replace("*q",answer).replace("*a",fullAddress)

    with conn.cursor() as cur:
        cur.execute(sql)

    message = TemplateSendMessage(
                alt_text='Buttons template',
                template=ButtonsTemplate(
                title='いつ市役所にはお越しになりますか？',
                text='以下よりご選択ください。',
                actions=[
                    DatetimePickerAction(
                        label='日時選択',
                        data=f"question_n:moving_3",
                        mode="datetime",
                    )
                ])
            )
    #APIの返り値による例外処理を無視したいので、一旦関数に入れ込む。
    push_message(user_id,message)
    return "OK"
    
    
def push_message(to,message):
    line_bot_api.push_message(to,messages=message)

if __name__ == "__main__":
    app.run(debug=True)