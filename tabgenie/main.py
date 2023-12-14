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
from xlsxwriter import Workbook
from flask import Flask, render_template, jsonify, request, send_file, session

from .loaders import DATASET_CLASSES
from .processing.processing import get_pipeline_class_by_name
from .utils.excel import write_html_table_to_excel, write_annotation_to_excel


TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


app = Flask("tabgenie", template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR)
app.config.update(SECRET_KEY=os.urandom(24))
app.db = {}
app.db["cfg_templates"] = {}

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
    global annotations
    data = request.get_json()
    annotations = data['annotations']
    return jsonify({'status': 'success'})

@app.route('/get_annotations')
def get_annotations():
    global annotations
    return jsonify({'annotations': annotations})


# @app.route("/pipeline", methods=["GET", "POST"])
# def get_pipeline_output():
#     content = request.json
#     logger.info(f"Incoming content: {content}")

#     if content.get("edited_cells"):
#         content["edited_cells"] = json.loads(content["edited_cells"])

#     pipeline_name = content["pipeline"]
#     out = run_pipeline(pipeline_name, pipeline_args=content, force=bool(content["edited_cells"]))

#     return {"out": str(out), "session": get_session()}


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


# def load_config_template(pipeline_name, pipeline_cfg):
#     if "config_template_file" in pipeline_cfg:
#         with app.app_context():
#             template = render_template(
#                 pipeline_cfg["config_template_file"],
#                 pipeline_name=pipeline_name,
#                 cfg=pipeline_cfg,
#                 prompts=app.db["prompts"],
#             )
#         app.db["cfg_templates"][pipeline_name] = template


# def initialize_pipeline(pipeline_name):
#     pipeline_cfg = app.db["pipelines_cfg"][pipeline_name]
#     load_config_template(pipeline_name, pipeline_cfg)
#     pipeline_cls = get_pipeline_class_by_name(pipeline_cfg["pipeline"])
#     app.db["pipelines_obj"][pipeline_name] = pipeline_cls(name=pipeline_name, cfg=pipeline_cfg)


# def run_pipeline(pipeline_name, pipeline_args, cache_only=False, force=False):
#     pipeline = app.db["pipelines_obj"].get(pipeline_name)
#     pipeline_args["pipeline_cfg"] = app.db["pipelines_cfg"][pipeline_name]

#     if pipeline_args.get("dataset") and pipeline_args.get("split"):
#         dataset_obj = get_dataset(dataset_name=pipeline_args["dataset"], split=pipeline_args["split"])
#         pipeline_args["dataset_obj"] = dataset_obj

#     out = pipeline.run(pipeline_args, cache_only=cache_only, force=force)

#     return out


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


def get_table_data(dataset_name, split, table_idx):
    dataset = get_dataset(dataset_name=dataset_name, split=split)
    table = dataset.get_table(split=split, table_idx=table_idx)
    html = dataset.render(table=table)
    generated_outputs = dataset.get_generated_outputs(split=split, output_idx=table_idx)
    dataset_info = dataset.get_info()
    return {
        "html": html,
        "raw_data" : table,
        "total_examples": dataset.get_example_count(split),
        "dataset_info": dataset_info,
        "generated_outputs": generated_outputs,
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


# def load_prompts():
#     prompts_dir = os.path.join(TEMPLATES_DIR, "prompts")
#     prompts = {}

#     for file in glob.glob(prompts_dir + "/" + "*.prompt"):
#         prompt_name = os.path.splitext(os.path.basename(file))[0]

#         with open(file) as f:
#             prompt = f.read()

#         prompts[prompt_name] = prompt

#     return prompts


# @app.route("/note", methods=["GET", "POST"])
# def note():
#     content = request.json
#     action = content.get("action", "edit_note")
#     dataset = content.get("dataset")
#     split = content.get("split")
#     table_idx = content.get("table_idx")
#     note = content.get("note", "")

#     notes = session.get("notes", {})

#     if action == "remove_all":
#         notes = {}
#     else:
#         assert action == "edit_note"
#         note_id = f"{dataset}-{split}-{table_idx}"
#         if len(note) == 0 and note_id in notes:
#             notes.pop(note_id)
#         else:
#             notes[note_id] = {"dataset": dataset, "split": split, "table_idx": table_idx, "note": note}

#     session["notes"] = notes
#     # Important. See https://tedboy.github.io/flask/interface_api.session.html#flask.session.modified
#     session.modified = True

#     logging.info(f"/note \n\t{content=}\n\t{get_session()}")
#     return jsonify(notes)


# @app.route("/favourite", methods=["GET", "POST"])
# def favourite():
#     content = request.json
#     dataset = content.get("dataset")
#     split = content.get("split")
#     table_idx = content.get("table_idx")
#     action = content.get("action", "get_all")
#     if action in ["remove", "insert"]:
#         assert dataset and split and isinstance(table_idx, int), (dataset, split, table_idx)
#         favourite_id = f"{dataset}-{split}-{table_idx}"
#     favourites = session.get("favourites", {})
#     if action == "remove":
#         favourite = favourites.pop(favourite_id, None)
#         logging.info(f"Removed {favourite}")
#     elif action == "insert":
#         favourites[favourite_id] = {"dataset": dataset, "split": split, "table_idx": table_idx}
#     elif action == "remove_all":
#         favourites = {}
#     else:
#         assert action == "get_all"

#     session["favourites"] = favourites
#     # Important. See https://tedboy.github.io/flask/interface_api.session.html#flask.session.modified
#     session.modified = True

#     logging.info(f"favourite\n\t{content=}\n\t{get_session()}")
#     return jsonify(favourites)


# @app.errorhandler(404)
# def page_not_found(error):
    # return render_template("404.html"), 404

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

    models = ["mistral-7b-instruct", "zephyr-7b-beta", "llama2-7b-chat"]
    dataset = ["openweather", "basketball", "gsmarena", "wikidata", "owid"]

    random.seed(42)
    annotation_set = [
        { "dataset": random.choice(dataset),
         "model": random.choice(models), 
         "split": "dev", 
         "task" : "direct", 
         "table_idx": random.randint(0,99) } 
         for _ in range(10)
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

    dataset_name = request.args.get("dataset")
    split = request.args.get("split")
    table_idx = request.args.get("table_idx")
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
        # pipelines=app.db["pipelines_cfg"],
        # pipelines_cfg_templates=app.db["cfg_templates"],
        # prompts=app.db["prompts"],
        default_dataset=default_dataset,
        host_prefix=app.config["host_prefix"],
        display_table=display_table,
        task_names=app.config["task_names"],
    )
