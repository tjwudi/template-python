import socketio
import eventlet

from flask import request
from flask import Flask
from PIL import Image
from io import BytesIO

import base64
import requests
import os
from flask import render_template

port = int(os.environ.get("PORT", 8080))
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


flask = Flask(__name__)


@flask.route("/live")
def live():
    return render_template("live.html")


@flask.route("/receive", methods=["POST"])
def receive():
    data = request.json
    image_data_base64 = data['image']
    image_data = base64.b64decode(data['image'])
    image_data_io = BytesIO(image_data)
    print("size (mb)", image_data_io.getbuffer().nbytes / 1024 / 1024)

    image = Image.open(image_data_io)
    # print image dimension
    print("image size", image.size)
    # get image format
    print("image format", image.format)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }

    payload = {
        "model": "gpt-4-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_data_base64}"
                        }
                    },
                    {
                        "type": "text",
                        "text": """Answer the multiple choice question in this screenshot.
                                    Only tell me the choice, and the content of the choice (e.g. 'A. Right Arm'), and don't add anything else in the front (like "The right answer is ...").
                                    Ignore other windows, only focus on the window with the question.
                                    If there are multiple questions, answer all of them."""
                    },
                ]
            }
        ],
        "max_tokens": 300
    }

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=payload,
    )
    sio.emit('response', response.json())
    return ""


sio = socketio.Server()


@sio.event
def connect(sid, environ):
    print(f"client connected {sid}")


@sio.event
def pulse(sid, data):
    print(f"pulse received, let's start the operation")
    sio.emit('start_operation', "ack")


app = socketio.WSGIApp(sio, flask)


if __name__ == '__main__':
    eventlet.wsgi.server(eventlet.listen(('127.0.0.1', port)), app)
