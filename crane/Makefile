BUILD_DIR=../build/crane

$(BUILD_DIR)/1-crane.log: Dockerfile
	mkdir -p "$(@D)"
	./make_with_log.sh "$@" docker build --no-cache -t tvm-ci-crane:latest .

$(BUILD_DIR)/2-poetry.log: ../pyproject.toml $(BUILD_DIR)/1-crane.log
	mkdir -p "$(@D)"
	./make_with_log.sh "$@" ./run.sh ./setup-virtualenv.sh

$(BUILD_DIR)/3-network.log: $(BUILD_DIR)/2-poetry.log
	mkdir -p "$(@D)"
	./make_with_log.sh "$@" ./network.sh create "$(BUILD_DIR)/network-id.txt"

crane: $(BUILD_DIR)/3-network.log

clean:
	docker network ./network.sh rm "$(BUILD_DIR)/network-id.txt"
	rm -rf $(BUILD_DIR)
.PHONY: crane

.DEFAULT_GOAL = crane
