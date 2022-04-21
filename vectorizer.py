'''
A more advanced version of the outline-tracer, using a different algorithm.
Here, find all the relevant pixels (which may include multiple 'islands'),
which can be the edge or any other area, and fill them with SVG's. This
should be useful for vector-drawing mechanisms (engravers, etc.).

An approach is to start at the edge and trace around until no neighbors remain,
which should typically mean the image is spiralling in, and then reverse the
vertices so it leads from inside out in manufacture.

Method options:
b: Boundary. Pixels that are neighboring 'content' pixels but background alone
o: Outline. Content pixels neighboring at least one background pixel
f: Fill. All non-background pixels (use with invert if needed!)
Note that the methods can be theoretically combined (united), if needed
'''

from PIL import Image as pil
import svggen

# Constants

# Dirs: E, NE, N, NW, W, SW, S, SE
DIRECTIONS = [(1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1)]

# MAIN FUNCTION


def vectorize(
    inputimg,  # PIL image handle or a file
    outputfile,  # If given, export to this SVG. Otherwise just return the SVGGEN vector pack
    method='b',  # Method to determine pixels to be vectorized (see docstring)
    invertpixels=False,  # Inverts pixel detection. Useful for e.g. black content on white
    diagnostic=False,  # Turn on to see various steps in the process, for debug purpose only
    expandsingles=0.2,  # Whether to convert 1-pixel lines into phantom -0.2..0.2 lines
    autoreduce=True,  # Whether to reduce unnecessary intermediate pixels on straight lines
    filtering=False,  # Whether to filter the final lines
    svgzoom=1,  # Final SVG zoom to apply (multiplier of all coordinates)
    splittogrid=None,  # (x,y) of size of sub-images to break into (for very large input images)
    calibrator=0.5,  # Add a little bottom-right corner line to help with alignments
):
    'Main function: supply the image, get back the vectors for SVGGEN or the SVG file itself.'

    # Load first, depending on type
    if isinstance(inputimg, str): img = pil.open(inputimg)
    else: img = inputimg
    px = img.load()

    # Firstly find all eligible pixels - depending on what the criterion method
    eligibles = []  # Master collector
    method = method.lower()
    # Iterate over all the pixels
    print('Determining required pixels...')
    # All pixels approach
    if 'f' in method:
        for cy in range(img.size[1]):
            if not cy % 500 and cy > 0: print('> Full: {0} rows done'.format(cy))
            for cx in range(img.size[0]):
                if _pxeligible(px[cx, cy], invertpixels): eligibles.append((cx, cy))
    # Iterate over 1-px-inside pixels for borderlines
    if 'o' in method or 'b' in method:
        for cy in range(1, img.size[1] - 1):
            if not cy % 500 and cy > 0: print('> Contour: {0} rows done'.format(cy))
            for cx in range(1, img.size[0] - 1):
                # Boundary (outside)
                if 'b' in method:
                    if not _pxeligible(px[cx, cy], invertpixels):
                        if _pxeligible(px[cx - 1, cy], invertpixels) or \
                                _pxeligible(px[cx + 1, cy], invertpixels) or  \
                                _pxeligible(px[cx, cy - 1], invertpixels) or \
                                _pxeligible(px[cx, cy + 1], invertpixels):
                            eligibles.append((cx, cy))
                # Outline (inside)
                if 'o' in method:
                    if _pxeligible(px[cx, cy], invertpixels):
                        if not _pxeligible(px[cx - 1, cy], invertpixels) or \
                                not _pxeligible(px[cx + 1, cy], invertpixels) or \
                                not _pxeligible(px[cx, cy - 1], invertpixels) or \
                                not _pxeligible(px[cx, cy + 1], invertpixels):
                            eligibles.append((cx, cy))
    print('Found {0} eligible pixels'.format(len(eligibles)))
    if not eligibles: quit()  # Abort if nothing to do
    # All eligibles collected. If needed, show diagnostics
    if diagnostic:
        for dx, dy in eligibles:
            px[dx, dy] = (255, 0, 255)
        img.save('vectorizer-diag-detection.png')
    # If needed, split the eligibles to relevant subsets
    if splittogrid:
        # Determine grid matrix size
        hgrid = img.size[0] // splittogrid[0] + 1
        vgrid = img.size[1] // splittogrid[1] + 1
        print('Splitting to a grid, {0}x{1}'.format(hgrid, vgrid))
        # Initialize grid
        grid = [[set() for tmp in range(hgrid)] for tmp2 in range(vgrid)]
        # Sort each eligible pixel in its corresponding set
        for cx, cy in eligibles:
            grid[cy // splittogrid[1]][cx // splittogrid[0]].add((cx, cy))

    # Ready to begin trac(k)ing
    eligibles = set(eligibles)  # Converting to a set should make it somewhat faster
    masterlines = []  # Overall collector of lines for exporting later (list of lists of (X,Y)'s)
    direction = 0  # Starting with northward search
    # Master line-by-line loop
    while eligibles:
        print('Iterating...{0} points remaining'.format(len(eligibles)))
        # Determine the closest pixel
        if masterlines:
            # If already having some lines, use the last added coordinate to optimize mechanics
            origin = masterlines[-1][-1]  # Last added point
        else:
            origin = (0, 0)  # If clean, use the top-left as the starting origin
        if diagnostic: print(' > Looking for the start point...')
        if not splittogrid:
            # Just plain direct search
            distances = sorted([(abs(origin[0] - kx) + abs(origin[1] - ky), kx, ky)
                                for kx, ky in eligibles])
            start = distances[0][1:3]  # Get x,y of the nearest point
        else:
            # More advanced grid search
            relgridx = origin[0] // splittogrid[0]
            relgridy = origin[1] // splittogrid[1]
            distances = sorted([(abs(origin[0] - kx) + abs(origin[1] - ky), kx, ky)
                                for kx, ky in grid[relgridy][relgridx]])
            if distances:
                start = distances[0][1:3]  # Get x,y of the nearest point
            else:
                # Not found in the local grid - so proceed to search in global eligibles
                distances = sorted([(abs(origin[0] - kx) + abs(origin[1] - ky), kx, ky)
                                    for kx, ky in eligibles])
                start = distances[0][1:3]  # Get x,y of the nearest point
        if diagnostic: print(' > Found at', start)
        currentline = [start]  # Create the new line for this iteration
        eligibles.remove(start)
        if splittogrid: grid[start[1] // splittogrid[1]][start[0] // splittogrid[0]].remove(start)
        # Ready to begin tracking this individual line until no eligible pixels remain
        while True:
            # Check in necessary directions
            currentpixel = currentline[-1]  # The most recent pixel in the line
            for checkdir in range(direction, direction + 8):
                checkdir = checkdir % 8  # Never exceed 8
                checkpixel = (currentpixel[0] + DIRECTIONS[checkdir][0],
                              currentpixel[1] + DIRECTIONS[checkdir][1])
                # Found the targeted pixel. Check if among the eligibles
                continuing = False
                if checkpixel in eligibles:
                    # It is. We've got another step of the line
                    eligibles.remove(checkpixel)
                    if splittogrid:
                        grid[checkpixel[1] // splittogrid[1]][checkpixel[0] // splittogrid[0]] \
                            .remove(checkpixel)
                    currentline.append(checkpixel)
                    direction = (checkdir + 4) % 8  # New direction to look for
                    continuing = True  # Important to know the cycle goes on
                    break
            if continuing: continue  # Multiple escape
            # No further continuation found - therefore we add this lina and get over again
            masterlines.append(currentline)
            break  # End this line and repeat from the next closes eligible
    # All lines completed
    print('Done. {0} lines detected'.format(len(masterlines)))

    # Post-processing
    print('Post-processing...')
    # Single pixel expansion
    if expandsingles:
        print('> Expanding singles')
        for id, line in enumerate(masterlines):
            if len(line) == 1:
                masterlines[id] = [(line[0][0] - expandsingles, line[0][1]),
                                   (line[0][0] + expandsingles, line[0][1])]
    # Line auto reduction
    if autoreduce:
        print('> Auto-reducing lines')
        for id, line in enumerate(masterlines):
            if len(line) <= 2: continue  # Nothing to do in a single straight line
            # Get all movements
            deltas = [(line[p][0] - line[p - 1][0], line[p][1] - line[p - 1][1])
                      for p in range(1, len(line))]
            deltas = [(0, 0)] + deltas  # To get ID numbering consistent
            # Locate all "surpluses"
            surplus = []  # Collector of surpluses
            for p in range(1, len(deltas) - 1):
                # If identical to the next neighbor, it's not needed
                if deltas[p] == deltas[p + 1]: surplus.append(p)
            # Delete them all in reverse order not to disturb the order
            surplus.sort(reverse=True)
            for pid in surplus: del line[pid]
            print('> > {0} surplus points deleted'.format(len(surplus)))
            masterlines[id] = line  # Return it to the master

    # Line filtering
    if filtering:
        print('> Filtering lines')
        for id, line in enumerate(masterlines):
            masterlines[id] = filter(line)

    # Calibration line to add
    if calibrator:
        masterlines.append([(img.size[0], img.size[1]),
                            (img.size[0] - calibrator, img.size[1] - calibrator)])

    # Final exporting and returning
    if outputfile: svggen.svggen(masterlines, outputfile, zoom=svgzoom)
    print('All done')
    return masterlines

# FILTER


def filter(POINTSLIST,  # A list of points (x,y)
           MASS=10,  # Filter 'mass' factor. The higher, the more filtered
           INTERPOINTS=6,  # Number of points 'per vertex' to calculate - the higher, the more precise
           FRICTION=.6,  # Friction of speed - to be multiplied with speed in every interstep
           ):
    '''
    Takes a list of (x,y) pairs of points' coordinates, and filters them according to mass factor.
    Returns a list again.
    '''
    # Main mover definition
    mover = list(POINTSLIST[0])
    speed = [0, 0]  # Initial speed
    print('Filtering, starting from:', mover)
    # Collector of final points
    filtered = []  # Add per iteration
    # Main iteration over all the additional points
    for ix, iy in POINTSLIST[1:]:
        for step in range(INTERPOINTS):
            # Calculate speeds
            dx = (ix - mover[0]) / MASS
            dy = (iy - mover[1]) / MASS
            speed[0] += dx
            speed[1] += dy
            speed[0] *= FRICTION
            speed[1] *= FRICTION
            # Execute step
            mover[0] += speed[0]
            mover[1] += speed[1]
            # Add to general collector
            filtered.append((mover[0], mover[1]))
    # Add the final point
    filtered.append(POINTSLIST[-1])
    # Return the final list
    print('Filtered to points:', len(filtered))
    return filtered

# Is a pixel eligible?


def _pxeligible(value, invert):
    '''For a value of a pixel (RGB or not), determine whether it is eligible for drawing.'''
    if isinstance(value, int): out = value >= 128
    else: out = sum(value) // 3 >= 128
    return out != invert  # Using != as XOR