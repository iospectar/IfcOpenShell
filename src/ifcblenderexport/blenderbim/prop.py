import json
import os
import csv
from pathlib import Path
from . import export_ifc
import bpy
from bpy.types import PropertyGroup
from bpy.app.handlers import persistent
from bpy.props import (
    StringProperty,
    EnumProperty,
    BoolProperty,
    IntProperty,
    FloatProperty,
    CollectionProperty
)

cwd = os.path.dirname(os.path.realpath(__file__))

class IfcSchema():
    def __init__(self):
        with open(os.path.join(cwd, 'schema', 'ifc_elements_IFC4.json')) as f:
            self.elements = json.load(f)

ifc_schema = IfcSchema()

diagram_scales_enum = []
classes_enum = []
types_enum = []
psetnames_enum = []
psetfiles_enum = []
classification_enum = []
reference_enum = []
attributes_enum = []
documents_enum = []
contexts_enum = []
subcontexts_enum = []
target_views_enum = []

@persistent
def setDefaultProperties(scene):
    if bpy.context.scene.BIMProperties.has_model_context \
            and len(bpy.context.scene.BIMProperties.model_subcontexts) == 0:
        subcontext = bpy.context.scene.BIMProperties.model_subcontexts.add()
        subcontext.name = 'Body'
        subcontext.target_view = 'MODEL_VIEW'


def getIfcPredefinedTypes(self, context):
    global types_enum
    if len(types_enum) < 1:
        for name, data in ifc_schema.elements.items():
            if name != self.ifc_class.strip():
                continue
            for attribute in data['attributes']:
                if attribute['name'] != 'PredefinedType':
                    continue
                types_enum.extend([(e, e, '') for e in attribute['enum_values']])
    return types_enum


def refreshPredefinedTypes(self, context):
    global types_enum
    types_enum.clear()
    getIfcPredefinedTypes(self, context)


def getDiagramScales(self, context):
    global diagram_scales_enum
    if len(diagram_scales_enum) < 1:
        diagram_scales_enum.extend([
            ('1:5000', '1:5000', ''),
            ('1:2000', '1:2000', ''),
            ('1:1000', '1:1000', ''),
            ('1:500', '1:500', ''),
            ('1:200', '1:200', ''),
            ('1:100', '1:100', ''),
            ('1:50', '1:50', ''),
            ('1:20', '1:20', ''),
            ('1:10', '1:10', ''),
            ('1:5', '1:5', ''),
            ('1:2', '1:2', ''),
            ('1:1', '1:1', '')
        ])
    return diagram_scales_enum


def getIfcClasses(self, context):
    global classes_enum
    if len(classes_enum) < 1:
        classes_enum.extend([(e, e, '') for e in ifc_schema.elements])
    return classes_enum


def getPsetNames(self, context):
    global psetnames_enum
    if len(psetnames_enum) < 1:
        psetnames_enum.clear()
        files = os.listdir(os.path.join(self.data_dir, 'pset'))
        psetnames_enum.extend([(f, f, '') for f in files])
    return psetnames_enum


def refreshPsetFiles(self, context):
    global psetfiles_enum
    psetfiles_enum.clear()
    getPsetFiles(self, context)


def getPsetFiles(self, context):
    global psetfiles_enum
    if len(psetfiles_enum) < 1:
        if not self.pset_name.strip():
            return psetfiles_enum
        files = os.listdir(os.path.join(self.data_dir, 'pset', self.pset_name.strip()))
        psetfiles_enum.extend([(f.replace('.csv', ''), f.replace('.csv', ''), '') for f in files])
    return psetfiles_enum


def getClassifications(self, context):
    global classification_enum
    if len(classification_enum) < 1:
        classification_enum.clear()
        with open(os.path.join(self.data_dir, 'class', 'classifications.csv'), 'r') as f:
            data = list(csv.reader(f))
            keys = data.pop(0)
            index = keys.index('Name')
            classification_enum.extend([(str(i), d[index], '') for i, d in enumerate(data)])
    return classification_enum


def refreshReferences(self, context):
    global reference_enum
    reference_enum.clear()
    getReferences(self, context)


def getReferences(self, context):
    global reference_enum
    if len(reference_enum) < 1:
        if not self.classification.strip():
            return reference_enum
        with open(os.path.join(self.data_dir, 'class', 'references.csv'), 'r') as f:
            data = list(csv.reader(f))
            keys = data.pop(0)
            reference_enum.extend([(d[0], '{} - {}'.format(d[0], d[1]), '') for d in data if
                    d[2] == self.classification.strip()])
    return reference_enum


def getApplicableAttributes(self, context):
    global attributes_enum
    attributes_enum.clear()
    if '/' in context.active_object.name \
        and context.active_object.name.split('/')[0] in ifc_schema.elements:
        attributes_enum.extend([(a['name'], a['name'], '') for a in
            ifc_schema.elements[context.active_object.name.split('/')[0]]['attributes']
            if self.attributes.find(a['name']) == -1])
    return attributes_enum


def getApplicableDocuments(self, context):
    global documents_enum
    documents_enum.clear()
    doc_path = os.path.join(context.scene.BIMProperties.data_dir, 'doc')
    for filename in Path(doc_path).glob('**/*'):
        uri = str(filename.relative_to(doc_path).as_posix())
        documents_enum.append((uri, uri, ''))
    return documents_enum


def getSubcontexts(self, context):
    global subcontexts_enum
    subcontexts_enum.clear()
    # TODO: allow override of generated subcontexts?
    subcontexts = export_ifc.IfcExportSettings().subcontexts
    for subcontext in subcontexts:
        subcontexts_enum.append((subcontext, subcontext, ''))
    return subcontexts_enum


def getTargetViews(self, context):
    global target_views_enum
    target_views_enum.clear()
    for target_view in export_ifc.IfcExportSettings().target_views:
        target_views_enum.append((target_view, target_view, ''))
    return target_views_enum


class Subcontext(PropertyGroup):
    name: StringProperty(name='Name')
    target_view: StringProperty(name='Target View')


class DocProperties(PropertyGroup):
    diagram_scale: EnumProperty(items=getDiagramScales, name='Diagram Scale')
    should_recut: BoolProperty(name="Should Recut", default=True)


class BIMProperties(PropertyGroup):
    schema_dir: StringProperty(default=os.path.join(cwd ,'schema') + os.path.sep, name="Schema Directory")
    data_dir: StringProperty(default=os.path.join(cwd, 'data') + os.path.sep, name="Data Directory")
    audit_ifc_class: EnumProperty(items=getIfcClasses, name="Audit Class")
    ifc_class: EnumProperty(items=getIfcClasses, name="Class", update=refreshPredefinedTypes)
    ifc_predefined_type: EnumProperty(
        items = getIfcPredefinedTypes,
        name="Predefined Type", default=None)
    ifc_userdefined_type: StringProperty(name="Userdefined Type")
    export_has_representations: BoolProperty(name="Export Representations", default=True)
    export_should_export_all_materials_as_styled_items: BoolProperty(name="Export All Materials as Styled Items", default=False)
    export_should_use_presentation_style_assignment: BoolProperty(name="Export with Presentation Style Assignment", default=False)
    import_should_ignore_site_coordinates: BoolProperty(name="Import Ignoring Site Coordinates", default=False)
    import_should_import_curves: BoolProperty(name="Import Curves", default=False)
    import_should_treat_styled_item_as_material: BoolProperty(name="Import Treating Styled Item as Material", default=False)
    import_should_use_legacy: BoolProperty(name="Import with Legacy Importer", default=False)
    import_should_use_cpu_multiprocessing: BoolProperty(name="Import with CPU Multiprocessing", default=False)
    qa_reject_element_reason: StringProperty(name="Element Rejection Reason")
    pset_name: EnumProperty(items=getPsetNames, name="Pset Name", update=refreshPsetFiles)
    pset_file: EnumProperty(items=getPsetFiles, name="Pset File")
    has_georeferencing: BoolProperty(name="Has Georeferencing", default=False)
    has_library: BoolProperty(name="Has Project Library", default=False)
    global_id: StringProperty(name="GlobalId")
    features_dir: StringProperty(default='', name="Features Directory")
    diff_json_file: StringProperty(default='', name="Diff JSON File")
    aggregate_class: EnumProperty(items=getIfcClasses, name="Aggregate Class")
    aggregate_name: StringProperty(name="Aggregate Name")
    classification: EnumProperty(items=getClassifications, name="Classification", update=refreshReferences)
    reference: EnumProperty(items=getReferences, name="Reference")
    has_model_context: BoolProperty(name="Has Model Context", default=True)
    has_plan_context: BoolProperty(name="Has Plan Context", default=False)
    model_subcontexts: CollectionProperty(name='Model Subcontexts', type=Subcontext)
    plan_subcontexts: CollectionProperty(name='Plan Subcontexts', type=Subcontext)
    available_subcontexts: EnumProperty(items=getSubcontexts, name="Available Subcontexts")
    available_target_views: EnumProperty(items=getTargetViews, name="Available Target Views")


class MapConversion(PropertyGroup):
    eastings: StringProperty(name="Eastings")
    northings: StringProperty(name="Northings")
    orthogonal_height: StringProperty(name="Orthogonal Height")
    x_axis_abscissa: StringProperty(name="X Axis Abscissa")
    x_axis_ordinate: StringProperty(name="X Axis Ordinate")
    scale: StringProperty(name="Scale")

class TargetCRS(PropertyGroup):
    name: StringProperty(name="Name")
    description: StringProperty(name="Description")
    geodetic_datum: StringProperty(name="Geodetic Datum")
    vertical_datum: StringProperty(name="Vertical Datum")
    map_projection: StringProperty(name="Map Projection")
    map_zone: StringProperty(name="Map Zone")
    map_unit: StringProperty(name="Map Unit")

class BIMLibrary(PropertyGroup):
    name: StringProperty(name="Name")
    version: StringProperty(name="Version")
    publisher: StringProperty(name="Publisher")
    version_date: StringProperty(name="Version Date")
    location: StringProperty(name="Location")
    description: StringProperty(name="Description")


class Attribute(PropertyGroup):
    name: StringProperty(name="Name")
    data_type: StringProperty(name="Data Type")
    string_value: StringProperty(name="Value")
    bool_value: BoolProperty(name="Value")
    int_value: IntProperty(name="Value")
    float_value: FloatProperty(name="Value")

class Pset(PropertyGroup):
    name: StringProperty(name="Name")
    file: StringProperty(name="File")

class Document(PropertyGroup):
    file: StringProperty(name="File")

class Classification(PropertyGroup):
    name: StringProperty(name="Name")
    identification: StringProperty(name="Identification")


class GlobalId(PropertyGroup):
    name: StringProperty(name="Name")


class BIMObjectProperties(PropertyGroup):
    global_ids: CollectionProperty(name="GlobalIds", type=GlobalId)
    attributes: CollectionProperty(name="Attributes", type=Attribute)
    psets: CollectionProperty(name="Psets", type=Pset)
    applicable_attributes: EnumProperty(items=getApplicableAttributes, name="Attribute Names")
    documents: CollectionProperty(name="Documents", type=Document)
    applicable_documents: EnumProperty(items=getApplicableDocuments, name="Available Documents")
    classifications: CollectionProperty(name="Classifications", type=Classification)


class BIMMaterialProperties(PropertyGroup):
    is_external: BoolProperty(name="Has External Definition")
    location: StringProperty(name="Location")
    identification: StringProperty(name="Identification")
    name: StringProperty(name="Name")


class SweptSolid(PropertyGroup):
    name: StringProperty(name="Name")
    outer_curve: StringProperty(name="Outer Curve")
    inner_curves: StringProperty(name="Inner Curves")
    extrusion: StringProperty(name="Extrusion")


class BIMMeshProperties(PropertyGroup):
    is_wireframe: BoolProperty(name="Is Wireframe")
    is_swept_solid: BoolProperty(name="Is Swept Solid")
    swept_solids: CollectionProperty(name="Swept Solids", type=SweptSolid)
