# -*- coding: utf-8 -*-
"""
simplex.py
==========
Método Simplex em quadros (tableau) para problemas de Programação Linear com
duas variáveis de decisão (x1 e x2), com suporte a restrições ``<=``, ``>=`` e ``=``.

Formulação resolvida
--------------------
    max (ou min)  Z = c1·x1 + c2·x2
    sujeito a     a1·x1 + a2·x2  (<=, >=, =)  b      (uma linha por restrição)
                  x1, x2 >= 0

Variáveis adicionais
--------------------
Para montar o quadro inicial, cada restrição recebe variáveis extras, nomeadas
em sequência ``x3, x4, x5, ...`` (na ordem em que são criadas):

* restrição ``<=``  ->  uma variável de **folga** (+1);
* restrição ``>=``  ->  uma variável de **excesso** (-1) e uma **artificial** (+1);
* restrição ``=``   ->  uma variável **artificial** (+1).

Método Big-M (exato)
--------------------
As variáveis artificiais têm custo ``-M`` (em maximização). Em vez de usar um
número grande (ex.: 1e6) e sofrer com erros numéricos, cada elemento da linha L0
é guardado como ``r + m·M``: a parte real em ``T[-1]`` e a parte de M em ``Zm``.
As comparações são feitas primeiro pela parte M e depois pela parte real, o que
equivale a tratar M como "infinitamente grande".

Convenção do quadro
-------------------
``L0`` = função objetivo, ``L1`` = 1ª restrição, ``L2`` = 2ª restrição, ...

Minimização
-----------
``min Z`` é resolvido como ``max (-Z)``; o valor final de Z é devolvido já com o
sinal original.
"""

import numpy as np

from formatacao import fmt_celula, fmt_linha, formata_quadro, tabela_txt

EPS = 1e-9
FLIP = {"<=": ">=", ">=": "<=", "=": "="}
MAX_ITER = 200   # trava de segurança contra ciclagem


def simplex(c, restr, maximizar=True):
    """
    Resolve o problema de PL pelo Simplex em quadros.

    Parâmetros
    ----------
    c : tuple[float, float]
        Coeficientes ``(c1, c2)`` da função objetivo.
    restr : list[tuple[float, float, str, float]]
        Restrições ``(a1, a2, sinal, b)`` com ``sinal`` em ``{"<=", ">=", "="}``.
    maximizar : bool
        ``True`` para maximizar Z, ``False`` para minimizar.

    Retorno
    -------
    dict com as chaves:

    ``status``  : ``"otimo"``, ``"inviavel"`` ou ``"ilimitado"``.
    ``x1, x2``  : valores ótimos (``None`` se não houver solução ótima).
    ``z``       : valor ótimo de Z, no sinal original (``None`` se não houver).
    ``quadros`` : lista de textos, um por quadro (inicial + um por iteração).
    ``paginas`` : lista de páginas do passo a passo. Cada página é um dict
                  ``{"titulo": str, "itens": [...]}``; cada item é uma tupla:

                  * ``("h", texto)``           título;
                  * ``("t", texto)``           texto comum;
                  * ``("c", texto)``           texto de cálculo (fonte monoespaçada);
                  * ``("q", texto, pivo)``     quadro; ``pivo`` é ``(L, j, m)`` ou ``None``.
    """
    cc = np.array(c, float)
    if not maximizar:
        cc = -cc  # min Z = - max(-Z)

    # ---- 1) garante b >= 0 (multiplica por -1 e inverte o sinal, se preciso)
    rows = []
    montagem = []
    for k, (a1, a2, s, b) in enumerate(restr, 1):
        if b < 0:
            a1, a2, b, s = -a1, -a2, -b, FLIP[s]
            montagem.append(f"R{k}: b negativo -> a restrição foi multiplicada por -1 (sinal invertido para '{s}').")
        rows.append((a1, a2, s, b))
    m = len(rows)

    # ---- 2) monta as colunas: x1, x2 e as variáveis adicionais x3, x4, ...
    cols = [[r[0] for r in rows], [r[1] for r in rows]]
    nomes = ["x1", "x2"]
    custo = [cc[0], cc[1]]
    eh_art = [False, False]
    base = [None] * m
    proximo = [3]   # índice da próxima variável adicional

    def add(i, val, art):
        """Cria a coluna de uma variável adicional (coeficiente ``val`` na linha i)."""
        col = [0.0] * m
        col[i] = val
        cols.append(col)
        nomes.append(f"x{proximo[0]}")
        proximo[0] += 1
        custo.append(0.0)
        eh_art.append(art)
        return len(nomes) - 1

    for i, (a1, a2, s, b) in enumerate(rows):
        lado = f"{a1:g}·x1 + {a2:g}·x2"
        if s == "<=":
            j = add(i, 1.0, False)
            base[i] = j
            montagem.append(f"R{i + 1}: {lado} <= {b:g}   ->   {lado} + {nomes[j]} = {b:g}"
                            f"   ({nomes[j]}: folga)")
        elif s == ">=":
            jf = add(i, -1.0, False)
            ja = add(i, 1.0, True)
            base[i] = ja
            montagem.append(f"R{i + 1}: {lado} >= {b:g}   ->   {lado} - {nomes[jf]} + {nomes[ja]} = {b:g}"
                            f"   ({nomes[jf]}: excesso; {nomes[ja]}: artificial)")
        else:
            ja = add(i, 1.0, True)
            base[i] = ja
            montagem.append(f"R{i + 1}: {lado} = {b:g}   ->   {lado} + {nomes[ja]} = {b:g}"
                            f"   ({nomes[ja]}: artificial)")

    n = len(nomes)
    na = sum(eh_art)
    T = np.zeros((m + 1, n + 1))
    T[:m, :n] = np.array(cols).T
    T[:m, n] = [r[3] for r in rows]
    T[m, :n] = -np.array(custo)                                   # L0 (parte real)
    Zm = np.array([1.0 if a else 0.0 for a in eh_art] + [0.0])    # L0 (parte M)

    # ---- 3) página 0: montagem do quadro inicial
    paginas = []
    if maximizar:
        txt_obj = f"Maximizar Z = {c[0]:g}·x1 + {c[1]:g}·x2"
    else:
        txt_obj = (f"Minimizar Z = {c[0]:g}·x1 + {c[1]:g}·x2   ->   resolvemos como "
                   f"Maximizar (-Z) = {cc[0]:g}·x1 {cc[1]:+g}·x2")
    itens = [
        ("h", "Passo 0 – Montagem do quadro inicial"),
        ("t", txt_obj),
        ("t", f"L0 (função objetivo):  Z {-cc[0]:+g}·x1 {-cc[1]:+g}·x2 = 0"),
        ("t", ""),
        ("t", "Restrições com as variáveis adicionais (x3, x4, ... = folga, excesso ou artificial):"),
    ]
    itens += [("c", "  " + linha) for linha in montagem]
    itens.append(("t", "L1 = 1ª restrição, L2 = 2ª restrição, e assim por diante."))
    if na:
        itens.append(("t", "Variáveis artificiais usam o método Big-M: custo -M no objetivo (+M em L0)."))
    itens.append(("t", ""))

    if na:
        itens.append(("t", "Quadro antes de zerar as artificiais em L0:"))
        itens.append(("q", tabela_txt(nomes, base, T, Zm), None))
    ops0 = []
    for i in range(m):
        if eh_art[base[i]]:
            Zm -= Zm[base[i]] * T[i]
            ops0.append(f"L0 <- L0 - M × L{i + 1}     (zera a coluna da artificial {nomes[base[i]]} em L0)")
    if na:
        itens.append(("t", ""))
        itens.append(("t", "Ajuste de L0:"))
        itens += [("c", "  " + o) for o in ops0]
        itens.append(("t", ""))
    itens.append(("t", "Quadro inicial:"))
    itens.append(("q", tabela_txt(nomes, base, T, Zm), None))
    paginas.append({"titulo": "Montagem", "itens": itens})

    quadros = [formata_quadro("Quadro inicial", nomes, base, T, Zm)]
    status = "otimo"
    motivo = ""

    # ---- 4) iterações do Simplex
    for it in range(1, MAX_ITER):
        # variável que entra: coluna mais negativa em L0 (compara a parte M, depois a real)
        melhor, j = None, None
        for k in range(n):
            chave = (Zm[k], T[m, k])
            negativo = Zm[k] < -EPS or (abs(Zm[k]) <= EPS and T[m, k] < -EPS)
            if negativo and (melhor is None or chave < melhor):
                melhor, j = chave, k
        if j is None:
            break   # nenhum coeficiente negativo em L0: ótimo

        # variável que sai: teste da razão (menor b / coeficiente, só coeficientes > 0)
        col = T[:m, j]
        pos = col > EPS
        if not pos.any():
            status = "ilimitado"
            faixa = "L1" if m == 1 else f"L1..L{m}"
            motivo = (f"A coluna de {nomes[j]} (a que entraria) não tem nenhum coeficiente positivo "
                      f"em {faixa}: não há limite para o crescimento de {nomes[j]} -> problema ILIMITADO.")
            break
        razoes = np.full(m, np.inf)
        razoes[pos] = T[:m, n][pos] / col[pos]
        i = int(np.argmin(razoes))
        sai = nomes[base[i]]
        entra = nomes[j]
        pv = T[i, j]

        # ----- página da iteração: quadro atual + escolha do pivô
        itens = [("h", f"Iteração {it}")]
        itens.append(("t", "1) Quadro atual (pivô entre colchetes; coluna e linha do pivô em destaque):"))
        itens.append(("q", tabela_txt(nomes, base, T, Zm, pivo=(i + 1, j)), (i + 1, j, m)))
        itens.append(("t", ""))
        itens.append(("t", "2) Escolha do pivô"))
        coefs = "   ".join(f"{nomes[k]}: {fmt_celula(T[m, k], Zm[k])}" for k in range(n))
        itens.append(("c", f"  Coeficientes de L0:  {coefs}"))
        itens.append(("t", f"  Entra na base: {entra}  (coeficiente mais negativo de L0 = {fmt_celula(T[m, j], Zm[j])})"))
        itens.append(("t", f"  Teste da razão (b ÷ coeficiente de {entra}, apenas coeficientes > 0):"))
        for k in range(m):
            if pos[k]:
                marca = f"   <- menor razão: sai {sai}" if k == i else ""
                itens.append(("c", f"    L{k + 1}: {T[k, n]:.2f} ÷ {col[k]:.2f} = {razoes[k]:.2f}{marca}"))
            else:
                itens.append(("c", f"    L{k + 1}: coeficiente {col[k]:.2f} <= 0  (não participa)"))
        itens.append(("t", f"  Sai da base: {sai}   |   Entra: {entra}   |   Pivô = {pv:.2f}  (linha L{i + 1}, coluna {entra})"))
        itens.append(("t", ""))

        # ----- pivoteamento (operações entre linhas)
        itens.append(("t", "3) Cálculos (operações entre linhas)"))
        itens.append(("c", "  Colunas: " + " | ".join(nomes + ["b"])))
        T[i] /= pv
        itens.append(("c", f"  L{i + 1}' = L{i + 1} ÷ {pv:.2f}"))
        itens.append(("c", f"       = {fmt_linha(nomes, T[i])}"))
        for k in [m] + [x for x in range(m) if x != i]:   # L0 primeiro, depois as restrições
            rot = "L0" if k == m else f"L{k + 1}"
            fr = T[k, j]
            fm = Zm[j] if k == m else 0.0
            if abs(fr) < EPS and abs(fm) < EPS:
                itens.append(("c", f"  {rot}' = {rot}      (o coeficiente de {entra} já é 0: a linha não muda)"))
                continue
            itens.append(("c", f"  {rot}' = {rot} - ({fmt_celula(fr, fm)}) × L{i + 1}'"))
            T[k] -= fr * T[i]
            if k == m:
                Zm -= fm * T[i]
                itens.append(("c", f"       = {fmt_linha(nomes, T[m], Zm)}"))
            else:
                itens.append(("c", f"       = {fmt_linha(nomes, T[k])}"))
        base[i] = j
        itens.append(("t", ""))
        itens.append(("t", f"4) Novo quadro (base: {entra} substitui {sai} em L{i + 1}):"))
        itens.append(("q", tabela_txt(nomes, base, T, Zm), None))
        paginas.append({"titulo": f"Iteração {it}", "itens": itens})

        quadros.append(formata_quadro(
            f"Iteração {it}:  entra {entra}, sai {sai}  (pivô = {pv:.2f}, linha L{i + 1}, coluna {entra})",
            nomes, base, T, Zm))

    res = {"status": status, "quadros": quadros, "paginas": paginas,
           "x1": None, "x2": None, "z": None}

    # ---- 5) viabilidade: artificial ainda na base com valor > 0 => inviável
    if status == "otimo":
        for i in range(m):
            if eh_art[base[i]] and T[i, n] > 1e-7:
                status = res["status"] = "inviavel"
                motivo = (f"A variável artificial {nomes[base[i]]} permanece na base com valor "
                          f"{T[i, n]:.2f} > 0 (linha L{i + 1}): as restrições são incompatíveis -> problema INVIÁVEL.")
                break

    # ---- 6) página final
    itens = [("h", "Resultado final")]
    if status in ("ilimitado", "inviavel"):
        itens.append(("t", motivo))
        itens.append(("q", tabela_txt(nomes, base, T, Zm), None))
        paginas.append({"titulo": "Resultado", "itens": itens})
        return res

    x = np.zeros(n)
    for i in range(m):
        x[base[i]] = T[i, n]
    zmax = T[m, n]
    z = zmax if maximizar else -zmax
    res.update(x1=x[0], x2=x[1], z=z)

    itens.append(("t", "Em L0 não há mais coeficientes negativos -> a solução atual é ótima."))
    itens.append(("q", tabela_txt(nomes, base, T, Zm), None))
    itens.append(("t", ""))
    itens.append(("t", "Variáveis básicas (valor = coluna b da sua linha):"))
    for i in range(m):
        itens.append(("c", f"  {nomes[base[i]]} = {T[i, n]:.4f}   (L{i + 1})"))
    itens.append(("t", "Demais variáveis (não básicas) valem 0."))
    itens.append(("t", ""))
    if maximizar:
        itens.append(("c", f"Z = b de L0 = {zmax:.4f}"))
    else:
        itens.append(("c", f"Z (mín) = -(b de L0) = -({zmax:.4f}) = {z:.4f}"))
    itens.append(("c", f"Solução:  X1 = {x[0]:.4f}   X2 = {x[1]:.4f}   Z = {z:.4f}"))
    paginas.append({"titulo": "Resultado", "itens": itens})
    return res
