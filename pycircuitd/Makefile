circuitd_pb2.py: circuitd.proto
	protoc circuitd.proto --python_out=.

default: circuitd_pb2.py

clean:
	rm circuitd_pb2.py

.PHONY: default clean
