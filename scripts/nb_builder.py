"""Utility to build .ipynb notebooks programmatically."""
import json

def md(source):
    return {"cell_type":"markdown","metadata":{},"source":[source]}

def code(source):
    return {"cell_type":"code","metadata":{},"source":[source],"outputs":[],"execution_count":None}

def build_notebook(cells, path="roi_lens.ipynb"):
    nb = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name":"Python 3","language":"python","name":"python3"},
            "language_info": {"name":"python","version":"3.10.0"}
        },
        "nbformat": 4,
        "nbformat_minor": 5
    }
    with open(path, 'w') as f:
        json.dump(nb, f, indent=1)
    print(f"✅ Notebook saved to {path} with {len(cells)} cells")
