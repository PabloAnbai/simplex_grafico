# Simplex Gráfico

Programa em Python com interface gráfica para resolver problemas de **Programação Linear com duas variáveis** (`X1` e `X2`):

- recebe a **função objetivo** (maximizar ou minimizar) e as **restrições** (`<=`, `>=`, `=`);
- resolve pelo **método Simplex em quadros (tableau)**, com **Big-M** para restrições `>=` e `=`;
- desenha o **gráfico** da região viável, dos vértices e do ponto ótimo;
- apresenta, se o usuário quiser, o **passo a passo** de cada iteração: pivô, variável que entra e que sai, teste da razão e as operações entre linhas.

## Problema resolvido

```
max (ou min)  Z = c1·X1 + c2·X2
sujeito a     a1·X1 + a2·X2  (<=, >=, =)  b      (uma linha por restrição)
              X1, X2 >= 0
```

## Requisitos

- Python 3.9 ou superior
- Tkinter (já vem com o Python no Windows e no macOS; no Linux: `sudo apt install python3-tk`)
- `numpy` e `matplotlib`

```bash
pip install -r requirements.txt
```

## Como executar

```bash
python main.py
```

Ao abrir, o programa já vem preenchido com um exemplo:

```
max Z = 3·X1 + 5·X2
     X1          <= 4
          2·X2   <= 12
     3·X1 + 2·X2 <= 18
```

Resultado esperado: **X1 = 2, X2 = 6, Z = 36**.

### Usando a interface

1. Escolha **Maximizar** ou **Minimizar** e informe os coeficientes de `Z`.
2. Preencha as restrições. Use **+ Restrição** / **– Restrição** para adicionar ou remover linhas.
3. Clique em **RESOLVER**. Os valores de `X1`, `X2` e `Z` aparecem à esquerda; o gráfico e os quadros, nas abas à direita.
4. (Opcional) Clique em **Ver passo a passo (quadros)** para abrir a apresentação das iterações. Navegue com os botões ou com as setas ← →.

## Convenções do quadro

| Linha | Significado |
|-------|-------------|
| `L0`  | função objetivo (primeira linha do quadro) |
| `L1`  | primeira restrição |
| `L2`  | segunda restrição, e assim por diante |

As variáveis adicionais são nomeadas em sequência `X3, X4, X5, ...`, na ordem em que são criadas:

| Restrição | Variáveis adicionais |
|-----------|----------------------|
| `<=` | uma variável de **folga** (+1) |
| `>=` | uma variável de **excesso** (−1) e uma **artificial** (+1) |
| `=`  | uma variável **artificial** (+1) |

A página de montagem do passo a passo informa o papel de cada uma, por exemplo `(x3: excesso; x4: artificial)`.

## Passo a passo (cada iteração)

Cada página mostra:

1. **Quadro atual**, com a célula do pivô entre colchetes e a coluna e a linha do pivô destacadas.
2. **Escolha do pivô**: coeficientes de `L0`, variável que **entra** (coeficiente mais negativo de `L0`), teste da razão `b ÷ coeficiente` e variável que **sai** (menor razão).
3. **Cálculos**: `L2' = L2 ÷ pivô`, `L0' = L0 − (fator) × L2'`, `L1' = L1 − (fator) × L2'` etc., cada um com a linha resultante.
4. **Novo quadro**, com a base atualizada.

A última página traz o quadro final, as variáveis básicas e a solução. Para problemas inviáveis ou ilimitados, ela explica o motivo.

## Como funciona o Big-M

Em vez de usar um número grande (por exemplo `1e6`), que gera erros numéricos, cada elemento de `L0` é guardado na forma `r + m·M`: a parte real e o coeficiente de `M` ficam separados. As comparações olham primeiro o coeficiente de `M` e depois a parte real, o que equivale a tratar `M` como "infinitamente grande". Nos quadros isso aparece como, por exemplo, `-4M+3.00`.

## Estrutura do projeto

```
simplex-grafico/
├── main.py            # ponto de entrada
├── interface.py       # janelas Tkinter (App e PassoAPasso)
├── simplex.py         # algoritmo Simplex em quadros (Big-M)
├── grafico.py         # vértices, região viável e desenho do gráfico
├── formatacao.py      # formatação em texto dos quadros
├── test_simplex.py    # testes automatizados (pytest)
├── requirements.txt
└── README.md
```

| Módulo | Responsabilidade |
|--------|------------------|
| `simplex.py` | `simplex(c, restr, maximizar)` devolve `status`, `x1`, `x2`, `z`, os `quadros` em texto e as `paginas` do passo a passo |
| `grafico.py` | `vertices`, `viavel`, `limite_grafico`, `desenha`; não depende de Tkinter |
| `formatacao.py` | `tabela_txt`, `formata_quadro`, `fmt_celula`, `fmt_linha`; define `LARG` e `PREFIXO` |
| `interface.py` | interface gráfica; usa os módulos acima |

### Usando o solver sem a interface

```python
from simplex import simplex

res = simplex((3, 5), [(1, 0, "<=", 4), (0, 2, "<=", 12), (3, 2, "<=", 18)], maximizar=True)
print(res["status"], res["x1"], res["x2"], res["z"])   # otimo 2.0 6.0 36.0
print(res["quadros"][0])                                # quadro inicial em texto
```

`status` pode ser `"otimo"`, `"inviavel"` ou `"ilimitado"`.

## Testes

```bash
pip install pytest
pytest -v
```

Os testes cobrem maximização, minimização com restrições `>=`, restrição de igualdade, `b` negativo, problema inviável, problema ilimitado, nomes das variáveis (`x3, x4, ...`), estrutura do passo a passo e vértices da região viável.

## Limitações

- O **gráfico** só existe para 2 variáveis (o Simplex em si funcionaria com mais, mas a interface é fixa em `X1` e `X2`).
- A escolha do pivô usa a regra do coeficiente mais negativo. Em casos degenerados raros o Simplex pode entrar em ciclo; há um limite de 200 iterações como trava de segurança.
- Em problemas com **múltiplas soluções ótimas**, o programa mostra apenas uma delas.
