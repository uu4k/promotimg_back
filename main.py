import subprocess
import logging
import tempfile
import base64
import os
import uuid
import flask
from google.cloud import storage
from flask import abort, jsonify


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


def create(request):
    if request.headers['Content-Type'] != 'application/json':
        abort(404)
        return

    logging.info('start create image.')

    # TODO validation
    text = request.json['text']
    textposition = request.json['textposition']
    textcolor = request.json['textcolor']
    bgcolor = request.json['bgcolor']
    textsize = int(request.json['textsize']) # px
    textsize_point = textsize / 1.33
    

    with tempfile.TemporaryDirectory() as tmpdir:
        baseimage = tmpdir + request.json['baseimagename']
        _, ext = os.path.splitext(baseimage)

        with open(baseimage, "wb") as fh:
            fh.write(base64.b64decode(request.json['baseimage']))
        

        
        # 文字列画像イメージ作成
        ## base64形式のデータから画像ファイル作成
        ## 元画像のサイズ取得
        command = ['identify', '-format', '%wx%h', baseimage]
        logging.info('identify base image.')
        logging.info(' '.join(command))
        res = subprocess.run(command, stdout=subprocess.PIPE)
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
            res = subprocess.run(command)

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
            res = subprocess.run(command)

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
    for index, chars in enumerate(line_chars):
        converted_line = ""
        for char in chars:
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
            '-gravity', 'center', \
            '-background', bgcolor, \
            '-fill', textcolor, \
            'caption:' + srctext, \
            _textimage \
            ]
        logging.info('create text image.(' + str(index) + ')')
        logging.info(' '.join(command))
        res = subprocess.run(command)
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
    res = subprocess.run(command)


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
    res = subprocess.run(command)

def add_access_control_headers(response):
    # TODO ドメイン絞る
    response.headers['Access-Control-Allow-Origin'] = "*"
    response.headers['Access-Control-Allow-Headers'] = "Content-Type"
    response.headers['Access-Control-Allow-Methods'] = "POST,OPTIONS"

    return response
