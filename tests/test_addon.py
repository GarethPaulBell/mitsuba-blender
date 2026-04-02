import bpy

from mathutils import Matrix
from pathlib import Path
import xml.etree.ElementTree as ET

def test_prespective_sensor():
    import importlib
    sensors = importlib.import_module("mitsuba-blender.io.importer.sensors")
    assert sensors
    common = importlib.import_module("mitsuba-blender.io.importer.common")
    assert common

    from mitsuba import Properties
    mi_sensor_props = Properties('perspective')
    mi_context = common.MitsubaSceneImportContext(bpy.context, bpy.context.scene, bpy.context.scene.collection, '', mi_sensor_props, Matrix())

    bl_camera, world_matrix = sensors.mi_perspective_to_bl_camera(mi_context, mi_sensor_props)
    assert bl_camera.type == 'PERSP'


def _export_test_scene(tmp_path, filename):
    output_scene_file = Path(tmp_path) / filename
    assert bpy.ops.export_scene.mitsuba(filepath=str(output_scene_file), ignore_background=True) == {'FINISHED'}
    return output_scene_file


def test_exporter_linked_duplicates_use_instances(tmp_path):
    import importlib
    io_module = importlib.import_module("mitsuba-blender.io")
    assert io_module

    bpy.ops.mesh.primitive_cube_add(location=(0.0, 0.0, 0.0))
    source = bpy.context.object
    source.name = "SharedCubeSource"
    source.data.name = "SharedCubeMesh"

    linked_duplicate = source.copy()
    linked_duplicate.data = source.data
    linked_duplicate.location = (2.0, 0.0, 0.0)
    linked_duplicate.name = "SharedCubeDuplicate"
    bpy.context.scene.collection.objects.link(linked_duplicate)

    output_scene_file = _export_test_scene(tmp_path, "linked_duplicates.xml")

    mesh_files = sorted(path.name for path in output_scene_file.parent.joinpath("meshes").glob("*.ply"))
    assert mesh_files == ["SharedCubeMesh.ply"]

    root = ET.parse(output_scene_file).getroot()
    shapegroups = [shape for shape in root.findall("shape") if shape.get("type") == "shapegroup"]
    assert len(shapegroups) == 1
    assert shapegroups[0].get("id") == "mesh-SharedCubeMesh"

    instances = [shape for shape in root.findall("shape") if shape.get("type") == "instance"]
    assert len(instances) == 2
    assert all(instance.find("./ref[@id='mesh-SharedCubeMesh']") is not None for instance in instances)


def test_exporter_single_mesh_stays_direct_shape(tmp_path):
    bpy.ops.mesh.primitive_cube_add(location=(0.0, 0.0, 0.0))
    cube = bpy.context.object
    cube.name = "SoloCube"
    cube.data.name = "SoloCubeMesh"

    output_scene_file = _export_test_scene(tmp_path, "single_mesh.xml")

    mesh_files = sorted(path.name for path in output_scene_file.parent.joinpath("meshes").glob("*.ply"))
    assert mesh_files == ["SoloCube.ply"]

    root = ET.parse(output_scene_file).getroot()
    shapegroups = [shape for shape in root.findall("shape") if shape.get("type") == "shapegroup"]
    instances = [shape for shape in root.findall("shape") if shape.get("type") == "instance"]
    ply_shapes = [shape for shape in root.findall("shape") if shape.get("type") == "ply"]

    assert shapegroups == []
    assert instances == []
    assert len(ply_shapes) == 1
