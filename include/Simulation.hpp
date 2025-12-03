#ifndef SIMULATION_HPP
#define SIMULATION_HPP

#include <vector>
#include <string>
#include <random>
#include <iostream>

struct SimulationResult {
    std::vector<double> hist;     
    double total_req_dist;        
    double mean_Q;          
    double mean_W;          
    double avg_req_dist;          
};

struct TraceJob {
    double inter_arrival_time;
    double duration;
};

class Simulation {
public:
    // Constructor
    Simulation(int n_, double lambda__, int m_, double mu__,
               const std::string &policy_,
               const std::string &topology_,
               const std::vector<std::vector<int>> &dist_,
               const std::vector<std::vector<int>> &k_nbrs_,
               int k_, int L_, int qmax_,
               int num_clusters_ = 1, 
               double comm_cost_ = 0.0,
               const std::string& trace_file_path = "");

    SimulationResult run();

private:
    int n;
    double lambda_;
    int m;
    double mu_;
    std::string policy;
    std::string topology;
    
    std::vector<std::vector<int>> dist;
    std::vector<std::vector<int>> k_nbrs;
    int k;
    int L;
    int qmax;
    
    // Cluster parameters
    int num_clusters;
    double comm_cost;

    double T;
    std::vector<int> q;
    std::vector<double> s_time;
    double t_arr;
    double req_dist;
    std::vector<double> q_mid_hist;
    int arrivals_recorded;

    // Trace Data
    std::vector<TraceJob> trace_jobs;
    size_t trace_idx;
    bool use_trace;

    std::mt19937_64 rng;

    double exp_rv(double rate);
    int choose_node(int s);
    double calculate_distance(int u, int v); 
    int get_cluster_id(int node_index) const;
    void load_trace(const std::string& filepath);
};

#endif