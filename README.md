# **Branch-and-Bound e Gurobi para Programação Linear Inteira Mista**

**Autores**: César Henrique Resende Soares e Henrique Souza Fagundes  
**Disciplina**: Pesquisa Operacional  
**Professor**: André L. Maravilha  
**Instituição**: CEFET-MG

---

## **1. Objetivo**

Este projeto tem como objetivo **resolver problemas de Programação Linear Inteira Mista** a partir de arquivos no formato AMPL simplificado, utilizando a API oficial do Gurobi:

---

## **2. Funcionamento**

### **2.1. Entrada**

O programa recebe um **arquivo de texto** (`*.txt`) no formato AMPL simplificado, contendo:

- Declaração das variáveis (tipo e domínio)
- Função objetivo (maximize ou minimize)
- Restrições lineares
- Linha final `end;`

**Exemplo de entrada:**
```
var x1 real >=0;
var x2 integer free;
maximize: 1*x1 + 2*x2;
subject to: 1*x1 - 2*x2 <= 4;
subject to: -3*x1 + 2*x2 <= 6;
subject to: 4*x1 + 5*x2 <= 20;
subject to: 2*x1 + 1*x2 >= 2;
end;
```

### **2.2. Saída**

Durante a execução, o programa exibe um log detalhado do Gurobi, contendo os nós, cortes, gaps e tempo

---

## **3. Métodos Utilizados**

- Utiliza o mesmo arquivo de entrada.
- Realiza o parsing do arquivo para extrair variáveis, restrições e a função objetivo.
- Cria o modelo diretamente com a biblioteca `gurobipy`.
- Define variáveis e restrições no modelo e resolve utilizando o solver do Gurobi.
- Exibe o log do Gurobi e a solução ótima.

---

## **4. Como Executar**

### **4.1. Pré-requisitos**

- Python 3.10 instalado.

#### Para Gurobi:

- Biblioteca: `gurobipy`  
  Instale com:
  ```bash
  pip install gurobipy
  ```
---

### **4.2. Comando de Execução**

```bash
python3 main.py <arquivo_de_entrada.txt>
```

---