#include "Simulation.hpp"
#include <algorithm>
#include <cmath>
#include <unordered_set>
#include <iostream>

Simulation::Simulation(int n_,
                       double lambda__,
                       int m_,
                       double mu__,
                       const std::string &policy_,
                       const std::vector<std::vector<int>> &G_,
                       const std::vector<std::vector<int>> &dist_,
                       const std::vector<std::vector<int>> &k_nbrs_,
                       int k_,
                       int L_,
                       int qmax_)
    : n(n_),
      lambda_(lambda__),
      m(m_),
      mu_(mu__),
      policy(policy_),
      G(G_),
      dist(dist_),
      k_nbrs(k_nbrs_),
      k(k_),
      L(L_),
      qmax(qmax_),
      T(0.0),
      q(n_, 0),
      s_time(n_, 1e30),
      req_dist(0.0),
      q_mid_hist(qmax_, 0.0)
{
    rng.seed(123456789ULL);

    // first arrival
    t_arr = exp_rv(n * lambda_);
    T += t_arr;

    // assign first job to random queue
    std::uniform_int_distribution<int> U(0, n - 1);
    int first = U(rng);
    q[first] += 1;
    s_time[first] = exp_rv(mu_);

    // schedule next arrival
    t_arr = exp_rv(n * lambda_);
}

double Simulation::exp_rv(double rate) {
    std::uniform_real_distribution<double> U(0.0, 1.0);
    double u = U(rng);
    return -std::log(1.0 - u) / rate;
}

int Simulation::choose_node(int s) {
    std::vector<int> candidates;
    candidates.push_back(s);

    std::uniform_int_distribution<int> U(0, n - 1);

    if (policy == "pot") {
        int r;
        do {
            r = U(rng);
        } while (r == s);
        candidates.push_back(r);
    } else if (policy == "poKL") {
        std::unordered_set<int> used;
        used.insert(s);
        while ((int)candidates.size() < 1 + k + L) {
            int r = U(rng);
            if (!used.count(r)) {
                used.insert(r);
                candidates.push_back(r);
            }
        }
    } else if (policy == "spatialKL") {
        for (int v : k_nbrs[s]) candidates.push_back(v);
        std::unordered_set<int> used(candidates.begin(), candidates.end());
        while ((int)candidates.size() < 1 + (int)k_nbrs[s].size() + L) {
            int r = U(rng);
            if (!used.count(r)) {
                used.insert(r);
                candidates.push_back(r);
            }
        }
    } else {
        // default: just s
    }

    int best = candidates[0];
    int best_load = q[best];
    for (int v : candidates) {
        if (q[v] < best_load) {
            best = v;
            best_load = q[v];
        }
    }
    return best;
}

std::pair<std::vector<double>, double> Simulation::run() {
    int arrivals = 1; // we already injected 1 job in the constructor

    while (arrivals < m) {
        // find earliest service completion
        int min_idx = -1;
        double min_service = 1e30;
        for (int i = 0; i < n; i++) {
            if (s_time[i] < min_service) {
                min_service = s_time[i];
                min_idx = i;
            }
        }

        if (t_arr <= min_service) {
            // arrival happens first
            arrivals++;
            T += t_arr;

            // source node
            std::uniform_int_distribution<int> U(0, n - 1);
            int s = U(rng);

            int chosen = choose_node(s);

            q[chosen] += 1;

            // record queue-length of middle queue
            int mid = n / 2;
            int len_mid = q[mid];
            if (len_mid < qmax)
                q_mid_hist[len_mid] += 1.0;

            // record distance
            req_dist += dist[s][chosen];

            // update times
            if (q[chosen] == 1) {
                s_time[chosen] = exp_rv(mu_);
                for (int i = 0; i < n; i++) {
                    if (i == chosen) continue;
                    if (s_time[i] < 1e29)
                        s_time[i] -= t_arr;
                }
            } else {
                for (int i = 0; i < n; i++) {
                    if (s_time[i] < 1e29)
                        s_time[i] -= t_arr;
                }
            }

            t_arr = exp_rv(n * lambda_);
        } else {
            // service happens first
            T += min_service;
            q[min_idx] -= 1;
            if (q[min_idx] == 0) {
                s_time[min_idx] = 1e30;
            } else {
                s_time[min_idx] = exp_rv(mu_);
            }

            t_arr -= min_service;

            for (int i = 0; i < n; i++) {
                if (i == min_idx) continue;
                if (s_time[i] < 1e29)
                    s_time[i] -= min_service;
            }
        }
    }

    double sum_hist = 0.0;
    for (double v : q_mid_hist) sum_hist += v;
    if (sum_hist > 0.0) {
        for (double &v : q_mid_hist) v /= sum_hist;
    }

    return {q_mid_hist, req_dist};
}
