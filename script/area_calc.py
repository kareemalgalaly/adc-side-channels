import os
import re
import sys
import argparse

argparser = argparse.ArgumentParser(prog="area_calc", description = "Calculate area consumption of list of standard cells")
argparser.add_argument("std_cell_path", type=str, help="Path to standard cells")
argparser.add_argument("-m", "--minimal", action="store_const", help="Only print numbers")
# argparser.add_argument("microns", type=int, default=1000, help="Unit of MICRONS in tech lef")
# units are nm
args = argparser.parse_args()

cell_re = re.compile(r'^(\w+)__(\w+)_(\d+)$')
area_re = re.compile(r'\s+SIZE\s+([0-9.]+)\s+BY\s+([0-9.]+)\s+;')

cell_areas = {}
total_area = 0
num_cells  = 0

for cell in sys.stdin.readlines():
    cell = cell.strip()

    if cell not in cell_areas:
        m = cell_re.match(cell)

        if m is None:
            raise RuntimeError(f"Error: cell <{cell}> did not match regex")

        lib, name, size = m.groups()

        with open(os.path.join(args.std_cell_path, name, cell + ".lef"), "r") as file:
            done = False
            for line in file.readlines():
                if m := area_re.match(line):
                    x, y = m.groups()
                    cell_areas[cell] = round(float(x)*float(y), 3)
                    done = True
                    break
            if not done:
                raise RuntimeError(f"Could not find area for cell <{cell}>")

    total_area += cell_areas[cell]
    num_cells += 1

if args.minimal:
    print(round(total_area, 3))
else:
    print(f"Total Area:             {round(total_area, 3)} nm")
    print(f"Number of Cells:        {num_cells}")
    print(f"Number of Unique Cells: {len(cell_areas)}")
    print('  ' + '\n  '.join(cell_areas.keys()))
