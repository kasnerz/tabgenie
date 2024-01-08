#!/usr/bin/env python3
import os
import json
import glob
import shutil
import logging
import linecache
import pandas as pd
import random
import time
import coloredlogs
import yaml
import threading
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
app.db["compl_code"] = "CK388WFU"
app.db["lock"] = threading.Lock()


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
    for source in ["gpt-4", "human"]:
        jsonl_files = glob.glob(os.path.join(ANNOTATIONS_DIR, source, "*.jsonl"))

        # contains annotations for each generated output
        annotations = defaultdict(list)

        for jsonl_file in jsonl_files:
            with open(jsonl_file) as f:
                for line in f:
                    annotation = json.loads(line)
                    
                    key = (annotation["dataset"], annotation["split"], annotation["table_idx"], annotation["model"], annotation["setup"])

                    annotations[key].append(annotation)

    app.db["annotation_index"] = annotations
    return annotations


def get_annotations(dataset_name, split, table_idx, model, setup):
    annotation_index = app.db["annotation_index"]
    key = (dataset_name, split, table_idx, model, setup)

    return annotation_index.get(key, [])



def get_table_data(dataset_name, split, table_idx):
    dataset = get_dataset(dataset_name=dataset_name, split=split)
    table = dataset.get_table(split=split, table_idx=table_idx)
    html = dataset.render(table=table)
    generated_outputs = dataset.get_generated_outputs(split=split, output_idx=table_idx)

    for output in generated_outputs:
        model = output["model"]
        setup = output["setup"]["name"]
        annotations = get_annotations(dataset_name, split, table_idx, model, setup)

        output["annotations"] = annotations

    dataset_info = dataset.get_info()
    
    return {
        "html": html,
        "raw_data": table,
        "total_examples": dataset.get_example_count(split),
        "dataset_info": dataset_info,
        "generated_outputs": generated_outputs,
        "session": get_session(),
    }


@app.route("/submit_annotations", methods=["POST"])
def submit_annotations():
    logger.info(f"Received annotations")
    data = request.get_json()
    annotator_id = data[0]["annotator_id"]
    now = int(time.time())

    os.makedirs(os.path.join(ANNOTATIONS_DIR, "human"), exist_ok=True)

    with app.db["lock"]:
        df = pd.read_csv("../annotations/annotations_prolific.csv")

        with open(os.path.join(ANNOTATIONS_DIR, "human", f"{annotator_id}-{now}.jsonl"), "w") as f:
            for row in data:
                f.write(json.dumps(row) + "\n")

                # mark the annotation as finished in the csv
                idx = df[(df["table_idx"] == row["table_idx"])
                ].index[0]

                df.loc[idx, "status"] = "finished"

        df.to_csv("../annotations/annotations_prolific.csv", index=False)
        logger.info(f"Annotations for {row['table_idx']} saved")

    return jsonify({"status": "success"})


def get_annotation_batch(args):
    PROLIFIC_PID = args.get("PROLIFIC_PID", "test")
    SESSION_ID = args.get("SESSION_ID")
    STUDY_ID = args.get("STUDY_ID")

    with app.db["lock"]:
        # load the csv and select 15 non-assigned examples, preferably in a sequential order
        df = pd.read_csv("../annotations/annotations_prolific.csv")
        free_examples = df[df["status"] == "free"]

        annotation_batch = []
        start = int(time.time())
        example = free_examples.sample()
        table_idx = int(example.table_idx.values[0])
        models = ["mistral", "llama2", "zephyr", "gpt-3.5"]

        logger.info(f"Selecting example {table_idx}")

        for dataset in ["ice_hockey", "gsmarena", "openweather", "owid", "wikidata"]:
            random.shuffle(models)
            for model in models:
                annotation_batch.append({
                    "annotator_id": PROLIFIC_PID,
                    "session_id": SESSION_ID,
                    "study_id": STUDY_ID,
                    "start_timestamp": start,
                    "dataset": dataset,
                    "split": "test",
                    "model": model,
                    "setup": "direct",
                    "table_idx": table_idx,
                })
                i = example.index[0]

                # update the CSV
                df.loc[i, "status"] = "assigned"
                df.loc[i, "annotator_id"] = PROLIFIC_PID

        df.to_csv("../annotations/annotations_prolific.csv", index=False)

    return annotation_batch

def get_setup_names():
    return sorted([x.stem for x in Path(SETUP_DIR).glob("*.yaml")])

def generate_annotation_csv():
    # load all outputs
    split = "test"
    records = []

    for table_idx in range(100):
        # for dataset_name in app.config["datasets"]:
            # dataset = get_dataset(dataset_name, split)

        records.append({
                # "dataset_name": dataset_name,
                "table_idx": table_idx,
                "annotator_id": "",
                "status": "free",
            })
            # generated_outputs = dataset.get_generated_outputs(split=split, output_idx=table_idx)

            # # keep only outputs with the "direct" setup
            # generated_outputs = [x for x in generated_outputs if x["setup"]["name"].startswith("direct")]

            # # shuffle the models
            # random.shuffle(generated_outputs)

            # for output in generated_outputs:
            #     if output["generated"] is None:
            #         continue

            #     model = output["model"]
            #     setup = output["setup"]["name"]

            #     records.append({
            #         "dataset_name": dataset_name,
            #         "table_idx": table_idx,
            #         "model": model,
            #         "setup": setup,
            #         "annotator_id": "",
            #         "status": "free",
            #     })

    df = pd.DataFrame.from_records(records)
    df.to_csv("../annotations/annotations_prolific.csv", index=False)


@app.route("/annotate", methods=["GET", "POST"])
def annotate():
    logger.info(f"Annotate page loaded")

    # generate_annotation_csv()

    PROLIFIC_PID = request.args.get("PROLIFIC_PID", "test")
    annotation_set = get_annotation_batch(request.args)

    return render_template(
        "annotate.html",
        datasets=app.config["datasets"],
        host_prefix=app.config["host_prefix"],
        annotation_set=annotation_set,
        annotation_example_cnt=len(annotation_set),
        annotator_id=PROLIFIC_PID,
        compl_code=app.db["compl_code"],
    )


@app.route("/data", methods=["GET", "POST"])
def index():
    logger.info(f"Page loaded")

    generate_annotation_index()

    dataset_name = request.args.get("dataset")
    split = request.args.get("split")
    table_idx = request.args.get("table_idx")
    
    setup_names = get_setup_names()

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
        setups=setups,
    )
