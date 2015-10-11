#include <cmath>

#include <ilcplex/ilocplex.h>

#include "minCut.hpp"

#include "defines.h"

#include <boost/python.hpp>
namespace py = boost::python;


typedef std::deque<int> tour_t;

class CplexTSPSolver
{
    public:
        CplexTSPSolver(int N, py::list d);
        ~CplexTSPSolver();

        double solve(double &relaxObj, int &searchedNodes, int& numCuts, int &relaxCuts);

        py::list nextRelaxation();
        void initial();

    private:
        int mip;
        int mtz;
        int cuts;
        int relaxCuts;
        int v;
        int seed;
        bool genericCuts;
        bool max_time;
        bool onlyLP;
        bool heuristic;
        int N;
        std::vector<double> c;
        bool first;
        bool finished;

        IloEnv env;
        IloNumVarArray x;                       // zu optimierende Variablen
        IloModel model;
        IloCplex cplex;

        IloNumVarArray init_var(IloModel model);
        IloNumVarArray init_symmetric_var(IloModel model);
        void add_MTZ_constraints(IloModel model, IloNumVarArray x);
        void add_inout_constraints(IloModel model, IloNumVarArray x);
        void add_symmetric_inout_constraints(IloModel model, IloNumVarArray x);
        void add_2tour_constraints(IloModel model, IloNumVarArray x);
};

int getTourLen(IloNumArray sol, IloNumArray visited, IloNum tol, tour_t *tour=NULL, bool mip=true);

inline IloConstraintArray subtourEliminationConstraint(IloEnv env, int N, IloNumArray sol, IloNumVarArray x, IloNum tol, int v, std::mt19937 *rng=NULL);
inline IloConstraint subtourConstraint(IloEnv env, int N, IloNumArray sol, IloNumVarArray x, IloNum tol, int v);
