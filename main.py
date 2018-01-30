#!/usr/bin/env python
# coding: utf-8

from gae_http_client import RequestsHttpClient

from google.appengine.api import taskqueue

from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, ImageMessage
)

import config
import re
from bs4 import BeautifulSoup
from google.appengine.api import urlfetch

app = Flask(__name__)

line_bot_api = LineBotApi(config.CHANNEL_ACCESS_TOKEN, http_client=RequestsHttpClient)
handler = WebhookHandler(config.CHANNEL_SECRET)


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # Task Queue Add
    taskqueue.add(url='/worker',
                  params={'body': body,
                          'signature': signature},
                  method="POST")

    return 'OK'


@app.route("/worker", methods=['POST'])
def worker():
    body = request.form.get('body')
    signature = request.form.get('signature')

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 最後印出的內容
    reply_text = u""""""
    try:
        # 看要用什麼關鍵字
        if event.message.text == u"房地產熱門推文":
            url = "https://www.ptt.cc/bbs/home-sale/index.html"
            reply_text = control_ptt(url, reply_text)
        elif event.message.text == u"信用卡精選討論":
            url = "https://www.ptt.cc/bbs/creditcard/index.html"
            reply_text = control_ptt(url, reply_text)
        elif event.message.text == u"汽車話題精選":
            url = "https://www.ptt.cc/bbs/car/index.html"
            reply_text = control_ptt(url, reply_text)
        elif event.message.text == u"房地產重磅新聞":
            url = "https://house.udn.com/house/cate/5885"
            reply_text = control_real_estate(url, reply_text)
        elif event.message.text == u"CMoney最新投資理財文章":
            url = "http://www.cmoney.tw/notes/?bid=22814"
            reply_text = control_invest_post(url, reply_text)


    except:
        # 如果都沒下關鍵字，直接回答一樣的內容
        reply_text = event.message.text
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text))


def control_ptt(url, text):
    from google.appengine.api import urlfetch
    count = 0
    response = urlfetch.fetch(url, method=urlfetch.GET)
    bsObj = BeautifulSoup(response.content, "html.parser")
    while (count <= 4):
        count, next_page, text = find_post(bsObj, count, text)
        url2 = next_page
        response2 = urlfetch.fetch(url2, method=urlfetch.GET)
        bsObj = BeautifulSoup(response2.content, "html.parser")
    return text
def find_post(bsObj_input, count, text):
    results = bsObj_input.findAll("div", {"class": "r-ent"})
    for item in results:
        if count > 4:
            break
        push_number = item.find("span", {"class": re.compile("hl.")})
        post_title = item.find("a")
        if post_title is not None:
            post_url = post_title.attrs["href"]
            post_url = "https://www.ptt.cc" + post_url
            # temp_b = item.find("div", {"class": "title"})
            if push_number is not None:
                try:
                    if push_number.text == u"爆" or int(push_number.text) > 9:
                        count += 1
                        text += post_title.text + "\n" + post_url + "\n\n"
                except:
                    pass
    next_page = "https://www.ptt.cc" + bsObj_input.find("a", text="最舊").find_next_sibling('a').attrs["href"]

    return count, next_page, text
def control_real_estate(url, text):
    count = 0
    response = urlfetch.fetch(url, method=urlfetch.GET)
    bsObj = BeautifulSoup(response.content, "html.parser")
    results = bsObj.findAll("div", {"class": "area_body", "id": "mag_most_hot_body"})
    for i in results:
        for j in i.findAll("a"):
            text += j.text  + "\n"
            text +=  'https://house.udn.com' + j.attrs['href'] + "\n\n"
            # text = '789'
    return text
def control_invest_post(url, text):
    count = 0
    response = urlfetch.fetch(url, method=urlfetch.GET)
    bsObj = BeautifulSoup(response.content, "html.parser")
    results = bsObj.findAll("div", {"class": "pt-bar"})
    for i in results:
        for j in i.findAll('h2'):
            if count < 5:
                text += j.find('a').text  + "\n" + 'http://www.cmoney.tw' + j.find('a').attrs['href']+ "\n\n"
                count += 1
            else:
                break
    return text

