###############################################################################
# File        : template_engine.py
# Author      : kareem
# Description : Basic template engine with 2 modes
#
#   -t  : $key  PEP292  using string.Template
#   -f  : {key} PEP3101 formatting
###############################################################################

from string import Template
import argparse
import re

argparser = argparse.ArgumentParser(prog="template_engine")
argparser.add_argument("template", type=str, help="Template file to process")
argparser.add_argument("-o", "--output", type=str, default=None, help="Output file to process")
argparser.add_argument("-t", "--tmpfmt", type=str, nargs="+", metavar="KEY=VALUE", help="key=value pairs for $key PEP292 formatting")
argparser.add_argument("-f", "--format", type=str, nargs="+", metavar="KEY=VALUE", help="key=value pairs for {key} PEP3101 formatting")
argparser.add_argument("-s", "--sformat",type=str, nargs="+", metavar="KEY=VALUE", help="key=value pairs for PEP3101-based formatting. Special options including ifdef/else/ifndef added.")

## --------------------------------------------------

class SafeDict(dict):
    def __missing__(self, key):
        return '{' + key + '}'

## --------------------------------------------------

vdef_re = re.compile(r'^(\w+)\s*=\s*([^}]+)$')
ifdefre = re.compile(r'^\s*{(ifdef|ifndef)\s+(\w+)}\s*$')
else_re = re.compile(r'^\s*{else}\s*$')
endifre = re.compile(r'^\s*{endif}\s*$')
#rep_re  = re.compile(r'^\s*{repeat\s+(\d+)\s+(\w+)}\s*$')
#endrpre = re.compile(r'^\s*{endrepeat}\s*$')
for__re = re.compile(r'^\s*{for\s+(\w+)\s+in\s+([^}]+)}\s*$')
endfore = re.compile(r'^\s*{endfor}\s*$')

class FancyDict(SafeDict):
    def __missing__(self, key):

        if key.startswith("ifdef ") or key.startswith("ifndef "):
            iftyp, skey, *value = key.split(" ")

            if value:
                if isinstance(value, list): 
                     value = " ".join(value)

                if " else " in value:
                    value, evalue = value.split(" else ")
                else:
                    evalue = ""

                if (skey in self) ^ (iftyp == 'ifndef'):
                    return value # TODO expression evaluation

                return evalue

        elif m := vdef_re.match(key):
            skey, default = m.groups()
            return self[skey] if skey in self else default

        return super().__missing__(key)

def handle_sformat_repeat(line_iter, mapping, key, for_iter):
    nlines = []

    for line in line_iter:
        if m := endfore.match(line):
            break
        elif m := for__re.match(line):
            _key, _iter = m.groups()
            _iter = eval(_iter, globals(), mapping)
            nlines.extend(handle_sformat_repeat(line_iter, mapping, _key, _iter))
        else:
            nlines.append(line)

    nlines2 = []
    for value in for_iter:
        for line in nlines:
            nlines2.append(line.format_map(SafeDict({key : value})))

    return nlines2

def handle_sformat_special(lines, mapping):
    nlines = []
    ifdepth = []
    include = True
    frdepth = 0

    line_iter = iter(lines)

    for line in line_iter:
        if m := ifdefre.match(line):
            iftyp, key = m.groups()
            include = include and ((key in mapping) ^ (iftyp == 'ifndef'))
            ifdepth.append(include)

        elif else_re.match(line):
            inc_fin = not ifdepth.pop()
            include = inc_fin and ifdepth[-1] if ifdepth else inc_fin
            ifdepth.append(include)

        elif endifre.match(line):
            ifdepth.pop()
            include = True if len(ifdepth) == 0 else ifdepth[-1]

        elif m := for__re.match(line):
            if include:
                _key, _iter = m.groups()
                _iter = eval(_iter, globals(), mapping)
                nlines.extend(handle_sformat_special(handle_sformat_repeat(line_iter, mapping, _key, _iter), mapping))
            else:
                frdepth += 1

        elif m := endfore.match(line):
            if frdepth == 0: raise RuntimeError("unexpected endfor block")
            frdepth -= 1

        else:
            if include:
                nlines.append(line)

    return nlines

def post_process_sformat(text, mapping):
    lines = handle_sformat_special(text.split("\n"), mapping)
    return "\n".join(lines)

## --------------------------------------------------

class FancyTemplate(Template):
    #idpattern      = r'([_a-zA-Z][_a-zA-Z0-9]*)'
    #stringliteral  = '[^}]*'
    #braceidpattern = f'({idpattern}|(ifdef|ifndef) {idpattern} {stringliteral})'
    pattern = r'\$(?:(?P<escaped>\$)|(?P<named>([_a-zA-Z][_a-zA-Z0-9]*))|{(?P<braced>(?-i:[_a-zA-Z][_a-zA-Z0-9]*|(ifdef|ifndef) [_a-zA-Z][_a-zA-Z0-9]* [^}]+))}|(?P<invalid>))'

    def substitute(self, dict):
        return super().substitute(FancyDict(dict))

    def safe_substitute(self, mapping={}, /, **kws):
        mapping = FancyDict(mapping)
        # Helper function for .sub()
        def convert(mo):
            named = mo.group('named') or mo.group('braced')
            if named is not None:
                try:
                    return str(mapping[named])
                except KeyError:
                    return mo.group()
            if mo.group('escaped') is not None:
                return self.delimiter
            if mo.group('invalid') is not None:
                return mo.group()
            raise ValueError('Unrecognized named group in pattern',
                             self.pattern)
        return self.pattern.sub(convert, self.template)

## --------------------------------------------------

def build_mapping(format_list):
    mapping = {}
    for fmt in format_list:
        if fmt:
            try:
                k, v = fmt.split("=")
                if v.startswith("eval:"):
                    v = eval(v[5:])
                mapping[k] = v
            except valueerror as e:
                print(f"failed to split <{fmt}> into key=value")
    return mapping

## --------------------------------------------------

if __name__ == "__main__":
    args = argparser.parse_args()

    with open(args.template, "r") as file:
        if args.tmpfmt:
            mapping  = build_mapping(args.tmpfmt)
            template = Template(file.read())
            processe = template.safe_substitute(mapping)

        elif args.format:
            mapping  = build_mapping(args.format)
            template = file.read()
            processe = template.format_map(SafeDict(mapping))

        elif args.sformat:
            mapping  = build_mapping(args.sformat)
            template = file.read()
            processe = template.format_map(FancyDict(mapping))
            processe = post_process_sformat(processe, mapping)

        else:
            template = Template(file.read())
            print("keys:", *template.get_identifiers(), sep=' $')
            exit()

        if args.output:
            with open(args.output, "w") as file: file.write(processe)
        else:
            print(processe)
