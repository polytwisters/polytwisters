"""Tools for making 2D vector image renders of CadQuery objects.
"""
import math
from typing import Optional

import cadquery
from OCP.BRepLib import BRepLib
from OCP.GCPnts import GCPnts_QuasiUniformDeflection
from OCP.HLRBRep import HLRBRep_Algo, HLRBRep_HLRToShape
from OCP.HLRAlgo import HLRAlgo_Projector
from OCP.gp import gp_Ax2, gp_Pnt, gp_Dir

Polylines = list[list[tuple[float, float]]]


TOLERANCE = 1e-6
DISCRETIZATION_TOLERANCE = 1e-3


def scale_polylines(polylines: Polylines, x_scale: float, y_scale: float):
    return [[(x * x_scale, y * y_scale) for x, y in polyline] for polyline in polylines]


def translate_polylines(polylines: Polylines, dx: float, dy: float) -> Polylines:
    return [[(x + dx, y + dy) for x, y in polyline] for polyline in polylines]


def get_polylines_bounding_box(polylines: Polylines) -> Optional[tuple[float, float, float, float]]:
    points = [point for polyline in polylines for point in polyline]
    if len(points) == 0:
        return None
    x_coordinates, y_coordinates = zip(*points)
    x_min = min(x_coordinates)
    x_max = max(x_coordinates)
    y_min = min(y_coordinates)
    y_max = max(y_coordinates)
    return x_min, x_max, y_min, y_max


def convert_edge_to_polyline(edge: cadquery.Edge) -> list[tuple[float, float]]:
    """Discretize a CadQuery Edge into a polyline. This was adapted from CadQuery internal source."""
    curve = edge._geomAdaptor()  # adapt the edge into curve
    start = curve.FirstParameter()
    end = curve.LastParameter()
    points = GCPnts_QuasiUniformDeflection(curve, DISCRETIZATION_TOLERANCE, start, end)
    if points.IsDone():
        points = [points.Value(i + 1) for i in range(points.NbPoints())]
        points = [(point.X(), point.Y()) for point in points]
        return points
    return points


def make_svg_document_from_polylines(polylines: Polylines, width: float, height: float, stroke_width: float = 3.0) -> str:
    svg_paths = [
        " ".join([f"{'M' if i == 0 else 'L'} {x} {y}" for i, (x, y) in enumerate(polyline)])
        for polyline in polylines
    ]
    svg_paths = "\n".join([f'<path d="{path}" />' for path in svg_paths])
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
     <svg
         xmlns:svg="http://www.w3.org/2000/svg"
         xmlns="http://www.w3.org/2000/svg"
         width="{width}"
         height="{height}">
         <g stroke="black" fill="none" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round">
             {svg_paths}
         </g>
    </svg>
     """


def render_as_polylines(workplane: cadquery.Workplane) -> Polylines:
    """Render a 2D image of a CadQuery Workplane in the form of a set of polylines. This is adapted
    from cadquery.Workplane.exportSvg, but removes the axes and backfaces.

    The polylines
    are returned as a list of lists of (x, y) tuples.
    """
    shape = workplane.val()

    # For some reason, an empty Workplane returns a vector here, which causes problems downstream.
    if isinstance(shape, cadquery.Vector):
        return []

    hlr = HLRBRep_Algo()
    hlr.Add(shape.wrapped)
    projection_direction = (-1.75, 1.1, 5)
    coordinate_system = gp_Ax2(gp_Pnt(), gp_Dir(*projection_direction))
    projector = HLRAlgo_Projector(coordinate_system)
    hlr.Projector(projector)
    hlr.Update()
    hlr.Hide()

    hlr_shapes = HLRBRep_HLRToShape(hlr)

    visible = []
    visible_sharp_edges = hlr_shapes.VCompound()
    if not visible_sharp_edges.IsNull():
        visible.append(visible_sharp_edges)

    visible_smooth_edges = hlr_shapes.Rg1LineVCompound()
    if not visible_smooth_edges.IsNull():
        visible.append(visible_smooth_edges)

    visible_contour_edges = hlr_shapes.OutLineVCompound()
    if not visible_contour_edges.IsNull():
        visible.append(visible_contour_edges)

    for el in visible:
        BRepLib.BuildCurves3d_s(el, TOLERANCE)

    visible = [cadquery.Shape(x) for x in visible]
    paths = []
    for shape in visible:
        for edge in shape.Edges():
            paths.append(convert_edge_to_polyline(edge))

    return paths


def export_svg(workplane, normalize=False, additional_scale=1.0) -> str:
    """Given a workplane, orthogonally project its curves to 2D with hidden backfaces (that is,
    create a 2D vector outline rendering of an opaque object, like a wireframe) and return the code
    for an SVG document.
    """
    canvas_size = 1500.0
    border_size = 100.0
    figure_size = canvas_size - 2 * border_size

    polylines = render_as_polylines(workplane)

    # Ensure a unit circle at the origin gets scaled so its diameter is the figure size.
    scale = figure_size / 2
    scale *= additional_scale
    if normalize:
        bounding_box = get_polylines_bounding_box(polylines)
        if bounding_box is not None:
            x_min, x_max, y_min, y_max = bounding_box
            max_dimension = max(x_max - x_min, y_max - y_min)
            scale /= max_dimension
    center = canvas_size / 2

    # Y-axis is flipped here.
    polylines = scale_polylines(polylines, scale, -scale)
    polylines = translate_polylines(polylines, center, center)
    return make_svg_document_from_polylines(polylines, canvas_size, canvas_size)


def export_montage_as_svg(polylines_list: list[Polylines], additional_scale=1.0):
    cell_size = 500.0
    gap = 50.0

    num_cells = len(polylines_list)
    num_rows = int(math.sqrt(num_cells))
    num_columns = num_cells // num_rows

    scale = cell_size * additional_scale / 2

    final_polylines = []
    for i, polylines in enumerate(polylines_list):
        row_index, column_index = divmod(i, num_columns)
        x_offset = gap + (gap + cell_size) * column_index
        y_offset = gap + (gap + cell_size) * row_index
        polylines = scale_polylines(polylines, scale, scale)
        # Flip Y-axis.
        polylines = scale_polylines(polylines, 1.0, -1.0)
        polylines = translate_polylines(polylines, cell_size / 2, cell_size / 2)
        polylines = translate_polylines(polylines, x_offset, y_offset)
        final_polylines.extend(polylines)

    return make_svg_document_from_polylines(
        final_polylines,
        gap + (gap + cell_size) * num_columns,
        gap + (gap + cell_size) * num_rows,
        stroke_width=1.0,
    )

