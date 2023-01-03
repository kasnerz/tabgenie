#!/usr/bin/env python3

import click
from flask import Flask
from flask.cli import FlaskGroup, with_appcontext
from .main import create_app


@click.group(cls=FlaskGroup, create_app=create_app)
def run():
    pass

@click.command()
@click.argument('name')
@with_appcontext
def export(name):
    print(name)
    print(app)