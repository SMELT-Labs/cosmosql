from SMELT.Store import Store, Connection
import sqlite3

class SQLiteStore(Store):


    def __before_run__(self):
        self.conn = sqlite3.connect(self.connection.database)
        self.c = self.conn.cursor()

    def __after_run__(self):
        # self.c.execute()
        self.conn.commit()
        self.conn.close()

    def __build_where__(self,query):
        if "where" in query.CRITERIA:
            doc = query.SELECTOR["document"]
            comps = ["%s.%s %s %s"%(doc, x[0],x[1],"?") if x[1] != "~=" else "%s.%s LIKE %s"%(doc,x[0], "?") for x in query.CRITERIA["where"]["comparisons"]]
            return "WHERE %s" % (
                (" %s " % (query.CRITERIA["where"]["boolean"] or '')).upper().join(comps)
            )
        return ''

    def __build_insert__(self, query, ordering):
        inserts = query.CRITERIA["set"]
        data = {x[0]: x[2] for x in inserts}
        return "INSERT INTO %s (%s) VALUES (%s)" % (
            query.SELECTOR["document"],
            ', '.join([x for x in data.keys()]),
            ', '.join(["?" for x in data.values()])
        ), [ordering["set"]]

    def __build_select__(self, query, ordering):
        doc = query.SELECTOR["document"]
        props = query.SELECTOR["properties"]
        return "SELECT %s FROM %s %s" % (
            ', '.join(["%s.%s" % (doc, prop) for prop in props]),
            doc,
            self.__build_where__(query)
        ), [ordering["where"]]

    def __build_update__(self, query, ordering):
        doc = query.SELECTOR["document"]
        inserts = query.CRITERIA["set"]
        # print(query)
        return "UPDATE %s SET %s %s" % (
            doc,
            ', '.join(["%s = %s" % (x[0], "?") for x in inserts]),
            self.__build_where__(query)
        ), [ordering["set"], ordering["where"]]


    def __build_delete__(self, query, ordering):
        doc = query.SELECTOR["document"]
        return "DELETE FROM %s %s" % (
            doc,
            self.__build_where__(query)
        ), [ordering["where"]]

    def __run_insert__(self, build, params):
        try:
            self.c.execute(build, params)
            return True
        except Exception:
            return False

    def __run_select__(self, build, params):
        self.c.execute(build, params)
        return self.c.fetchall()

    def __run_update__(self, build, params):
        print(build, params)
        self.c.execute(build, params)
        return self.c.rowcount

    def __run_delete__(self, build, params):
        self.c.execute(build, params)
        return self.c.rowcount




