#!/usr/bin/env python3
"""Master script to assemble the ROI Lens notebook from all step modules."""
import sys
sys.path.insert(0, '.')

from nb_builder import build_notebook
import cells_step0
import cells_step1
import cells_step2
import cells_step3
import cells_step4
import cells_step5
import cells_step6

cells = []
cells.extend(cells_step0.get_cells())
cells.extend(cells_step1.get_cells())
cells.extend(cells_step2.get_cells())
cells.extend(cells_step3.get_cells())
cells.extend(cells_step4.get_cells())
cells.extend(cells_step5.get_cells())
cells.extend(cells_step6.get_cells())

build_notebook(cells, "roi_lens.ipynb")
print(f"📓 Notebook assembled with {len(cells)} cells across Steps 0-6.")
