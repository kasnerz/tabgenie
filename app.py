#!/usr/bin/env python3

import os
import sys

sys.path.append(os.path.dirname(__name__))

from src import create_app

if __name__ == '__main__':
    app = create_app()
    app.run()
