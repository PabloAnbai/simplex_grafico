# -*- coding: utf-8 -*-
"""
grafico.py
==========
Método gráfico para problemas de PL com duas variáveis: cálculo dos vértices da
região viável e desenho (retas das restrições, região viável, vértices, ponto
ótimo e reta da função objetivo).

Este módulo não depende de Tkinter; ``desenha`` recebe um ``matplotlib.axes.Axes``
qualquer, o que permite usá-lo também em scripts e testes.
"""

import numpy as np

EPS = 1e-9


def viavel(p, restr, L=None):
    """
    Verifica se o ponto ``p = (x1, x2)`` satisfaz x1, x2 >= 0 e todas as restrições.

    ``L`` (opcional) acrescenta a caixa auxiliar ``x1 <= L`` e ``x2 <= L``, usada
    para fechar regiões viáveis ilimitadas na hora de desenhar.
    """
    if p[0] < -1e-7 or p[1] < -1e-7:
        return False
    if L is not None and (p[0] > L + 1e-7 or p[1] > L + 1e-7):
        return False
    for a1, a2, s, b in restr:
        v = a1 * p[0] + a2 * p[1]
        if s == "<=" and v > b + 1e-7:
            return False
        if s == ">=" and v < b - 1e-7:
            return False
        if s == "=" and abs(v - b) > 1e-7:
            return False
    return True


def vertices(restr, L=None):
    """
    Devolve os vértices da região viável (lista de ``numpy.ndarray`` com 2 elementos).

    Os vértices são as interseções, duas a duas, das retas das restrições e dos
    eixos (x1 = 0 e x2 = 0) que sejam pontos viáveis. Se ``L`` for informado,
    também são consideradas as retas ``x1 = L`` e ``x2 = L``.
    """
    retas = [(a1, a2, b) for a1, a2, _, b in restr] + [(1, 0, 0), (0, 1, 0)]
    if L is not None:
        retas += [(1, 0, L), (0, 1, L)]
    pts = []
    for i in range(len(retas)):
        for j in range(i + 1, len(retas)):
            A = np.array([[retas[i][0], retas[i][1]], [retas[j][0], retas[j][1]]], float)
            if abs(np.linalg.det(A)) < 1e-12:
                continue   # retas paralelas
            p = np.linalg.solve(A, [retas[i][2], retas[j][2]])
            if viavel(p, restr, L) and not any(np.allclose(p, q, atol=1e-7) for q in pts):
                pts.append(p)
    return pts


def limite_grafico(restr, extra=()):
    """Escolhe o limite (L) dos eixos: 25% acima do maior intercepto/valor relevante."""
    vals = [1.0]
    for a1, a2, _, b in restr:
        if a1 > 0 and b / a1 > 0:
            vals.append(b / a1)
        if a2 > 0 and b / a2 > 0:
            vals.append(b / a2)
    vals += [abs(v) for v in extra if v is not None]
    return max(vals) * 1.25


def desenha(ax, c, restr, maximizar, res):
    """
    Desenha o método gráfico em ``ax``.

    Parâmetros
    ----------
    ax : matplotlib.axes.Axes
    c : tuple[float, float]
        Coeficientes da função objetivo.
    restr : list[tuple]
        Restrições ``(a1, a2, sinal, b)``.
    maximizar : bool
        Tipo de otimização (reservado; a reta de Z é a mesma nos dois casos).
    res : dict
        Resultado de :func:`simplex.simplex` (usa ``status``, ``x1``, ``x2``, ``z``).
    """
    ax.clear()
    L = limite_grafico(restr, [res.get("x1"), res.get("x2")])

    # região viável (polígono ordenado pelo ângulo em torno do centróide)
    pts = vertices(restr, L)
    if len(pts) >= 3:
        P = np.array(pts)
        cen = P.mean(axis=0)
        ordem = np.argsort(np.arctan2(P[:, 1] - cen[1], P[:, 0] - cen[0]))
        P = P[ordem]
        ax.fill(P[:, 0], P[:, 1], color="#4c9be8", alpha=0.30, label="Região viável")

    # retas das restrições
    xs = np.linspace(0, L, 400)
    for k, (a1, a2, s, b) in enumerate(restr, 1):
        rot = f"R{k}: {a1:g}x1 + {a2:g}x2 {s} {b:g}"
        if abs(a2) > EPS:
            ys = (b - a1 * xs) / a2
            m = (ys >= -0.01 * L) & (ys <= L * 1.01)
            ax.plot(xs[m], ys[m], lw=1.6, label=rot)
        elif abs(a1) > EPS:
            ax.axvline(b / a1, lw=1.6, label=rot)

    # vértices (sem a caixa auxiliar)
    vt = vertices(restr)
    if vt:
        V = np.array(vt)
        ax.plot(V[:, 0], V[:, 1], "ko", ms=5, zorder=5)
        for v in V:
            ax.annotate(f"({v[0]:.2f}; {v[1]:.2f})", v, textcoords="offset points",
                        xytext=(6, 6), fontsize=8)

    # solução ótima e reta da função objetivo passando por ela
    if res["status"] == "otimo":
        x1, x2, z = res["x1"], res["x2"], res["z"]
        ax.plot(x1, x2, "r*", ms=16, zorder=6, label=f"Ótimo ({x1:.2f}; {x2:.2f})  Z = {z:.2f}")
        c1, c2 = c
        if abs(c2) > EPS:
            ys = (z - c1 * xs) / c2
            m = (ys >= 0) & (ys <= L)
            ax.plot(xs[m], ys[m], "r--", lw=1.4, label="Função objetivo no ótimo")
        elif abs(c1) > EPS:
            ax.axvline(z / c1, color="r", ls="--", lw=1.4, label="Função objetivo no ótimo")

    ax.set_xlim(0, L)
    ax.set_ylim(0, L)
    ax.set_xlabel("X1")
    ax.set_ylabel("X2")
    ax.set_title("Método gráfico")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper right", fontsize=8)
