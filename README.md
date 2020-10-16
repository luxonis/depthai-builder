# Depreciated - is now developed as a part of [Pipeline Builder Gen2](https://github.com/luxonis/depthai/issues/136)

This repository contained an early representation of pipeline builder concepts. It is building a dynamic Python classes and modules based on JSON Schema files, wchich was our initial idea about new API. 

Since the architecture has changed and we dropped JSON Schema dependency, this repository was archived and serves as an example for anyone interested.

# DepthAI Pipeline Builder Python API

This tool is a Python API for DepthAI Pipeline Builder v2

## Install

```
python setup.py develop
```

## Usage

```python
from depthai_builder import PipelineBuilder, ProcessorType

builder = PipelineBuilder(pipelineVersion="2", pipelineName="testpipeline")\
    .set_global_properties(leonOsFrequencyKhz=550000)\
    .set_global_properties(leonRtFrequencyKhz=550000)

xin = builder.add_node("XLinkIn", properties={"streamName": "testin"})
xout = builder.add_node("XLinkOut", properties={"streamName": "testout", "maxFpsLimit": 30})
producer = builder.add_node("MyProducer", properties={"processorPlacement": ProcessorType.LRT})

builder.connect(xin, "out", xout, "in")
builder.connect(producer, "out", xout, "in")

print(builder.to_dict())
```
