import argparse
import json
import os

## Arg Parsing --------------------------------------

argparser = argparse.ArgumentParser(prog="json2spice", description = "Generate spice from yosys json description")
argparser.add_argument("input_json", type=str, help="Path to Yosys generated json")
argparser.add_argument("cell_path", type=str, help="Path to standard cells library folder")
argparser.add_argument("module", type=str, help="Module name")
argparser.add_argument("outfile", type=str, help="Output file path")

## JSON Parsing Nets --------------------------------

#bits = set()
#for net in module['netnames']:
#    v = tuple(module['netnames'][net]['bits'])
#    if v in bits: print("DUPE BITS", v)
#    else:         bits.add(v)
# bits is a valid unique representation of a net
# at top level it would be nice to have usable names, but everything internal can be bit name. 
# OPTION 1: double wrapper
# OPTION 2: voltage source with no value btw top level ports
# OPTION 3: mix naming between bits and names

def parse_nets(netname_dict):
    netnames = {}
    tieoffs  = {}

    for netname in netname_dict:
        net = netname_dict[netname]
        v = tuple(net['bits'])

        if net['hide_name']:
            for b in net['bits']:
                if isinstance(b, str):
                    raise NotImplementedError("Python parser does not support tie-offs on signals with hidden names (hide_name = 1)")
                else:
                    netnames[b] = f"__{b}__"
        else:
            if len(net['bits']) == 1:
                b = net['bits'][0]
                if isinstance(b, str):
                    tieoffs[netname] = int(b)
                else:
                    netnames[b] = netname
            else:
                i = 0
                for b in net['bits']:
                    bname = f"{netname}.{i}"
                    if isinstance(b, str):
                        tieoffs[bname] = int(b)
                    else:
                        netnames[b] = bname
                    i += 1

    return netnames, tieoffs

## JSON Parsing Cells -------------------------------

def parse_cells(cell_dict):
    types = {}
    cells = {}

    i = 0

    for cellname, cell in cell_dict.items():
        type = cell["type"]
        if type not in types: types[type] = {}

        if cell["hide_name"]:
            cname = f"__{i}__"
        else:
            cname = cellname

        cells[cname] = dict(type = type, conn = cell["connections"])

        i += 1

    return types, cells

## LIB Parsing Cells --------------------------------

def parse_cell_types(celltypes, cell_path, module_dict):
    all_pg_pins = set()

    for ctype in celltypes:
        ccatg = ctype.split('_')[-2]
        cpath = os.path.join(cell_path, ccatg, ctype + ".spice")
        with open(cpath, "r") as file:
            for line in file.readlines():
                if line.startswith(".subckt"):
                    pins = line.split()[2:]
                    pg = []
                    for pin in pins:
                        if (pin not in module_dict[ctype]['ports']):
                            pg.append(1)
                            all_pg_pins.add(pin)
                        else:
                            pg.append(0)

                    celltypes[ctype]['pins'] = list(zip(pins, pg))
                    celltypes[ctype]['path'] = cpath
                    break

    return all_pg_pins


## Build Spice Includes -----------------------------

def gen_spice_inc(celltypes, file):
    file.write("* Standard Cell Includes\n")

    for ctype, cell in celltypes.items():
        file.write(f".include {cell['path']}\n")

def gen_spice_mod(celltypes, cells, netnames):
    file.write("* Standard Cells\n")

    for cellname, cell in cells.items():
        ctype = celltypes[cell['type']]
        ports = []

        for pin, pg in ctype['pins']:
            if pg:
                ports.append(pin)
            else:
                ports.append(netnames[cell['conn'][pin][0]])

        file.write(f"x{cellname} {' '.join(ports)} {cell['type']}\n")

def gen_spice_ports(module, modulename, pg_pins, file):
    ports = {}
    mindex = 9999

    file.write("\n* Subcircuit Definition\n")

    for portname, port in module["ports"].items():
        bits = port['bits']

        if len(bits) == 1:
            ports[bits[0]] = portname
            mindex = min(bits[0], mindex)
        else:
            i = 0
            for b in bits:
                ports[b] = f"{portname}.{i}"
                mindex = min(b, mindex)
                i += 1

    plist = []
    for i in range(mindex, mindex+len(ports)):
        plist.append(ports[i])

    pg_pins = sorted(pg_pins)

    file.write(f".subckt {modulename} {' '.join(plist)} {' '.join(pg_pins)}\n\n")

def gen_spice_ties(tieoffs, pin_lo, pin_hi, file):
    i = 0

    file.write("* Tieoffs\n")
    for tie, value in tieoffs.items():
        tie_pin = pin_hi if value else pin_lo

        file.write(f"v__{i}__ {tie_pin} {tie} DC 0\n")
        i += 1

## Main ---------------------------------------------

if __name__ == '__main__':
    args = argparser.parse_args()

    with open(args.input_json, "r") as file:
        data = json.load(file)

    try:
        module = data["modules"][args.module]
    except:
        RuntimeError(f"Module {args.module} not found.")

    netnames, tieoffs = parse_nets(module['netnames'])
    celltypes, cells  = parse_cells(module['cells'])
    all_pg_pins       = parse_cell_types(celltypes, args.cell_path, data["modules"])

    with open(args.outfile, "w") as file:
        file.write(f"* {args.module}.spice\n")
        file.write("* File autogenerated by json2spice.py\n\n")

        gen_spice_inc(celltypes, file)
        gen_spice_ports(module, args.module, all_pg_pins, file)
        gen_spice_mod(celltypes, cells, netnames)
        file.write("\n")
        gen_spice_ties(tieoffs, "VGND", "VPWR", file)
        file.write("\n.ends\n\n")


#print(netnames)
#print(tieoffs)

