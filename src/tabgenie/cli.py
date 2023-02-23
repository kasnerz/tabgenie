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
    type=click.Choice(["json", "csv", "xlsx", "html", "txt"]),
    help="Output file format",
)
@click.option("--include_props", "-p", type=bool, is_flag=True, default=False, help="Include properties in the output")
@click.option(
    "--table_id",
    "-t",
    multiple=True,
    type=int,
    help="Table ID to export (can be specified multiple times), all tables are exported by default",
)
@with_appcontext
def export(dataset, split, out_dir, export_format, include_props, table_id):
    from .main import export_dataset

    export_dataset(
        dataset_name=dataset,
        split=split,
        out_dir=out_dir,
        export_format=export_format,
        include_props=include_props,
        table_ids=table_id,
    )


@click.command()
@click.option("--dataset", "-d", required=True, type=str)
@click.option("--split", "-s", default="dev", type=str)
@click.option(
    "--in_file",
    "-i",
    default=None,
    type=str,
    help="Path to the file with hypotheses (JSONL format). The field 'output' has to contain a list of hypotheses. Currently only the first hypothesis is used.",
)
@click.option("--out_file", "-o", default=None, type=str, help="Path to the output file")
@click.option(
    "--count",
    "-c",
    type=int,
    help="Number of randomly selected examples for the error analysis",
)
@click.option(
    "--random_seed",
    "-r",
    type=int,
    default=42,
    help="Random seed.",
)
@with_appcontext
def sheet(dataset, split, in_file, out_file, count, random_seed):
    from .main import export_error_analysis

    export_error_analysis(
        dataset_name=dataset, split=split, in_file=in_file, out_file=out_file, count=count, random_seed=random_seed
    )


@click.command()
@click.option("--dataset", "-d", type=str, default=None)
@with_appcontext
def info(dataset):
    logging.disable(logging.CRITICAL)
    from .main import get_dataset_info

    get_dataset_info(dataset_name=dataset)
