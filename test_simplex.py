# -*- coding: utf-8 -*-
"""
Testes automatizados do solver e da geometria (não precisam de Tkinter).

Execução:
    pip install pytest
    pytest -v
"""

import pytest

from grafico import vertices
from simplex import simplex

EXEMPLO_MAX = [(1, 0, "<=", 4), (0, 2, "<=", 12), (3, 2, "<=", 18)]


def test_maximizacao_basica():
    r = simplex((3, 5), EXEMPLO_MAX, maximizar=True)
    assert r["status"] == "otimo"
    assert r["x1"] == pytest.approx(2)
    assert r["x2"] == pytest.approx(6)
    assert r["z"] == pytest.approx(36)


def test_minimizacao_com_restricoes_maior_igual():
    r = simplex((2, 3), [(1, 1, ">=", 4), (1, 3, ">=", 6)], maximizar=False)
    assert r["status"] == "otimo"
    assert r["x1"] == pytest.approx(3)
    assert r["x2"] == pytest.approx(1)
    assert r["z"] == pytest.approx(9)


def test_restricao_de_igualdade():
    r = simplex((1, 2), [(1, 1, "=", 4), (1, 0, "<=", 3)], maximizar=True)
    assert r["status"] == "otimo"
    assert r["x1"] == pytest.approx(0)
    assert r["x2"] == pytest.approx(4)
    assert r["z"] == pytest.approx(8)


def test_b_negativo_e_normalizado():
    # x1 - x2 >= -2  equivale a  -x1 + x2 <= 2
    r = simplex((1, 1), [(1, -1, ">=", -2), (1, 1, "<=", 6)], maximizar=True)
    assert r["status"] == "otimo"
    assert r["z"] == pytest.approx(6)


def test_problema_inviavel():
    r = simplex((1, 1), [(1, 1, "<=", 2), (1, 1, ">=", 5)], maximizar=True)
    assert r["status"] == "inviavel"
    assert r["z"] is None


def test_problema_ilimitado():
    r = simplex((1, 1), [(1, -1, "<=", 2)], maximizar=True)
    assert r["status"] == "ilimitado"
    assert r["z"] is None


def test_variaveis_adicionais_se_chamam_x3_x4():
    r = simplex((2, 3), [(1, 1, ">=", 4), (1, 3, ">=", 6)], maximizar=False)
    cabecalho = r["quadros"][0].splitlines()[1]
    for nome in ("x1", "x2", "x3", "x4", "x5", "x6"):
        assert nome in cabecalho
    assert "f1" not in cabecalho and "a1" not in cabecalho


def test_estrutura_do_passo_a_passo():
    r = simplex((3, 5), EXEMPLO_MAX, maximizar=True)
    paginas = r["paginas"]
    # montagem + 2 iterações + resultado
    assert [p["titulo"] for p in paginas][0] == "Montagem"
    assert paginas[-1]["titulo"] == "Resultado"
    # as páginas de iteração trazem o pivô e os cálculos
    texto = "\n".join(i[1] for i in paginas[1]["itens"])
    assert "Entra na base" in texto and "Sai da base" in texto and "Pivô" in texto
    assert "L0'" in texto and "L1" in texto


def test_vertices_da_regiao_viavel():
    v = {(round(float(p[0]), 6), round(float(p[1]), 6)) for p in vertices(EXEMPLO_MAX)}
    assert v == {(0, 0), (4, 0), (4, 3), (2, 6), (0, 6)}
