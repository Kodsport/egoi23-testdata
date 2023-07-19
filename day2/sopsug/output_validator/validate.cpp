#include "validate.h"

#include <bits/stdc++.h>
using namespace std;

#define rep(i, a, b) for(int i = a; i < (b); ++i)
#define all(x) begin(x), end(x)
#define sz(x) (int)(x).size()
typedef long long ll;
typedef pair<int, int> pii;
typedef vector<int> vi;
typedef long double ld;

void toupper_string(string &s){
    for (char& c : s) c = (char)toupper(c);
}

int main(int argc, char **argv) {
    init_io(argc, argv);

    int n,m,k;
    judge_in >> n >> m >> k;

    set<pii> edges1, edges2;

    for(int c1 = 0; c1 < m; c1++){
        int a,b;
        judge_in >> a >> b;
        //a--;
        //b--;
        edges1.insert({a, b});
    }

    for(int c1 = 0; c1 < k; c1++){
        int a,b;
        judge_in >> a >> b;
        //a--;
        //b--;
        edges2.insert({a, b});
    }

    
    string answer, answer_judge;

    if(!(author_out >> answer)){
        wrong_answer("Could not read first string");
    }
    judge_ans >> answer_judge;
    toupper_string(answer);
    toupper_string(answer_judge);

    if(answer == "NO"){
        if(answer_judge != "NO"){
            wrong_answer("Answered 'NO', but solution existed");
        }
    }
    else{
        int u0;
        try{
            size_t pos;
            u0 = stoi(answer, &pos);
            if (pos != answer.size()) throw 0;
        }
        catch(...){
            wrong_answer("First number was not an integer");
        }
        vector<vi> graph(n, vi());
        set<pii> edges;
        vi indeg(n, 0);
        for(int c1 = 0; c1 < n-1; c1++){
            int u,v;
            if(c1 == 0){
                if(!(author_out >> v)){
                    wrong_answer("Could not read second edge endpoint");
                }
                u = u0;
            }
            else{
                if(!(author_out >> u >> v)){
                    wrong_answer("Could not read %dth edge", c1+1);
                }
            }
            //u--;
            //v--;
            if(u < 0 || u >= n || v < 0 || v >= n){
                wrong_answer("Edge (%d,%d) out of range", u, v);
            }
            pair p = {u, v};
            if(edges2.find(p) != edges2.end()){
                wrong_answer("Edge (%d,%d) was not allowed", u, v);
            }
            edges.insert(p);
            graph[v].push_back(u);
            indeg[u]++;
        }

        for(auto p : edges1){
            if(edges.find(p) == edges.end()){
                wrong_answer("Edge (%d,%d) was not included", p.first, p.second);
            }
        }

        int root = -1;
        for(int c1 = 0; c1 < n; c1++){
            if(indeg[c1] == 0){
                root = c1;
            }
        }

        if(root == -1){
            wrong_answer("The arborescence did not have a root");
        }

        vi Q;
        Q.push_back(root);
        vi mark(n, 0);
        int seen = 1;
        mark[root] = 1;
        while(!Q.empty()){
            int u = Q.back();
            Q.pop_back();
            for(auto v : graph[u]){
                if(mark[v] == 0){
                    seen++;
                    mark[v] = 1;
                    Q.push_back(v);
                }
            }
        }

        if(seen != n){
            wrong_answer("The arborescence was not connected");
        }

        if(answer_judge == "NO"){
            judge_error("Contestant found a solution but judge said 'NO'");
        }
    }

    string trailing;
    if(author_out >> trailing){
        wrong_answer("Trailing output");
    }


    accept();
}
