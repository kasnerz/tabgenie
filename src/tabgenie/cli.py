#!/usr/bin/env python3
import click
import os
import logging
from flask.cli import FlaskGroup, with_appcontext, pass_script_info


logger = logging.getLogger(__name__)


def create_app(**kwargs):
    import yaml

    with open("config.yml") as f:
        config = yaml.safe_load(f)

    # Imports from main slow down flask CLI
    # since main have very time-consuming libraries to import
    from .main import app, initialize_pipeline, load_prompts

    app.config.update(config)
    app.config["root_dir"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir)

    app.db["datasets_obj"] = {}
    app.db["pipelines_obj"] = {}
    app.db["prompts"] = load_prompts()
    app.db["pipelines_cfg"] = app.config["pipelines"]

    if app.config.get("pipelines"):
        for pipeline_name in app.config["pipelines"].keys():
            initialize_pipeline(pipeline_name)
    else:
        app.db["pipelines_cfg"] = {}

    # preload
    if config["cache_dev_splits"]:
        from .main import get_dataset

        for dataset_name in app.config["datasets"]:
            get_dataset(dataset_name, "dev")

    if config["debug"] is False:
        logging.getLogger("werkzeug").disabled = True

    logger.info("Application ready")

    return app


@click.group(cls=FlaskGroup, create_app=create_app)
@click.option("--disable_pipelines", type=bool, is_flag=True, default=False)
@pass_script_info
def run(script_info, disable_pipelines):
    script_info.disable_pipelines = disable_pipelines


@click.command()
@click.option("--dataset", "-d", required=True, type=str)
@click.option("--split", "-s", default="dev", type=str)
@click.option("--out_dir", "-o", required=True, type=str, help="Path to the output directory")
@click.option(
    "--export_format",
    "-f",
    required=True,
    type=click.Choice(["json", "csv", "xlsx", "html"]),
    help="Output file format",
)
@click.option(
    "--json_template",
    "-t",
    type=str,
    help="Template used for formatting JSON file",
)
@with_appcontext
def export(dataset, split, out_dir, export_format, json_template):
    from .main import export_dataset

    export_dataset(
        dataset_name=dataset,
        split=split,
        out_dir=out_dir,
        export_format=export_format,
        json_template=json_template,
    )
