import argparse
import json
import os

## Arg Parsing --------------------------------------

argparser = argparse.ArgumentParser(prog="json2spice", description = "Generate spice from yosys json description")
argparser.add_argument("input_json", type=str, help="Path to Yosys generated json")
argparser.add_argument("cell_path", type=str, help="Path to standard cells library folder")
argparser.add_argument("module", type=str, help="Module name")
argparser.add_argument("outfile", type=str, help="Output file path")
argparser.add_argument("-f", "--fullpaths", const=True, default=False, action="store_const", help="Use full paths in synthesis output")
argparser.add_argument("-d", "--debug", const=True, default=False, action="store_const", help="Enable debug printing")

errors = 0
warns  = 0

def err(*args):
    print("ERROR:", *args)
    global errors
    errors += 1

def warn(*args):
    print("WARNING:", *args)
    global warns
    warns += 1

def info(*args):
    print("INFO:", *args)

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
    netnames = {} # bit       : netname
    tieoffs  = {} # netname   : value
    aliases  = {} # aliasname : netname

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
                    if netname in tieoffs: 
                        warn(f"net {netname} already in tieoffs {tieoffs[netname]}. Ignoring additional tie to {b}")
                    else:
                        tieoffs[netname] = int(b)
                else:
                    if b in netnames:
                        if "." in netname:
                            info(f"bit {b:4} already named. {netname} => {netnames[b]}")
                            aliases[netname] = netnames[b]
                        else:
                            info(f"bit {b:4} already named. {netnames[b]} => {netname}")
                            aliases[netnames[b]] = netname
                            netnames[b] = netname
                    else:
                        netnames[b] = netname
            else:
                i = 0
                for b in net['bits']:
                    bname = f"{netname}.{i}"
                    if isinstance(b, str):
                        if bname in tieoffs:
                            warn(f"net {bname} already in tieoffs {tieoffs[bname]}. Ignoring additional tie to {b}")
                        else:
                            tieoffs[bname] = int(b)
                    else:
                        if b in netnames:
                            warn(f"bit {b} already named in netnames as <{netnames[b]}>. Ignoring additional name <{bname}>")
                            aliases[bname] = netnames[b]
                        else:
                            netnames[b] = bname
                    i += 1

    return netnames, tieoffs, aliases

## JSON Parsing Cells -------------------------------

def parse_cells(cell_dict):
    types = {} # std_cell_type : {}
    cells = {} # cell_name     : {type:std_cell_type, conn=connections}

    i = 0

    for cellname, cell in cell_dict.items():
        type = cell["type"]
        if type == "$scopeinfo":
            if len(cell["connections"]) != 0:
                err(f"$scopeinfo cell {cellname} has defined connections that are being ignored.")
            continue
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
    unified_spice = cell_path.endswith("spice")

    if unified_spice:
        # Read the consolidated spice file and parse all subcircuit definitions
        subckt_definitions = {}
        with open(cell_path, "r") as spice_file:
            lines = spice_file.readlines()
        
        for i, line in enumerate(lines):
            if line.startswith(".subckt"):
                parts = line.split()
                subckt_name = parts[1]
                pins = parts[2:]
                subckt_definitions[subckt_name] = {
                    "pins": pins,
                    "path": cell_path,
                    "line_index": i
                }

    # Match cell types to subcircuit definitions
    for ctype in celltypes:
        if unified_spice:
            if ctype not in subckt_definitions:
                raise ValueError(f"Subcircuit definition for cell type {ctype} not found in {cell_path}")
            else:
                subckt_info = subckt_definitions[ctype]
                pins = subckt_info["pins"]
                pg = []
        else:
            ccatg = ctype.split('_')[-2]
            cpath = os.path.join(cell_path, ccatg, ctype + ".spice")
            rpath = os.path.join(os.path.basename(cell_path), ccatg, ctype + ".spice")
            with open(cpath, "r") as file:
                for line in file.readlines():
                    if line.startswith(".subckt"):
                        pins = line.split()[2:]
                        pg = []
                        break

        for pin in pins:
            # only available if yosys reads liberty as design file
            if pin not in module_dict[ctype]['ports']:
                pg.append(1)
                all_pg_pins.add(pin)
            else:
                pg.append(0)

            celltypes[ctype]['pins'] = list(zip(pins, pg))
            celltypes[ctype]['path'] = cell_path if unified_spice else cpath if args.fullpaths else rpath

    return all_pg_pins


## Build Spice Includes -----------------------------

def gen_spice_inc(celltypes, file):
    file.write("* Standard Cell Includes\n")

    for ctype, cell in celltypes.items():
        file.write(f".include {cell['path']}\n")

def gen_spice_mod(celltypes, cells, netnames, ports, file):
    file.write("* Standard Cells\n")

    for cellname, cell in cells.items():
        ctype = celltypes[cell['type']]
        pins = []

        for pin, pg in ctype['pins']:
            if pg:
                pins.append(pin)  # Power or ground pin
            else:
                # Map connection to a port or net
                conn = cell['conn'].get(pin, [])
                if len(conn) == 1:
                    pins.append(netnames.get(conn[0], f"NET{conn[0]}"))
                elif len(conn) == 0:
                    pins.append("0")  # Default to 0 if not connected
                else:
                    raise RuntimeError("Got more than one conn.")

        file.write(f"x{cellname} {' '.join(pins)} {cell['type']}\n")

def gen_spice_ports(module, modulename, pg_pins, aliases, file):
    ports = {}
    mindex = 9999

    file.write("\n* Subcircuit Definition\n")

    for portname, port in module["ports"].items():
        bits = port['bits']

        if len(bits) == 1:
            if portname in aliases: portname = aliases[portname]
            ports[bits[0]] = portname
            mindex = min(bits[0], mindex)
        else:
            i = 0
            for b in bits:
                pname = f"{portname}.{i}"
                if pname in aliases: pname = aliases[pname]
                ports[b] = pname
                mindex = min(b, mindex)
                i += 1

    plist = []
    for i in range(mindex, mindex+len(ports)):
        plist.append(ports[i])

    pg_pins = sorted(pg_pins)

    file.write(f".subckt {modulename} {' '.join(plist)} {' '.join(pg_pins)}\n\n")
    return ports

def gen_spice_ties(tieoffs, pin_lo, pin_hi, file):
    i = 0

    file.write("* Tieoffs\n")
    for tie, value in tieoffs.items():
        tie_pin = pin_hi if value else pin_lo

        file.write(f"v__{i}__ {tie_pin} {tie} DC 0\n")
        i += 1

## Main ---------------------------------------------

if __name__ == '__main__':
    print("Starting json2spice.py")
    args = argparser.parse_args()

    with open(args.input_json, "r") as file:
        data = json.load(file)

    try:
        module = data["modules"][args.module]
    except:
        RuntimeError(f"Module {args.module} not found.")

    netnames, tieoffs, aliases = parse_nets(module['netnames'])
    celltypes, cells           = parse_cells(module['cells'])
    all_pg_pins                = parse_cell_types(celltypes, args.cell_path, data["modules"])

    if args.debug: print("netnames",    netnames)
    if args.debug: print("tieoffs",     tieoffs)
    if args.debug: print("celltypes",   celltypes)
    if args.debug: print("cells",       cells)
    if args.debug: print("all_pg_pins", all_pg_pins)

    with open(args.outfile, "w") as file:
        file.write(f"* {args.module}.spice\n")
        file.write("* File autogenerated by json2spice.py\n\n")

        gen_spice_inc(celltypes, file)
        ports = gen_spice_ports(module, args.module, all_pg_pins, aliases, file)
        gen_spice_mod(celltypes, cells, netnames, ports, file)
        file.write("\n")
        gen_spice_ties(tieoffs, "VGND", "VPWR", file)
        file.write("\n.ends\n\n")

    print(f"Completed with {errors} errors and {warns} warnings")


#print(netnames)
#print(tieoffs)

