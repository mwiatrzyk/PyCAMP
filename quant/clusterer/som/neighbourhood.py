"""Definition of neighbourhood functions. Each neighbourhood function is a
generator taking four arguments: 
    * index of central node
    * radius of neighbourhood
    * number of columns in SOM grid
    * number of rows in SOM grid"""


def rectangular(index, radius, rows, cols):
    """Defines rectangular neighbourhood (the SOM's default)."""
    row = index / cols
    col = index % cols
    radius = int(radius)
    rowstart = row-radius
    if rowstart < 0:
        rowstart = 0
    rowend = row+radius
    if rowend >= rows:
        rowend = rows-1
    colstart = col-radius
    if colstart < 0:
        colstart = 0
    colend = col + radius
    if colend >= cols:
        colend = cols-1
    for r in xrange(rowstart, rowend+1):
        for c in xrange(colstart, colend+1):
            yield r * cols + c, max(abs(r-row), abs(c-col))
