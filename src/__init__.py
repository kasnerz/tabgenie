#!/usr/bin/env python3

import os
import requests
import json
import logging
import random
from .data import get_dataset_class_by_name

from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO, datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)

def success():
    resp = jsonify(success=True)
    return resp

@app.route('/table', methods=['GET', 'POST'])
def render_table():
    dataset_name = request.args.get('dataset')
    dataset_split = request.args.get('split')
    table_idx = request.args.get('i')
    increment = request.args.get('inc')

    if dataset_name:
        app.config["dataset_name"] = dataset_name

    if dataset_split: 
        app.config["dataset_split"] = dataset_split

    if table_idx:
        app.config["table_idx"] = int(table_idx)

    if increment:
        app.config["table_idx"] += int(increment)

    table = get_table_html()
    return table

    # return render_template('index.html',
    #     dataset=app.config["dataset_name"],
    #     table=table
    # )


@app.route('/', methods=['GET', 'POST'])
def index():
    logger.info(f"Page loaded")
    table = get_table_html()

    return render_template('index.html',
        dataset=app.config["dataset_name"],
        table=table
    )

def load_dataset(dataset_name, split="dev"):
    logger.info(f"Loading {dataset_name}")
    dataset = get_dataset_class_by_name(dataset_name)()
    dataset.load(splits=[split])
    app.config["datasets"][dataset_name] = dataset


def get_dataset(dataset_name):
    return app.config["datasets"].get(dataset_name)


def get_table_html(dataset_name=None, split=None, index=None):
    if not dataset_name:
        dataset_name = app.config["dataset_name"]

    if not split:
        split = app.config["dataset_split"]

    if not index:
        index = app.config["table_idx"]

    dataset = get_dataset(dataset_name)
    html = dataset.get_table_html(split=split, index=index)
    return html


def create_app(*args, **kwargs):
    random.seed(42)

    app.config["datasets"] = {}
    app.config["dataset_name"] = "totto"
    app.config["dataset_split"] = "dev"
    app.config["table_idx"] = 0

    load_dataset(app.config["dataset_name"])

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)