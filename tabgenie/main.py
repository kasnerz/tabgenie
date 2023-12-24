#!/usr/bin/env python3
import os
import json
import glob
import shutil
import logging
import linecache
import pandas as pd
import random
import coloredlogs
import yaml
import traceback
from flask import Flask, render_template, jsonify, request, send_file, session
from collections import defaultdict
from .loaders import DATASET_CLASSES
from pathlib import Path


TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
ANNOTATIONS_DIR = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, "annotations")
SETUP_DIR = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, "setups")

app = Flask("tabgenie", template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR)
app.config.update(SECRET_KEY=os.urandom(24))
app.db = {}
app.db["cfg_templates"] = {}
app.db["annotation_index"] = {}

file_handler = logging.FileHandler("error.log")
file_handler.setLevel(logging.ERROR)

logging.basicConfig(
    format="%(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[file_handler, logging.StreamHandler()],
)
logger = logging.getLogger(__name__)
coloredlogs.install(level="INFO", logger=logger, fmt="%(asctime)s %(levelname)s %(message)s")


def success():
    resp = jsonify(success=True)
    return resp

@app.route('/save_annotations', methods=['POST'])
def save_annotations():
    data = request.get_json()
    annotations = data['annotations']

    with open(os.path.join(ANNOTATIONS_DIR, "annotations.jsonl"), "w") as f:
        for row in annotations:
            f.write(json.dumps(row) + "\n")

    return jsonify({'status': 'success'})


def get_session():
    """Retrieve session with default values and serializable"""
    s = {}
    s["favourites"] = session.get("favourites", {})
    s["notes"] = session.get("notes", {})
    return s


@app.route("/table", methods=["GET", "POST"])
def render_table():
    dataset_name = request.args.get("dataset")
    split = request.args.get("split")
    table_idx = int(request.args.get("table_idx"))
    # displayed_props = json.loads(request.args.get("displayed_props"))

    try:
        table_data = get_table_data(dataset_name, split, table_idx)
    except Exception as e:
        traceback.print_exc()
        logger.error(f"Error while getting table data: {e}")
        table_data = {}

    return jsonify(table_data)



def initialize_dataset(dataset_name):
    dataset = DATASET_CLASSES[dataset_name]()
    app.db["datasets_obj"][dataset_name] = dataset

    return dataset



def get_dataset(dataset_name, split):
    dataset = app.db["datasets_obj"].get(dataset_name)
    max_examples = app.config.get("max_examples_per_split", None)
    if max_examples is not None and max_examples < 1:
        max_examples = None

    if not dataset:
        logger.info(f"Initializing {dataset_name}")
        dataset = initialize_dataset(dataset_name)

    if not dataset.has_split(split):
        logger.info(f"Loading {dataset_name} / {split}")
        dataset.load(split=split, max_examples=max_examples)
        # dataset.load_generated_outputs(split=split)

    return dataset

def generate_annotation_index():
    with open(os.path.join(ANNOTATIONS_DIR, "annotations.jsonl"), "r") as f:
        annotations = [json.loads(line) for line in f.readlines()]

    app.db["annotation_index"] = defaultdict(list)

    for annotation in annotations:
        dataset_name = annotation["dataset"]
        split = annotation["split"]
        table_idx = annotation["table_idx"]
        app.db["annotation_index"][(dataset_name, split, table_idx)].append(annotation)

def get_annotations(dataset_name, split, table_idx):
    return app.db["annotation_index"].get((dataset_name, split, table_idx), [])


def get_table_data(dataset_name, split, table_idx):
    dataset = get_dataset(dataset_name=dataset_name, split=split)
    table = dataset.get_table(split=split, table_idx=table_idx)
    html = dataset.render(table=table)
    generated_outputs = dataset.get_generated_outputs(split=split, output_idx=table_idx)
    annotations = get_annotations(dataset_name, split, table_idx)
    dataset_info = dataset.get_info()

    return {
        "html": html,
        "raw_data" : table,
        "total_examples": dataset.get_example_count(split),
        "dataset_info": dataset_info,
        "generated_outputs": generated_outputs,
        "annotations": annotations,
        "session": get_session(),
    }


def get_dataset_info(dataset_name):

    if dataset_name is None:
        print("========================================")
        print("               TabGenie                ")
        print("========================================")
        datasets = app.config["datasets"]

        print("Available datasets:")

        for dataset in datasets:
            print(f"- {dataset}")

        print("========================================")
        print("For more information about the dataset, type `tabgenie info -d <dataset_name>`")
        return

    dataset = get_dataset(dataset_name=dataset_name, split="dev")

    info = dataset.get_info()

    info_yaml = {
        "dataset": dataset.name,
        "description": info["description"].replace("\n", ""),
        "examples": info["examples"],
        "version": info["version"],
        "license": info["license"],
        "citation": info["citation"].replace("\n", ""),
    }

    if "changes":
        info_yaml["changes"] = info["changes"]

    print(yaml.dump(info_yaml, sort_keys=False))


@app.route("/submit_annotations", methods=["POST"])
def submit_annotations():
    logger.info(f"Received annotations")
    data = request.get_json()

    with open("annotations.jsonl", "w") as f:
        for row in data:
            f.write(json.dumps(row) + "\n")
    
    return jsonify({"status": "success"})



@app.route("/annotate", methods=["GET", "POST"])
def annotate():
    logger.info(f"Annotate page loaded")

    models = ["mistral-7b-instruct", "zephyr-7b-beta", "llama2-7b-32k"]
    dataset = ["openweather", "basketball", "gsmarena", "wikidata", "owid"]

    random.seed(42)
    # annotation_set = [
    #     { "dataset": random.choice(dataset),
    #      "model": random.choice(models), 
    #      "split": "dev", 
    #      "setup" : "direct", 
    #      "table_idx": random.randint(0,99) } 
    #      for _ in range(10)
    # ]
    annotation_set = [
        { "dataset": "basketball",
         "model": models[i], 
         "split": "dev", 
         "setup" : "direct", 
         "table_idx": 0 } 
         for i in range(3)
    ]

    return render_template(
        "annotate.html",
        datasets=app.config["datasets"],
        host_prefix=app.config["host_prefix"],
        annotation_set=annotation_set,
    )


@app.route("/", methods=["GET", "POST"])
def index():
    logger.info(f"Page loaded")

    generate_annotation_index()

    dataset_name = request.args.get("dataset")
    split = request.args.get("split")
    table_idx = request.args.get("table_idx")
    setup_names = [x.stem for x in Path(SETUP_DIR).glob("*.yaml")]

    # load the yamls, create a dict
    setups = {}
    for setup_name in setup_names:
        with open(os.path.join(SETUP_DIR, f"{setup_name}.yaml"), "r") as f:
            setups[setup_name] = yaml.safe_load(f)

    if (
        dataset_name
        and split
        and table_idx
        and dataset_name in app.config["datasets"]
        and split in ["train", "dev", "test"]
        and table_idx.isdigit()
    ):
        display_table = {"dataset": dataset_name, "split": split, "table_idx": int(table_idx)}
        default_dataset = display_table["dataset"]
        logger.info(f"Serving permalink for {display_table}")
    else:
        default_dataset = app.config["default_dataset"]
        display_table = None

    return render_template(
        "index.html",
        datasets=app.config["datasets"],
        default_dataset=default_dataset,
        host_prefix=app.config["host_prefix"],
        display_table=display_table,
        setups=setups
    )
