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


@app.route("/pipeline", methods=["GET", "POST"])
def get_pipeline_output():
    content = request.json
    logger.info(f"Incoming content: {content}")

    if content.get("edited_cells"):
        content["edited_cells"] = json.loads(content["edited_cells"])

    pipeline_name = content["pipeline"]
    out = run_pipeline(pipeline_name, pipeline_args=content, force=bool(content["edited_cells"]))

    return {"out": str(out), "session": get_session()}


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
    displayed_props = json.loads(request.args.get("displayed_props"))
    table_data = get_table_data(dataset_name, split, table_idx, displayed_props)

    return jsonify(table_data)


def export_error_analysis(dataset_name, split, in_file, out_file, count, random_seed):
    dataset_obj = get_dataset(dataset_name, split)
    predictions = []

    with open(in_file) as f:
        for line in f.readlines():
            j = json.loads(line)
            predictions.append(j["out"][0])

    random.seed(random_seed)
    selected_example_ids = random.sample(range(len(predictions)), count)

    assert len(predictions) == dataset_obj.get_example_count(split)
    tables = []

    for example_id in selected_example_ids:
        table_obj = dataset_obj.get_table(split, example_id)
        table = {
            "table": table_obj,
            "table_id": example_id,
            "reference": table_obj.props.get("reference", ""),
            "prediction": predictions[example_id],
        }
        tables.append(table)

    prop_list = ["reference", "prediction"]
    ann_columns = ["notes"]
    write_annotation_to_excel(tables, prop_list, ann_columns, out_file)

    logger.info(f"Exported spreasheet for error analysis to {out_file}")


@app.route("/export_to_file", methods=["GET", "POST"])
def export_to_file():
    content = request.json
    export_option = content["export_option"]
    export_format = content["export_format"]
    linearization_style = content["linearization_style"]
    include_props = content["include_props"]
    export_examples = json.loads(content["export_examples"])
    edited_cells = json.loads(content.get("edited_cells", "{}"))
    export_notes = content["export_notes"]

    export_dir = os.path.join(app.config["root_dir"], "tmp")

    if os.path.isdir(export_dir):
        shutil.rmtree(export_dir)

    os.makedirs(os.path.join(export_dir, "files"))

    notes = session.get("notes", {})
    logging.warning(f"{export_examples=}  {notes=}")
    file_to_download = export_examples_to_file(
        export_examples,
        export_dir=os.path.join(export_dir, "files"),
        export_format=export_format,
        linearization_style=linearization_style,
        include_props=include_props,
        edited_cells=edited_cells,
        notes=session.get("notes", {}),
    )
    if export_notes is True:
        export_notes_to_file(notes, export_dir=os.path.join(export_dir, "files"))

    if export_option in ["favourites", "notes"]:
        file_to_download = os.path.join(export_dir, "export.zip")
        shutil.make_archive(file_to_download.rsplit(".", 1)[0], "zip", os.path.join(export_dir, "files"))

    logger.info("Sending file")
    return send_file(file_to_download, mimetype="text/plain", as_attachment=True)


def export_notes_to_file(notes, export_dir):
    csv_data = []
    headers = ["dataset", "split", "table_idx", "note"]
    csv_data.append(headers)

    for note in notes.values():
        csv_data.append([note["dataset"], note["split"], note["table_idx"], note["note"]])

    df = pd.DataFrame(csv_data[1:], columns=csv_data[0])
    csv_file = os.path.join(export_dir, "notes.csv")

    df.to_csv(csv_file, index=False)


def export_examples_to_file(
    examples_to_export, export_format, linearization_style, export_dir, include_props, edited_cells, notes=None
):
    if type(examples_to_export) is dict:
        # favourites / notes
        examples_to_export = examples_to_export.values()

    pipeline_args = {
        "examples_to_export": examples_to_export,
        "export_format": export_format,
        "linearization_style": linearization_style,
        "include_props": include_props,
        "edited_cells": edited_cells,
        "dataset_objs": {
            dataset_name: get_dataset(dataset_name, split)
            for dataset_name, split in map(lambda x: (x["dataset"], x["split"]), examples_to_export)
        },
    }
    os.makedirs(export_dir, exist_ok=True)
    exported = run_pipeline("export", pipeline_args=pipeline_args, force=True)

    # ZK: commented this block out for now
    # for now, the notes can be exported in a ZIP file alongside other files

    # ========================
    # notes = notes if notes is not None else {}

    # tables = []
    # for e, exported_table in zip(examples_to_export, exported):
    #     # See get_note_id in JS
    #     table_id = f"{e['dataset']}-{e['split']}-{e['table_idx']}"
    #     note = notes.get(table_id, {"note": ""})["note"]
    #     # TODO make sure that export pipeline does NOT allow changing original table
    #     # adding notes to the table
    #     tables.append({"table": exported_table, "table_id": table_id, "reference": exported_table.props.get("reference", ""), "Tabgenie-Notes": note})

    # # TODO infer from highligheted properties in JS
    # # and add the tabgenie notes added to properties
    # prop_list = ["reference"] + ["Tabgenie-Notes"]
    # ann_columns = ["notes"]  # able to specify in JS columns? Is it necessary?
    # write_annotation_to_excel(tables, prop_list, ann_columns, os.path.join(export_dir, out_filename))
    # ========================

    for e, exported_table in zip(examples_to_export, exported):
        out_filename = f"{e['dataset']}_{e['split']}_tab_{e['table_idx']}.{export_format}"
        write_exported_table_to_file(exported_table, export_format, export_dir, out_filename)

    return os.path.join(export_dir, out_filename)


def write_exported_table_to_file(exported_table, export_format, export_dir, out_filename):
    if export_format == "xlsx":
        exported_table.filename = os.path.join(export_dir, out_filename)
        exported_table.close()
    elif export_format == "json":
        with open(os.path.join(export_dir, out_filename), "w") as f:
            json.dump(exported_table, f)
    else:
        with open(os.path.join(export_dir, out_filename), "w") as f:
            f.write(exported_table)


def export_dataset(dataset_name, split, out_dir, export_format, linearization_style, include_props, table_ids):
    dataset = get_dataset(dataset_name, split)
    example_ids = table_ids or range(dataset.get_example_count(split))

    examples_to_export = [
        {"dataset": dataset_name, "split": split, "table_idx": table_idx} for table_idx in example_ids
    ]

    export_examples_to_file(
        examples_to_export,
        export_format=export_format,
        export_dir=out_dir,
        linearization_style=linearization_style,
        # export_filename=export_filename,
        include_props=include_props,
        edited_cells={},
    )

    logger.info("Export finished")


def initialize_dataset(dataset_name):
    dataset = DATASET_CLASSES[dataset_name]()
    app.db["datasets_obj"][dataset_name] = dataset

    return dataset


def load_config_template(pipeline_name, pipeline_cfg):
    if "config_template_file" in pipeline_cfg:
        with app.app_context():
            template = render_template(
                pipeline_cfg["config_template_file"],
                pipeline_name=pipeline_name,
                cfg=pipeline_cfg,
                prompts=app.db["prompts"],
            )
        app.db["cfg_templates"][pipeline_name] = template


def initialize_pipeline(pipeline_name):
    pipeline_cfg = app.db["pipelines_cfg"][pipeline_name]
    load_config_template(pipeline_name, pipeline_cfg)
    pipeline_cls = get_pipeline_class_by_name(pipeline_cfg["pipeline"])
    app.db["pipelines_obj"][pipeline_name] = pipeline_cls(name=pipeline_name, cfg=pipeline_cfg)


def run_pipeline(pipeline_name, pipeline_args, cache_only=False, force=False):
    pipeline = app.db["pipelines_obj"].get(pipeline_name)
    pipeline_args["pipeline_cfg"] = app.db["pipelines_cfg"][pipeline_name]

    if pipeline_args.get("dataset") and pipeline_args.get("split"):
        dataset_obj = get_dataset(dataset_name=pipeline_args["dataset"], split=pipeline_args["split"])
        pipeline_args["dataset_obj"] = dataset_obj

    out = pipeline.run(pipeline_args, cache_only=cache_only, force=force)

    return out


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


def get_generated_outputs(dataset_name, split, output_idx):
    outputs = {}

    out_dir = os.path.join(app.config["root_dir"], app.config["generated_outputs_dir"], dataset_name, split)
    if not os.path.isdir(out_dir):
        return outputs

    for filename in glob.glob(out_dir + "/" + "*.jsonl"):
        line = linecache.getline(filename, output_idx + 1)  # 1-based indexing
        j = json.loads(line)
        model_name = os.path.basename(filename).rsplit(".", 1)[0]
        outputs[model_name] = j

    return outputs


def get_table_data(dataset_name, split, table_idx, displayed_props):
    dataset = get_dataset(dataset_name=dataset_name, split=split)
    table = dataset.get_table(split=split, table_idx=table_idx)
    html = dataset.export_table(table=table, export_format="html", displayed_props=displayed_props)
    generated_outputs = get_generated_outputs(dataset_name=dataset_name, split=split, output_idx=table_idx)
    dataset_info = dataset.get_info()

    return {
        "html": html,
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

    print(yaml.dump(info_yaml, sort_keys=False))


def load_prompts():
    prompts_dir = os.path.join(TEMPLATES_DIR, "prompts")
    prompts = {}

    for file in glob.glob(prompts_dir + "/" + "*.prompt"):
        prompt_name = os.path.splitext(os.path.basename(file))[0]

        with open(file) as f:
            prompt = f.read()

        prompts[prompt_name] = prompt

    return prompts


@app.route("/note", methods=["GET", "POST"])
def note():
    content = request.json
    action = content.get("action", "edit_note")
    dataset = content.get("dataset")
    split = content.get("split")
    table_idx = content.get("table_idx")
    note = content.get("note", "")

    notes = session.get("notes", {})

    if action == "remove_all":
        notes = {}
    else:
        assert action == "edit_note"
        note_id = f"{dataset}-{split}-{table_idx}"
        if len(note) == 0 and note_id in notes:
            notes.pop(note_id)
        else:
            notes[note_id] = {"dataset": dataset, "split": split, "table_idx": table_idx, "note": note}

    session["notes"] = notes
    # Important. See https://tedboy.github.io/flask/interface_api.session.html#flask.session.modified
    session.modified = True

    logging.info(f"/note \n\t{content=}\n\t{get_session()}")
    return jsonify(notes)


@app.route("/favourite", methods=["GET", "POST"])
def favourite():
    content = request.json
    dataset = content.get("dataset")
    split = content.get("split")
    table_idx = content.get("table_idx")
    action = content.get("action", "get_all")
    if action in ["remove", "insert"]:
        assert dataset and split and isinstance(table_idx, int), (dataset, split, table_idx)
        favourite_id = f"{dataset}-{split}-{table_idx}"
    favourites = session.get("favourites", {})
    if action == "remove":
        favourite = favourites.pop(favourite_id, None)
        logging.info(f"Removed {favourite}")
    elif action == "insert":
        favourites[favourite_id] = {"dataset": dataset, "split": split, "table_idx": table_idx}
    elif action == "remove_all":
        favourites = {}
    else:
        assert action == "get_all"

    session["favourites"] = favourites
    # Important. See https://tedboy.github.io/flask/interface_api.session.html#flask.session.modified
    session.modified = True

    logging.info(f"favourite\n\t{content=}\n\t{get_session()}")
    return jsonify(favourites)


@app.route("/", methods=["GET", "POST"])
def index():
    logger.info(f"Page loaded")

    return render_template(
        "index.html",
        datasets=app.config["datasets"],
        pipelines=app.db["pipelines_cfg"],
        pipelines_cfg_templates=app.db["cfg_templates"],
        prompts=app.db["prompts"],
        default_dataset=app.config["default_dataset"],
        host_prefix=app.config["host_prefix"],
    )
