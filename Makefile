CXX = g++
CXXFLAGS = -O3 -std=c++17 -march=native -Wall -I./include

SRC_DIR = src
BIN_DIR = bin
RESULTS_DIR = results

TARGET = $(BIN_DIR)/loadbal_sim
SOURCES = $(wildcard $(SRC_DIR)/*.cpp)
OBJECTS = $(SOURCES:$(SRC_DIR)/%.cpp=$(BIN_DIR)/%.o)

all: $(TARGET)

$(TARGET): $(OBJECTS)
	@mkdir -p $(BIN_DIR)
	$(CXX) $(CXXFLAGS) -o $@ $^
	@echo "Build complete. Run ./bin/loadbal_sim"

$(BIN_DIR)/%.o: $(SRC_DIR)/%.cpp
	@mkdir -p $(BIN_DIR)
	$(CXX) $(CXXFLAGS) -c $< -o $@

run_fair: $(TARGET)
	@mkdir -p $(RESULTS_DIR)
	./$(TARGET) --mode fair --n 1000 --m 200000

run_large: $(TARGET)
	@mkdir -p $(RESULTS_DIR)
	./$(TARGET) --mode large --n 100000 --m 10000000

clean:
	rm -rf $(BIN_DIR) $(OBJ_DIR)