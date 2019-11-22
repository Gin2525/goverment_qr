import os
import sys
from flask import *
import psycopg2
from . import tools
from datetime import datetime
import qrcode
from imgurpython import ImgurClient
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    SourceUser, SourceGroup, SourceRoom,
    TemplateSendMessage, ConfirmTemplate, MessageAction,
    ButtonsTemplate, ImageCarouselTemplate, ImageCarouselColumn, URIAction,
    PostbackAction, DatetimePickerAction,
    CameraAction, CameraRollAction, LocationAction,
    CarouselTemplate, CarouselColumn, PostbackEvent,
    StickerMessage, StickerSendMessage, LocationMessage, LocationSendMessage,
    ImageMessage, VideoMessage, AudioMessage, FileMessage,
    UnfollowEvent, FollowEvent, JoinEvent, LeaveEvent, BeaconEvent,
    FlexSendMessage, BubbleContainer, ImageComponent, BoxComponent,
    TextComponent, SpacerComponent, IconComponent, ButtonComponent,
    SeparatorComponent, QuickReply, QuickReplyButton,
    ImageSendMessage,
)

###
# imgur 
CLIENT_ID = "11c33d95d3e8ffe"
CLIENT_SERCRET = "3f81c51cc9611fb18a74b653d26a7126e688e90d"
Client = ImgurClient(CLIENT_ID,CLIENT_SERCRET)


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

# 表名,列名を定義
TRANSACTION_TABLE = "TRANSACTION_TABLE"
C_TRANSACTIONID = "transactionid"
C_USERID = "userid"
C_QUESTION_TYPE = "questiontype"
C_AT_DATETIME = "at_datetime"
C_ANSWER = "answer"

QUESTION_TYPE = [
    "start",
    "question_n",  # n は 1から nは小文字
    "confirm",
]
ANSWER = {
    "start": {
        "引越し手続き": "moving",
        "住民票発行": "issueResidentCard",
        "マイナンバーカードの発行": "issueMyNumberCard"
    },
    "question_n": {
        "引越し手続き_質問1": "moving_1",
        "引越し手続き_質問2": "moving_2",
        "引越し手続き_質問3": "moving_3"
    },
    "confirm": {
        "引越し手続き": "moving_end",
    },
}

LAST_SQL = f"""SELECT {C_QUESTION_TYPE}, {C_ANSWER} FROM {TRANSACTION_TABLE}
            WHERE '*u'={C_USERID}
            AND {C_AT_DATETIME} IN (
                SELECT MAX({C_AT_DATETIME}) FROM {TRANSACTION_TABLE} 
                WHERE '*u'={C_USERID}
                AND {C_QUESTION_TYPE} LIKE '*qt%'
                GROUP BY {C_QUESTION_TYPE}
            )
            ORDER BY {C_AT_DATETIME} ASC;
            """

I_SQL = f"""
            INSERT INTO {TRANSACTION_TABLE}({C_USERID},{C_QUESTION_TYPE},{C_AT_DATETIME},{C_ANSWER})
            VALUES('*u', '*q', CURRENT_TIMESTAMP, '*a');
        """

# 以下、Flask web app
app = Flask(__name__)

# os.environ['LINE_CHANNEL_ACCESS_TOKEN']
CHANNEL_ACCESS_TOKEN = "lFl6Qfb1LlSds5DSMSnt1e2dc+o5DnymdAEWECCEnCMgLw0PiFVJ9ny3hs1tes5fOtE+gG6P7fxJd42bfRnMaR/h2LB/oj5SBLmG/Ah51CTykpdIxr+W/nBuP0HYKC18f1k5+i5qvd6JXQTl7AHmBQdB04t89/1O/w1cDnyilFU="
# os.environ['LINE_CHANNEL_SECRET']
CHANNEL_SECRET = "5ab046b03214bd09c3162a124a3ad784"

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# 以下、処理


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
    # https://developers.line.biz/console/channel/1653365219/basic/
    # LINEコンソールのwebhook URL のエラー回避用.
    if event.reply_token == "00000000000000000000000000000000":
        return

    if event.message.text == "最初から" or event.message.text == "さいしょから":
        user_id = event.source.user_id
        # DBからこれまでのトランザクションを削除
        sql = f"DELETE FROM {TRANSACTION_TABLE} WHERE {C_USERID}='{user_id}'"
        with conn.cursor() as cur:
            cur.execute(sql)

        # ボタンテンプレートメッセージを作成
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
        line_bot_api.reply_message(
            event.reply_token, messages=buttons_template_message)

    else:  # その他のメッセージがきた場合。
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="最初から選び直したいときは\n「最初から」or「さいしょから」\nと入力してください。")
        )


@handler.add(PostbackEvent)
def handle_postback(event):
    rt = event.reply_token
    user_id = event.source.user_id
    print(f"debug log -> {event.postback.data}")
    question, answer = event.postback.data.split(
        ':')  # ':'で文字列を分解し、[questionType,answer]　で分ける。

    # type:start
    if(question == QUESTION_TYPE[0]):
        if(answer == ANSWER[question]["引越し手続き"]):  # answer:moving
            # どちらにもstartのインスタンスが入る。
            sql = I_SQL.replace("*u", user_id).replace("*q",
                                                       answer).replace("*a", answer)

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
            # 返信
            line_bot_api.reply_message(rt, messages=message)

        elif(answer == ANSWER[question]["住民票発行"]):  # answer:issueResidentCart
            # 未定
            print("debug:entered 住民票発行")
            line_bot_api.reply_message(rt, TextSendMessage(text="続きは開発中です"))

        elif(answer == ANSWER[question]["マイナンバーカードの発行"]):  # answer:issueMyNumber
            print("debug:entered マイナンバーカードの発行")
            # 未定
            line_bot_api.reply_message(rt, TextSendMessage(text="続きは開発中です"))

    # type:question_n
    if(question == QUESTION_TYPE[1]):
        # answer:moving_1
        if(answer == ANSWER[question]["引越し手続き_質問1"]):
            print("debug:entered 引越し手続き_質問1")

            sql = I_SQL.replace("*u", user_id).replace("*q", answer).replace(
                "*a", event.postback.params["date"])  # answerは分かりにくいが、moving_1を格納しないといけないのでこうなる。
            with conn.cursor() as cur:
                cur.execute(sql)

            message = TemplateSendMessage(
                alt_text='Buttons template',
                template=ButtonsTemplate(
                    title='お引越し先のご住所はどちらですか？',
                    text='以下よりご入力ください。',
                    actions=[
                        URIAction(
                            label='住所を入力',
                            uri='line://app/1653526331-jJQZGQGJ',
                            data="question_n:moving_2"
                        )
                    ])
            )
            # 返信
            line_bot_api.reply_message(rt, messages=message)

        # answer:moving_3
        elif(answer == ANSWER[question]["引越し手続き_質問3"]):
            sql = I_SQL.replace("*u", user_id).replace("*q",
                                                       answer).replace("*a", event.postback.params["datetime"])
            with conn.cursor() as cur:
                cur.execute(sql)

            sql = LAST_SQL.replace("*u", user_id).replace("*qt", "moving")

            with conn.cursor() as cur:
                cur.execute(sql)
                results = cur.fetchall()

            # フレックスで入力内容を確認。
            bubble = BubbleContainer(
                # 左から右に文章が進むように設定
                direction='ltr',
                body=BoxComponent(
                    layout='vertical',
                    contents=[
                        # title
                        TextComponent(text='入力内容の確認',
                                      weight='bold', size='xxl'),
                        SeparatorComponent(margin='lg'),
                        BoxComponent(
                            layout='vertical',
                            margin='lg',
                            contents=tools.box_gen(results)
                        ),
                    ]
                ),
            )
            message = FlexSendMessage(alt_text="入力内容を確認", contents=bubble)
            line_bot_api.push_message(to=user_id, messages=message)

            # 確認メッセ confirm_moving
            confirm_message = TemplateSendMessage(
                alt_text='Confirm template',
                template=ConfirmTemplate(
                    text='入力に問題はないですか?',
                    actions=[
                        PostbackAction(
                            label='OK',
                            data='confirm:moving_end'
                        ),
                        PostbackAction(
                            label='取り消し',
                            # 訂正についてはまだ未実装。
                            data='correct:moving_end'
                        )
                    ]
                )
            )
            line_bot_api.reply_message(rt, confirm_message)

    # type:confirm
    if(question == QUESTION_TYPE[2]):
        # confirm:moving_end
        if(answer == ANSWER[question]["引越し手続き"]):
            # 引越しに関するクエリを実行
            sql = LAST_SQL.replace("*u", user_id).replace("*qt", "moving")
            with conn.cursor() as cur:
                cur.execute(sql)
                results = cur.fetchall()

            qr_data = dict()
            qr_data["purpose"] = results[0][1]
            qr_data["movingOutDay"] = results[1][1]
            qr_data["fullAddress"] = results[2][1]
            qr_data["receiveDay"] = results[3][1]

            now = datetime.now()
            path = "./img/"
            imagename = now.isoformat() + user_id + ".png"
            imagepath = path + imagename
            
            img = qrcode.make(qr_data)
            print(type(img))
            img.save(imagepath)
            
            imagelink = Client.upload_from_path(imagepath, config=None, anon=True)["link"]
            print(f"uploaded to {imagelink}")


            image_message = ImageSendMessage(
                original_content_url=imagelink,
                preview_image_url=imagelink
            )
            line_bot_api.push_message(user_id,TextSendMessage(text="予約が完了しました。当日、スタッフにこちらのQRコードをご提示ください。"))

            line_bot_api.reply_message(rt, messages=image_message)


@handler.add(FollowEvent)
def handle_follow(event):
    reply_token = event.reply_token
    userID = event.source.user_id

    # ボタンテンプレートメッセージを作成
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

# @handler.add(UnfollowEvent):
#     #DBからアンフォローしたユーザのトランザクションデータを全て削除。

# LIFF
@app.route("/enter_address", methods=["GET", "POST"])
def display_liff():
    return render_template("enter_address.html")

# moving_2のハンドラ
@app.route("/recieve_address", methods=["POST"])
def recieve_liff():
    # 受け取った情報をDBに格納。
    user_id = request.form["user_id"]
    answer = request.form["answer"]
    zipcode = request.form["zipcode"]
    street_address = request.form["streetAddress"]
    address = request.form["address"]
    fullAddress = f"{zipcode},{street_address},{address}"

    sql = I_SQL.replace("*u", user_id).replace("*q",
                                               answer).replace("*a", fullAddress)

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
    # APIの返り値による例外処理を無視したいので、一旦関数に入れ込む。
    push_message(user_id, message)
    return render_template("confirm.html")


def push_message(to, message):
    line_bot_api.push_message(to, messages=message)


if __name__ == "__main__":
    app.run(debug=True)
