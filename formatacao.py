# -*- coding: utf-8 -*-
"""
formatacao.py
=============
Funções de formatação em texto dos quadros (tableaus) do Simplex.

Convenção do quadro
-------------------
* ``L0``  -> função objetivo (primeira linha do quadro)
* ``L1``  -> primeira restrição
* ``L2``  -> segunda restrição, e assim por diante.

Cada coluna ocupa ``LARG`` caracteres. As duas primeiras colunas ("Linha" e "Base")
ocupam, juntas, ``PREFIXO`` caracteres. Esses valores são usados pela interface
gráfica para destacar a célula do pivô, por isso não devem ser alterados
isoladamente.
"""

LARG = 13      # largura de cada coluna numérica do quadro (em caracteres)
PREFIXO = 11   # largura somada das colunas "Linha" (6) + "Base" (5)


def fmt_celula(r, m=0.0):
    """
    Formata um número do tipo ``r + m·M`` (método Big-M).

    Parâmetros
    ----------
    r : float
        Parte real do número.
    m : float
        Coeficiente de M (constante "muito grande" do Big-M).

    Exemplos
    --------
    >>> fmt_celula(3.0)
    '3.00'
    >>> fmt_celula(3.0, -4.0)
    '-4M+3.00'
    >>> fmt_celula(0.0, 1.0)
    '1M'
    """
    r = 0.0 if abs(r) < 1e-9 else r
    m = 0.0 if abs(m) < 1e-9 else m
    ms = f"{m:.2f}".rstrip("0").rstrip(".")   # 1.00 -> "1", -0.67 -> "-0.67"
    if m == 0:
        return f"{r:.2f}"
    if r == 0:
        return f"{ms}M"
    return f"{ms}M{r:+.2f}"


def tabela_txt(nomes, base, T, Zm, pivo=None):
    """
    Devolve o quadro em texto: cabeçalho, separador, L0 e L1..Lm.

    Parâmetros
    ----------
    nomes : list[str]
        Nomes das colunas de variáveis (``x1``, ``x2``, ``x3``, ...).
    base : list[int]
        Índice (em ``nomes``) da variável básica de cada restrição.
    T : numpy.ndarray
        Matriz do quadro. As ``m`` primeiras linhas são as restrições, a última
        linha (``T[m]``) é L0. A última coluna é o lado direito ``b``.
    Zm : numpy.ndarray
        Parte "M" da linha L0 (mesmo comprimento que uma linha de ``T``).
    pivo : tuple[int, int] | None
        ``(L, j)``: marca com colchetes a célula do pivô (linha ``L`` do quadro,
        coluna ``j``). ``L = 0`` seria L0; para restrições ``L = i + 1``.
    """
    m = T.shape[0] - 1
    ncol = T.shape[1]

    def cel(L, k, txt):
        if pivo is not None and pivo[0] == L and pivo[1] == k:
            txt = f"[{txt}]"
        return f"{txt:>{LARG}}"

    cab = f"{'Linha':<6}{'Base':<5}" + "".join(f"{n:>{LARG}}" for n in nomes) + f"{'b':>{LARG}}"
    linhas = [cab, "-" * len(cab)]
    linhas.append(
        f"{'L0':<6}{'Z':<5}" + "".join(cel(0, k, fmt_celula(T[m, k], Zm[k])) for k in range(ncol))
    )
    for i in range(m):
        linhas.append(
            f"{'L' + str(i + 1):<6}{nomes[base[i]]:<5}"
            + "".join(cel(i + 1, k, fmt_celula(T[i, k])) for k in range(ncol))
        )
    return "\n".join(linhas)


def formata_quadro(titulo, nomes, base, T, Zm, pivo=None):
    """Igual a :func:`tabela_txt`, mas precedido por uma linha de título."""
    return titulo + "\n" + tabela_txt(nomes, base, T, Zm, pivo)


def fmt_linha(nomes, linha, linha_m=None):
    """
    Escreve uma linha do quadro como ``x1=0.33 | x2=1.00 | ... | b=4.00``.

    ``linha_m`` (opcional) traz a parte M de cada elemento (usado apenas em L0).
    """
    partes = []
    for k, v in enumerate(linha):
        nome = nomes[k] if k < len(nomes) else "b"
        partes.append(f"{nome}={fmt_celula(v, 0.0 if linha_m is None else linha_m[k])}")
    return " | ".join(partes)
