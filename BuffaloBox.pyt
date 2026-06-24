# BuffaloBox.pyt
# ArcGIS Pro Python Toolbox - Buffalo Box Tools
# City of Elgin, IL - Illinois State Plane (US Feet)

import arcpy
import re

class Toolbox:
    def __init__(self):
        self.label = "Buffalo Box Tools"
        self.alias = "BuffaloBox"
        self.tools = [MoveBuffaloBoxes]


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

CORNER_LIST    = ["NE Corner", "NW Corner", "SE Corner", "SW Corner"]
MATERIAL_LIST  = ["Copper", "Galvanized Steel", "Cast Iron", "PVC", "Ductile Iron", "Lead", "Unknown"]
DIRECTION_LIST = ["North", "South", "East", "West"]
MAX_BOXES      = 10

CORNER_ALONG_WALL = {
    "SE Corner": (-1,  0),
    "SW Corner": ( 1,  0),
    "NE Corner": (-1,  0),
    "NW Corner": ( 1,  0),
}

DIRECTION_VECTOR = {
    "North": ( 0,  1),
    "South": ( 0, -1),
    "East":  ( 1,  0),
    "West":  (-1,  0),
}


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def parse_coords(coord_string):
    cleaned = coord_string.strip().replace(",", "")
    numbers = re.findall(r"\d+\.?\d*", cleaned)
    if len(numbers) < 2:
        raise ValueError(
            f"Could not read coordinates from: '{coord_string}'\n"
            "Paste the full string from ArcGIS, e.g.  985,972.32E 1,956,223.01N ftUS"
        )
    return float(numbers[0]), float(numbers[1])


def calc_location(corner_coords, corner_id, dist_corner, curb_coords, curb_direction, dist_curb):
    cx, cy = corner_coords
    rx, ry = curb_coords
    wall_dx, wall_dy = CORNER_ALONG_WALL.get(corner_id, (-1, 0))
    corner_x = cx + (dist_corner * wall_dx)
    corner_y = cy + (dist_corner * wall_dy)
    curb_dx, curb_dy = DIRECTION_VECTOR[curb_direction]
    curb_x = rx + (dist_curb * curb_dx)
    curb_y = ry + (dist_curb * curb_dy)
    if wall_dx != 0:
        return corner_x, curb_y
    else:
        return curb_x, corner_y


def get_workspace(layer):
    """Walk up to the geodatabase workspace, skipping feature datasets."""
    desc = arcpy.Describe(layer)
    workspace = desc.path
    try:
        ws_desc = arcpy.Describe(workspace)
        if hasattr(ws_desc, "dataType") and ws_desc.dataType == "FeatureDataset":
            workspace = ws_desc.path
    except Exception:
        pass
    return workspace


def get_fields(bbox_layer, messages):
    field_names = [f.name.upper() for f in arcpy.ListFields(bbox_layer)]
    field_map = {
        "DIAMETER": ["DIAMETER", "DIAM", "SIZE"],
        "MATERIAL": ["MATERIAL", "MAT", "PIPE_MAT"],
        "NOTES":    ["NOTES", "COMMENTS", "COMMENT", "REMARKS"],
    }
    update_fields = ["SHAPE@"]
    field_keys = []
    for key, candidates in field_map.items():
        for c in candidates:
            if c in field_names:
                update_fields.append(c)
                field_keys.append(key)
                break
    return update_fields, field_keys


def move_bbox_feature(bbox_layer, target_oid, new_geom, update_fields, field_keys,
                      diameter, material, notes):
    oid_field = arcpy.Describe(bbox_layer).OIDFieldName
    where     = f"{oid_field} = {target_oid}"
    workspace = get_workspace(bbox_layer)
    edit = arcpy.da.Editor(workspace)
    edit.startEditing(False, True)
    edit.startOperation()
    updated = False
    try:
        with arcpy.da.UpdateCursor(bbox_layer, update_fields, where_clause=where) as cursor:
            for row in cursor:
                row[0] = new_geom
                for i, key in enumerate(field_keys, start=1):
                    if key == "DIAMETER": row[i] = diameter
                    elif key == "MATERIAL": row[i] = material
                    elif key == "NOTES": row[i] = notes
                cursor.updateRow(row)
                updated = True
    except Exception as e:
        edit.stopOperation()
        edit.stopEditing(False)
        raise e
    edit.stopOperation()
    edit.stopEditing(True)
    if not updated:
        raise Exception(f"No row found with {oid_field} = {target_oid}")


def make_box_params(n):
    """Build the 10 parameters for box number n."""
    params = []

    p_header = arcpy.Parameter(
        displayName=f"━━━━━━━━━━━━━━━━━━━━  BOX {n}  ━━━━━━━━━━━━━━━━━━━━",
        name=f"box{n}_header", datatype="GPString",
        parameterType="Optional", direction="Input")
    p_header.value = f"Fill in Box {n} info below — leave blank to skip"
    params.append(p_header)                   # base + 0

    p_corner_coords = arcpy.Parameter(
        displayName=f"BOX {n} — Corner Coordinates  (right-click corner → Copy Coordinates → paste)",
        name=f"corner_coords_{n}", datatype="GPString",
        parameterType="Optional", direction="Input")
    p_corner_coords.value = ""
    params.append(p_corner_coords)            # base + 1

    p_corner_id = arcpy.Parameter(
        displayName=f"BOX {n} — Which corner is that?",
        name=f"corner_id_{n}", datatype="GPString",
        parameterType="Optional", direction="Input")
    p_corner_id.filter.type = "ValueList"
    p_corner_id.filter.list = CORNER_LIST
    p_corner_id.value = "SE Corner"
    params.append(p_corner_id)               # base + 2

    p_dist_corner = arcpy.Parameter(
        displayName=f"BOX {n} — Distance from corner - feet",
        name=f"dist_corner_{n}", datatype="GPDouble",
        parameterType="Optional", direction="Input")
    p_dist_corner.value = 0.0
    params.append(p_dist_corner)             # base + 3

    p_curb_coords = arcpy.Parameter(
        displayName=f"BOX {n} — Curb Coordinates  (right-click curb → Copy Coordinates → paste)",
        name=f"curb_coords_{n}", datatype="GPString",
        parameterType="Optional", direction="Input")
    p_curb_coords.value = ""
    params.append(p_curb_coords)             # base + 4

    p_dist_curb = arcpy.Parameter(
        displayName=f"BOX {n} — Distance from curb - feet",
        name=f"dist_curb_{n}", datatype="GPDouble",
        parameterType="Optional", direction="Input")
    p_dist_curb.value = 0.0
    params.append(p_dist_curb)              # base + 5

    p_curb_dir = arcpy.Parameter(
        displayName=f"BOX {n} — Direction from curb toward house",
        name=f"curb_dir_{n}", datatype="GPString",
        parameterType="Optional", direction="Input")
    p_curb_dir.filter.type = "ValueList"
    p_curb_dir.filter.list = DIRECTION_LIST
    p_curb_dir.value = "North"
    params.append(p_curb_dir)               # base + 6

    p_diameter = arcpy.Parameter(
        displayName=f"BOX {n} — Diameter (inches)",
        name=f"diameter_{n}", datatype="GPDouble",
        parameterType="Optional", direction="Input")
    p_diameter.value = 1.0
    params.append(p_diameter)               # base + 7

    p_material = arcpy.Parameter(
        displayName=f"BOX {n} — Material",
        name=f"material_{n}", datatype="GPString",
        parameterType="Optional", direction="Input")
    p_material.filter.type = "ValueList"
    p_material.filter.list = MATERIAL_LIST
    p_material.value = "Copper"
    params.append(p_material)               # base + 8

    p_notes = arcpy.Parameter(
        displayName=f"BOX {n} — Notes (optional)",
        name=f"notes_{n}", datatype="GPString",
        parameterType="Optional", direction="Input")
    params.append(p_notes)                  # base + 9

    return params  # 10 params per box


def is_box_filled(parameters, base):
    corner_str = parameters[base + 1].valueAsText or ""
    curb_str   = parameters[base + 4].valueAsText or ""
    return bool(corner_str.strip()) and bool(curb_str.strip())


def read_box_params(parameters, base):
    return {
        "corner_coords": parameters[base + 1].valueAsText or "",
        "corner_id":     parameters[base + 2].valueAsText,
        "dist_corner":   float(parameters[base + 3].value or 0),
        "curb_coords":   parameters[base + 4].valueAsText or "",
        "dist_curb":     float(parameters[base + 5].value or 0),
        "curb_dir":      parameters[base + 6].valueAsText,
        "diameter":      float(parameters[base + 7].value or 1),
        "material":      parameters[base + 8].valueAsText,
        "notes":         parameters[base + 9].valueAsText or "",
    }


# ─────────────────────────────────────────────────────────────────────────────
# TOOL — MOVE BUFFALO BOXES (1 to 10)
# ─────────────────────────────────────────────────────────────────────────────

class MoveBuffaloBoxes:
    def __init__(self):
        self.label = "Move Buffalo Boxes  (1 to 10)"
        self.description = (
            "Move 1 to 10 buffalo boxes in one run. "
            "Select your boxes on the map, fill in the card info for each one, "
            "and leave any unused sections blank."
        )
        self.canRunInBackground = False

    def getParameterInfo(self):
        p0 = arcpy.Parameter(
            displayName="Buffalo Box Feature Layer  (select your box(es) on the map first)",
            name="bbox_layer", datatype="GPFeatureLayer",
            parameterType="Required", direction="Input")

        all_params = []
        for n in range(1, MAX_BOXES + 1):
            all_params.extend(make_box_params(n))

        return [p0] + all_params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        bbox_layer = parameters[0].valueAsText

        # Get selected OIDs
        selected = []
        with arcpy.da.SearchCursor(bbox_layer, ["OID@"]) as cur:
            for row in cur:
                selected.append(row[0])
        selected.sort()

        if len(selected) == 0:
            messages.addErrorMessage(
                "No buffalo boxes selected. Select your box(es) on the map and run again."
            )
            return

        # Find which box sections are filled in — params start at index 1
        filled = []
        for i in range(MAX_BOXES):
            base = 1 + (i * 10)
            if is_box_filled(parameters, base):
                filled.append(i)

        if len(filled) == 0:
            messages.addErrorMessage(
                "No boxes have coordinates filled in. Fill in at least one box and run again."
            )
            return

        if len(selected) != len(filled):
            messages.addErrorMessage(
                f"{len(filled)} box section(s) are filled in but {len(selected)} box(es) are selected on the map.\n"
                f"Please select exactly {len(filled)} buffalo box(es) to match."
            )
            return

        sr = arcpy.Describe(bbox_layer).spatialReference
        update_fields, field_keys = get_fields(bbox_layer, messages)

        messages.addMessage(f"\n  Processing {len(filled)} buffalo box(es)...\n")

        success_count = 0
        for slot, i in enumerate(filled):
            n    = i + 1
            base = 1 + (i * 10)
            p    = read_box_params(parameters, base)

            try:
                c_coords = parse_coords(p["corner_coords"])
                r_coords = parse_coords(p["curb_coords"])
            except ValueError as e:
                messages.addErrorMessage(f"BOX {n} — {e}")
                continue

            new_x, new_y = calc_location(
                c_coords, p["corner_id"], p["dist_corner"],
                r_coords, p["curb_dir"],  p["dist_curb"]
            )
            new_geom = arcpy.PointGeometry(arcpy.Point(new_x, new_y), sr)

            try:
                move_bbox_feature(bbox_layer, selected[slot], new_geom,
                                  update_fields, field_keys,
                                  p["diameter"], p["material"], p["notes"])
                messages.addMessage(
                    f"  BOX {n} ✓ — OID {selected[slot]} moved\n"
                    f"    New location  : X={new_x:.2f}, Y={new_y:.2f}\n"
                    f"    Corner        : {p['corner_id']}  Dist: {p['dist_corner']} ft\n"
                    f"    Curb dist     : {p['dist_curb']} ft {p['curb_dir']}\n"
                    f"    Diameter      : {p['diameter']} in  |  Material: {p['material']}"
                )
                success_count += 1
            except Exception as e:
                messages.addErrorMessage(f"BOX {n} — Failed to update OID {selected[slot]}: {e}")

        messages.addMessage(
            f"\n  ── DONE: {success_count} of {len(filled)} buffalo boxes moved successfully ──"
        )

    def postExecute(self, parameters):
        return
