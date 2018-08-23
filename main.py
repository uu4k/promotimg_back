import subprocess
import logging
import tempfile
import base64
import os
import uuid
from google.cloud import storage
from flask import abort, jsonify


def image(request):
    # 分岐
    # http://flask.pocoo.org/docs/1.0/api/#flask.Request.path
    if request.method == 'POST':
        return create(request)

    abort(404)


def create(request):
    if request.headers['Content-Type'] != 'application/json':
        abort(404)
        return

    logging.info('start create image.')

    # res = subprocess.run(['convert', '-list', 'font'], stdout=subprocess.PIPE)
    # return res.stdout.decode('utf-8')
    text = request.json['text']
    textposition = request.json['textposition']
    textcolor = request.json['textcolor']
    bgcolor = request.json['bgcolor']
    textsize = int(request.json['textsize']) # px
    

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

        ## TODO 縦書きの場合の改行補正
        srctext = text

        ## 文字列画像出力
        textsize_point = textsize / 1.33
        textimage = tmpdir + '/textimage' + ext
        command = ['convert', \
            '-font', './mplus-1c-bold.ttf', \
            '-size', width + 'x', \
            '-pointsize', str(textsize_point), \
            '-gravity', 'center', \
            '-background', bgcolor, \
            '-fill', textcolor, \
            'caption:' + srctext, \
            textimage \
            ]
        logging.info('create text image.')
        logging.info(' '.join(command))
        res = subprocess.run(command)
        # TODO エラー判定

        # 元画像と文字列画像結合
        joinedimage = tmpdir + '/joinedimage' + ext

        # 縦に結合
        command = ['convert', \
            '-append', \
            baseimage, textimage, \
            '-geometry', width+'x', \
            joinedimage
        ]
        logging.info('join image.')
        logging.info(' '.join(command))
        res = subprocess.run(command)

        # 横に結合
        # res = subprocess.run(['convert', \
        #     '+append', \
        #     baseimage, textimage, \
        #     '-geometry', 'x'+height, \
        #     joinedimage
        # ])

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
