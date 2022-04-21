'''Generate an SVG file from a given list.
I.e. give a list of a lists of vertices.
E.g. [[0,1,2,3],[3,4,5,6,7,8,9,10]]
or a list of lists of vertex coordinate pairs
E.g. [[[0,1],[0,2]],[[3,4],[5,6]]]
...always in X-Y succession. If there are two points, use line, or use polyline
if three or more. If three numbers, it's a X-Y-R circle.
If color specified, add it as a color name as a last item in the list. [1,2,3,4,'blue'] for a 1,2-3,4 line

Return a text file that can be written out.

Warning! In comparison to original, ViewBox has been omitted
'''


def svggen(vertices, filename=None, xoffset=0, yoffset=0, zoom=1, linewidth=1):
    '''Main one, works as described above.
    If as a second parameter file with path is specified, it's saved there too.
    Xoffset, Yoffset: added to all positions
    zoom: Multiplicator of all positions
    linewidth: how wide is each line
    '''
    header = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<!-- Creator: Python_SVGGEN -->
<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" width="{0}mm" height="{1}mm" version="1.1" style="shape-rendering:geometricPrecision; text-rendering:geometricPrecision; image-rendering:optimizeQuality; fill-rule:evenodd; clip-rule:evenodd" viewBox="0 0 {0} {1}"
 xmlns:xlink="http://www.w3.org/1999/xlink">
 <defs>
  <style type="text/css">
   <![CDATA[
    .fil0 {fill:none}
   ]]>
  </style>
 </defs>
 <g id="Layer1">
'''
    outfile = ''  # Collector

    xylist = []  # Aggregator of all X/Y points for viewport calculations

    for seg in vertices:
        loccolor = 'black'  # Which color is it?

        # Find if color is specified
        if isinstance(seg[-1], str):
            loccolor = seg[-1]
            seg = seg[0:-1]
            # Check if instead of raw name or hex, it was in 'r,g,b' format
            if loccolor.count(',') == 2:
                # Indeed, r,g,b
                loccolor = loccolor.split(',')
                loccolor = [int(v) for v in loccolor]
                loccolor = '#%02x%02x%02x' % tuple(loccolor)

        # Process segment by segment
        if len(seg) == 3 and (isinstance(seg[0], float) or isinstance(seg[0], int)):
            # Circle
            outfile += ('  <circle class="fil0" style="stroke-width:{3};stroke:{4};" cx="{0}" cy="{1}" r="{2}" />\n').format(
                seg[0] * zoom + xoffset, seg[1] * zoom + yoffset, seg[2] * zoom, linewidth, loccolor)
            xylist.append([seg[0] * zoom + xoffset + seg[2] * zoom, seg[1] * zoom + yoffset + seg[2] * zoom])
            xylist.append([seg[0] * zoom + xoffset - seg[2] * zoom, seg[1] * zoom + yoffset - seg[2] * zoom])
            continue

        # Check if pairs of coordinates need to be split out (flattened)
        if isinstance(seg[0], list) or isinstance(seg[0], tuple):
            # Yes, flatten it out
            collect = []
            [collect.extend([x, y]) for x, y in seg]
            seg = collect

        # Generate either

        if len(seg) % 2:
            print('Warning! Odd number of vertices in SVGGEN:', seg)
            continue  # Odd number of vertices, ignore!

        # Get to generation
        if len(seg) == 4:
            # Standard line
            outfile += (('  <line class="fil0" style="stroke-width:{4};stroke:{5};" x1="{0}" y1="{1}" x2="{2}" y2= "{3}" />\n').format(
                seg[0] * zoom + xoffset, seg[1] * zoom + yoffset, seg[2] * zoom + xoffset, seg[3] * zoom + yoffset, linewidth, loccolor))
            xylist.append([seg[0] * zoom + xoffset, seg[1] * zoom + yoffset])
            xylist.append([seg[2] * zoom + xoffset, seg[3] * zoom + yoffset])

        else:
            # Polyline
            outfile += ('  <polyline class="fil0" style="stroke-width:{0};stroke:{1};" points="').format(
                linewidth, loccolor)
            for p in range(0, len(seg), 2):
                outfile += '{0},{1} '.format(seg[p] * zoom + xoffset, seg[p + 1] * zoom + yoffset)
                xylist.append([seg[p] * zoom + xoffset, seg[p + 1] * zoom + yoffset])
            outfile += '"/>\n'

    # Close up
    outfile += ' </g></svg>'

    # Add extents
    xcos = max([e[0] for e in xylist])
    ycos = max([e[1] for e in xylist])
    header = header.replace('{0}', str(xcos))
    header = header.replace('{1}', str(ycos))
    outfile = header + outfile

    # Export to file?
    if filename:
        fhand = open(filename, 'w')
        fhand.write(outfile)
        fhand.close()

    return outfile


# ## Self test
if __name__ == '__main__':
    print(svggen([[1, 2, 3, 4, '255,0,255'], [[5, 6], [7, 8], [9, 10], '#00FFFF'], [11, 12, 10, 'blue']], 'test.svg'))
