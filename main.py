import subprocess
import logging
import tempfile
import base64
import os
import uuid
import flask
from google.cloud import storage
from flask import abort, jsonify
from jsonschema import validate, ValidationError


def image(request):
    # 分岐
    # http://flask.pocoo.org/docs/1.0/api/#flask.Request.path
    if request.method == 'POST':
        resp = create(request)
        add_access_control_headers(resp)
        return resp
    elif request.method == 'OPTIONS':
        resp = flask.Response("Access-Control-Allow")
        add_access_control_headers(resp)
        return resp

    abort(404)


schema = {
    "$schema": "http://json-schema.org/draft-06/schema#",
    "properties": {
        "text": {
            "type": "string"
        },
        "textposition": {
            "type": "string",
            "enum": [
                "right",
                "left",
                "top",
                "bottom"
            ]
        },
        "textcolor": {
            "type": "string",
            "pattern": "^#[a-fA-F0-9]{6}"
        },
        "bgcolor": {
            "type": "string",
            "pattern": "^#[a-fA-F0-9]{6}"
        },
        "textsize": {
            "type": "number"
        },
        "baseimagename": {
            "type": "string"
        },
        "baseimage": {
            "type": "string"
        }
    },
    "required": [
        "text",
        "textposition",
        "textcolor",
        "bgcolor",
        "textsize",
        "baseimagename",
        "baseimage",
    ],
    "additionalProperties": False,
    "type": "object"
}

def create(request):
    if request.headers['Content-Type'] != 'application/json':
        abort(404)
        return

    logging.info('start create image.')

    try:
        validate(request.json, schema)
    except ValidationError as e:
        m = 'Invalid JSON - {0}'.format(e.message)
        logging.error(m)
        abort(400, {'message': m})

    text = request.json['text']
    textposition = request.json['textposition']
    textcolor = request.json['textcolor']
    bgcolor = request.json['bgcolor']
    textsize = int(request.json['textsize']) # px
    # textsize_point = textsize / 1.33
    textsize_point = textsize
    

    with tempfile.TemporaryDirectory() as tmpdir:
        baseimage = tmpdir + request.json['baseimagename']
        _, ext = os.path.splitext(baseimage)

        with open(baseimage, "wb") as fh:
            fh.write(base64.b64decode(request.json['baseimage']))
        
        # TODO 画像ファイルか判定

        
        # 文字列画像イメージ作成
        ## base64形式のデータから画像ファイル作成
        ## 元画像のサイズ取得
        command = ['identify', '-format', '%wx%h', baseimage]
        logging.info('identify base image.')
        logging.info(' '.join(command))
        res = subprocess.run(command, stdout=subprocess.PIPE, check=True)
        width_x_height = res.stdout.decode('utf-8')
        width, height = width_x_height.split("x")
        # width = int(width)
        # height = int(height)

        textimage = tmpdir + '/textimage' + ext
        joinedimage = tmpdir + '/joinedimage' + ext
        if textposition in ['right', 'left']:
            ## 文字列画像出力
            create_vertical_textimage(
                text, textsize_point, textcolor, bgcolor, height, textimage)

            # 元画像と文字列画像結合
            images = [baseimage, textimage]
            if textposition == 'left':
                images.reverse()
            
            command = ['convert', \
                '+append', \
                *images, \
                '-geometry', 'x'+height, \
                joinedimage
            ]
            logging.info('join image.')
            logging.info(' '.join(command))
            res = subprocess.run(command, check=True)

        elif textposition in ['top', 'bottom']:
            ## 文字列画像出力
            create_horizontal_textimage(
                text, textsize_point, textcolor, bgcolor, width, textimage)

            # 元画像と文字列画像結合
            images = [baseimage, textimage]
            if textposition == 'top':
                images.reverse()
            command = ['convert', \
                '-append', \
                *images, \
                '-geometry', width+'x', \
                joinedimage
            ]
            logging.info('join image.')
            logging.info(' '.join(command))
            res = subprocess.run(command, check=True)

        # 画像をgcsにアップ
        logging.info('upload image.')
        project = os.environ['storage_project']
        storage_client = storage.Client() if project == "" else storage.Client(project)
        bucket_name = os.environ['storage_bucket']
        bucket = storage_client.get_bucket(bucket_name)
        blob = bucket.blob(str(uuid.uuid4()) + ext)
        blob.upload_from_filename(joinedimage)
        blob.make_public()

        # gcsの画像のURLをレスポンスとして返却(json形式)
        logging.info('image url:' + blob.public_url)
        return jsonify({ 'url': blob.public_url })

def convert_to_vertical_string(text):
    lines = text.split("\n")
    line_chars = []
    for l in lines:
        line_chars.append([c for c in l])

    converted_lines = []
    for chars in line_chars:
        converted_line = ""
        for char in chars:
            if char == 'ー':
                char = '｜'
            # TODO 半角英数文字列判定
            converted_line += char
            converted_line += "\n"
        converted_lines.append(converted_line[:-1])

    return converted_lines


def create_vertical_textimage(text, textsize_point, textcolor, bgcolor, height, textimage):
    ## 縦書きの場合の改行補正
    vertical_texts = convert_to_vertical_string(text)
    ## 行ごとに画像化して結合
    textimages = []
    for index, srctext in enumerate(vertical_texts):
        basepath, ext = os.path.splitext(textimage)
        _textimage = basepath + '.' + str(index) + ext
        command = ['convert', \
            '-font', './mplus-1c-bold.ttf', \
            '-size', 'x' + height, \
            '-pointsize', str(textsize_point), \
            '-interline-spacing', '-10', \
            '-gravity', 'center', \
            '-background', bgcolor, \
            '-fill', textcolor, \
            'caption:' + srctext, \
            _textimage \
            ]
        logging.info('create text image.(' + str(index) + ')')
        logging.info(' '.join(command))
        res = subprocess.run(command, check=True)
        textimages.append(_textimage)
    
    textimages.reverse()
    command = ['convert', \
        '+append', \
        *textimages, \
        '-geometry', 'x'+height, \
        textimage
    ]
    logging.info('create text image.')
    logging.info(' '.join(command))
    res = subprocess.run(command, check=True)


def create_horizontal_textimage(text, textsize_point, textcolor, bgcolor, width, textimage):
    command = ['convert', \
        '-font', './mplus-1c-bold.ttf', \
        '-size', width + 'x', \
        '-pointsize', str(textsize_point), \
        '-gravity', 'center', \
        '-background', bgcolor, \
        '-fill', textcolor, \
        'caption:' + text, \
        textimage \
        ]
    logging.info('create text image.')
    logging.info(' '.join(command))
    res = subprocess.run(command, check=True)

def add_access_control_headers(response):
    response.headers['Access-Control-Allow-Origin'] = "promotimg.uu4k.me"
    response.headers['Access-Control-Allow-Headers'] = "Content-Type"
    response.headers['Access-Control-Allow-Methods'] = "POST,OPTIONS"

    return response
