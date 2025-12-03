#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <cstring>
#include <sys/stat.h>
#include <filesystem>
#include "Simulation.hpp"
#include "Graph.hpp"

namespace fs = std::filesystem;

static void write_hist_csv(const std::vector<double>& hist, const std::string& path) {
    std::ofstream out(path);
    out << "QueueLength,Probability\n";
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
                               int num_clusters, double comm_cost,
                               double total_req_dist,
                               double mean_Q,
                               double mean_W,
                               double avg_req_dist) {
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
    out << "  \"num_clusters\": " << num_clusters << ",\n";
    out << "  \"comm_cost\": " << comm_cost << ",\n";
    out << "  \"total_req_dist\": " << total_req_dist << ",\n";
    out << "  \"mean_Q\": " << mean_Q << ",\n";
    out << "  \"mean_W\": " << mean_W << ",\n";
    out << "  \"avg_req_dist\": " << avg_req_dist << "\n";
    out << "}\n";
}

int main(int argc, char* argv[]) {
    int n = 1000;
    int m = 100000;
    double lambda = 0.9;
    double mu = 1.0;
    std::string policy = "pot";
    std::string topo = "cycle";
    int k = 1;
    int L = 1;
    int qmax = 100;
    
    int num_clusters = 1;
    double comm_cost = 0.0;
    std::string trace_file = "";

    std::string outdir = "results";
    std::string tag_suffix = "";

    for(int i=1; i<argc; ++i) {
        if(strcmp(argv[i], "--n")==0) n = std::stoi(argv[++i]);
        else if(strcmp(argv[i], "--m")==0) m = std::stoi(argv[++i]);
        else if(strcmp(argv[i], "--lambda")==0) lambda = std::stod(argv[++i]);
        else if(strcmp(argv[i], "--mu")==0) mu = std::stod(argv[++i]);
        else if(strcmp(argv[i], "--policy")==0) policy = argv[++i];
        else if(strcmp(argv[i], "--topo")==0) topo = argv[++i];
        else if(strcmp(argv[i], "--k")==0) k = std::stoi(argv[++i]);
        else if(strcmp(argv[i], "--L")==0) L = std::stoi(argv[++i]);
        else if(strcmp(argv[i], "--clusters")==0) num_clusters = std::stoi(argv[++i]);
        else if(strcmp(argv[i], "--cost")==0) comm_cost = std::stod(argv[++i]);
        else if(strcmp(argv[i], "--trace")==0) trace_file = argv[++i];
        else if(strcmp(argv[i], "--outdir")==0) outdir = argv[++i];
        else if(strcmp(argv[i], "--tag")==0) tag_suffix = argv[++i];
    }

    fs::create_directories(outdir);

    std::vector<std::vector<int>> k_nbrs;
    std::vector<std::vector<int>> dist; 

    if (policy == "spatialKL") {
        if (topo == "cycle") k_nbrs = generate_cycle_neighbors(n, k);
        else if (topo == "grid") k_nbrs = generate_grid_neighbors(n, k);
        else if (topo == "cluster") k_nbrs = generate_cluster_neighbors(n, num_clusters);
    }

    std::cout << "Running: N=" << n << " Policy=" << policy 
              << " Topo=" << topo;
    if (!trace_file.empty()) std::cout << " [Trace: " << trace_file << "]";
    std::cout << "..." << std::flush;
    
    Simulation sim(n, lambda, m, mu, policy, topo, dist, k_nbrs, k, L, qmax, 
                   num_clusters, comm_cost, trace_file);
                   
    SimulationResult result = sim.run();

    std::cout << " Done. E[Q]=" << result.mean_Q << "\n";

    std::string filename_base = policy + "_" + topo 
                              + "_n" + std::to_string(n);
    if(trace_file.empty()) filename_base += "_lam" + std::to_string(lambda).substr(0,4);
    else filename_base += "_trace";
    
    if (!tag_suffix.empty()) filename_base += "_" + tag_suffix;

    std::string hist_path = outdir + "/" + filename_base + "_hist.csv";
    std::string meta_path = outdir + "/" + filename_base + "_metrics.json";

    write_hist_csv(result.hist, hist_path);
    write_metrics_json(meta_path, policy, topo, n, m, lambda, mu, k, L, qmax,
                       num_clusters, comm_cost,
                       result.total_req_dist, 
                       result.mean_Q, 
                       result.mean_W, result.avg_req_dist);

    return 0;
}