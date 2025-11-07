#ifndef SIMULATION_HPP
#define SIMULATION_HPP

#include <vector>
#include <string>
#include <random>

class Simulation {
public:
    Simulation(int n,
               double lambda_,
               int m,
               double mu_,
               const std::string &policy,
               const std::vector<std::vector<int>> &G,
               const std::vector<std::vector<int>> &dist,
               const std::vector<std::vector<int>> &k_nbrs,
               int k,
               int L,
               int qmax);

    std::pair<std::vector<double>, double> run();

private:
    int n;
    double lambda_;
    int m;
    double mu_;
    std::string policy;
    const std::vector<std::vector<int>> &G;
    const std::vector<std::vector<int>> &dist;
    const std::vector<std::vector<int>> &k_nbrs;
    int k;
    int L;
    int qmax;

    double T;
    std::vector<int> q;
    std::vector<double> s_time;
    double t_arr;
    double req_dist;
    std::vector<double> q_mid_hist;
    std::mt19937_64 rng;

    double exp_rv(double rate);
    int choose_node(int s);
};

#endif
