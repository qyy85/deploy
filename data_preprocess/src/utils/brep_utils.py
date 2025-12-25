"""
Utility functions for BRep processing
"""
from OCC.Core.Bnd import Bnd_Box
from OCC.Core.BRepBndLib import brepbndlib_AddOptimal
from OCC.Core.TopoDS import (
    TopoDS_Edge,
    TopoDS_Face,
    TopoDS_Shell,
    TopoDS_Solid,
    TopoDS_Vertex,
    TopoDS_Wire,
    TopoDS_Compound,
    TopoDS_CompSolid,
)

# occwl
from occwl.solid import Solid
from occwl.compound import Compound
from occwl.shell import Shell
from occwl.face import Face
from occwl.edge import Edge
from occwl.wire import Wire
from occwl.vertex import Vertex


def find_box(solid):
    """
    Find the bounding box of a solid
    """
    bbox = Bnd_Box()
    use_triangulation = True
    use_shapetolerance = False
    brepbndlib_AddOptimal(solid, bbox, use_triangulation, use_shapetolerance)
    return bbox


def scale_solid_to_unit_box(solid):
    """
    Scale a solid body into a box [-1, 1]^3
    """
    if isinstance(solid, Solid):
        return solid.scale_to_unit_box(copy=True)
    solid = create_occwl(solid)
    solid = solid.scale_to_unit_box(copy=True)
    return solid.topods_shape()


def create_occwl(topo_ds_shape):
    """
    Create an occwl version 1.0.0 entity from a TopoDS entity 
    """
    if isinstance(topo_ds_shape, TopoDS_Edge):
        occwl_ent = Edge(topo_ds_shape)
    elif isinstance(topo_ds_shape, TopoDS_Face):
        occwl_ent = Face(topo_ds_shape)
    elif isinstance(topo_ds_shape, TopoDS_Shell):
        occwl_ent = Shell(topo_ds_shape)
    elif isinstance(topo_ds_shape, TopoDS_Solid):
        occwl_ent = Solid(topo_ds_shape)
    elif isinstance(topo_ds_shape, TopoDS_Vertex):
        occwl_ent = Vertex(topo_ds_shape)
    elif isinstance(topo_ds_shape, TopoDS_Wire):
        occwl_ent = Wire(topo_ds_shape)
    elif isinstance(topo_ds_shape, TopoDS_CompSolid) or isinstance(topo_ds_shape, TopoDS_Compound):
        occwl_ent = Compound(topo_ds_shape)
    else:
        assert False, f"Unsupported entity {type(topo_ds_shape)}. Cant convert to occwl"
    
    return occwl_ent


