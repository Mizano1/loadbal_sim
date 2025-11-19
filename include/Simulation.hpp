#pragma once
#include <vector>
#include <string>
#include <random>

struct SimulationResult {
    std::vector<double> hist;     
    double total_req_dist;        
    double mean_Q;                
    double mean_W;                
    double avg_req_dist;          
};

class Simulation {
public:
    // Constructor matched to src/Simulation.cpp
    Simulation(int n_, double lambda__, int m_, double mu__,
               const std::string &policy_,
               const std::string &topology_,
               const std::vector<std::vector<int>> &dist_,
               const std::vector<std::vector<int>> &k_nbrs_,
               int k_, int L_, int qmax_);

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

    double T;
    std::vector<int> q;
    std::vector<double> s_time;
    double t_arr;
    double req_dist;
    std::vector<double> q_mid_hist;
    double time_integral_Q; 
    int arrivals_recorded;

    std::mt19937_64 rng;

    double exp_rv(double rate);
    int choose_node(int s);
    int calculate_distance(int u, int v);
};