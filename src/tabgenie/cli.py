#!/usr/bin/env python3

import json
import os
import logging
import click
from flask import Flask
from flask.cli import FlaskGroup, with_appcontext, pass_script_info
from .main import create_app, app, export_dataset


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
    export_dataset(
        dataset_name=dataset, split=split, out_dir=out_dir, export_format=export_format, json_template=json_template
    )
