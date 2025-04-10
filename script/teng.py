###############################################################################
# File        : teng.py
# Author      : kareem
# Description : Basic template engine with 2 modes
#
###############################################################################

import os
import re
import sys
import argparse

argparser = argparse.ArgumentParser(prog="teng")
argparser.add_argument("template", type=str, help="Template file to process")
argparser.add_argument("-o", "--output", type=str, default=None, help="Output file to process")
argparser.add_argument("-g", "--enable-globals", action="store_true", help="Allow evals to access python globals()")
argparser.add_argument("-s", "--safe",           action="store_true", help="Disable evals")
argparser.add_argument(      "--strict",         action="store_true", help="Error if a substitution fails")
argparser.add_argument("-e", "--env",            action="store_true", help="Allow pulling values from environment variables")
argparser.add_argument("-d", "--debug",          action="store_true", help="Debug output")
argparser.add_argument("-A", "--start",  type=str, default="{", help="Start string for format token. Default is {")
argparser.add_argument("-B", "--stop",   type=str, default="}", help="End   string for format token. Default is }")
argparser.add_argument("--test",         type=str, help="Debug regex matching")
argparser.add_argument("vars", nargs=argparse.REMAINDER, help="List of variable definitions")

escape_chars = "+?.*^$[](){}"
def escape_regex(string):
    for c in escape_chars:
        string = string.replace("c", f"\\{c}")
    return string

var___re = re.compile(r"\s*(\w+)(=(.*))?\s*")                                 # Basic variable substitution token
ifinl_re = re.compile(r"\s*if(n)?def\s+(\w+)\s+(.*?)(\s+else\s+(.*))?")       # Inline ifdef statement (contains then/else)
ifdef_re = re.compile(r"\s*if((n)?(def|xst))\s+(.*)\s*")                      # Standard ifdef / ifxst (file exists)
ifexp_re = re.compile(r"\s*if\s+(.*)\s*")                                     # Generic if statement
endif_re = re.compile(r"\s*(endif)\s*")                                       # End of if statement
econd_re = re.compile(r"\s*(endif|else)\s*")                                  # End of block of if statement
loop__re = re.compile(r"\s*for\s+(\w+)\s+in\s+(.*)\s*")                       # Loop
eloop_re = re.compile(r"\s*endfor\s*")                                        # End of Loop
decl1_re = re.compile(r"\s*(assert|eval|import)\s+(.*)\s*")                   # Assert / Eval
decl2_re = re.compile(r"\s*(default|define)\s+(\w+)\s+(.*)\s*")               # Default / Define
func__re = re.compile(r"\s*(\w+)\s*\(.*\)\s*")                                # Custom function evaluation

## --------------------------------------------------

_errors = 0
_warnings = 0

def error(*msg):
    global _errors
    _errors += 1
    print("ERROR  :", *msg, file=sys.stderr)

def warn(*msg):
    global _warnings
    _warnings += 1
    print("WARNING:", *msg, file=sys.stderr)

## --------------------------------------------------

def build_mapping(format_list, mapping={}):
    for fmt in format_list:
        if fmt:
            try:
                k, v = fmt.split("=")
                if v.startswith("eval:"):
                    v = eval(v[5:], mapping, get_globals())
                mapping[k] = v
            except ValueError as e:
                print(f"failed to split <{fmt}> into key=value")
    return mapping

def get_globals():
    if args.enable_globals:
        return globals()
    return {}

## --------------------------------------------------

class TEngine:
    def __init__(self, template):
        self.tokens = token_re.split(template)

    def token_iter(self):
        i = iter(self.tokens)
        try:
            while True:
                yield next(i)
                yield next(i)#[start_i:stop_i]
                next(i)
        except StopIteration:
            return
        
    def process(self, env, tokens=None, include=True, target=None):
        static = True
        if tokens is None:
            tokens = self.token_iter() # iter(self.tokens)

        for token in tokens:
            if static:
                yield token
            else:
                if target and (m:=target.fullmatch(token)):
                    yield m.groups()[0]; return
                else:
                    yield from self.handle_token(token, tokens, env, include)
            static = not static

    def handle_token(self, token, tokens, env, include=True): # , target=None
        if   m := ifexp_re.fullmatch(token): yield from self.handle_cond("if",          include and self.eval_expr(m.groups()[0], env), env, tokens, include)
        elif m := loop__re.fullmatch(token): yield from self.handle_loop(m.groups()[0], (include or []) and self.eval_expr(m.groups()[1], env), env, tokens, include)
        elif (m := ifinl_re.fullmatch(token)) and include: yield m.groups()[2] if (m.groups()[0] == "n") ^ (m.groups()[1] in env) else m.groups()[4] or ""
        elif m := ifdef_re.fullmatch(token): yield from self.handle_cond(m.groups()[0],                m.groups()[3],       env, tokens, include)
        elif include == False: return
        elif m := var___re.fullmatch(token): yield self.lookup(m.groups()[0], env, default=m.groups()[2]) or (f_unstrict_mode and token_start + token + token_stop) or ""
        elif m := decl1_re.fullmatch(token): yield self.handle_decl(m.groups(), env)
        elif m := decl2_re.fullmatch(token): self.handle_decl(m.groups(), env)
        elif m := func__re.fullmatch(token): yield self.eval_expr(token, env) # [1:-1]
        elif not f_unstrict_mode:
            raise NotImplementedError(f"Unknown/Unexpected token {token}")
        else:
            yield token_start + token + token_stop

    def handle_cond(self, typ, value, env, tokens, include=True):
        inc_if = 0

        if include:
            if typ == "if":
                inc_if = value 
            elif typ.endswith("def"):
                inc_if = value in env
            elif typ.endswith("xst"):
                inc_if = os.path.exists(value)

            if typ.startswith("n"):
                inc_if = not inc_if

        inc_el = include and not inc_if
        inc_if = include and inc_if

        for token in self.process(env, tokens, inc_if, target=econd_re):
            if token == "endif": return 
            if token == "else" : break
            if inc_if: yield token

        for token in self.process(env, tokens, inc_el, target=endif_re):
            if token == "endif": return 
            if inc_el: yield token

    def handle_loop(self, var, values, env, tokens, include):
        loop_tokens = []
        loop_depth = 0

        for token in tokens:
            if loop__re.fullmatch(token):
                loop_depth += 1

            if eloop_re.fullmatch(token):
                if loop_depth == 0:
                    break
                else:
                    loop_depth -= 1
            loop_tokens.append(token)

        if include:
            for value in values:
                nenv = dict(env)
                nenv[var] = value
                tkns = iter(loop_tokens)

                yield from self.process(nenv, tkns, include)

    def handle_decl(self, args, env):
        typ, *args = args

        match typ:
            case "assert":
                if not (v:=self.eval_expr(args[0], env)):
                    error(f"Assertion Failed {args[0]} -> {v}")

            case "eval":
                return self.eval_expr(args[0], env)

            case "import":
                return self.eval_expr(f"exec('import {args[0]}')", env)

            case "default":
                if args[0] not in env:
                    env[args[0]] = self.eval_expr(args[1], env)

            case "define":
                if args[1].startswith("eval:"):
                    env[args[0]] = self.eval_expr(args[1][5:], env)
                elif args[1].startswith("func:"):
                    env[args[0]] = self.eval_expr("lambda " + args[1][5:], env)
                else:
                    env[args[0]] = args[1]

    def lookup(self, var, env, safe=0, default=None):
        if var in env:
            return env[var]
        if default:
            return default
        if f_unstrict_mode or safe:
            return None
        raise KeyError(f"{var} Not Defined")

    def eval_expr(self, expr, env):
        if args.safe: 
            warn(f"Safe Mode: Skipping evaluated expression <{expr}>")
            return None
        try:
            return eval(expr, env, get_globals())
        except NameError as e:
            error(f"Undefined variable in expression {expr}: {e}")
        
## main ----------------------------------------------------

if __name__ == "__main__":
    args = argparser.parse_args()

    token_start = args.start
    token_stop  = args.stop
    start_re = escape_regex(token_start)
    stop_re  = escape_regex(token_stop)
    start_i  = len(token_start)
    stop_i   = -len(token_stop)

    token_re = re.compile(f"{start_re}(((?!{start_re}|{stop_re}).)+){stop_re}")   # Generic token regex
    tokens = zip([token_re, var___re, ifinl_re, ifdef_re, ifexp_re, endif_re, econd_re, loop__re, eloop_re, decl1_re, decl2_re, func__re],
                 ["token_re", "var___re", "ifinl_re", "ifdef_re", "ifexp_re", "endif_re", "econd_re", "loop__re", "eloop_re", "decl1_re", "decl2_re", "func__re"])

    if args.test:
        for token, name in tokens:
            print(name, token.fullmatch(args.test), sep="\t--\t")
        exit()

    f_unstrict_mode = not args.strict

    env = build_mapping(args.vars, mapping=dict(os.environ) if args.env else {})

    with open(args.template, "r") as file:
        engine = TEngine(file.read())
        
    if args.output:
        with open(args.output, "w") as file:
            for token in engine.process(env):
                if token is not None:
                    file.write(str(token))

    elif args.debug:
        for token in engine.process(env):
            #if token == '\n': continue
            if token is not None:
                print(repr(token), end="")

    else:
        for token in engine.process(env):
            #if token == '\n': continue
            if token is not None:
                print(token, end="")

