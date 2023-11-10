from collections import namedtuple

# classes for inputs
Table = namedtuple("Table", "nick, name, columns")
Feature = namedtuple("Feature", "nick, name, operations")
Condition = namedtuple("Condition", "main_feat, comparison_feats, operator")

class RawSelectQuery:
    """
    make basic queries in SQL
    """
    def __init__(self, **kwargs) -> None:
        self.query = ''
        self.construct(**kwargs)

    def construct(self, **kwargs):
        if 'tables' not in kwargs:
            raise KeyError("Must specify what table to use")
        self.query += "SELECT "

        if 'distinct' in kwargs:
            self.query += "DISTINCT "

        tables = kwargs["tables"]

        all_flag = False
        names = {}
        for i, (nick, name, table) in enumerate(tables):
            # use nick name if provided else use name
            assert nick not in names
            if nick:
                names[nick] = name
            else:
                names[name] = name

            if all_flag:
                break
            for column in table:
                if isinstance(column, str):
                    # breakout if select all
                    if column == "*":
                        self.query += column
                        all_flag = True
                        break
                    else:
                        self.query += f"{nick}.{column}, "
                    continue

                assert column.operations # must include an operations field if not a string input
                operations = column.operations
                for operation in operations:
                    self.query += f"{operation.upper()}("
                self.query += f"{nick}.{column.name}" + ")"*len(operations) + ", "


        self.query = self.query[:-2] + "\nFROM "

        for nick, name in names.items():
            if name != nick:

                self.query += f"{name} AS {nick}, "
            else:
                self.query += f"{name}, "
        self.names = names
        self.query = self.query[:-2]
        # From here on, if there was a self join, then we use indices to refer to features in the input
        # otherwise column name + feature name is acceptable
        if "where" in kwargs:
            self.where(kwargs["where"])
        if "group" in kwargs:
            self.group(kwargs["where"])
            if "having" in kwargs:
                self.having(kwargs["having"])
        if "order" in kwargs:
            self.order(kwargs["order"])

    def _add_condition(self, op, operands, condition):
        if condition.upper() == "IN":
                self.query += f"{op} {condition} ({', '.join(operands)})"
        elif condition.upper() == "BETWEEN":
            self.query += f"{op} {condition} {operands[0]} AND {operands[1]}"
        else:
            self.query += f"{op} {condition} {operands}"

    def where(self, where):
        """add where conditions and join together by logical operators"""
        self.query += "\nWHERE "
        conditions, ops = where[0::2], where[1::2]
        for (op, operands, condition), joiner in zip(conditions, ops):
            self._add_condition(op, operands, condition)
            self.query += f"\n{joiner} "

        self._add_condition(*conditions[-1])
        # where follows the pattern of columns, relation, restriction


    def order(self, order):
        if order.direction not in ("ASC", "DESC"):
            raise ValueError("Must either be ascending or descending")
        self.query += f"\n ORDER BY {order.nick}.{order.name} {order.direction}"

    def group(self, group):
        self.query += f"\nGROUP BY {group.nick}.{group.name}"

    def limit(self, limit:int):
        if not isinstance(limit, int):
            raise TypeError("Limit must be an integer value")
        self.query += f"\nLIMIT {limit}"

    def having(self, having):
        self.query += "\nHAVING "
        conditions, ops = having[0::2], having[1::2]
        for (preprocess, op, operands, condition), joiner in zip(conditions, ops):
            self._add_condition(op, operands, condition)
            self.query += f"\n{joiner} "

        self._add_condition(*conditions[-1])

    def get_query(self):
        return self.query




def make_select_query(**kwargs):
    print(kwargs)
    q = RawSelectQuery(**kwargs)
    return q.get_query()

if __name__ == "__main__":

    print(
        make_select_query(
            tables=(
                Table("d0", "dogs",
                 [Feature("b0","breed",("COUNT",)),
                 "weight"]),
                Table("c0", "cats",
                 ["breed","weight"])
                ),
            where=(("d0.weight", ("c0.weight",), "IN"),"AND",("c0.weight", (10,20), "BETWEEN"))
            ),
            ### operands, operator,

        )