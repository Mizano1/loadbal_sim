#include <iostream>
#include <string>
#include "Graph.hpp"
#include "Simulation.hpp"

int main(int argc, char** argv) {
    // default params
    int n = 100;
    int m = 100000;
    double lambda_ = 0.95;
    double mu_ = 1.0;
    std::string policy = "spatialKL"; // "pot", "poKL", "spatialKL"
    std::string graph_type = "cycle"; // "cycle" or "grid"
    int k = 1;
    int L = 1;
    int qmax = 100;

    // very simple CLI: --n 200 --policy pot etc.
    for (int i = 1; i + 1 < argc; i += 2) {
        std::string key = argv[i];
        std::string val = argv[i+1];
        if (key == "--n") n = std::stoi(val);
        else if (key == "--m") m = std::stoi(val);
        else if (key == "--lambda") lambda_ = std::stod(val);
        else if (key == "--mu") mu_ = std::stod(val);
        else if (key == "--policy") policy = val;
        else if (key == "--graph") graph_type = val;
        else if (key == "--k") k = std::stoi(val);
        else if (key == "--L") L = std::stoi(val);
        else if (key == "--qmax") qmax = std::stoi(val);
    }

    std::vector<std::vector<int>> G;
    if (graph_type == "cycle") {
        G = build_cycle_graph(n);
    } else if (graph_type == "grid") {
        G = build_grid_graph(n);
    } else {
        std::cerr << "Unknown graph type, using cycle.\n";
        G = build_cycle_graph(n);
    }

    auto dist = all_pairs_shortest_paths(G);

    std::mt19937_64 rng(987654321ULL);
    auto k_nbrs = get_k_hop_neighbors(dist, k, rng);

    Simulation sim(n, lambda_, m, mu_, policy, G, dist, k_nbrs, k, L, qmax);
    auto result = sim.run();

    const auto &hist = result.first;
    double total_req_dist = result.second;

    std::cout << "Queue-length distribution for queue n/2:\n";
    for (int i = 0; i < (int)hist.size(); i++) {
        if (hist[i] > 0.0) {
            std::cout << i << " " << hist[i] << "\n";
        }
    }

    std::cout << "Total request distance: " << total_req_dist << "\n";
    std::cout << "Average request distance: " << (total_req_dist / m) << "\n";

    return 0;
}

