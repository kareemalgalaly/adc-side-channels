import random
import argparse
from string import Template

MAX_VAL = 255

argparser = argparse.ArgumentParser(prog="gen_spice_regression")
#argparser.add_argument("template",        type=str,              help="Template file")
#argparser.add_argument("outfile",         type=str,              help="Output file")
argparser.add_argument("-s", "--seed",    type=int, default=0  , help="Seed")
argparser.add_argument("-p", "--pixels",  type=int, default=1  , help="Number of pixels")
argparser.add_argument("-n", "--num",     type=int, default=50 , help="Number of random seeds")
argparser.add_argument("-r", "--range",   type=float, default=256, help="Number of random seeds")
argparser.add_argument(      "--start",   type=int, default=0  , help="Start point for saving num seeds")
argparser.add_argument("-i", "--index",   type=int, default=0  , help="Initial index for output naming")
#argparser.add_argument("-t", "--tmpfmt",  type=str, default=[] , nargs="+", metavar="KEY=VALUE", help="key=value pairs for $key PEP292 formatting")
args = argparser.parse_args()

random.seed(args.seed)

if args.range > 1:
    def get_rval():
        return tuple(random.randint(0, int(args.range)) for j in range(args.pixels))
else:
    def get_rval():
        return tuple(random.random()*args.range for j in range(args.pixels))

def get_unique_rval(seen):
    rval = get_rval()
    while rval in seen: rval = get_rval()
    seen.add(rval)
    return rval

def get_rvals():
    rvals = []
    seen = set()

    for i in range(args.start):
        get_unique_rval(seen)

    for i in range(args.num):
        rvals.append(get_unique_rval(seen))

    return rvals

def generate_rval_strings():
    rvals = get_rvals()
    vectors = tuple(zip(*rvals))

    #strings = {}
    strings = []
    for i, vec in enumerate(vectors):
        #strings[f"pixelvec_{i}"] = f"compose pixelvec_{i} values {' '.join(str(v) for v in vec)}"
        strings.append(f"randvec_{i+args.index}=compose randvec_{i+args.index} values {' '.join(str(v) for v in vec)}")

    return strings

# def build_mapping(format_list):
#     mapping = {}
#     for fmt in format_list:
#         k, v = fmt.split("=")
#         mapping[k] = v
#     return mapping
# 
# mapping = build_mapping(args.tmpfmt)
# mapping.update(generate_rval_strings())
# 
# #print(*generate_rval_strings().items(), sep="\n")
# 
# with open(args.template, "r") as file:
#     template = Template(file.read())
#     file_raw = template.safe_substitute(mapping)
# 
# with open(args.outfile, "w") as file:
#     file.write(file_raw)

print("\n".join(generate_rval_strings()))
