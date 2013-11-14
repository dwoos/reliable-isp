default:
	protoc messages.proto --python_out=daemons/
	protoc messages.proto --python_out=clients/

.PHONY: default
