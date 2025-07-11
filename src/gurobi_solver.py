import sys
import re
import gurobipy as gp
from gurobipy import GRB

# Função para parsear o arquivo AMPL simplificado, extraindo variáveis, tipos, bounds, objetivo e restrições
def parse_ampl_file(filepath):
    variables = []
    var_types = {}
    var_bounds = {}
    constraints = []
    objective = None
    sense = None

    # Lê o arquivo ignorando linhas vazias e comentários
    with open(filepath, 'r') as f:
        lines = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]

    for line in lines:
        # Identificação de variáveis declaradas
        if line.startswith('var'):
            m = re.match(r'var\s+(\w+)\s+(real|integer)\s+(>=0|<=0|free);', line)
            if m:
                name, vtype, bound = m.groups()
                variables.append(name)
                var_types[name] = vtype
                if bound == '>=0':
                    var_bounds[name] = (0, GRB.INFINITY)
                elif bound == '<=0':
                    var_bounds[name] = (-GRB.INFINITY, 0)
                else:
                    var_bounds[name] = (-GRB.INFINITY, GRB.INFINITY)
        # Identificação do tipo de otimização e expressão objetivo
        elif line.startswith('maximize') or line.startswith('minimize'):
            sense = GRB.MAXIMIZE if line.startswith('maximize') else GRB.MINIMIZE
            expr = line.split(':',1)[1].rstrip(';').strip()
            objective = expr
        # Identificação de restrições
        elif line.startswith('subject to'):
            expr = line.split(':',1)[1].rstrip(';').strip()
            constraints.append(expr)
        # Fim do arquivo
        elif line.startswith('end;'):
            break

    return variables, var_types, var_bounds, sense, objective, constraints

# Função para parsear expressões lineares do tipo "1*x1 + 2*x2"
def parse_linear_expr(expr, var_objs):
    terms = re.findall(r'([+-]?\s*\d*\.?\d*)\s*\*\s*(\w+)', expr)
    result = 0
    for coef, var in terms:
        coef = coef.replace(' ', '')
        if coef in ('', '+'):
            coef = 1
        elif coef == '-':
            coef = -1
        else:
            coef = float(coef)
        result += coef * var_objs[var]
    return result

# Função para parsear restrições do tipo "1*x1 + 2*x2 <= 10"
def parse_constraint(expr, var_objs):
    m = re.match(r'(.+)\s*(<=|=|>=)\s*([+-]?\d*\.?\d+)', expr)
    if not m:
        raise ValueError(f"Restrição inválida: {expr}")
    lexpr, op, rhs = m.groups()
    lhs = parse_linear_expr(lexpr, var_objs)
    rhs = float(rhs)
    if op == '<=':
        return lhs <= rhs
    elif op == '>=':
        return lhs >= rhs
    else:
        return lhs == rhs

# Função principal que cria e resolve o modelo usando Gurobi
def solve_with_gurobi(filepath):
    # Parse do arquivo AMPL
    variables, var_types, var_bounds, sense, objective, constraints = parse_ampl_file(filepath)

    # Criação do modelo no Gurobi
    model = gp.Model("MIP_from_AMPL")
    model.setParam('OutputFlag', 1)  # Ativa o log de execução do Gurobi

    # Criação das variáveis no modelo
    var_objs = {}
    for v in variables:
        lb, ub = var_bounds[v]
        vtype = GRB.INTEGER if var_types[v] == 'integer' else GRB.CONTINUOUS
        var_objs[v] = model.addVar(lb=lb, ub=ub, vtype=vtype, name=v)

    model.update()  # Atualiza o modelo após a inserção das variáveis

    # Define a função objetivo
    obj_expr = parse_linear_expr(objective, var_objs)
    model.setObjective(obj_expr, sense)

    # Adiciona as restrições ao modelo
    for c in constraints:
        constr = parse_constraint(c, var_objs)
        model.addConstr(constr)

    # Resolve o modelo
    model.optimize()

    # Mostra o resultado encontrado
    if model.status == GRB.OPTIMAL:
        print("\nSolução ótima encontrada:")
        for v in variables:
            print(f"  {v} = {var_objs[v].X:.4f}")
        print(f"Valor ótimo da função objetivo: {model.ObjVal:.4f}")
    elif model.status == GRB.INFEASIBLE:
        print("O problema é inviável.")
    elif model.status == GRB.UNBOUNDED:
        print("O problema é ilimitado.")
    else:
        print(f"Status do solver: {model.status}")

# Execução via terminal recebendo o arquivo de entrada
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python gurobi_solver.py <arquivo_de_entrada>")
        sys.exit(1)
    solve_with_gurobi(sys.argv[1])
