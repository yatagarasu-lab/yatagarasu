#!/bin/bash

# 環境変数の読み込み
export $(cat .env | xargs)

# Flaskアプリを起動
gunicorn run:app --bind 0.0.0.0:$PORT
