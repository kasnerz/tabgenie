#!/usr/bin/env python3

from ..processing import Pipeline
from ..processors.translate_processor import TranslateProcessor

class TranslatePipeline(Pipeline):
    # example pipeline demonstrating pipeline capabilities
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.processors = [TranslateProcessor()]