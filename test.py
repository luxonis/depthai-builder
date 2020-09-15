import json

from depthai_builder import PipelineBuilder, ProcessorType

builder = PipelineBuilder(pipelineVersion="2", pipelineName="testpipeline")\
    .set_global_properties(leonOsFrequencyKhz=550000)\
    .set_global_properties(leonRtFrequencyKhz=550000)

xin = builder.add_node("XLinkIn", properties={"streamName": "testin"})
xout = builder.add_node("XLinkOut", properties={"streamName": "testout", "maxFpsLimit": 30})
producer = builder.add_node("MyProducer", properties={"processorPlacement": ProcessorType.LRT})

builder.connect(xin, "out", xout, "in")
builder.connect(producer, "out", xout, "in")

print(json.dumps(builder.to_dict(), indent=4))
