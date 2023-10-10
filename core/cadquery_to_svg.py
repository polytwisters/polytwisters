import cadquery
from OCP.BRepLib import BRepLib
from OCP.GCPnts import GCPnts_QuasiUniformDeflection
from OCP.HLRBRep import HLRBRep_Algo, HLRBRep_HLRToShape
from OCP.HLRAlgo import HLRAlgo_Projector
from OCP.gp import gp_Ax2, gp_Pnt, gp_Dir


TOLERANCE = 1e-6
DISCRETIZATION_TOLERANCE = 1e-3


def convert_edge_to_polyline(e):
    curve = e._geomAdaptor()  # adapt the edge into curve
    start = curve.FirstParameter()
    end = curve.LastParameter()
    points = GCPnts_QuasiUniformDeflection(curve, DISCRETIZATION_TOLERANCE, start, end)
    if points.IsDone():
        points = [points.Value(i + 1) for i in range(points.NbPoints())]
        points = [(point.X(), point.Y()) for point in points]
        return points
    return points


def make_svg_document_from_paths(paths: list[str], canvas_size: float):
    svg_paths = "\n".join([f'<path d="{path}" />' for path in paths])
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
     <svg
         xmlns:svg="http://www.w3.org/2000/svg"
         xmlns="http://www.w3.org/2000/svg"
         width="{canvas_size}"
         height="{canvas_size}">
         <g stroke="black" fill="none" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
             {svg_paths}
         </g>
    </svg>
     """


def export_svg(workplane, normalize=False):
    shape = workplane.val()

    canvas_size = 500.0
    border_size = 20.0
    figure_size = canvas_size - 2 * border_size

    # For some reason, an empty Workplane returns a vector here, which causes problems downstream.
    if isinstance(shape, cadquery.Vector):
        return make_svg_document_from_paths([], canvas_size)

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

    if normalize:
        points = [point for path in paths for point in path]
        x_coordinates, y_coordinates = zip(*points)
        x_min = min(x_coordinates)
        x_max = max(x_coordinates)
        y_min = min(y_coordinates)
        y_max = max(y_coordinates)
        max_dimension = max(x_max - x_min, y_max - y_min)
        scale = figure_size / max_dimension
    else:
        scale = figure_size / 2
    center = canvas_size / 2

    # Note: Y-axis is flipped here.
    paths = [
        [(center + x * scale, center - y * scale) for x, y in path]
        for path in paths
    ]

    svg_paths = [
        " ".join([f"{'M' if i == 0 else 'L'} {x} {y}" for i, (x, y) in enumerate(path)])
        for path in paths
    ]
    return make_svg_document_from_paths(svg_paths, canvas_size)
