from pyparsing import (
    Word,
    delimitedList,
    Optional,
    Group,
    alphanums,
    nums,
    CaselessKeyword,
    pyparsing_common as ppc,
    Suppress,
    Literal,
    removeQuotes,
    printables,
    Combine,
)


def string_with_delim(delim, start=None, end=None, name=None):
    res = Literal(delim)
    if start:
        res += start

    if end:
        res += Word(printables, excludeChars=[Literal(delim), end])
        res += end
    else:
        res += Word(printables, excludeChars=[Literal(delim)])

    res += Literal(delim)
    return Combine(res).setName(name)


def string(start=None, end=None):
    return (
            string_with_delim('"', start, end, "DOUBLE_STRING")
            | string_with_delim('`', start, end, "SINGLE_STRING")
            | string_with_delim("'", start, end, "BACK_STRING")
    ).setName("STRING").addParseAction(removeQuotes)


def arg(thing, optional=False):
    if optional:
        return Group(Optional(LPAREN + thing + RPAREN))
    return Group(LPAREN + thing + RPAREN).setName("arg")


def args(thing, optional=False, delim=","):
    if optional:
        return Group(Optional(LPAREN + delimitedList(thing, delim=delim) + RPAREN))
    return Group(LPAREN + delimitedList(thing, delim=delim) + RPAREN).setName("args")


def add_boolean_type(_type):
    def add_boolean(_, __, tokens):
        return [_type] + [token for token in tokens]

    return add_boolean


def convertToNone(*args):
    return [None]


STRING = (string()).setName("STRING")

TOKEN = (Word(alphanums + "_$"))

DIGIT = (
        Literal("0")
        | Literal("1")
        | Literal("2")
        | Literal("3")
        | Literal("4")
        | Literal("5")
        | Literal("6")
        | Literal("7")
        | Literal("8")
        | Literal("9")
)

NULL = CaselessKeyword("NULL") \
    .addParseAction(convertToNone)

INTEGER = Combine(
    Optional('-')
    + Word(nums)
).addParseAction(ppc.convertToInteger)

FLOAT = Combine(
    Optional('-')
    + Word(nums)
    + '.'
    + Word(nums)
    + Optional('f').suppress()
).addParseAction(ppc.convertToFloat)

FLOAT2 = Combine(
    Optional('-')
    + Word(nums)
    + Literal('f').suppress()
).addParseAction(ppc.convertToFloat)

NUMBER = (
        FLOAT2 | FLOAT | INTEGER
).setName("NUMBER")

DATE_DDMMYYYY = Combine(
    DIGIT + DIGIT
    + '-'
    + DIGIT + DIGIT
    + '-'
    + DIGIT + DIGIT + DIGIT + DIGIT
).addParseAction(ppc.convertToDate('%d-%m-%Y'))

DATE_YYYYMMDD = Combine(
    DIGIT + DIGIT + DIGIT + DIGIT
    + '-'
    + DIGIT + DIGIT
    + '-'
    + DIGIT + DIGIT
).addParseAction(ppc.convertToDate('%Y-%m-%d'))

DATE = (
        DATE_DDMMYYYY
        | DATE_YYYYMMDD
)

DATETIME_DDMMYYYY = Combine(
    DATE_DDMMYYYY + "T"
    + DIGIT + DIGIT + ":"
    + DIGIT + DIGIT + ":"
    + DIGIT + DIGIT + "."
    + DIGIT + DIGIT + DIGIT
).addParseAction(ppc.convertToDatetime("%d-%m-%YT%H:%M:%S.%f"))

DATETIME_YYYYMMDD = Combine(
    DATE_YYYYMMDD + "T"
    + DIGIT + DIGIT + ":"
    + DIGIT + DIGIT + ":"
    + DIGIT + DIGIT + "."
    + DIGIT + DIGIT + DIGIT
).addParseAction(ppc.convertToDatetime("%Y-%m-%dT%H:%M:%S.%f"))

DATETIME = (
        DATETIME_DDMMYYYY
        | DATETIME_YYYYMMDD
)

# How to remember what enclosure to use.
# [P][a]rens = [P]roperties and [A]rguments to functions
# [C]urly [B]race = [C]riteria [B]ody
# [S]quare Bracket = [S]ummary aka Aggregates
LPAREN, RPAREN, LBRACE, RBRACE, LBRACKET, RBRACKET = map(
    Suppress, "(){}[]"
)

CREATE, INSERT, SAVE, SELECT, READ, GET, UPDATE, DELETE, REMOVE, DROP = map(
    CaselessKeyword, "create insert save select read get update delete remove drop".split()
)

_CREATE = (CREATE | INSERT)
_READ = (READ | GET | SELECT)
_UPDATE = (UPDATE | SAVE)
_DELETE = (DELETE | REMOVE | DROP)

CRUD = (_CREATE | _READ | _UPDATE | _DELETE).setName("CRUD_TOKEN")

PROPERTY = TOKEN.setName("DOCUMENT_PROPERTY")
ORDERED_PROPERTY = Group(
    (Literal("-") | Literal("+"))
    + TOKEN
).setName("ORDERED_DOCUMENT_PROPERTY")
WILDCARD_PROPERTY = (
    Optional(Literal("*"))
)

DOCUMENT = Group(
    TOKEN
    + args(PROPERTY, optional=True)
).setName("DOCUMENT_SELECTOR").setResultsName("DOCUMENTS")

SORT = (
        CaselessKeyword("sort")
        + args(ORDERED_PROPERTY)
).setName("METHOD_SORT")

LIMIT = (
        CaselessKeyword("limit")
        + Group(LPAREN + INTEGER + Optional(Literal(",").suppress() + INTEGER) + RPAREN)
).setName("METHOD_LIMIT")

COUNT = (
        CaselessKeyword("count")
        + ((LPAREN + Literal("*") + RPAREN)
           | arg(PROPERTY))
).setName("METHOD_COUNT")

AVG = (
        CaselessKeyword("AVG")
        + arg(PROPERTY)
).setName("METHOD_AVG")

MAX = (
        CaselessKeyword("MAX")
        + arg(PROPERTY)
).setName("METHOD_MAX")

MIN = (
        CaselessKeyword("MIN")
        + arg(PROPERTY)
).setName("METHOD_MIN")

COMPARATOR = (
        Literal("==")
        | Literal("<=")
        | Literal(">=")
        | Literal(">")
        | Literal("<")
        | Literal("!=")
        | Literal("is")
).setName("COMPARATOR")

LIKE = (
        PROPERTY
        + "~="
        + (
            Literal("?")
            | (string() | string(start="%") | string(start="%", end="%") | string(end="%"))
        )
).setName("SEARCH_STRING")

VALUE = (
        Literal("?")
        | NULL
        | DATETIME
        | DATE
        | NUMBER
        | string()
).setName("VALUE")

BOOLEAN = Group(
    (PROPERTY + COMPARATOR + VALUE)
    | LIKE
).setName("BOOLEAN")

BOOLEANS = (
        arg(BOOLEAN).setParseAction(add_boolean_type(None))
        | args(BOOLEAN, delim=',').setParseAction(add_boolean_type('and'))
        | args(BOOLEAN, delim='|').setParseAction(add_boolean_type('or'))
).setName("BOOLEANS")

WHERE = (
        CaselessKeyword("where")
        + BOOLEANS
).setResultsName('WHERE')

SET = (
        CaselessKeyword("set")
        + args(Group(PROPERTY + Literal("=") + VALUE))
).setName("METHOD_SET")

VALID_METHOD = Group(SORT ^ LIMIT ^ WHERE ^ SET)
VALID_AGGREGATE = Group(COUNT ^ AVG ^ MAX ^ MIN)

CRITERIA = Group(
    LBRACE
    + delimitedList(VALID_METHOD)
    + RBRACE
).setName("CRITERIA").setResultsName('CRITERIA')

AGGREGATES = Group(
    LBRACKET
    + delimitedList(VALID_AGGREGATE)
    + RBRACKET
).setName("AGGREGATES").setResultsName('AGGREGATES')

QUERY = (
        CRUD
        + DOCUMENT
        + Optional(CRITERIA, default=None)
        + Optional(AGGREGATES, default=None)

).setName("QUERY").setResultsName('QUERY')


def _list(thing):
    return [x for x in thing]


class Query:
    def __str__(self):
        return """
        \rCRUD = %r
        \rSELECTOR = %r
        \rCRITERIA = %r
        \rAGGREGATES = %r
        """ % (self.CRUD, self.SELECTOR, self.CRITERIA, self.AGGREGATES)

    def __init__(self, query):
        self.RAW = QUERY.parseString(query, parseAll=True)
        self.CRUD = self.RAW[0]
        selector = self.RAW[1]
        criteria = self.RAW[2]
        aggregates = self.RAW[3]
        self.SELECTOR = {
            'document': selector[0],
            'properties': selector[1].asList()
        }
        # for selector in selectors:
        #     self.SELECTORS[selector[0]] = list(selector[1])

        self.AGGREGATES = {}
        if aggregates:
            for aggregate in aggregates:
                self.AGGREGATES[aggregate[0]] = aggregate[1:]

        self.CRITERIA = {}
        if criteria:
            for criterion in criteria:
                self.CRITERIA[criterion[0]] = criterion[1:]
            if 'limit' in self.CRITERIA:
                l = [x for x in list(self.CRITERIA['limit'])[0]][::-1]
                # print(l)
                self.CRITERIA['limit'] = {'limit': (l[0:1] or [None])[0], 'offset': (l[1:2] or [None])[0]}
            if 'set' in self.CRITERIA:
                sets = []
                for i in self.CRITERIA['set']:
                    for j in i:
                        sets.append(j.asList())
                self.CRITERIA['set'] = sets
            if 'sort' in self.CRITERIA:
                SORT = {}
                sort = list(self.CRITERIA['sort'])[0]
                print(sort)
                for s in sort:
                    if s[0] == '-':
                        SORT[s[1]] = -1
                    else:
                        SORT[s[1]] = 1
                self.CRITERIA['sort'] = SORT
            if 'where' in self.CRITERIA:
                where = self.CRITERIA['where']
                self.CRITERIA['where'] = {
                    'boolean': where[0],
                    'comparisons': [list(comp) for comp in where[1]]
                }

c = """create artists(name,songs){set(name = "john", songs = 24-12-2020, balance = 3.001)}"""
# r = """select artists(name, songs){limit(1,5), where(name == "john")}[count(*), AVG(songs)]"""
# u = """update artists(name){set(name = "john", songs = 3f)}"""
# d = """delete artists(songs){where(songs < 5)}"""
print(Query(c).RAW)
# print(Query(r).CRITERIA)
# print(Query(u).RAW)
# print(Query(d).RAW)
