#!/usr/bin/env python
# vim: et ts=4 sw=4


class Cell(object):

    """
    This class represents a single table cell. It does not hold a value,
    only references to the Column and Row which it intersects. The value
    is fetched from the Row, and rendered by the Column.
    """

    def __init__(self, column, row):
        self.column = column
        self.row = row

    def __unicode__(self):
        """Return the rendered (via self.column) value of this cell."""
        return unicode(self.column.render(self))

    @property
    def value(self):
        """Return the value of this cell."""
        return getattr(self.row, self.column.name)
