from string import Template
import argparse

argparser = argparse.ArgumentParser(prog="template_engine")
argparser.add_argument("template", type=str, help="Template file to process")
argparser.add_argument("-o", "--output", type=str, default=None, help="Output file to process")
argparser.add_argument("-t", "--tmpfmt", type=str, nargs="+", metavar="KEY=VALUE", help="key=value pairs for $key PEP292 formatting")
argparser.add_argument("-f", "--format",   type=str, nargs="+", metavar="KEY=VALUE", help="key=value pairs for {key} PEP3101 formatting")
args = argparser.parse_args()

class SafeDict(dict):
    def __missing__(self, key):
        return '{' + key + '}'

class FancyDict(dict):
    def __missing__(self, key):
        print(f"handling missing", key)
        if key.startswith("ifdef ") or key.startswith("ifndef "):
            iftyp, key, value = key.split(" ")
            if (key in self) ^ iftyp == 'ifndef':
                return value
            return ""
        raise KeyError(f"Dictionary has no key {key}")

class FancyTemplate(Template):
    idpattern      = '[_a-zA-Z][_a-zA-Z0-9]*'
    stringliteral  = '[^}]*'
    braceidpattern = f'({idpattern}|(ifdef|ifndef) {idpattern} {stringliteral})'
    flags = 0

    def substitute(self, dict):
        return super().substitute(FancyDict(dict))

    def safe_substitute(self, dict):
        return super().safe_substitute(FancyDict(dict))

def build_mapping(format_list):
    mapping = {}
    for fmt in format_list:
        k, v = fmt.split("=")
        mapping[k] = v
    return mapping

with open(args.template, "r") as file:
    if args.tmpfmt:
        mapping  = build_mapping(args.tmpfmt)
        #template = Template(file.read())
        template = FancyTemplate(file.read())
        #print(template.pattern)
        #print(template.idpattern)
        #print(template.braceidpattern)
        processe = template.safe_substitute(mapping)
    elif args.format:
        mapping  = build_mapping(args.format)
        template = file.read()
        processe = template.format_map(SafeDict(mapping))
    else:
        template = FancyTemplate(file.read())
        print("keys:", *template.get_identifiers(), sep=' $')
        exit()

    if args.output:
        with open(args.output, "w") as file: file.write(processe)
    else:
        print(processe)
