import os
import tempfile
import pytest
from pprint import pprint
from flask import Flask
from flask import request
from main import create
from google.cloud import storage
import logging
import base64


@pytest.fixture
def client():
    # setup
    app = Flask(__name__)

    @app.route("/", methods=['GET', 'POST'])
    def _create():
        return create(request)

    app.config['TESTING'] = True
    client = app.test_client()

    # テスト用バケット作成
    os.environ['storage_project'] = 'promotimg'
    os.environ['storage_bucket'] = 'promotimg_test'

    storage_client = storage.Client(os.environ['storage_project'])
    storage_client.create_bucket(os.environ['storage_bucket'])

    yield client

    # teardown
    bucket = storage_client.get_bucket(os.environ['storage_bucket'])
    bucket.delete(force=True)


def test_404(client):
    rv = client.get('/')
    assert rv.status_code == 404


def test_post(client):
    testimgstr = base64.b64encode(
        open('./test_main_001.png', 'rb').read()).decode('utf-8')
    rv = client.post('/', json={
        'text': 'サンプル',
        'textposition': 'right',
        'textcolor': '#FFF000',
        'bgcolor': '#000FFF',
        'textsize': '22',
        'baseimagename': 'sample.png',
        'baseimage': testimgstr,
    })

    # TODO gcs周りモック化or前処理後処理
