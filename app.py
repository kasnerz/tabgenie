#!/usr/bin/env python3

import os
import sys
import argparse

sys.path.append(os.path.dirname(__name__))

from src import create_app

app = create_app()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, default="full", choices=["full", "light"],
         help="Deployment mode: full = with model loading, light = visualization only")

    args = parser.parse_args()
    app.config["mode"] = args.mode
    app.run()
