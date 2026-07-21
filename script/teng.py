###############################################################################
# File        : teng.py
# Author      : kareem
# Description : Basic template engine with 2 modes
#
###############################################################################

import os
import re
import sys
import importlib
import argparse
import traceback

argparser = argparse.ArgumentParser(prog="teng")
argparser.add_argument("template", type=str, help="Template file to process")
argparser.add_argument("-o", "--output", type=str, default=None, help="Output file to process")
argparser.add_argument("-g", "--enable-globals", action="store_true", help="Allow evals to access python globals()")
argparser.add_argument("-s", "--safe",           action="store_true", help="Disable evals")
argparser.add_argument(      "--strict",         action="store_true", help="Error if a substitution fails")
argparser.add_argument("-e", "--env",            action="store_true", help="Allow pulling values from environment variables")
argparser.add_argument("-d", "--debug",          action="store_true", help="Debug output")
argparser.add_argument(      "--show-env",       action="store_true", help="Print Env")
argparser.add_argument("-A", "--start",  type=str, default="{", help="Start string for format token. Default is {")
argparser.add_argument("-B", "--stop",   type=str, default="}", help="End   string for format token. Default is }")
#argparser.add_argument("-c", "--clean",        action="store_true", dest="clean", help="Clean tokens on separate lines.")
argparser.add_argument("-C", "--noclean",        action="store_false", dest="clean", help="Don't clean tokens on separate lines.")
argparser.add_argument("--test",         type=str, help="Debug regex matching")
argparser.add_argument("vars", nargs=argparse.REMAINDER, help="List of variable definitions")

escape_chars = "+?.*^$[](){}"
def escape_regex(string):
    for c in escape_chars:
        string = string.replace("c", f"\\{c}")
    return string

var___re = re.compile(r"\s*(\w+)(=(.*))?\s*")                               # Basic variable substitution token
ifinl_re = re.compile(r"\s*if(n)?def\s+(\w+)\s+(.*?)(\s+else\s+(.*))?")     # Inline ifdef statement (contains then/else)
ifdef_re = re.compile(r"\s*if((n)?(def|xst))\s+(.*)\s*")                    # Standard ifdef / ifxst (file exists)
ifexp_re = re.compile(r"\s*if\s+(.*)")                                      # Generic if statement
endif_re = re.compile(r"\s*(endif)\s*")                                     # End of if statement
econd_re = re.compile(r"\s*(endif|else)\s*")                                # End of block of if statement
error_re = re.compile(r"\s*error(.*)")                                      # Error
match_re = re.compile(r"\s*(s)?match\s+(.*)")                               # Match
case__re = re.compile(r"\s*(\+?case\s+(.*))")                               # Case
ecase_re = re.compile(r"\s*(\+?case\s+(.*)|endmatch)")                      # End of case/match
#emtch_re = re.compile(r"\s*(endmatch)\s*")                                 # End of match
loop__re = re.compile(r"\s*for\s+(\w+)\s+in\s+(.*)")                        # Loop
eloop_re = re.compile(r"\s*endfor\s*")                                      # End of Loop
decl1_re = re.compile(r"\s*(assert|eval|import)\s+(.*)")                    # Assert / Eval
decl2_re = re.compile(r"\s*(default|define)\s+(\w+)\s+(.*)")                # Default / Define
func__re = re.compile(r"\s*(\w+)\s*\(.*\)\s*")                              # Custom function evaluation

## --------------------------------------------------

_errors = 0
_warnings = 0

def error(*msg, context=None, **kwargs):
    global _errors
    _errors += 1
    if context is not None:
        print("------------------------------------------------------------", file=sys.stderr)
        print("Context:", file=sys.stderr)
        print(context, file=sys.stderr)                                 
    print("ERROR:", *msg, file=sys.stderr, **kwargs)
    if context is not None:
        print("------------------------------------------------------------", file=sys.stderr)
                                                                        
def warn(*msg, context=None, **kwargs):                                 
    global _warnings                                                    
    _warnings += 1                                                      
    if context is not None:                                             
        print("------------------------------------------------------------", file=sys.stderr)
        print("Context:", file=sys.stderr)
        print(context, file=sys.stderr)                                 
    print("WARNING:", *msg, file=sys.stderr, **kwargs)                  
    if context is not None:
        print("------------------------------------------------------------", file=sys.stderr)

## --------------------------------------------------

def build_mapping(format_list, mapping={}):
    pend = ""
    end  = ""
    for fmt in format_list:
        if fmt:
            if pend:
                if fmt[-1] == end:
                    pend = pend + " " + fmt[:-1]

                    if pend.startswith("eval:"):
                        pend = eval(pend[5:], mapping, get_globals())
                    mapping[k] = pend
                    pend = ""
                else:
                    pend = pend + " " + fmt

                continue
            try:
                k, v = fmt.split("=")
                if v and v[0] in ("'", '"') and v[-1] != v[0]: # , "/"
                    pend = v[1:]
                    end  = v[0]
                    continue
                if v.startswith("eval:"):
                    v = eval(v[5:], mapping, get_globals())
                mapping[k] = v
            except ValueError as e:
                error(f"failed to split <{fmt}> into key=value")
    return mapping

def get_globals():
    if args.enable_globals:
        return globals()
    return {}

## --------------------------------------------------

class TEngine:
    def __init__(self, template):
        self.tokens = token_re.split(template)
        self.index = 0

    def token_iter(self):
        i = iter(self.tokens)
        try:
            while True:
                yield next(i) # non-token (static)
                self.index += 1
                yield next(i) # token #[start_i:stop_i]
                self.index += 1
                next(i)       # token internal subgroup
                self.index += 1
        except StopIteration:
            return

    def context(self, window=8):
        lb = max(0, self.index - window)
        rb = min(len(self.tokens)-1, self.index + window)
        lb -= lb % 3
        # index = min(len(self.tokens), self.index)
        # ret = ["\033[38;2;50;50;50"]
        fmt_hi = "\033[0m\033[41m" # "\033[41;5m"
        fmt_mn = "\033[0m\033[37m"
        ret = [fmt_mn]
        for i in range(lb, rb, 3):
            if i == self.index:
                ret.append(fmt_hi + self.tokens[i] + f"{fmt_mn}{{" + self.tokens[i+1] + "}")
            elif (i + 1) == self.index:
                ret.append(self.tokens[i] + f"{fmt_hi}{{" + self.tokens[i+1] + f"}}{fmt_mn}")
            elif (i + 2) == self.index:
                ret.append(fmt_hi + self.tokens[i] + "{" + self.tokens[i+1] + f"}}{fmt_mn}")
            else:
                ret.append(self.tokens[i] + "{" + self.tokens[i+1] + "}")
        ret.append("\033[0m")
        return "".join(ret)
        
    def process(self, env, tokens=None, include=True, target=None, exit_on_target=True):
        static = True
        if tokens is None:
            tokens = self.token_iter() # iter(self.tokens)

        for token in tokens:
            if static:
                if args.debug: print("static:", token)
                yield token
            else:
                if args.debug: print("dynamic:", token)
                if target and (m:=target.fullmatch(token)):
                    yield m.groups()[0]
                    if exit_on_target: return
                else:
                    yield from self.handle_token(token, tokens, env, include)
            static = not static

    def handle_token(self, token, tokens, env, include=True): # , target=None
        if   m := ifexp_re.fullmatch(token): yield from self.handle_cond("if", include and self.eval_expr(m.groups()[0], env), env, tokens, include)
        elif m := match_re.fullmatch(token): yield from self.handle_match(include and self.eval_expr(m.groups()[1], env), m.groups()[0], env, tokens, include)
        elif m := loop__re.fullmatch(token): yield from self.handle_loop(m.groups()[0], (include or []) and self.eval_expr(m.groups()[1], env), env, tokens, include)
        elif (m := ifinl_re.fullmatch(token)) and include: yield m.groups()[2] if (m.groups()[0] == "n") ^ (m.groups()[1] in env) else m.groups()[4] or ""
        elif m := ifdef_re.fullmatch(token): yield from self.handle_cond(m.groups()[0], m.groups()[3], env, tokens, include)
        elif include == False: return
        elif m := error_re.fullmatch(token):
            error("TemplateError", m.groups()[0] or "", context=self.context())
        elif m := var___re.fullmatch(token): 
            val = self.lookup(m.groups()[0], env, default=m.groups()[2])
            if val is None:
                val = (f_unstrict_mode and token_start + token + token_stop) or ""
            yield val
        elif m := decl1_re.fullmatch(token): yield self.handle_decl(m.groups(), env)
        elif m := decl2_re.fullmatch(token): self.handle_decl(m.groups(), env)
        elif m := func__re.fullmatch(token): yield self.eval_expr(token, env) # [1:-1]
        elif not f_unstrict_mode:
            error(f"Unknown/Unexpected token {token}", context=self.context())
        else:
            # print("f_unstrict_mode")
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

    def handle_match(self, value, strict, env, tokens, include):
        found_match = False
        default_tokens = [] 

        # Read default case
        for token in self.process(env, tokens, include, target=case__re):
            if token.startswith("case") or token.startswith("+case"): break
            # if token == "endmatch": raise SyntaxError("Expected case statement got endmatch")
            default_tokens.append(token)

        # Read cases
        while token != "endmatch":
            if include and \
                    self.case_cond(case__re.fullmatch(token).groups()[1], value, env):
                found_match = True

                for token in self.process(env, tokens, True, target=ecase_re, exit_on_target=False):
                    if isinstance(token, str): 
                        if token == "endmatch": return
                        if token.startswith("case"): break
                        if token.startswith("+case"): continue
                    yield token
            else:
                for token in self.process(env, tokens, False, target=ecase_re):
                    continue
                    # if isinstance(token, str):
                    #     if token == "endmatch" or token.startswith("case") or token.startswith("+case"): 
                    #         break

        # Default case if not found
        if include and not found_match:
            if strict:
                error(f"Strict match did not find valid case for value {value!r}", context=self.context())
            else:
                yield from self.process(env, iter(default_tokens), include)

    def case_cond(self, case_exp, value, env):
        exps = case_exp.split("||")
        for exp in exps:
            if value == self.eval_expr(exp, env):
                return True
        return False

    def handle_decl(self, args, env):
        typ, *args = args

        match typ:
            case "assert":
                if not (v:=self.eval_expr(args[0], env)):
                    error(f"Assertion Failed {args[0]} -> {v}")

            case "eval":
                return self.eval_expr(args[0], env)

            case "import":
                # return self.exec_expr(f"import {args[0]}", env)
                match args[0]:
                    case "math"  : env["math"] = importlib.import_module("math")
                    case "random": env["random"] = importlib.import_module("random")
                    case _: error(f"Unsupported library <{args[0]}>")

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
        error(f"lookup: {var} Not Defined", context=self.context())

    def eval_expr(self, expr, env):
        if args.safe: 
            warn(f"Safe Mode: Skipping evaluated expression <{expr}>")
            return None
        try:
            return eval(expr, env, get_globals())
        except NameError as e:
            error(f"Undefined variable in expression {expr}: {e}")
        except Exception as e:
                error(f"Exception occurred while evaluating expression\n  Expression: {expr}\n  Exception : {e}\n{traceback.format_exc()}")
                # error(f"Exception occurred while evaluating expression\n  Expression: {expr}\n  Exception : {e}\n  Env : {env}\n{traceback.format_exc()}")

    def exec_expr(self, expr, env):
        if args.safe: 
            warn(f"Safe Mode: Skipping evaluated expression <{expr}>")
            return None
        try:
            return exec(expr, env, get_globals())
        except NameError as e:
            error(f"Undefined variable in expression {expr}: {e}")
        except Exception as e:
            error(f"Exception occurred while evaluating expression\n  Expression: {expr}\n  Exception : {e}\n{traceback.format_exc()}")

        
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
    tokens = zip([token_re, var___re, ifinl_re, ifdef_re, ifexp_re, endif_re, econd_re, match_re, case__re, ecase_re, loop__re, eloop_re, decl1_re, decl2_re, func__re],
                 ["token_re", "var___re", "ifinl_re", "ifdef_re", "ifexp_re", "endif_re", "econd_re", "match_re", "case__re", "ecase_re", "loop__re", "eloop_re", "decl1_re", "decl2_re", "func__re"])

    if args.test:
        for token, name in tokens:
            print(name, token.fullmatch(args.test), sep="\t--\t")
        exit()

    f_unstrict_mode = not args.strict

    env = build_mapping(args.vars, mapping=dict(os.environ) if args.env else {})

    with open(args.template, "r") as file:
        if args.clean:
            clean_re = re.compile(f"^\\s*({start_re}(((?!{start_re}|{stop_re}).)+){stop_re})\\s*$")
            data = []
            for line in file.readlines():
                if (m := clean_re.fullmatch(line)) and not var___re.match(m.groups()[2]):
                    data.append(m.groups()[0])
                else:
                    data.append(line)
            data = "".join(data)

        else:
            data = file.read()

        engine = TEngine(data)
        
    if args.output:
        with open(args.output, "w") as file:
            for token in engine.process(env):
                if token is not None:
                    file.write(str(token))

    # elif args.debug:
    #     for token in engine.process(env):
    #         #if token == '\n': continue
    #         if token is not None:
    #             print(repr(token), end="")

    else:
        for token in engine.process(env):
            #if token == '\n': continue
            if token is not None:
                print(token, end="")

    if args.show_env:
        print(env)

    if _errors or _warnings:
        print(f"Completed with {_errors} errors and {_warnings} warnings.", file=sys.stderr)
        exit(1)
