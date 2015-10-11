#include "minCut.hpp"

/* findet den Min Cut des aktuellen Tour Graphen
 * ftp://mojca.iems.northwestern.edu/Yue%20Geng/Ch1/literature/min-cut.pdf
 *
 * in left und right werden die endpunkte der geschnittenen Kanten
 * eingetragen, sodass daraus die Cut-Set Constraints http://rma350.scripts.mit.edu/home/?p=116
 * gewonnen werden können
 *
 * es wird die summe der gewichte der geschnittenen Kanten zurück gegeben
 * */

double minCutWrapper(IloNumArray sol, IloNum tol, std::vector<cut_t> &cuts, std::mt19937 *rng)
{
    const int n = sol.getSize();

    std::vector<double> matrix(n, 0);
    for(int i=0; i<n; i++)
        matrix[i] = sol[i] < tol ? 0.0 : sol[i];

    double min;
    min = minCut(matrix, cuts);

    return min;
}

// http://www.boost.org/doc/libs/1_57_0/libs/graph/example/stoer_wagner.cpp
// zu großen Teilen ist dies das Beispiel aus der Boost Dokumentation
double minCut(const std::vector<double> &matrix, std::vector<cut_t> &cuts)
{
    typedef boost::adjacency_list<boost::vecS, boost::vecS, boost::undirectedS, boost::no_property, boost::property<boost::edge_weight_t, double> > undirected_graph;

    const int n = matrix.size();
    const int N = round(sqrt(n));

    double w;

    std::vector<std::pair<int, int> > edge;
    std::vector<double> weight;

    for(int i=0; i<N; i++)
        for(int j=0; j<=i; j++)
            if(matrix[i*N+j])
            {
                edge.push_back(std::pair<int, int>(i, j));
                weight.push_back(matrix[i*N+j]);
            }

    undirected_graph g(edge.begin(), edge.end(), weight.begin(), N);

    // teste zunächst, mit einer schnellen DFS, ob der Graph zusammenhängend ist
    // vgl. http://www.boost.org/doc/libs/1_57_0/libs/graph/example/connected_components.cpp
    std::vector<int> component(N);
    int num = connected_components(g, &component[0]);
    // wenn er nicht zusammhängend ist, generiere für jede Komponente einen Cut.
    // je mehr Cuts desto Besser. Falls das Problem zu groß wird, sollte
    // cplex überflüssige selbstständig bereinigen
    if(num > 1)
    {
        for(int j=0; j<num; j++)
        {
            int cur = cuts.size();
            cuts.push_back(cut_t());
            for(int i=0; i<N; i++)
            {
                if(component[i] == j)
                    cuts[cur].first.push_back(i);
                else
                    cuts[cur].second.push_back(i);
            }
        }
        w = 0.0;
    }
    else
    {
        // define a property map, `parities`, that will store a boolean value for each vertex.
        // Vertices that have the same parity after `stoer_wagner_min_cut` runs are on the same side of the min-cut.
        BOOST_AUTO(parities, boost::make_one_bit_color_map(num_vertices(g), get(boost::vertex_index, g)));

        // run the Stoer-Wagner algorithm to obtain the min-cut weight. `parities` is also filled in.
        w = boost::stoer_wagner_min_cut(g, get(boost::edge_weight, g), boost::parity_map(parities));

        // iteriere über Knoten, und sortiere sie in 2 Sets, zwischen denen der
        // Min Cut verläuft
        int cur = cuts.size();
        cuts.push_back(cut_t());
        BGL_FORALL_VERTICES(v, g, undirected_graph)
        {
            if (get(parities, v))
                cuts[cur].first.push_back(v);
            else
                cuts[cur].second.push_back(v);
        }
    }

    return w;
}

