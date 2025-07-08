import sys
import time
import pulp
import re
from collections import deque

def parse_ampl_file(filepath):
    # Faz o parsing do arquivo AMPL simplificado
    variables = []
    var_types = {}
    var_bounds = {}
    constraints = []
    objective = None
    sense = None

    with open(filepath, 'r') as f:
        lines = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]

    for line in lines:
        if line.startswith('var'):
            # Exemplo: var x1 real >=0;
            m = re.match(r'var\s+(\w+)\s+(real|integer)\s+(>=0|<=0|free);', line)
            if m:
                name, vtype, bound = m.groups()
                variables.append(name)
                var_types[name] = vtype
                if bound == '>=0':
                    var_bounds[name] = (0, None)
                elif bound == '<=0':
                    var_bounds[name] = (None, 0)
                else:
                    var_bounds[name] = (None, None)
        elif line.startswith('maximize') or line.startswith('minimize'):
            # Exemplo: maximize: 1*x1 + 2*x2;
            sense = pulp.LpMaximize if line.startswith('maximize') else pulp.LpMinimize
            expr = line.split(':',1)[1].rstrip(';').strip()
            objective = expr
        elif line.startswith('subject to'):
            # Exemplo: subject to: 1*x1 - 2*x2 <= 4;
            expr = line.split(':',1)[1].rstrip(';').strip()
            constraints.append(expr)
        elif line.startswith('end;'):
            break

    return variables, var_types, var_bounds, sense, objective, constraints

def build_lp(variables, var_types, var_bounds, sense, objective, constraints, extra_constraints=None):
    # Monta o modelo de PL usando pulp
    prob = pulp.LpProblem("MIP", sense)
    var_objs = {}
    for v in variables:
        cat = pulp.LpInteger if var_types[v] == 'integer' else pulp.LpContinuous
        lb, ub = var_bounds[v]
        var_objs[v] = pulp.LpVariable(v, lowBound=lb, upBound=ub, cat=cat)
    # Função objetivo
    prob += parse_linear_expr(objective, var_objs)
    # Restrições
    for c in constraints:
        prob += parse_constraint(c, var_objs)
    # Restrições extras (para ramificações)
    if extra_constraints:
        for c in extra_constraints:
            prob += c
    return prob, var_objs

def parse_linear_expr(expr, var_objs):
    # Faz o parsing de uma expressão linear, exemplo: "1*x1 + 2*x2"
    terms = re.findall(r'([+-]?\s*\d*\.?\d*)\s*\*\s*(\w+)', expr)
    result = 0
    for coef, var in terms:
        coef = coef.replace(' ', '')
        if coef in ('', '+'): coef = 1
        elif coef == '-': coef = -1
        else: coef = float(coef)
        result += coef * var_objs[var]
    return result

def parse_constraint(expr, var_objs):
    # Faz o parsing de uma restrição, exemplo: "1*x1 - 2*x2 <= 4"
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

def is_integral(var_objs, solution, var_types, tol=1e-5):
    # Verifica se todas as variáveis inteiras têm valor inteiro na solução
    for v in var_objs:
        if var_types[v] == 'integer':
            val = solution[v]
            if abs(val - round(val)) > tol:
                return False, v
    return True, None

def format_solution(solution, variables):
    # Formata a solução para exibição
    return [f"{solution[v]:.4f}" for v in variables]

def branch_and_bound(filepath):
    variables, var_types, var_bounds, sense, objective, constraints = parse_ampl_file(filepath)
    best_obj = None
    best_sol = None
    start_time = time.time()
    node_queue = deque()
    node_queue.append(([], 1))  # (restrições extras, id do nó)
    iter_count = 0
    evaluated_nodes = 0
    node_id_counter = 2
    log_lines = []
    best_obj_history = []
    while node_queue:
        extra_constraints, node_id = node_queue.popleft()
        iter_count += 1
        prob, var_objs = build_lp(variables, var_types, var_bounds, sense, objective, constraints, extra_constraints)
        prob.solve(pulp.PULP_CBC_CMD(msg=0))
        evaluated_nodes += 1
        status = pulp.LpStatus[prob.status]
        elapsed = time.time() - start_time
        action = ''
        obj_val = None
        improved = ''
        if status == 'Infeasible':
            action = 'I'
        elif status == 'Unbounded':
            action = 'L'
        elif status == 'Optimal':
            obj_val = pulp.value(prob.objective)
            solution = {v: var_objs[v].varValue for v in variables}
            integral, frac_var = is_integral(var_objs, solution, var_types)
            if integral:
                action = 'O'
                if (best_obj is None) or \
                   (sense == pulp.LpMaximize and obj_val > best_obj + 1e-5) or \
                   (sense == pulp.LpMinimize and obj_val < best_obj - 1e-5):
                    best_obj = obj_val
                    best_sol = solution
                    improved = '*'
            else:
                # Ramifica na primeira variável inteira fracionária encontrada
                action = 'D'
                val = solution[frac_var]
                floor = int(val)
                ceil = floor + 1
                # Ramo esquerdo: var <= floor
                left = extra_constraints + [var_objs[frac_var] <= floor]
                # Ramo direito: var >= ceil
                right = extra_constraints + [var_objs[frac_var] >= ceil]
                node_queue.append((left, node_id_counter))
                node_id_counter += 1
                node_queue.append((right, node_id_counter))
                node_id_counter += 1
        else:
            action = 'I'
        # Log da iteração
        log_lines.append([
            f"{iter_count}",
            f"{evaluated_nodes}",
            f"{len(node_queue)}",
            f"{obj_val:.4f}" if obj_val is not None else "-",
            action,
            f"{best_obj:.4f}{improved}" if best_obj is not None else "-",
            f"{elapsed:.4f}"
        ])
        best_obj_history.append(best_obj)
        # Poda por limite
        if obj_val is not None and best_obj is not None:
            if sense == pulp.LpMaximize and obj_val < best_obj - 1e-5:
                action = 'L'
            elif sense == pulp.LpMinimize and obj_val > best_obj + 1e-5:
                action = 'L'
    # Imprime a tabela de log
    print(f"{'Iter':>4} {'Aval.':>6} {'Pend.':>6} {'ObjRelax':>10} {'Ação':>4} {'MelhorInt':>12} {'Tempo(s)':>10}")
    for l in log_lines:
        print(f"{l[0]:>4} {l[1]:>6} {l[2]:>6} {l[3]:>10} {l[4]:>4} {l[5]:>12} {l[6]:>10}")
    print()
    # Saída final
    print("RESULTADO FINAL")
    if best_obj is not None:
        print(f"Valor ótimo: {best_obj:.4f}")
        print(f"Número total de iterações: {evaluated_nodes}")
        print(f"Tempo total: {time.time()-start_time:.4f} segundos")
        print("Solução ótima encontrada:")
        for v in variables:
            print(f"  {v} = {best_sol[v]:.4f}")
    else:
        # Detecta se foi inviável ou ilimitado
        if any(l[4] == 'L' for l in log_lines):
            print("Problema ilimitado.")
        else:
            print("Problema inviável.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python main.py <arquivo_de_entrada>")
        sys.exit(1)
    branch_and_bound(sys.argv[1])