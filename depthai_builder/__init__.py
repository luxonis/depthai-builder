import importlib.util
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import inspect
from random import randint
from typing import Any


def __get_fullpath(path):
    return (Path(__file__).parent / Path(path)).resolve().absolute()


spec = importlib.util.spec_from_file_location(
    "pipeline_types",
    __get_fullpath('depthai-shared/pipeline_builder/generated/depthai-shared/python/types.py')
)
pipeline_types = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline_types)
pipeline_classes = {
    classname: classtype
    for classname, classtype in inspect.getmembers(pipeline_types, inspect.isclass)
    if classtype.__module__ == "pipeline_types"
}

for pipeline_class in pipeline_classes:
    if issubclass(pipeline_classes[pipeline_class], Enum):
        globals()[pipeline_class] = pipeline_classes[pipeline_class]

hierarchy_json = json.load(__get_fullpath("depthai-shared/pipeline_builder/common/DatatypeHierarchy.json").open())
datatypes = {}


def resolve_datatypes(obj, parents):
    datatype = type(obj.get("datatype"), parents, {})
    datatypes[obj.get("datatype")] = datatype
    if "children" in obj:
        for child in obj.get("children"):
            resolve_datatypes(child, (datatype, *parents))


for hierarchy_root in hierarchy_json['hierarchies']:
    resolve_datatypes(hierarchy_root, tuple())


@dataclass
class NodeInput:
    name: str
    inputtype: str
    acceptedTypes: list

    @staticmethod
    def from_json(obj: dict):
        assert isinstance(obj, dict)
        name = obj.get("name")
        inputtype = obj.get("type")
        acceptedTypes = [
            datatypes.get(item.get("datatype"))
            for item in obj.get("acceptedDatatypes")
            if item.get("datatype") in datatypes
        ]
        return NodeInput(name, inputtype, acceptedTypes)


@dataclass
class NodeOutput:
    name: str
    outputtype: str
    possibleTypes: list

    @staticmethod
    def from_json(obj: dict):
        assert isinstance(obj, dict)
        name = obj.get("name")
        outputtype = obj.get("type")
        possibleTypes = [
            datatypes.get(item.get("datatype"))
            for item in obj.get("possibleDatatypes")
            if item.get("datatype") in datatypes
        ]
        return NodeOutput(name, outputtype, possibleTypes)


@dataclass
class NodeClass:
    name: str
    description: str
    properties_class: Any
    inputs: dict
    outputs: dict

    @staticmethod
    def from_json(obj: dict):
        assert isinstance(obj, dict)
        name = obj.get("name")
        description = obj.get("description")
        properties_class = pipeline_classes.get(obj.get("properties").split('.')[0] + "Properties")
        inputs = {
            input_item.get("name"): NodeInput.from_json(input_item)
            for input_item in obj.get("inputs", [])
        }
        outputs = {
            input_item.get("name"): NodeOutput.from_json(input_item)
            for input_item in obj.get("outputs", [])
        }
        return NodeClass(name, description, properties_class, inputs, outputs)

@dataclass
class NodeInstance(pipeline_classes['NodeObjInfo']):
    id: int = field(default_factory=lambda: int(time.time() * 1000) + randint(1000, 9999))
    name: str = ""
    properties: Any = None
    parent: NodeClass = None

    @staticmethod
    def from_dict(obj):
        node = pipeline_classes['NodeObjInfo'].from_dict(obj)
        node.parent = node_classes.get(node.name)
        node.properties = node.parent.properties_class.from_dict(obj.get("properties"))
        return node

    def to_dict(self):
        dict = super().to_dict()
        dict['name'] = self.parent.name
        dict['properties'] = self.properties.to_dict()
        return dict


node_paths = __get_fullpath("depthai-shared/pipeline_builder/nodes").glob('*')

node_classes = {
    node_path.stem: NodeClass.from_json(json.load((node_path / Path(node_path.stem).with_suffix('.json')).open()))
    for node_path in node_paths
}


class PipelineBuilder(pipeline_classes["PipelineSchema"]):
    def __init__(self, **kwargs):
        self.global_properties = pipeline_classes["GlobalProperties"].from_dict({
            # Default values are not supported by quicktype generator https://github.com/quicktype/quicktype/issues/486
            **{"leonOsFrequencyKhz": 600000, "leonRtFrequencyKhz": 600000},
            **kwargs,
        })
        self.nodes = []
        self.connections = []

    def set_global_properties(self, **kwargs):
        self.global_properties = pipeline_types.GlobalProperties.from_dict({
            **self.global_properties.to_dict(),
            **kwargs
        })
        return self

    def add_node(self, name: str, **kwargs) -> NodeInstance:
        assert name in node_classes, f"Node \"{name}\" is not in the node list (Available: {list(node_classes.keys())})"
        parent = node_classes[name]
        properties = parent.properties_class.from_dict(kwargs.pop('properties', {}))
        node_instance = NodeInstance(parent=parent, properties=properties, **kwargs)
        self.nodes.append(node_instance)
        return node_instance

    def connect(self, source: 'NodeInstance', output_name: str, target: 'NodeInstance', input_name: str):
        node_output = source.parent.outputs.get(output_name)
        node_input = target.parent.inputs.get(input_name)
        if len(set(node_output.possibleTypes) & set(node_input.acceptedTypes)) == 0:
            raise ValueError(
                f"Connection from \"{source.parent.name}\"->\"{output_name}\" "
                f"to \"{target.parent.name}\"->\"{input_name}\" is not possible - no matching datatypes found"
            )
        connection = pipeline_classes["NodeConnectionSchema"](source.id, output_name, target.id, input_name)
        self.connections.append(connection)
        return connection
