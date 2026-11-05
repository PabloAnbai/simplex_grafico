# -*- coding: utf-8 -*-
"""
interface.py
============
Interface gráfica (Tkinter + Matplotlib).

Classes
-------
``PassoAPasso`` : janela que apresenta, página por página, as iterações do Simplex
                  (quadro com o pivô destacado, variável que entra/sai, teste da
                  razão e operações entre linhas).
``App``         : janela principal (entrada dos dados, resultado, gráfico e quadros).
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from formatacao import LARG, PREFIXO
from grafico import desenha
from simplex import simplex

FONTE_MONO = ("Consolas", 10)


class PassoAPasso(tk.Toplevel):
    """
    Janela de apresentação passo a passo.

    Recebe a lista ``paginas`` devolvida por :func:`simplex.simplex`. A navegação
    é feita pelos botões ou pelas setas do teclado (← e →).
    """

    def __init__(self, master, paginas):
        super().__init__(master)
        self.title("Simplex – passo a passo")
        self.geometry("1050x720")
        self.paginas = paginas
        self.idx = 0

        topo = ttk.Frame(self, padding=6)
        topo.pack(fill="x")
        self.b_ini = ttk.Button(topo, text="⏮ Início", command=lambda: self.ir(0))
        self.b_ant = ttk.Button(topo, text="◀ Anterior", command=lambda: self.ir(self.idx - 1))
        self.b_prox = ttk.Button(topo, text="Próximo ▶", command=lambda: self.ir(self.idx + 1))
        self.b_fim = ttk.Button(topo, text="Fim ⏭", command=lambda: self.ir(len(self.paginas) - 1))
        for b in (self.b_ini, self.b_ant, self.b_prox, self.b_fim):
            b.pack(side="left", padx=2)
        self.lbl = ttk.Label(topo, text="", font=("", 10, "bold"))
        self.lbl.pack(side="left", padx=14)
        ttk.Label(topo, text="(use as setas ← →)").pack(side="right")

        corpo = ttk.Frame(self)
        corpo.pack(fill="both", expand=True)
        self.txt = tk.Text(corpo, wrap="none", font=FONTE_MONO, padx=10, pady=8)
        sy = ttk.Scrollbar(corpo, orient="vertical", command=self.txt.yview)
        sx = ttk.Scrollbar(corpo, orient="horizontal", command=self.txt.xview)
        self.txt.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        sy.pack(side="right", fill="y")
        sx.pack(side="bottom", fill="x")
        self.txt.pack(side="left", fill="both", expand=True)

        # tags de formatação (a última criada tem maior prioridade; "pivo" é elevada)
        self.txt.tag_configure("h", font=("Consolas", 13, "bold"), spacing3=6)
        self.txt.tag_configure("mono", font=FONTE_MONO)
        self.txt.tag_configure("colpivo", background="#fff3bf")
        self.txt.tag_configure("linhapivo", background="#ffe3c2")
        self.txt.tag_configure("pivo", background="#ff922b", font=("Consolas", 10, "bold"))
        self.txt.tag_raise("pivo")

        self.bind("<Left>", lambda e: self.ir(self.idx - 1))
        self.bind("<Right>", lambda e: self.ir(self.idx + 1))
        self.ir(0)
        self.focus_set()

    def ir(self, k):
        """Mostra a página ``k`` (ignora índices fora do intervalo)."""
        if not 0 <= k < len(self.paginas):
            return
        self.idx = k
        pg = self.paginas[k]
        t = self.txt
        t.configure(state="normal")
        t.delete("1.0", "end")
        for item in pg["itens"]:
            tipo, texto = item[0], item[1]
            if tipo == "h":
                t.insert("end", texto + "\n", "h")
            elif tipo == "q":
                self._quadro(texto, item[2])
            elif tipo == "c":
                t.insert("end", texto + "\n", "mono")
            else:
                t.insert("end", texto + "\n")
        t.configure(state="disabled")
        t.yview_moveto(0)
        self.lbl.config(text=f"Página {k + 1} de {len(self.paginas)}  –  {pg['titulo']}")
        self.b_ini.state(["!disabled"] if k > 0 else ["disabled"])
        self.b_ant.state(["!disabled"] if k > 0 else ["disabled"])
        self.b_prox.state(["!disabled"] if k < len(self.paginas) - 1 else ["disabled"])
        self.b_fim.state(["!disabled"] if k < len(self.paginas) - 1 else ["disabled"])

    def _quadro(self, texto, pivo):
        """
        Insere um quadro e, se ``pivo = (L, j, m)`` for informado, destaca a coluna
        do pivô, a linha do pivô e a célula do pivô.

        Linhas do texto do quadro: 0 = cabeçalho, 1 = separador, 2 = L0, 3 = L1, ...
        """
        t = self.txt
        ini = int(t.index("end-1c").split(".")[0])   # número da linha onde o quadro começa
        t.insert("end", texto + "\n\n", "mono")
        if not pivo:
            return
        Lp, j, m = pivo
        c0 = PREFIXO + LARG * j
        c1 = c0 + LARG
        t.tag_add("colpivo", f"{ini}.{c0}", f"{ini}.{c1}")             # cabeçalho da coluna
        for L in range(m + 1):                                         # L0..Lm
            ln = ini + 2 + L
            t.tag_add("colpivo", f"{ln}.{c0}", f"{ln}.{c1}")
        ln = ini + 2 + Lp
        t.tag_add("linhapivo", f"{ln}.0", f"{ln}.end")
        t.tag_add("pivo", f"{ln}.{c0}", f"{ln}.{c1}")


class App(tk.Tk):
    """Janela principal: entrada, botão RESOLVER, resultado, gráfico e quadros."""

    def __init__(self):
        super().__init__()
        self.title("Programação Linear – Simplex e Gráfico")
        self.geometry("1100x650")
        self.res = None
        self.janela_passos = None

        esq = ttk.Frame(self, padding=10)
        esq.pack(side="left", fill="y")

        # --- função objetivo
        ttk.Label(esq, text="Função objetivo", font=("", 11, "bold")).pack(anchor="w")
        self.tipo = tk.StringVar(value="max")
        f0 = ttk.Frame(esq)
        f0.pack(anchor="w", pady=2)
        ttk.Radiobutton(f0, text="Maximizar", variable=self.tipo, value="max").pack(side="left")
        ttk.Radiobutton(f0, text="Minimizar", variable=self.tipo, value="min").pack(side="left", padx=8)

        f1 = ttk.Frame(esq)
        f1.pack(anchor="w", pady=4)
        ttk.Label(f1, text="Z =").pack(side="left")
        self.c1 = ttk.Entry(f1, width=6)
        self.c1.pack(side="left", padx=2)
        ttk.Label(f1, text="X1 +").pack(side="left")
        self.c2 = ttk.Entry(f1, width=6)
        self.c2.pack(side="left", padx=2)
        ttk.Label(f1, text="X2").pack(side="left")
        self.c1.insert(0, "3")
        self.c2.insert(0, "5")

        # --- restrições
        ttk.Label(esq, text="Restrições (X1, X2 ≥ 0)", font=("", 11, "bold")).pack(anchor="w", pady=(12, 0))
        self.fr = ttk.Frame(esq)
        self.fr.pack(anchor="w", pady=4)
        self.linhas = []
        for a1, a2, s, b in [(1, 0, "<=", 4), (0, 2, "<=", 12), (3, 2, "<=", 18)]:
            self.add_restricao(a1, a2, s, b)

        fb = ttk.Frame(esq)
        fb.pack(anchor="w", pady=4)
        ttk.Button(fb, text="+ Restrição", command=self.add_restricao).pack(side="left")
        ttk.Button(fb, text="– Restrição", command=self.rem_restricao).pack(side="left", padx=6)

        ttk.Button(esq, text="RESOLVER", command=self.resolver).pack(fill="x", pady=(14, 4), ipady=4)
        self.btn_passos = ttk.Button(esq, text="Ver passo a passo (quadros)",
                                     command=self.abrir_passos, state="disabled")
        self.btn_passos.pack(fill="x", pady=(0, 6), ipady=2)

        self.lbl_res = ttk.Label(esq, text="", font=("Consolas", 11), justify="left")
        self.lbl_res.pack(anchor="w", pady=6)

        # --- abas (gráfico e quadros)
        dir_ = ttk.Notebook(self)
        dir_.pack(side="right", fill="both", expand=True, padx=6, pady=6)

        aba_g = ttk.Frame(dir_)
        dir_.add(aba_g, text="Gráfico")
        self.fig = Figure(figsize=(6, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=aba_g)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        aba_q = ttk.Frame(dir_)
        dir_.add(aba_q, text="Quadros do Simplex")
        self.txt = scrolledtext.ScrolledText(aba_q, font=FONTE_MONO, wrap="none")
        self.txt.pack(fill="both", expand=True)

        self.resolver()

    # ---- restrições dinâmicas
    def add_restricao(self, a1="", a2="", s="<=", b=""):
        """Acrescenta uma linha de restrição ``a1·X1 + a2·X2 (sinal) b``."""
        f = ttk.Frame(self.fr)
        f.pack(anchor="w", pady=1)
        e1 = ttk.Entry(f, width=6)
        e2 = ttk.Entry(f, width=6)
        cb = ttk.Combobox(f, values=["<=", ">=", "="], width=3, state="readonly")
        e3 = ttk.Entry(f, width=7)
        e1.pack(side="left")
        ttk.Label(f, text="X1 +").pack(side="left", padx=2)
        e2.pack(side="left")
        ttk.Label(f, text="X2").pack(side="left", padx=2)
        cb.pack(side="left", padx=2)
        e3.pack(side="left")
        e1.insert(0, str(a1))
        e2.insert(0, str(a2))
        cb.set(s)
        e3.insert(0, str(b))
        self.linhas.append((f, e1, e2, cb, e3))

    def rem_restricao(self):
        """Remove a última restrição (mantém pelo menos uma)."""
        if len(self.linhas) > 1:
            self.linhas.pop()[0].destroy()

    @staticmethod
    def num(entry, nome):
        """Lê um número de um campo (aceita vírgula decimal); levanta ValueError se inválido."""
        try:
            return float(entry.get().replace(",", "."))
        except ValueError:
            raise ValueError(f"Valor inválido em {nome}.")

    # ---- passo a passo
    def fechar_passos(self):
        """Fecha a janela do passo a passo, se estiver aberta."""
        if self.janela_passos is not None:
            try:
                self.janela_passos.destroy()
            except tk.TclError:
                pass
            self.janela_passos = None

    def abrir_passos(self):
        """Abre a janela do passo a passo para o último problema resolvido."""
        if not self.res:
            return
        self.fechar_passos()
        self.janela_passos = PassoAPasso(self, self.res["paginas"])

    # ---- resolver
    def resolver(self):
        """Lê os dados, resolve pelo Simplex, atualiza resultado, quadros e gráfico."""
        try:
            c = (self.num(self.c1, "função objetivo"), self.num(self.c2, "função objetivo"))
            restr = []
            for k, (_, e1, e2, cb, e3) in enumerate(self.linhas, 1):
                restr.append((self.num(e1, f"restrição {k}"), self.num(e2, f"restrição {k}"),
                              cb.get(), self.num(e3, f"restrição {k}")))
        except ValueError as e:
            messagebox.showerror("Erro", str(e))
            return

        maximizar = self.tipo.get() == "max"
        res = simplex(c, restr, maximizar)
        self.res = res
        self.fechar_passos()
        self.btn_passos.config(state="normal")

        # quadros
        self.txt.delete("1.0", "end")
        self.txt.insert("end", "\n\n".join(res["quadros"]) + "\n\n")
        if res["status"] == "ilimitado":
            self.txt.insert("end", ">>> Problema ILIMITADO (sem solução ótima finita).\n")
            self.lbl_res.config(text="Problema ilimitado.")
        elif res["status"] == "inviavel":
            self.txt.insert("end", ">>> Problema INVIÁVEL (restrições incompatíveis).\n")
            self.lbl_res.config(text="Problema inviável.")
        else:
            self.txt.insert(
                "end",
                f">>> SOLUÇÃO ÓTIMA:  X1 = {res['x1']:.4f}   X2 = {res['x2']:.4f}   Z = {res['z']:.4f}\n",
            )
            if not maximizar:
                self.txt.insert("end", "(Minimização resolvida como max de −Z; o Z acima já está no sinal original.)\n")
            self.lbl_res.config(text=f"X1 = {res['x1']:.4f}\nX2 = {res['x2']:.4f}\nZ  = {res['z']:.4f}")

        # gráfico
        desenha(self.ax, c, restr, maximizar, res)
        self.canvas.draw()
