import os
import tempfile
import pytest
from pprint import pprint
from flask import Flask
from flask import request
from main import create, convert_to_vertical_string
from google.cloud import storage
import logging
import base64


@pytest.fixture(scope='session', autouse=True)
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

    # storage_client = storage.Client(os.environ['storage_project'])
    # storage_client.create_bucket(os.environ['storage_bucket'])

    yield client

    # teardown
    # bucket = storage_client.get_bucket(os.environ['storage_bucket'])
    # bucket.delete(force=True)


def test_image_404(client):
    rv = client.get('/')
    assert rv.status_code == 404


def test_image_1lineText_right(client):
    testimgstr = base64.b64encode(
        open('./test_main_001.png', 'rb').read()).decode('utf-8')
    rv = client.post('/', json={
        'text': 'サンプル',
        'textposition': 'right',
        'textcolor': '#FFF000',
        'bgcolor': '#000FFF',
        'textsize': 22,
        'baseimagename': 'sample.png',
        'baseimage': testimgstr,
    })

    # TODO 画像判定
    assert rv.is_json == True
    assert 'url' in rv.get_json()

def test_2lineText_right(client):
    testimgstr = base64.b64encode(
        open('./test_main_001.png', 'rb').read()).decode('utf-8')
    rv = client.post('/', json={
        'text': 'サンプル\nですよ',
        'textposition': 'right',
        'textcolor': '#FFF000',
        'bgcolor': '#000FFF',
        'textsize': 22,
        'baseimagename': 'sample.png',
        'baseimage': testimgstr,
    })

    # TODO 画像判定

    assert rv.is_json == True
    assert 'url' in rv.get_json()

def test_image_1lineText_left(client):
    testimgstr = base64.b64encode(
        open('./test_main_001.png', 'rb').read()).decode('utf-8')
    rv = client.post('/', json={
        'text': 'サンプル',
        'textposition': 'left',
        'textcolor': '#FFF000',
        'bgcolor': '#000FFF',
        'textsize': 22,
        'baseimagename': 'sample.png',
        'baseimage': testimgstr,
    })

    # TODO 画像判定

    assert rv.is_json == True
    assert 'url' in rv.get_json()


def test_image_2lineText_left(client):
    testimgstr = base64.b64encode(
        open('./test_main_001.png', 'rb').read()).decode('utf-8')
    rv = client.post('/', json={
        'text': 'サンプル\nですよ',
        'textposition': 'left',
        'textcolor': '#FFF000',
        'bgcolor': '#000FFF',
        'textsize': 22,
        'baseimagename': 'sample.png',
        'baseimage': testimgstr,
    })

    # TODO 画像判定

    assert rv.is_json == True
    assert 'url' in rv.get_json()


def test_image_1lineText_top(client):
    testimgstr = base64.b64encode(
        open('./test_main_001.png', 'rb').read()).decode('utf-8')
    rv = client.post('/', json={
        'text': 'サンプル',
        'textposition': 'top',
        'textcolor': '#FFF000',
        'bgcolor': '#000FFF',
        'textsize': 22,
        'baseimagename': 'sample.png',
        'baseimage': testimgstr,
    })

    # TODO 画像判定

    assert rv.is_json == True
    assert 'url' in rv.get_json()


def test_image_2lineText_top(client):
    testimgstr = base64.b64encode(
        open('./test_main_001.png', 'rb').read()).decode('utf-8')
    rv = client.post('/', json={
        'text': 'サンプル\nですよ',
        'textposition': 'top',
        'textcolor': '#FFF000',
        'bgcolor': '#000FFF',
        'textsize': 22,
        'baseimagename': 'sample.png',
        'baseimage': testimgstr,
    })

    # TODO 画像判定

    assert rv.is_json == True
    assert 'url' in rv.get_json()


def test_image_1lineText_bottom(client):
    testimgstr = base64.b64encode(
        open('./test_main_001.png', 'rb').read()).decode('utf-8')
    rv = client.post('/', json={
        'text': 'サンプル',
        'textposition': 'bottom',
        'textcolor': '#FFF000',
        'bgcolor': '#000FFF',
        'textsize': 22,
        'baseimagename': 'sample.png',
        'baseimage': testimgstr,
    })

    # TODO 画像判定

    assert rv.is_json == True
    assert 'url' in rv.get_json()


def test_image_2lineText_bottom(client):
    testimgstr = base64.b64encode(
        open('./test_main_001.png', 'rb').read()).decode('utf-8')
    rv = client.post('/', json={
        'text': 'サンプル\nですよ',
        'textposition': 'bottom',
        'textcolor': '#FFF000',
        'bgcolor': '#000FFF',
        'textsize': 22,
        'baseimagename': 'sample.png',
        'baseimage': testimgstr,
    })

    # TODO 画像判定

    assert rv.is_json == True
    assert 'url' in rv.get_json()


def test_image_400(client):
    testimgstr = base64.b64encode(
        open('./test_main_001.png', 'rb').read()).decode('utf-8')
    rv = client.post('/', json={
        # 'text': 'サンプル',
        'textposition': 'right',
        'textcolor': '#FFF000',
        'bgcolor': '#000FFF',
        'textsize': 22,
        'baseimagename': 'sample.png',
        'baseimage': testimgstr,
    })

    assert rv.status_code == 400
    assert b'\'text\' is a required property' in rv.data

    rv = client.post('/', json={
        'text': 1,
        'textposition': 'right',
        'textcolor': '#FFF000',
        'bgcolor': '#000FFF',
        'textsize': 22,
        'baseimagename': 'sample.png',
        'baseimage': testimgstr,
    })

    assert rv.status_code == 400
    assert b'1 is not of type \'string\'' in rv.data

    rv = client.post('/', json={
        'text': 'サンプル',
        # 'textposition': 'right',
        'textcolor': '#FFF000',
        'bgcolor': '#000FFF',
        'textsize': 22,
        'baseimagename': 'sample.png',
        'baseimage': testimgstr,
    })

    assert rv.status_code == 400
    assert b'\'textposition\' is a required property' in rv.data

    rv = client.post('/', json={
        'text': 'サンプル',
        'textposition': 'center',
        'textcolor': '#FFF000',
        'bgcolor': '#000FFF',
        'textsize': 22,
        'baseimagename': 'sample.png',
        'baseimage': testimgstr,
    })

    assert rv.status_code == 400
    assert b'\'center\' does not match \'^(right|left|top|bottom)$\'' in rv.data

    rv = client.post('/', json={
        'text': 'サンプル',
        'textposition': 'right',
        # 'textcolor': '#FFF000',
        'bgcolor': '#000FFF',
        'textsize': 22,
        'baseimagename': 'sample.png',
        'baseimage': testimgstr,
    })

    assert rv.status_code == 400
    assert b'\'textcolor\' is a required property' in rv.data

    rv = client.post('/', json={
        'text': 'サンプル',
        'textposition': 'right',
        'textcolor': '#FFF00',
        'bgcolor': '#000FFF',
        'textsize': 22,
        'baseimagename': 'sample.png',
        'baseimage': testimgstr,
    })

    assert rv.status_code == 400
    assert b'\'#FFF00\' does not match \'^#[A-F0-9]{6}\'' in rv.data

    rv = client.post('/', json={
        'text': 'サンプル',
        'textposition': 'right',
        'textcolor': '#FFF000',
        # 'bgcolor': '#000FFF',
        'textsize': 22,
        'baseimagename': 'sample.png',
        'baseimage': testimgstr,
    })

    assert rv.status_code == 400
    assert b'\'bgcolor\' is a required property' in rv.data

    rv = client.post('/', json={
        'text': 'サンプル',
        'textposition': 'right',
        'textcolor': '#FFF000',
        'bgcolor': '#000FF',
        'textsize': 22,
        'baseimagename': 'sample.png',
        'baseimage': testimgstr,
    })

    assert rv.status_code == 400
    assert b'\'#000FF\' does not match \'^#[A-F0-9]{6}\'' in rv.data


    rv = client.post('/', json={
        'text': 'サンプル',
        'textposition': 'right',
        'textcolor': '#FFF000',
        'bgcolor': '#000FFF',
        # 'textsize': 22,
        'baseimagename': 'sample.png',
        'baseimage': testimgstr,
    })

    assert rv.status_code == 400
    assert b'\'textsize\' is a required property' in rv.data

    rv = client.post('/', json={
        'text': 'サンプル',
        'textposition': 'right',
        'textcolor': '#FFF000',
        'bgcolor': '#000FFF',
        'textsize': 22,
        # 'baseimagename': 'sample.png',
        'baseimage': testimgstr,
    })

    assert rv.status_code == 400
    assert b'\'baseimagename\' is a required property' in rv.data

    rv = client.post('/', json={
        'text': 'サンプル',
        'textposition': 'right',
        'textcolor': '#FFF000',
        'bgcolor': '#000FFF',
        'textsize': 22,
        'baseimagename': 'sample.png',
        # 'baseimage': testimgstr,
    })

    assert rv.status_code == 400
    assert b'\'baseimage\' is a required property' in rv.data



def test_convert_to_vertical_string(client):
    lines = convert_to_vertical_string("あいうえお")
    assert ["あ\nい\nう\nえ\nお"] == lines

    lines = convert_to_vertical_string("あいうえお\nかきくけこ")
    assert ["あ\nい\nう\nえ\nお", "か\nき\nく\nけ\nこ"] == lines
