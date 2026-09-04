import csv
import re
# from retools import infer_type
from dataclasses import dataclass

# Retools --------------------------------------------------

@dataclass
class RegexMatch(str):
    dtstr: str
    match: re.Match = None

    def __eq__(self, regex):
        if isinstance(regex, str):
            self.match = re.fullmatch(regex, self.dtstr)
        else:
            self.match = regex.fullmatch(self.dtstr)

        return self.match is not None

# ------------------------------------------------
# func: infer_type
# - basic type inference from 
# ------------------------------------------------

def infer_type(value):
    match RegexMatch(value):
        case r'\d+'                  : return int(value)
        case r'\d*\.\d+([eE]-?\d+)?' : return float(value)
        case r'(NaN|nan)'            : return float('nan')
        case r'(inf|-inf)'           : return float(value)
        case r'(true|True)'          : return True
        case r'(false|False)'        : return False
    return value

# CSV LIB --------------------------------------------------

addr_re = re.compile(r'([A-Z]+)([0-9]+)')

def std_column_gen(lang=" ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
    base = len(lang)
    i = 1

    while True:
        v = i
        i += 1

        if v % base == 0: continue

        s = ""
        while v > 0:
            s = lang[v % base] + s
            v //= base
        yield s

def get_n_from_gen(n, gen):
    return [v for i,v in zip(range(n),gen)]

def read(file, dialect='unix', read_header=True, start=0, stop=-1):
    return CSV.from_file(file, dialect, read_header, start, stop)

class CSV:
    @classmethod
    def from_file(cls, file, dialect='unix', read_header=True, start=0, stop=-1):
        with open(file, "r", newline="") as csvfile:
            reader = csv.reader(csvfile)

            if read_header: 
                header = [h.strip() for h in next(reader)]
                data = [None, header]
            else:
                header = None
                data = [None]

            for i in range(start): next(reader)

            i = start
            for row in reader:
                data.append([infer_type(v.strip()) for v in row])
                i += 1
                if i == stop: break

        return cls(header, data)

    def __init__(self, header, data):
        self.raw_header = header
        self.data = data

        self.stdgen = std_column_gen()
        self.header = {h:i for i,h in enumerate(header)}
        self.stdhdr = {v:i for i,v in zip(range(len(header)), self.stdgen)}

    def columns(self):
        return [CSVColumn(h) for h in self.raw_header or self.stdhdr]

    def rows(self):
        if self.raw_header: return self.data[2:]
        return self.data[1:]

    def __getitem__(self, key):
        match key:
            case int() as row: 
                return self.data[row]
            case int() as row, int() as col: 
                return self.data[row][col]

            case str():
                if key.isalpha():
                    c = self.hdr2col(key)
                    return [row[c] for row in self.rows()]
                else:
                    col, row = addr_re.fullmatch(key).groups()
                    return self.data[int(row)][self.hdr2col(col)]
            case CSVColumn() as col:
                return self[col.name]

            case str() as col, int() as row:
                return self.data[row][self.hdr2col(col)]
            case int() as row, str() as col:
                return self.data[row][self.hdr2col(col)]

            # case slice() as mslice:
            #     raise NotImplementedError
            # case int() as row, slice() as cslice:
            #     raise NotImplementedError
            # case str() as col, slice() as rslice:
            #     raise NotImplementedError
            # case slice() as cslice, slice() as rslice:
            #     raise NotImplementedError



            case _: 
                raise NotImplementedError(f"Key: {key}")

    def hdr2col(self, key):
        if (v := self.stdhdr.get(key)) is not None:
            return v
        if self.header:
            if (v := self.header.get(key)) is not None:
                return v
        raise KeyError

    def add_computed_column(self, formula, *cols, name=None):
        stdh = next(self.stdgen)
        coli = len(self.header)
        start = 1

        if self.raw_header:
            self.raw_header.append(name or "")
            start = 2
        if name:
            self.header[name] = coli
        self.stdhdr[stdh] = coli

        for r in range(start, len(self.data)):
            self.data[r].append(formula(*[self[r, c] for c in cols]))

    def write(self, file, dialect='unix'):
        with open(file, "w", newline='') as csvfile:
            writer = csv.writer(csvfile)
            for row in self.data[1:]:
                writer.writerow(row)

    # --------------------------------------------
    # func: pivot
    # - filters: dict col : function(value in col)
    # - rows: list of cols
    # - data: dict col : function([values in col])
    # --------------------------------------------

    def pivot(self, data={}, rows=[], cols=[], filters={}):
        groups = {}
        dcs, dfs = zip(*[(self.hdr2col(c),f) for c,f in data.items()])
        # dcs, dfs = zip(*[(self.hdr2col(c),f[1] if isinstance(f, (list, tuple)) else f) for c,f in data.items()])

        # TODO : support multiple outputs that use the same column: eg average, stdev of same col
        # TODO : support simple filters where value is a value to match or a list to select from

        for row in self.rows():

            # Filter ---------------------------------------

            inc = True
            for c, f in filters.items(): 
                if not f(row[self.hdr2col(c)]):
                    inc = False
                    break
            if not inc: continue

            # Groups ---------------------------------------

            gs = (tuple([row[self.hdr2col(c)] for c in rows]),
                  tuple([row[self.hdr2col(c)] for c in cols]))
            if gs not in groups:
                groups[gs] = [[row[c]] for c in dcs]
            else:
                for i, c in enumerate(dcs):
                    groups[gs][i].append(row[c])

        # Compute --------------------------------------

        table = {}
        for key, group in groups.items():
            table[key] = [f(group[i]) for i,f in enumerate(dfs)]

        return table

    def write_pivot(self, file, data={}, rows=[], cols=[], filters={}):
        pivot = self.pivot(data=data, rows=rows, cols=cols, filters=filters)

        #             col 0            C0v1             C0v2
        #             col 1            C1v1   C1v2      C1v1        C1v2
        # rowheader   data 1   data 2 
        # R0v1  R1v1  
        # R0v2  R1v1

        table = []

        unique_cols = set()
        unique_rows = set()

        for row, col in pivot:
            unique_rows.add(row)
            unique_cols.add(col)
        sorted_cols = sorted(unique_cols)
        sorted_rows = sorted(unique_rows)

        ndata = len(data)
        ncols = len(sorted_cols)
        entries = ndata * ncols
        

        # data header
        # table.append([""]*max(1,len(rows)) + sum([[d] + [""]*(len(sorted_cols)-1) for d in data], start=[]))

        # column header
        for i in range(len(cols)): 
            table.append([""] * max(1,len(rows)-1) + [cols[i]] + [c[i] for c in sorted_cols]*ndata)

        # row and data header
        # table.append(rows) # row only
        table.append(rows + sum([[d] + [""]*(len(sorted_cols)-1) for d in data], start=[]))

        # data
        for row in sorted_rows:
            data_row = [""] * ndata * ncols
            for c, col in enumerate(sorted_cols):
                key = (row, col)
                if (data := pivot.get(key)) is not None:
                    for d, dat in enumerate(data):
                        data_row[c+d*ncols] = dat
            if row:
                table.append([*row, *data_row])
            else:
                table.append(["", *data_row])

        # write to file
        with open(file, "w", newline='') as csvfile:
            writer = csv.writer(csvfile)
            for row in table:
                writer.writerow(row)



@dataclass(frozen=True)
class CSVColumn:
    name: str
    # index: int

