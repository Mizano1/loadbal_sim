#include "Simulation.hpp" 
#include <algorithm>
#include <cmath>
#include <iostream>
#include <unordered_set>

Simulation::Simulation(int n_, double lambda__, int m_, double mu__,
                       const std::string &policy_,
                       const std::string &topology_,
                       const std::vector<std::vector<int>> &dist_,
                       const std::vector<std::vector<int>> &k_nbrs_,
                       int k_, int L_, int qmax_)
    : n(n_), lambda_(lambda__), m(m_), mu_(mu__), 
      policy(policy_), topology(topology_),
      dist(dist_), k_nbrs(k_nbrs_), k(k_), L(L_), qmax(qmax_),
      T(0.0), q(n_, 0), s_time(n_, 1e30), t_arr(0.0), 
      req_dist(0.0), q_mid_hist(qmax_, 0.0), 
      time_integral_Q(0.0), arrivals_recorded(0)
{
    rng.seed(123456789ULL);
    std::uniform_int_distribution<int> U(0, n - 1);
    int first = U(rng);
    q[first]++;
    s_time[first] = exp_rv(mu_);
    t_arr = exp_rv(n * lambda_);
}

double Simulation::exp_rv(double rate) {
    std::uniform_real_distribution<double> U(0.0, 1.0);
    return -std::log(1.0 - U(rng)) / rate;
}

int Simulation::calculate_distance(int u, int v) {
    if (u == v) return 0;
    if (!dist.empty()) return dist[u][v];

    if (topology == "cycle") {
        int d = std::abs(u - v);
        return std::min(d, n - d);
    } 
    else if (topology == "grid") {
        int S = (int)std::round(std::sqrt(n));
        int r1 = u/S, c1 = u%S;
        int r2 = v/S, c2 = v%S;
        int dr = std::abs(r1-r2);
        int dc = std::abs(c1-c2);
        return std::min(dr, S-dr) + std::min(dc, S-dc);
    }
    return 0;
}

int Simulation::choose_node(int s) {
    std::vector<int> candidates;
    candidates.reserve(1 + k + L);
    candidates.push_back(s);
    std::uniform_int_distribution<int> U(0, n - 1);

    if (policy == "pot") {
        int r; do { r = U(rng); } while (r == s);
        candidates.push_back(r);
    } 
    else if (policy == "poKL") {
        std::unordered_set<int> used; used.insert(s);
        while ((int)candidates.size() < 1 + k + L) {
            int r = U(rng);
            if (used.find(r) == used.end()) {
                used.insert(r);
                candidates.push_back(r);
            }
        }
    } 
    else if (policy == "spatialKL") {
        for (int v : k_nbrs[s]) candidates.push_back(v);
        std::unordered_set<int> used(candidates.begin(), candidates.end());
        int target = 1 + k_nbrs[s].size() + L;
        while ((int)candidates.size() < target) {
            int r = U(rng);
            if (used.find(r) == used.end()) {
                used.insert(r);
                candidates.push_back(r);
            }
        }
    }

    int best = candidates[0];
    int best_load = q[best];
    for (size_t i = 1; i < candidates.size(); ++i) {
        if (q[candidates[i]] < best_load) {
            best = candidates[i];
            best_load = q[candidates[i]];
        }
    }
    return best;
}

SimulationResult Simulation::run() {
    int arrivals = 1;
    int warmup = static_cast<int>(m * 0.2);
    std::uniform_int_distribution<int> US(0, n - 1);
    std::uniform_int_distribution<int> U(0, n - 1);

    while (arrivals < m) {
        int min_idx = -1;
        double min_service = 1e30;
        for (int i = 0; i < n; i++) {
            if (q[i] > 0 && s_time[i] < min_service) {
                min_service = s_time[i];
                min_idx = i;
            }
        }

        double dt = std::min(t_arr, min_service);
        int total_Q = 0;
        for (int i = 0; i < n; ++i) total_Q += q[i];
        time_integral_Q += dt * static_cast<double>(total_Q);
        T += dt;

        if (dt > 0) {
             t_arr -= dt;
             for (int i=0; i<n; i++) if(q[i]>0) s_time[i] -= dt;
        }

        if (t_arr <= 1e-9) { // Arrival
            arrivals++;
            if (arrivals > warmup) {
                int len = q[US(rng)];
                if (len < qmax) q_mid_hist[len] += 1.0;
            }

            int s = U(rng);
            int chosen = choose_node(s);
            q[chosen]++;

            if (arrivals > warmup) {
                req_dist += calculate_distance(s, chosen);
                arrivals_recorded++;
            }

            if (q[chosen] == 1) s_time[chosen] = exp_rv(mu_);
            t_arr = exp_rv(n * lambda_);
        } 
        else { // Service
            q[min_idx]--;
            if (q[min_idx] == 0) s_time[min_idx] = 1e30;
            else s_time[min_idx] = exp_rv(mu_);
        }
    }

    double sum_hist = 0;
    for(double v : q_mid_hist) sum_hist += v;
    if (sum_hist > 0) for(double &v : q_mid_hist) v /= sum_hist;
    
    double mean_Q = (T > 0) ? (time_integral_Q/T)/n : 0;
    double mean_W = (lambda_ > 0) ? mean_Q / lambda_ : 0;
    return {q_mid_hist, req_dist, mean_Q, mean_W, (arrivals_recorded>0 ? req_dist/arrivals_recorded : 0)};
}