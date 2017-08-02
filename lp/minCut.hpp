#include <ilcplex/ilocplex.h>

#include <cstddef>
#include <cstdlib>
#include <iostream>
#include <random>
#include <boost/graph/adjacency_list.hpp>
#include <boost/graph/connected_components.hpp>
#include <boost/graph/stoer_wagner_min_cut.hpp>
#include <boost/graph/random.hpp>
#include <boost/graph/iteration_macros.hpp>

typedef std::pair<int, int> coord_t;
typedef std::pair<double, coord_t > weight_t;

typedef std::pair<std::vector<int>, std::vector<int> > cut_t;
typedef boost::adjacency_list<boost::listS, boost::listS, boost::undirectedS, boost::no_property, boost::property<boost::edge_weight_t, weight_t> > undirected_graph;

typedef boost::graph_traits<undirected_graph>::vertex_descriptor vertex_t;


double minCutWrapper(IloNumArray sol, IloNum tol, std::vector<cut_t> &cuts, std::mt19937 *rng=NULL); // ohne rng -> Stoer Wagner, mit RNG -> Karger
double minCut(const std::vector<double> &matrix, std::vector<cut_t> &cuts);

