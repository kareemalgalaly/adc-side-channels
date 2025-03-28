###############################################################################
# File        : template_engine.py
# Author      : kareem
# Description : Basic template engine with 2 modes
#
###############################################################################

import os
import re
import sys
import argparse

argparser = argparse.ArgumentParser(prog="template_engine v0.1")
argparser.add_argument("template", type=str, help="Template file to process")
argparser.add_argument("-o", "--output", type=str, default=None, help="Output file to process")
argparser.add_argument("-u", "--unsafe", default=False, const=True, action="store_const", help="Error if a substitution fails")
argparser.add_argument("-e", "--env",    default=False, const=True, action="store_const", help="Allow pulling values from environment variables")
argparser.add_argument("-d", "--debug",  default=False, const=True, action="store_const", help="Debug output")
argparser.add_argument("--test",         type=str, help="Debug regex matching")
argparser.add_argument("vars", nargs=argparse.REMAINDER, help="List of variable definitions")

token_re = re.compile(r"({[^{}]+})")                                            # Generic token regex
#token_re = re.compile(r"({[^{}]+|\w+\s+\(.*\)})")                                   # Generic token regex
var___re = re.compile(r"{\s*(\w+)(=(.*))?\s*}")                                 # Basic variable substitution token
ifinl_re = re.compile(r"{\s*if(n)?def\s+(\w+)\s+(.*?)(\s+else\s+(.*))?}")       # Inline ifdef statement (contains then/else)
ifdef_re = re.compile(r"{\s*if((n)?(def|xst))\s+(\w+)\s*}")                     # Standard ifdef / ifxst (file exists)
ifexp_re = re.compile(r"{\s*if\s+(.*)\s*}")                                     # Generic if statement
endif_re = re.compile(r"{\s*(endif)\s*}")                                       # End of if statement
econd_re = re.compile(r"{\s*(endif|else)\s*}")                                  # End of block of if statement
loop__re = re.compile(r"{\s*for\s+(\w+)\s+in\s+(.*)\s*}")                       # Loop
eloop_re = re.compile(r"{\s*endfor\s*}")                                        # End of Loop
decl1_re = re.compile(r"{\s*(assert)\s+(.*)\s*}")                               # Assert
decl2_re = re.compile(r"{\s*(default|define)\s+(\w+)\s+(.*)\s*}")               # Default / Define
func__re = re.compile(r"{\s*(\w+)\s*\(.*\)\s*}")                                # Custom function evaluation

tokens = zip([token_re, var___re, ifinl_re, ifdef_re, ifexp_re, endif_re, econd_re, loop__re, eloop_re, decl1_re, decl2_re, func__re],
             ["token_re", "var___re", "ifinl_re", "ifdef_re", "ifexp_re", "endif_re", "econd_re", "loop__re", "eloop_re", "decl1_re", "decl2_re", "func__re"])


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

def build_mapping(format_list):
    mapping = {}
    for fmt in format_list:
        if fmt:
            try:
                k, v = fmt.split("=")
                if v.startswith("eval:"):
                    v = eval(v[5:])
                mapping[k] = v
            except ValueError as e:
                print(f"failed to split <{fmt}> into key=value")
    return mapping

## --------------------------------------------------

class TEngine:
    def __init__(self, template):
        self.tokens = token_re.split(template)
        
    def process(self, env, tokens=None, include=True, target=None):
        static = True
        if tokens is None:
            tokens = iter(self.tokens)
        #if f_env_allow:
        #    environ = dict(os.environ)
        #    environ.update(env)
        #    env = environ

        for token in tokens:
            if static:
                yield token
            else:
                if target and (m:=target.match(token)):
                    yield m.groups()[0]; return
                else:
                    yield from self.handle_token(token, tokens, env, include)
            static = not static

    def handle_token(self, token, tokens, env, include=True): # , target=None
        #if target and target.match(token): return
        if   m := ifdef_re.match(token): yield from self.handle_cond(m.groups()[0],                m.groups()[3],       env, tokens, include)
        elif m := ifexp_re.match(token): yield from self.handle_cond("if",          self.eval_expr(m.groups()[0], env), env, tokens, include)
        elif m := loop__re.match(token): yield from self.handle_loop(m.groups()[0], self.eval_expr(m.groups()[1], env), env, tokens, include)
        elif m := ifinl_re.match(token): 
            yield m.groups()[2] if (m.groups()[0] == "n") ^ (self.lookup(m.groups()[2], env, safe=1) is not None) else m.groups()[4] or ""
        # elif include == 0: return
        elif m := var___re.match(token): yield self.lookup(m.groups()[0], env, default=m.groups()[2]) or (f_safe_mode and token) or ""
        elif m := decl1_re.match(token): self.handle_decl(m.groups(), env)
        elif m := decl2_re.match(token): self.handle_decl(m.groups(), env)
        elif m := func__re.match(token): yield self.eval_expr(token[1:-1], env)
        #elif      econd_re.match(token): yield token
        elif not f_safe_mode:
            raise NotImplementedError(f"Unknown/Unexpected token {token}")
        else:
            yield token

    def handle_cond(self, typ, value, env, tokens, include=True):
        inc_if = 0

        if include:
            if typ == "if":
                inc_if = value 
            elif typ.endswith("def"):
                inc_if = (value in env) or f_env_allow and (value in os.environ)
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
            if loop__re.match(token):
                loop_depth += 1

            if eloop_re.match(token):
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
        if f_env_allow and var in os.environ:
            return os.environ[var]
        if default:
            return default
        if f_safe_mode or safe:
            return None
        raise KeyError(f"{var} Not Defined")

    def eval_expr(self, expr, env):
        try:
            if f_env_allow:
                return eval(expr, os.environ, env)
            else:
                return eval(expr, env)
        except NameError as e:
            error(f"Undefined variable in expression {expr}: {e}")
        
## --------------------------------------------------

if __name__ == "__main__":
    args = argparser.parse_args()
    #print(args.output)
    #print(args)

    if args.test:
        for token, name in tokens:
            print(name, token.match(args.test), sep="\t--\t")
        exit()

    f_env_allow = args.env
    f_safe_mode = not args.unsafe

    env = build_mapping(args.vars)

    with open(args.template, "r") as file:
        engine = TEngine(file.read())
        
    if args.output:
        with open(args.output, "w") as file:
            for token in engine.process(env):
                file.write(token)

    elif args.debug:
        for token in engine.process(env):
            #if token == '\n': continue
            print(repr(token), end="")

    else:
        for token in engine.process(env):
            #if token == '\n': continue
            print(token, end="")

