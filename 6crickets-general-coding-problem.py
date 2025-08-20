


def coversTarget(target, pieces):
    """Return True if union of pieces covers the whole target range."""

    targetStart, targetEnd = target
    # clip each piece to the target and keep the ones that touch it
    clipped = []
    for start, end in pieces:
        start = max(start, targetStart)
        end = min(end, targetEnd)
        if start <= end:
            clipped.append((start, end))

    if not clipped:
        return False

    # sort by start, sweep left to right
    clipped.sort()
    coveredTo = targetStart
    for start,end in clipped:
        if start > coveredTo:
            return False #Gap found
        coveredTo = max(end, coveredTo) #using max so we always move forward
        if coveredTo >= targetEnd:
            return True
    return coveredTo >= targetEnd


def willCamerasWork(desiredDistance, desiredLight, cameras):
    dmin, dmax = desiredDistance
    lmin, lmax = desiredLight
    if dmin > dmax or lmin > lmax:
        raise ValueError("Ranges are invalid")
    
    if dmin == dmax:
        activeLights = [light for dist, light in cameras if dist[0] <= dmin <= dist[1]]
        return coversTarget(desiredLight, activeLights)
    

    # Build Breakpoints

    points = {dmin, dmax}

    for dist, _l in cameras:
        if dist[0] >= dmin and dist[0] <= dmax: 
            points.add(dist[0])
        if dist[1] >= dmin and dist[1] <= dmax: 
            points.add(dist[1])


    sortedPoints = sorted(points)



    # Iterate all panes

    for i in range(len(sortedPoints) - 1):
        left = sortedPoints[i]
        right = sortedPoints[i + 1]

        mid = (left + right) / 2.0

        activeLights = [light for dist, light in cameras if dist[0] <= mid <= dist[1]]

        if not coversTarget(desiredLight, activeLights):
            return False
        
    return True



##  Example Tests   ##

def run(desc, desiredDist, desiredLight, cams, expected):
    got = willCamerasWork(desiredDist, desiredLight, cams)
    print(f"{desc:60} -> {got} (expected {expected})", "✅" if got == expected else "❌")


# 1) Single camera covers everything (easy pass)
run(
    "Single camera covers full distance & light",
    (0, 10), (0, 10),
    [((0, 10), (0, 10))],
    True
)

# 2) Split light across multiple cameras, same distance for all (pass)
run(
    "Split light across three cams, all cover same distance",
    (0, 10), (0, 10),
    [((0, 10), (0, 4)), ((0, 10), (4, 7)), ((0, 10), (7, 10))],
    True
)

# 3) Light gap at some distances (fail)
run(
    "At some distances, light union has a gap",
    (0, 10), (0, 10),
    [((3, 9), (0, 4)), ((2, 6), (4, 7)), ((4, 10), (7, 10))],
    False
)

# 4) Split distance into near/far, each side fully covers light (pass)
run(
    "Near (0–5) has full light; far (5–10) has full light via two cams",
    (0, 10), (0, 10),
    [((0, 5), (0, 10)), ((5, 10), (0, 5)), ((5, 10), (5, 10))],
    True
)

# 5) Distance gap: no camera valid around mid-distance (fail)
run(
    "Distance gap: no cameras active in (4,6)",
    (0, 10), (0, 10),
    [((0, 4), (0, 10)), ((6, 10), (0, 10))],
    False
)

# 6) Exact-touching light intervals count as covered (inclusive ends) (pass)
run(
    "Light intervals touch at endpoints (0–4, 4–7, 7–10) => covered",
    (0, 10), (0, 10),
    [((0, 10), (0, 4)), ((0, 10), (4, 7)), ((0, 10), (7, 10))],
    True
)

# 7) Nested intervals won’t “shrink” coverage thanks to max() (pass)
run(
    "Nested light intervals; outer one provides main coverage",
    (0, 10), (0, 10),
    [((0, 10), (0, 7)), ((0, 10), (3, 5)), ((0, 10), (6, 9)), ((0, 10), (9, 10))],
    True
)

# 8) Camera spans beyond desired distance; still okay (pass)
run(
    "Camera distance spans outside desired, still covers inside",
    (0, 10), (0, 10),
    [((-100, 100), (0, 10))],
    True
)

# 9) Cameras exist but their light is outside target (fail after clipping)
run(
    "Cameras' light ranges outside target; clipping empties coverage",
    (0, 10), (0, 10),
    [((0, 10), (11, 20)), ((0, 10), (-5, -1))],
    False
)

# 10) Unordered cameras; algorithm should still work (pass)
run(
    "Unordered cams; sorting inside algorithm handles it",
    (0, 10), (0, 10),
    [((0, 10), (7, 10)), ((0, 10), (0, 4)), ((0, 10), (4, 7))],
    True
)

# 11) Very small (float) panes: coverage in small steps (pass)
run(
    "Floats: light covered in small steps (0–1 via 0.3 steps)",
    (0.0, 10.0), (0.0, 1.0),
    [((0.0, 10.0), (0.0, 0.3)), ((0.0, 10.0), (0.3, 0.6)), ((0.0, 10.0), (0.6, 1.0))],
    True
)

# 12) Floats with a tiny gap (fail)
run(
    "Floats: tiny gap (0.6–0.61) leaves target (0–1) uncovered",
    (0.0, 10.0), (0.0, 1.0),
    [((0.0, 10.0), (0.0, 0.6)), ((0.0, 10.0), (0.61, 1.0))],
    False
)

# 13) Zero-width desired LIGHT (point coverage) with valid cam (pass)
run(
    "Desired light is a single value; a cam must include that value",
    (0, 10), (5, 5),
    [((0, 10), (3, 7))],
    True
)

# 14) Zero-width desired LIGHT with no cam including the point (fail)
run(
    "Desired light is point 5; no camera includes 5",
    (0, 10), (5, 5),
    [((0, 10), (0, 4)), ((0, 10), (6, 10))],
    False
)

# 15) Zero-width desired DISTANCE (your special-case path) (pass)
run(
    "Zero-width distance at 5; at that distance, lights cover fully",
    (5, 5), (0, 10),
    [((0, 6), (0, 4)), ((0, 6), (4, 10))],
    True
)

# 16) Zero-width distance at 5 but light gap at that point (fail)
run(
    "Zero-width distance at 5; light gap at that point",
    (5, 5), (0, 10),
    [((0, 6), (0, 4)), ((0, 6), (6, 10))],
    False
)

# 17) Coverage fails only in one distance pane (fail)
run(
    "Two panes: left ok, right has light gap -> overall fail",
    (0, 10), (0, 10),
    [((0, 5), (0, 10)), ((5, 10), (0, 4)), ((5, 10), (6, 10))],
    False
)

# 18) Large numbers (stress basic arithmetic) (pass)
run(
    "Large numbers: still a simple sort & sweep",
    (0, 1_000_000), (0, 1_000_000),
    [((0, 1_000_000), (0, 600_000)), ((0, 1_000_000), (600_000, 1_000_000))],
    True
)

# 19) Negative ranges (algorithm doesn’t assume positives) (pass)
run(
    "Negative ranges: cameras cover (-10..10) in light via two pieces",
    (-5, 5), (-10, 10),
    [((-5, 5), (-10, 0)), ((-5, 5), (0, 10))],
    True
)

# 20) Cameras active only at a boundary distance; others cover rest (pass)
run(
    "Boundary-only camera at distance 3; others cover panes; still pass",
    (3, 10), (0, 10),
    [((3, 3), (0, 10)), ((3, 10), (0, 4)), ((3, 10), (4, 10))],
    True
)

# 21) No cameras at all (fail)
run(
    "No cameras -> can't cover anything",
    (0, 10), (0, 10),
    [],
    False
)

# 22) Light coverage depends on different cameras in different panes (pass)
run(
    "Different panes use different cams; each pane still fully covers light",
    (0, 10), (0, 10),
    [((0, 4), (0, 10)), ((4, 7), (0, 10)), ((7, 10), (0, 10))],
    True
)

# 23) Light clipping inside target (partial pieces still help) (pass)
run(
    "Pieces extend beyond target light; clipping preserves coverage",
    (0, 10), (2, 8),
    [((0, 10), (0, 5)), ((0, 10), (5, 10))],
    True
)

# 24) Pane with no active cameras (fail fast)
run(
    "A pane has zero active cams by distance -> immediate fail",
    (0, 10), (0, 10),
    [((0, 3), (0, 10)), ((7, 10), (0, 10))],  # nothing covers (3,7)
    False
)
