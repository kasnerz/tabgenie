#!/usr/bin/env python3

import click
from flask import Flask
from flask.cli import FlaskGroup, with_appcontext
from .main import create_app, app, export_dataset


@click.group(cls=FlaskGroup, create_app=create_app)
def run():
    pass

@click.command()
@click.option('--dataset', '-d', required=True, type=str)
@click.option('--split', '-s', default="dev", type=str)
@click.option('--out', '-o', required=True, type=str, help="Path to the output file")
@click.option('--template', '-t', default="export/default.yml", type=str)
@with_appcontext
def export(dataset, split, out, template):
    export_dataset(dataset_name=dataset, split=split, out_file=out, template_file=template)