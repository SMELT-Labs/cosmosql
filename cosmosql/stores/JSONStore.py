import json
import os
# import uuid
from SMELT.Store import Store, Connection
from datetime import datetime, date


def deserializeJSON(obj):
    if "$DATETIME" in obj:
        return datetime.fromisoformat(obj["$DATETIME"])
    elif "$DATE" in obj:
        return date.fromisoformat(obj["$DATE"])
    return obj


def serializeJSON(obj):
    if isinstance(obj, datetime):
        return {"$DATETIME": obj.isoformat()}
    elif isinstance(obj, date):
        return {"$DATE": obj.isoformat()}


class JSONStore(Store):
    """
    TODO: Implement sorting in JSONStore
    TODO: Implement limit in JSONStore
    TODO: Implement AGGREGATES
    """

    def __init__(self, connection: Connection):
        super().__init__(connection)
        try:
            with open(self.connection.database) as infile:
                self.data = json.load(infile, object_hook=deserializeJSON)
        except FileNotFoundError:
            self.data = {
                'tables': {}
            }

    def __save__(self):
        with open(self.connection.database, 'w') as outfile:
            json.dump(self.data, outfile,
                      default=serializeJSON,
                      indent=self.connection.options.get("indent", None),
                      sort_keys=self.connection.options.get("sort_keys", False))

    def where(self, prop, comparison, value, entries=[]):
        if comparison == "==":
            return list(filter(lambda x: x[prop] == value, entries))
        elif comparison == "!=":
            return list(filter(lambda x: x[prop] != value, entries))
        elif comparison == "<=":
            return list(filter(lambda x: x[prop] <= value, entries))
        elif comparison == ">=":
            return list(filter(lambda x: x[prop] >= value, entries))
        elif comparison == "<":
            return list(filter(lambda x: x[prop] < value, entries))
        elif comparison == ">":
            return list(filter(lambda x: x[prop] > value, entries))
        elif comparison == "~=":
            if isinstance(value, str):
                if value[0] == "%" and value[-1] == "%":
                    return list(filter(lambda x: value[1:-1] in x[prop], entries))
                elif value[0] == "%":
                    return list(filter(lambda x: x[prop].endswith(value[1:]), entries))
                elif value[-1] == "%":
                    return list(filter(lambda x: x[prop].startswith(value[:-1]), entries))
                elif "%" in value:
                    start, end = value.split("%", 1)
                    return list(filter(lambda x: x[prop].startswith(start) and x[prop].endswith(end), entries))
                else:
                    return self.where(prop, "==", value, entries)
            return []

    def __build_insert__(self, query, ordering):
        inserts = query.CRITERIA["set"]
        return {
                   'name': query.SELECTOR["document"],
                   'columns': [x[0] for x in inserts],
                   'entry': {x[0]: "?" for x in inserts}
               }, [ordering["set"]]

    def __build_select__(self, query, ordering):
        return {
                   "doc": query.SELECTOR["document"],
                   "query": query,
               }, [ordering["where"]]

    def __build_update__(self, query, ordering):
        query.SELECTOR["properties"] = []
        build, _ = self.__build_select__(query, ordering)
        return {
                   "select_build": build,
                   "ordering": ordering,
                   "columns": [x[0] for x in query.CRITERIA["set"]]
               }, [ordering["set"]]

    def __build_delete__(self, query, ordering):
        query.SELECTOR["properties"] = []
        build, _ = self.__build_select__(query, ordering)
        return {
                   "select_build": build,
                   "ordering": ordering,
               }, []

    def __run_insert__(self, build, params):

        param = iter(params)
        entry = {key: next(param) for key in build["entry"].keys()}

        if build["name"] not in self.data["tables"]:
            self.data["tables"][build["name"]] = {
                'columns': build['columns'],
                'entries': [entry]
            }
        else:
            self.data["tables"][build["name"]]["entries"].append(entry)
        try:
            self.__save__()
            return True
        except:
            return False

    def __run_select__(self, build, params):
        query = build["query"]
        param = iter(params)
        entries = self.data["tables"].get(build["doc"], {}).get("entries", [])
        if 'where' in query.CRITERIA:
            tmp = []
            for comp in query.CRITERIA["where"]["comparisons"]:
                if query.CRITERIA["where"]["boolean"] == "and":
                    tmp = self.where(comp[0], comp[1], next(param), entries=tmp)
                else:
                    tmp += self.where(comp[0], comp[1], next(param), entries=entries)
                    added = []
                    _tmp = []
                    for t in tmp:
                        unique = str(t)
                        if unique not in added:
                            _tmp.append(t)
                            added.append(unique)
                    tmp = _tmp
            entries = tmp
        if query.SELECTOR["properties"]:
            return list(map(lambda x: {key: x[key] for key in query.SELECTOR["properties"]}, entries))
        else:
            return entries

    def __run_update__(self, data, params):
        entries = self.__run_select__(data["select_build"], data["ordering"]["where"])
        table_entries = self.data["tables"].get(data["select_build"]["doc"], {}).get("entries", [])

        for entry in entries:
            if entry in table_entries:
                index = table_entries.index(entry)
                table_entries[index].update(dict(zip(data["columns"], params)))

        try:
            self.__save__()
            return len(entries)
        except:
            return 0

    def __run_delete__(self, data, params):
        entries = self.__run_select__(data["select_build"], data["ordering"]["where"])
        table_entries = self.data["tables"].get(data["select_build"]["doc"], {}).get("entries", [])

        for entry in entries:
            if entry in table_entries:
                table_entries.remove(entry)

        try:
            self.__save__()
            return len(entries)
        except:
            return 0
