#!/usr/bin/env python3
import os
import json
import glob
import shutil
import logging

import yaml
import coloredlogs
import pandas as pd
from flask import Flask, render_template, jsonify, request, send_file
from click import get_current_context

from .loaders import DATASET_CLASSES
from .processing.processing import get_pipeline_class_by_name


TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


app = Flask("tabgenie", template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR)

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

    return {"out": str(out)}


@app.route("/table", methods=["GET", "POST"])
def render_table():
    dataset_name = request.args.get("dataset")
    split = request.args.get("split")
    table_idx = int(request.args.get("table_idx"))
    table_data = get_table_data(dataset_name, split, table_idx)
    return table_data


@app.route("/export_to_file", methods=["GET", "POST"])
def export_to_file():
    content = request.json
    export_option = content["export_option"]
    export_format = content["export_format"]
    export_examples = json.loads(content["export_examples"])
    # TODO export edited cells
    # edited_cells = json.loads(content.get("edited_cells") or {})

    export_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir, "tmp")

    if os.path.isdir(export_dir):
        shutil.rmtree(export_dir)

    default_template = "export/json_templates/default.yml"

    os.makedirs(os.path.join(export_dir, "files"))
    file_to_download = export_examples_to_file(
        export_examples,
        export_dir=os.path.join(export_dir, "files"),
        export_format=export_format,
        json_template=default_template,
    )

    if export_option == "favourites":
        file_to_download = os.path.join(export_dir, "export.zip")
        shutil.make_archive(file_to_download.rstrip(".zip"), "zip", os.path.join(export_dir, "files"))

    logger.info("Sending file")
    return send_file(file_to_download, mimetype="text/plain", as_attachment=True)


def export_examples_to_file(examples_to_export, export_format, export_dir, export_filename=None, json_template=None):

    if type(examples_to_export) is dict:
        # TODO look at this in more detail, favourites behaves differently
        examples_to_export = examples_to_export.values()

    pipeline_args = {
        "examples_to_export": examples_to_export,
        "export_format": export_format,
        "json_template": json_template,
        "dataset_objs": {
            dataset_name: get_dataset(dataset_name, split)
            for dataset_name, split in map(lambda x: (x["dataset"], x["split"]), examples_to_export)
        },
    }
    os.makedirs(export_dir, exist_ok=True)
    exported = run_pipeline("export", pipeline_args=pipeline_args, force=True)

    if export_format == "json":
        # only a single, aggregated output
        out_filename = export_filename or "out.json"

        with open(os.path.join(export_dir, out_filename), "w") as f:
            json.dump(exported, f, indent=4, ensure_ascii=False)
    else:
        # multiple outputs
        for e, exported_table in zip(examples_to_export, exported):
            out_filename = f"{e['dataset']}_{e['split']}_tab_{e['table_idx']}.{export_format}"

            if export_format == "xlsx":
                write_path = os.path.join(export_dir, out_filename)
                header = exported_table.columns.to_frame(index=False).T  # for hierarchical tables
                table_wo_header = exported_table.set_axis(range(exported_table.shape[1]), axis=1)

                with pd.ExcelWriter(write_path) as writer:
                    header.to_excel(writer, header=False, index=False)
                    table_wo_header.to_excel(writer, header=False, index=False, startrow=header.shape[0])

            else:
                with open(os.path.join(export_dir, out_filename), "w") as f:
                    f.write(exported_table)

    return os.path.join(export_dir, out_filename)


def export_dataset(dataset_name, split, out_dir, export_format, json_template=None):
    dataset = get_dataset(dataset_name, split)

    examples_to_export = [
        {"dataset": dataset_name, "split": split, "table_idx": table_idx}
        for table_idx in range(dataset.get_example_count(split))
    ]

    # only relevant for JSON
    export_filename = f"{split}.json"

    export_examples_to_file(
        examples_to_export,
        export_format=export_format,
        export_dir=out_dir,
        export_filename=export_filename,
        json_template=json_template,
    )

    logger.info("Export finished")


def initialize_dataset(dataset_name):
    # dataset_path = app.config["dataset_paths"][dataset_name]
    dataset_path = None  # not needed for HF
    dataset = DATASET_CLASSES[dataset_name](path=dataset_path)
    app.config["datasets_obj"][dataset_name] = dataset

    return dataset


def initialize_pipeline(pipeline_name):
    pipeline_cfg = app.config["pipelines"][pipeline_name]

    with app.app_context():
        if "config_template_file" in pipeline_cfg:
            # TODO make the prompts less hard-coded
            template = render_template(
                pipeline_cfg["config_template_file"],
                pipeline_name=pipeline_name,
                cfg=pipeline_cfg,
                prompts=app.config["prompts"],
            )
            pipeline_cfg["config_template"] = template

    pipeline_obj = get_pipeline_class_by_name(pipeline_cfg["class"])(name=pipeline_name, cfg=pipeline_cfg)
    app.config["pipelines_obj"][pipeline_name] = pipeline_obj

    return pipeline_obj


def run_pipeline(pipeline_name, pipeline_args, cache_only=False, force=False):
    pipeline = app.config["pipelines_obj"].get(pipeline_name)
    pipeline_args["pipeline_cfg"] = app.config["pipelines"][pipeline_name]

    if pipeline_args.get("dataset") and pipeline_args.get("split"):
        dataset_obj = get_dataset(dataset_name=pipeline_args["dataset"], split=pipeline_args["split"])
        pipeline_args["dataset_obj"] = dataset_obj

    out = pipeline.run(pipeline_args, cache_only=cache_only, force=force)

    return out


def get_dataset(dataset_name, split):
    dataset = app.config["datasets_obj"].get(dataset_name)
    max_examples = app.config.get("max_examples_per_split", None)
    if max_examples is not None and max_examples < 1:
        max_examples = None

    if not dataset:
        logger.info(f"Initializing {dataset_name}")
        dataset = initialize_dataset(dataset_name)

    if not dataset.has_split(split):
        logger.info(f"Loading {dataset_name} / {split}")
        dataset.load(split=split, max_examples=max_examples)

        for name in app.config["generated_outputs"]:
            dataset.load_outputs(split=split, name=name)

    return dataset


def get_table_data(dataset_name, split, table_idx):
    dataset = get_dataset(dataset_name=dataset_name, split=split)
    table = dataset.get_table(split=split, table_idx=table_idx)
    html = dataset.export_table(table=table, export_format="html")
    generated_outputs = dataset.get_generated_outputs(table=table)
    dataset_info = dataset.get_info()

    return {
        "html": html,
        "total_examples": dataset.get_example_count(split),
        "dataset_info": dataset_info,
        "generated_outputs": generated_outputs,
    }


def load_prompts():
    prompts_dir = os.path.join(TEMPLATES_DIR, "prompts")
    prompts = {}

    for file in glob.glob(prompts_dir + "/" + "*.prompt"):
        prompt_name = os.path.splitext(os.path.basename(file))[0]

        with open(file) as f:
            prompt = f.read()

        prompts[prompt_name] = prompt

    return prompts


def filter_dummy_pipelines(pipelines):
    return dict(
        (pipeline_name, pipeline_cfg)
        for pipeline_name, pipeline_cfg in app.config["pipelines"].items()  # TODO: should it be `pipelines`?
        if "dummy" not in pipeline_cfg
    )


@app.route("/", methods=["GET", "POST"])
def index():
    logger.info(f"Page loaded")

    return render_template(
        "index.html",
        datasets=app.config["datasets"],
        pipelines=filter_dummy_pipelines(app.config["pipelines"]),
        generated_outputs=app.config["generated_outputs"],
        prompts=app.config["prompts"],
        default_dataset=app.config["default_dataset"],
        host_prefix=app.config["host_prefix"],
    )


def create_app(**kwargs):
    ctx = get_current_context(silent=True)
    if ctx:
        disable_pipelines = ctx.obj.disable_pipelines
    else:
        # Production server, e.g., gunincorn
        # We don't have access to the current context, so must read kwargs instead.
        disable_pipelines = kwargs.get('disable_pipelines', False)

    with open("config.yml") as f:
        config = yaml.safe_load(f)

    app.config.update(config)
    app.config["datasets_obj"] = {}
    app.config["pipelines_obj"] = {}
    app.config["prompts"] = load_prompts()

    if app.config.get("pipelines") and not disable_pipelines:
        for pipeline_name in app.config["pipelines"].keys():
            initialize_pipeline(pipeline_name)
    else:
        app.config["pipelines"] = {}

    # preload
    if config["cache_dev_splits"]:
        for dataset_name in app.config["datasets"]:
            get_dataset(dataset_name, "dev")

    if config["debug"] is False:
        logging.getLogger("werkzeug").disabled = True

    logger.info("Application ready")

    return app
