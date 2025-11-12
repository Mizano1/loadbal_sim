#include <iostream>
#include <string>
#include "Graph.hpp"
#include "Simulation.hpp"
#include <fstream>
#include <filesystem>
namespace fs = std::filesystem;
static void write_hist_csv(const std::vector<double>& hist, const std::string& path) {
    std::ofstream out(path);
    out << "# queue_length,probability\n";
    for (size_t i = 0; i < hist.size(); ++i) {
        if (hist[i] > 0.0)
            out << i << "," << hist[i] << "\n";
    }
}

static void write_metrics_json(const std::string& path,
                               const std::string& policy,
                               const std::string& graph_type,
                               int n, int m, double lambda_, double mu_,
                               int k, int L, int qmax,
                               double total_req_dist) {
    std::ofstream out(path);
    out << "{\n";
    out << "  \"policy\": \"" << policy << "\",\n";
    out << "  \"graph\": \"" << graph_type << "\",\n";
    out << "  \"n\": " << n << ",\n";
    out << "  \"m\": " << m << ",\n";
    out << "  \"lambda\": " << lambda_ << ",\n";
    out << "  \"mu\": " << mu_ << ",\n";
    out << "  \"k\": " << k << ",\n";
    out << "  \"L\": " << L << ",\n";
    out << "  \"qmax\": " << qmax << ",\n";
    out << "  \"total_req_dist\": " << total_req_dist << ",\n";
    out << "  \"avg_req_dist\": " << (total_req_dist / m) << "\n";
    out << "}\n";
}
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
    std::string outdir = "plots";
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
        else if (key == "--outdir") outdir = val;
    }
    
    fs::create_directories(outdir);

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

    // after you compute `hist` and `total_req_dist`
    std::string tag = policy + "_" + graph_type
        + "_n" + std::to_string(n)
        + "_m" + std::to_string(m)
        + "_k" + std::to_string(k)
        + "_L" + std::to_string(L);

    std::string hist_path = (fs::path(outdir) / (tag + "_hist.csv")).string();
    std::string metrics_path = (fs::path(outdir) / (tag + "_metrics.json")).string();

    write_hist_csv(hist, hist_path);
    write_metrics_json(metrics_path, policy, graph_type,
                    n, m, lambda_, mu_, k, L, qmax, total_req_dist);

    std::cout << "Wrote: " << hist_path << "\n";
    std::cout << "Wrote: " << metrics_path << "\n";

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

