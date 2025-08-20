

def overlap_range(r1, r2):
    """Return the overlap of two ranges or None if they don't overlap."""
    start = max(r1[0], r2[0])
    end = min(r1[1], r2[1])
    return (start, end) if start <= end else None

def merge_ranges(ranges):
    """Merge overlapping or touching ranges into a sorted list."""
    if not ranges:
        return []
    ranges = sorted(ranges)  # sort by start
    merged = [ranges[0]]
    for s, e in ranges[1:]:
        last_s, last_e = merged[-1]
        if s <= last_e:  # overlap or touch
            merged[-1] = (last_s, max(last_e, e))
        else:
            merged.append((s, e))
    return merged

def covers_target(target_range, pieces):
    """
    Do the ranges in 'pieces' fully cover 'target_range'?
    Steps:
      1) Clip each piece to target
      2) Merge
      3) Check for gaps
    """
    clipped = []
    for piece in pieces:
        o = overlap_range(piece, target_range)
        if o:
            clipped.append(o)

    merged = merge_ranges(clipped)
    if not merged:
        return False

    need_start, need_end = target_range
    covered_to = need_start

    for s, e in merged:
        if s > covered_to:       # gap found
            return False
        covered_to = max(covered_to, e)
        if covered_to >= need_end:
            return True

    return covered_to >= need_end

def will_cameras_work(desired_distance, desired_light, cameras):
    """
    Return True if the cameras cover every point in:
      distance in desired_distance  ×  light in desired_light

    Method (2D panes):
      - Break the distance axis into panes using all distance endpoints.
      - In each pane, active cameras (by distance) don't change.
      - For that pane, check if the union of their light ranges
        covers the whole desired_light range.
    """
    dist_min, dist_max = desired_distance
    light_min, light_max = desired_light

    if dist_min > dist_max or light_min > light_max:
        raise ValueError("Ranges must be (min <= max).")

    points = {dist_min, dist_max}
    for (cam_dist, cam_light) in cameras:
        points.add(cam_dist[0])
        points.add(cam_dist[1])

    xs = sorted(points)

    # Check each distance pane that overlaps the desired distance
    for i in range(len(xs) - 1):
        pane_start = xs[i]
        pane_end = xs[i + 1]

        if pane_end <= dist_min or pane_start >= dist_max:
            continue

        # Clip pane to desired distance and pick midpoint
        left = max(pane_start, dist_min)
        right = min(pane_end, dist_max)
        if left >= right:
            continue

        mid = (left + right) / 2.0

        # Light ranges of cameras active at this distance
        active_lights = []
        for (cam_dist, cam_light) in cameras:
            if cam_dist[0] <= mid <= cam_dist[1]:
                active_lights.append(cam_light)

        # Must cover the whole desired light range in this pane
        if not covers_target(desired_light, active_lights):
            return False

    return True

# -----------------------
# Example tests
# -----------------------
if __name__ == "__main__":
    # Example 1: Works (cameras split light but all cover the full distance)
    want_distance = (3, 10)
    want_light = (0, 10)
    cams_ok = [
        ((0, 10), (0, 4)),
        ((0, 10), (4, 7)),
        ((0, 10), (7, 10)),
    ]
    print("Example 1 ->", will_cameras_work(want_distance, want_light, cams_ok))  # True

    # Example 2: Fails (gap in light coverage for some distance pane)
    cams_bad = [
        ((3, 9),  (0, 4)),
        ((2, 6),  (4, 7)),
        ((4, 10), (7, 10)),
    ]
    print("Example 2 ->", will_cameras_work((3, 10), (0, 10), cams_bad))  # False

    # Example 3: Different distance sets; each pane still covers full light
    cams_mixed = [
        ((0, 5),  (0, 10)),  # near distances: full light
        ((5, 10), (0, 5)),   # far distances: lower half light
        ((5, 10), (5, 10)),  # far distances: upper half light
    ]
    print("Example 3 ->", will_cameras_work((0, 10), (0, 10), cams_mixed))  # True
