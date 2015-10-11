#include "cplex.hpp"

#define LU(i, j, N) ((i)*(N)+(j))

ILOSTLBEGIN

// Achtung! hier ist C mit Klassen C++ code :/

// Konstruktor
CplexTSPSolver::CplexTSPSolver(int n, py::list d)
    : mip(0), mtz(0), cuts(1), v(0), seed(42), genericCuts(false), max_time(0), onlyLP(false), heuristic(false)
{
    first = true;
    N = n;
    std::vector<double> mat(N*N);
    for(int i=0; i<N*N; ++i)
        mat[i] = py::extract<double>(d[i]);

    c = std::move(mat);

    initial();
}

// Dekonstruktor
CplexTSPSolver::~CplexTSPSolver()
{
    cplex.clearModel();
    model.end();
    cplex.end();
    env.end();
}

/* initialisiere N^2 Variablen und erstelle eine zu minimierende
 * Strecken-Zielfunktion über die Distanzmatrix c
 *
 * eigentlich sind nur (N*N-N)/2 Variablen nötig, aber dafür müsste
 * ich mir etwas schlaues zur Adressierung ausdenken (weil das untere linke
 * Dreieck einer Matrix adressiert werden muss, ist das nicht trivial)
 * Der Presolver scheint die überflüssigen Variablen allerdings
 * direkt zu verwerfen, weshalb das nicht dringend ist.
 * */
IloNumVarArray CplexTSPSolver::init_symmetric_var(IloModel model)
{
    IloEnv env = model.getEnv();

    // Edge Variables
    IloNumVarArray x(env);
    for(int i=0; i<N; i++)
        for(int j=0; j<N; j++)
            if(j<i)
                x.add(IloNumVar(env, 0, 1, mip ? ILOINT : ILOFLOAT));
            else
                x.add(IloNumVar(env, 0, 0, ILOFLOAT)); // fülle oben rechts mit dummies
    model.add(x);

    // Cost Function
    IloExpr expr(env);

    // die folgenden Schleifen adressieren ein unteres linkes
    // Dreieck in einer quadratischen Matrix
    for(int i=0; i<N; i++)
        for (int j=0; j<i; j++)
            expr += c[i*N + j] * x[i*N + j];

    model.add(IloMinimize(env, expr));
    expr.end();

    return x;
}

/* füge die symmetrsichen Constraints hinzu (sum_{j<i} x_{ij} = 2)
 * Diese sind zwar auch Randfälle der SubtourEliminationConstraints, aber wenn man
 * sie per Hand hinzufügt, beschleunigt das die Berechnungen extrem
 * */
void CplexTSPSolver::add_symmetric_inout_constraints(IloModel model, IloNumVarArray x)
{

    // wegen der Symmetrie ist nur das untere linke Dreieck mit
    // variablen gefüllt. die inneren Schleifen gehen zeilen entlang
    // und "reflektieren" an der Diagonalen.
    // Die Kommentare "eingehend" und "ausgehend" stimmen so nicht,
    // da tatsächlich symmetrie vorliegt, machen aber dennoch den Zweck
    // deutlich

    IloEnv env = model.getEnv();
    for(int i=0; i<N; i++)
    {
        IloExpr expr(env);
        // eingehende
        for(int j=0; j<i; j++)
            expr += x[i*N+j];
        // ausgehende
        for(int j=i+1; j<N; j++)
            expr += x[j*N+i];

        model.add(expr == 2);
        expr.end();
    }
}

/* prüft, die Länge der Tour, dabei ist
 * sol ein Array, dass die Werte der Kanten enthält (angeordnet als LU Dreieck),
 * visited ist ein Hilfsarray, dass sich merkt, welche Punkte schon besucht wurden
 * tol ist die numerische Toleranz (vgl. andere Bsp. für Lazy Constraints)
 * */
int getTourLen(IloNumArray sol, IloNumArray visited, IloNum tol, tour_t *tour, bool mip)
{
    int j;
    const int n = sol.getSize();
    const int N = sqrt(n);
    int last = -1;
    int length = 0;
    int current = 0;

    visited.clear();
    visited.add(n, 0.0); // mit 0 initialisieren

    // Problemgröße von 0? Das sollte nicht passieren
    if(n == 0)
    {
        printf(ERROR "argghh! zero! zero length LP representation!\n");
        return (N+1);
    }

    // bis ich wieder da ankomme, wo ich gewesen bin
    while(visited[current] == 0)
    {
        length++;
        visited[current] = length; // notiere Position auf der Stadt

        // suche die nächste Stadt in der Waagerechten des UL Dreiecks
        for(j=0; j<current; j++)
            if(j != last && sol[current*N + j] >= 1.0-tol)
                break;

        // wenn ich nicht abgebrochen habe -> nicht gefunden
        // suche die nächste Stadt in der Senkrechten des UL Dreiecks
        if(j == current)
            for(j = current+1; j < N; j++)
                if(j != last && sol[j*N + current] >= 1.0-tol)
                    break;

        // es gibt keinen Nachbarn ?! Das sollte nicht passieren.
        if(j == N)
        {
            if(mip)
                printf(ERROR "argghh! separated point! no neighbors! everybody panic!\n");
            return (N+1);
        }

        // gehe zur nächsten Stadt
        last = current;
        current = j;

        if(tour != NULL)
            tour->push_back(current);
    }

    // Länge der getroffenen Subtour
    return length;
}

/* Erstelle eine SubtourElimination Constraint aus einer fraktionalen Lösung mittels
 * MinCut Orakel. Wenn der Probalistische Karger Algorithmus genutzt werden
 * soll, muss ein RNG mitgegeben werden. Wenn statt RNG eine NULL
 * übergeben wird, wird der deterministische Stör-Wagner Algorithmus benutzt.
 *
 * statische Funktion, wird von den Lazy- und UserCut-Callbacks genutzt
 * */
IloConstraintArray subtourEliminationConstraint(IloEnv env, int N, IloNumArray sol, IloNumVarArray x, IloNum tol, int v, std::mt19937 *rng)
{
    if(v >= 5)
        std::cout << INFO "Min Cut!" << std::endl;

    std::vector<cut_t> cuts;
    std::vector<int> left, right;

    IloConstraintArray out(env);

    double cut = minCutWrapper(sol, tol, cuts, rng);

    for(size_t i=0; i<cuts.size(); i++)
    {
        left = std::move(cuts[i].first);
        right = std::move(cuts[i].second);

        if(cut >= 2.0-tol)
        {
            if(v >= 5)
                std::cout << INFO "Valid!" << std::endl;
        }
        else
        {
            // verletzte SubtourEliminationConstraint hinzufügen und weiter lösen
            //~ Implementing the Dantzig-Fulkerson-Johnson algorithm for large traveling salesman problems
            //~ http://dx.doi.org/10.1007/s10107-003-0440-4
            IloExpr expr(env);
            for(size_t i=0; i<left.size(); i++)
                for(size_t j=0; j<right.size(); j++)
                    if(left[i]>right[j])
                        expr += x[left[i]*N + right[j]];
                    else
                        expr += x[right[j]*N + left[i]];

            out.add(expr >= 2);
            expr.end();
        }

        left.clear();
        right.clear();
    }

    return out;
}



void CplexTSPSolver::initial()
{
    // zu kleine Systeme (bspw. N=0) bringen den solver zum Absturz
    if(N <= 3)
    {
        printf(ERROR "%d cities do not make sense! aborting...\n", N);
        return;
        //~ return -3;
    }

    // create the CPLEX objects
    model = IloModel(env);
    cplex = IloCplex(model);

    // how verbose are we?
    if(v<4)
        cplex.setOut(env.getNullStream());
    if(v==0)
        cplex.setWarning(env.getNullStream());

    x = init_symmetric_var(model);
    add_symmetric_inout_constraints(model, x);

    cplex.setParam(IloCplex::HeurFreq, -1);

    //~ cplex.setParam(IloCplex::RootAlg, IloCplex::Barrier);
    cplex.setParam(IloCplex::Threads, 1);
    cplex.setParam(IloCplex::NodeFileInd, 3);
    // maximal 900MB Tree Size
    cplex.setParam(IloCplex::TreLim, 900);

    cplex.solve();

}

py::list CplexTSPSolver::nextRelaxation()
{
    IloInt n   = N*N;
    py::list ret;
    IloNumArray sol(env, n);

    if(!first)
    {
        cplex.getValues(sol, x);

        IloConstraintArray constraints = subtourEliminationConstraint(env, N, sol, x, 10e-5, v);
        for(int i=0; i<constraints.getSize(); i++)
            model.add(constraints[i]);

        std::cout << constraints.getSize() << " Constraints\n";
        if(!constraints.getSize())
        {
            std::cout << "finished!\n";
            return ret; // return empty list
        }

        constraints.end();

        cplex.solve();
    }
    first = false;

    cplex.getValues(sol, x);

    //return adjacency matrix as pyList
    for(int i=0; i<n; ++i)
        ret.append(sol[i]);

    sol.end();
    return ret;
}

BOOST_PYTHON_MODULE(CplexTSPSolver)
{
    py::class_<CplexTSPSolver>("CplexTSPSolver", py::init<int, py::list>())
        .def("nextRelaxation", &CplexTSPSolver::nextRelaxation)
    ;
}
