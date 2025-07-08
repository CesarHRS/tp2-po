# **Branch-and-Bound para Programação Linear Inteira Mista**

**Autor**: César Henrique Resende Soares e Henrique Souza Fagundes  
**Disciplina**: Pesquisa Operacional 
**Professor**: André L. Maravilha  
**Instituição**: CEFET-MG

---

## **1. Objetivo**

Este programa tem como objetivo **resolver problemas de Programação Linear Inteira Mista** utilizando o algoritmo de **Branch-and-Bound** baseado em relaxação linear, identificando a solução ótima, além de detectar casos de inviabilidade e ilimitado.

---

## **2. Funcionamento**

### **2.1. Entrada**

O programa recebe um **arquivo de texto** (`*.txt`) no formato AMPL, contendo:

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

Durante a execução, o programa exibe uma tabela a cada iteração do Branch-and-Bound, contendo:

- Número da iteração
- Número de nós avaliados
- Número de nós pendentes
- Valor da função objetivo da relaxação linear
- Ação tomada (O: ótimo, L: poda por limite, I: inviável, D: decomposição)
- Valor da melhor solução inteira conhecida (com * se melhorou)
- Tempo decorrido (segundos)

Ao final, são exibidos:

- Valor ótimo da função objetivo (ou mensagem de inviabilidade/ilimitado)
- Número total de iterações
- Tempo total de execução
- Solução ótima encontrada (valores das variáveis)

---

## **3. Método Utilizado**

### **3.1. Algoritmo**

1. **Parsing do arquivo de entrada**:
    - Interpreta variáveis, tipos, domínios, função objetivo e restrições.

2. **Branch-and-Bound**:
    - Resolve a relaxação linear do problema atual.
    - Se a solução for inteira, atualiza a melhor solução.
    - Se não for, ramifica na primeira variável inteira fracionária, criando dois subproblemas.
    - Realiza poda por inviabilidade, otimalidade e limite.
    - Mantém log detalhado de cada iteração.

3. **Tratamento de casos especiais**:
    - Detecta e informa problemas inviáveis ou ilimitados.

### **3.2. Bibliotecas Utilizadas**

- `pulp`: Para modelagem e resolução de problemas de programação linear.
- `re`: Para parsing das expressões do arquivo de entrada.
- `collections.deque`: Para gerenciamento da fila de nós do Branch-and-Bound.
- `time`: Para cálculo do tempo de execução.

---

## **4. Como Executar**

### **4.1. Pré-requisitos**

- Python 3.x instalado.
- Biblioteca: `pulp` (instalável via `pip install pulp`).

### **4.2. Comando de Execução**

```bash
python3 main.py <arquivo_de_entrada.txt>
```

**Exemplo:**

```bash
python3 main.py exemplo1.txt
```

---

## **5. Limitações**

- **Eficiência**: Para problemas grandes, o Branch-and-Bound pode ser lento devido ao crescimento exponencial do número de nós.
- **Parsing**: O parser foi desenvolvido para o formato AMPL simplificado conforme o enunciado; entradas fora desse padrão podem não ser reconhecidas.
- **Precisão Numérica**: Pequenas imprecisões podem ocorrer devido à tolerância na verificação de integridade das variáveis.

---