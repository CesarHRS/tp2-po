import sys
import time
import re
import gurobipy as gp
from gurobipy import GRB

def parse_ampl_file(filepath):

    #Lê um arquivo e extrai a lista de variáveis, função objetivo e restrições.
    variables = []        
    var_types = {}        
    var_bounds = {}       
    constraints = []      
    objective = None      
    sense = None          

    # Lê o arquivo, ignorando linhas vazias e comentários
    with open(filepath, 'r') as f:
        lines = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]

    for line in lines:
        # Feclaração de variável: var nome tipo limite;
        if line.startswith('var'):
            m = re.match(r'var\s+(\w+)\s+(real|integer)\s+(>=0|<=0|free);', line)
            if m:
                name, vtype, bound = m.groups()
                variables.append(name)
                var_types[name] = vtype
                # Definição dos limites de acordo com o tipo
                if bound == '>=0':
                    var_bounds[name] = (0, GRB.INFINITY)
                elif bound == '<=0':
                    var_bounds[name] = (-GRB.INFINITY, 0)
                else:
                    var_bounds[name] = (-GRB.INFINITY, GRB.INFINITY)
        # Max ou Min
        elif line.startswith('maximize') or line.startswith('minimize'):
            sense = GRB.MAXIMIZE if line.startswith('maximize') else GRB.MINIMIZE
            expr = line.split(':',1)[1].rstrip(';').strip()
            objective = expr
        # Restrição
        elif line.startswith('subject to'):
            expr = line.split(':',1)[1].rstrip(';').strip()
            constraints.append(expr)
        # Fim
        elif line.startswith('end;'):
            break

    return variables, var_types, var_bounds, sense, objective, constraints

# Converte input para o Gurobi
def parse_linear_expr(expr, var_objs):

    # Extrai termos ('coef * var')
    terms = re.findall(r'([+-]?\s*\d*\.?\d*)\s*\*\s*(\w+)', expr)
    result = 0
    for coef, var in terms:
        coef = coef.replace(' ', '')
        # Trata os sinais
        if coef in ('', '+'):
            coef = 1
        elif coef == '-':
            coef = -1
        else:
            coef = float(coef)
        # Soma o termo à expressão
        result += coef * var_objs[var]
    return result

# Converte as restrições (input) para o Gurobi
def parse_constraint(expr, var_objs):
    # Divide a restrição em lado esquerdo, operador e lado direito
    m = re.match(r'(.+)\s*(<=|=|>=)\s*([+-]?\d*\.?\d+)', expr)
    if not m:
        raise ValueError(f"Restrição inválida: {expr}")
    lexpr, op, rhs = m.groups()
    lhs = parse_linear_expr(lexpr, var_objs)
    rhs = float(rhs)
    # Retorna a restrição
    if op == '<=':
        return lhs <= rhs
    elif op == '>=':
        return lhs >= rhs
    else:
        return lhs == rhs

def solve(filepath):
    # Faz o parsing do input
    variables, var_types, var_bounds, sense, objective, constraints = parse_ampl_file(filepath)
    start_time = time.time()  

    model = gp.Model("MIP_from_AMPL")
    model.setParam('OutputFlag', 1) 

    # Cria as variáveis conforme tipo e limites
    var_objs = {}
    for v in variables:
        lb, ub = var_bounds[v]
        vtype = GRB.INTEGER if var_types[v] == 'integer' else GRB.CONTINUOUS
        var_objs[v] = model.addVar(lb=lb, ub=ub, vtype=vtype, name=v)

    model.update() 

    # Define a função objetivo
    obj_expr = parse_linear_expr(objective, var_objs)
    model.setObjective(obj_expr, sense)

    # Adiciona as restrições
    for c in constraints:
        constr = parse_constraint(c, var_objs)
        model.addConstr(constr)

    model.optimize()

    print()
    print("RESULTADO FINAL")
    if model.status == GRB.OPTIMAL:
        print(f"Valor ótimo: {model.ObjVal:.4f}")
        print(f"Tempo total: {time.time()-start_time:.4f} segundos")
        print("Solução ótima encontrada:")
        for v in variables:
            print(f"  {v} = {var_objs[v].X:.4f}")
    elif model.status == GRB.INFEASIBLE:
        print("Problema inviável.")
    elif model.status == GRB.UNBOUNDED:
        print("Problema ilimitado.")
    else:
        print(f"Status do solver: {model.status}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python main.py <arquivo_de_entrada>")
        sys.exit(1)
    solve(sys.argv[1])