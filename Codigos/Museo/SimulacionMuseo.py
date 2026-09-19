"""
================================================================================
 SIMULACIÓN - MUSEO DE CIENCIAS
================================================================================
Animación + gráficas en vivo + panel de resultados | Tema 3 completo
================================================================================
"""

import math
import random
import tkinter as tk
from tkinter import ttk, scrolledtext
from collections import deque

random.seed(42)

def uniforme():
    return random.random()

def exponencial(lam):
    return -math.log(1 - uniforme()) / lam

def tipo_visitante():
    u = uniforme()
    if u < 0.45: return "Escolar"
    if u < 0.80: return "Individual"
    return "Turista"

def erlang_convolucion(k, mu):
    return sum(exponencial(mu) for _ in range(k))

def composicion_tiempo(tipo):
    if tipo == "Escolar":   return erlang_convolucion(3, 0.75)
    if tipo == "Turista":   return erlang_convolucion(4, 0.55)
    return exponencial(0.55)

def normal_box_muller(mu, sigma):
    u1, u2 = uniforme(), uniforme()
    z = math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * u2)
    return mu + sigma * z

def prueba_chi2(datos, lam, k=6):
    if len(datos) < 10: return "Pocos datos"
    mx = max(datos); ancho = mx / k
    obs = [0]*k
    for d in datos:
        obs[min(int(d/ancho), k-1)] += 1
    chi2 = 0.0
    for i in range(k):
        a, b = i*ancho, (i+1)*ancho
        p = math.exp(-lam*a) - math.exp(-lam*b)
        esp = max(p*len(datos), 1e-6)
        chi2 += (obs[i]-esp)**2 / esp
    return f"χ² ≈ {chi2:.3f}"

class Visitante:
    def __init__(self, cid, tipo, t_vis):
        self.id = cid
        self.tipo = tipo
        self.t_vis = t_vis
        self.x = 20
        self.y = 340
        self.estado = "entrando"
        self.restante = t_vis
        self.sala = 0
        self.color = {"Escolar":"#e74c3c","Individual":"#3498db","Turista":"#f39c12"}[tipo]

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulación  Museo de Ciencias ")
        self.root.geometry("1280x780")
        self.root.configure(bg="#1e272e")

        self.canvas = tk.Canvas(root, width=760, height=420, bg="#dfe6e9", highlightthickness=0)
        self.canvas.place(x=10, y=10)
        self.canvas_g = tk.Canvas(root, width=760, height=220, bg="#f5f6fa",
                                  highlightthickness=1, highlightbackground="#636e72")
        self.canvas_g.place(x=10, y=440)

        fr = ttk.LabelFrame(root, text=" PANEL DE RESULTADOS  ")
        fr.place(x=780, y=10, width=480, height=650)
        self.txt = scrolledtext.ScrolledText(fr, font=("Consolas", 9), wrap=tk.WORD,
                                             bg="#2d3436", fg="#dfe6e9")
        self.txt.pack(fill="both", expand=True, padx=4, pady=4)

        ctrl = ttk.Frame(root)
        ctrl.place(x=780, y=670, width=480, height=90)
        ttk.Label(ctrl, text="N:").grid(row=0, column=0)
        self.var_n = tk.IntVar(value=35)
        ttk.Entry(ctrl, textvariable=self.var_n, width=6).grid(row=0, column=1, padx=4)
        ttk.Label(ctrl, text="λ:").grid(row=0, column=2, padx=(8,0))
        self.var_lam = tk.DoubleVar(value=1.4)
        ttk.Entry(ctrl, textvariable=self.var_lam, width=6).grid(row=0, column=3, padx=4)
        self.btn = ttk.Button(ctrl, text="▶ INICIAR", command=self.iniciar)
        self.btn.grid(row=0, column=4, padx=10)
        self.lbl = ttk.Label(ctrl, text="Listo")
        self.lbl.grid(row=1, column=0, columnspan=5, sticky="w", pady=4)

        self.vis = []
        self.inter = []
        self.tiempos = []
        self.hist_i = deque(maxlen=80)
        self.hist_t = deque(maxlen=80)
        self.reloj = 0.0
        self.prox = 0.0
        self.gen = 0
        self.total = 35
        self.anim = False
        self.hecho = False
        self.dibujar_fondo()
        self.dibujar_g()

    def log(self, m):
        self.txt.insert(tk.END, m+"\n"); self.txt.see(tk.END)

    def dibujar_fondo(self):
        c = self.canvas
        c.delete("all")
        # 4 salas completas dentro del canvas (760 px)
        # ancho sala=165, espacio=12, margen izq=25
        salas = [
            ("Sala 1\nDinos",   25,  35),
            ("Sala 2\nEspacio", 202, 35),
            ("Sala 3\nRobots",  379, 35),
            ("Sala 4\nEnergía", 556, 35),
        ]
        for nom, x, y in salas:
            c.create_rectangle(x, y, x + 165, y + 125, fill="#ecf0f1", outline="#636e72", width=2)
            c.create_text(x + 82, y + 62, text=nom, font=("Arial", 10, "bold"), fill="#2c3e50")
        # Pasillo
        c.create_rectangle(25, 250, 735, 400, fill="#b2bec3", outline="#636e72")
        # Entrada / salida
        c.create_rectangle(5, 280, 25, 380, fill="#00b894", outline="")
        c.create_text(15, 330, text="IN", angle=90, fill="white", font=("Arial", 8, "bold"))
        c.create_rectangle(735, 280, 755, 380, fill="#e17055", outline="")
        c.create_text(745, 330, text="OUT", angle=90, fill="white", font=("Arial", 8, "bold"))

    def dibujar_g(self):
        g = self.canvas_g
        g.delete("all")
        g.create_text(180,12, text="Inter-llegadas (Exp)", font=("Arial",9,"bold"))
        g.create_text(540,12, text="Tiempos de visita", font=("Arial",9,"bold"))
        g.create_line(30,200,340,200); g.create_line(30,30,30,200)
        g.create_line(390,200,700,200); g.create_line(390,30,390,200)
        def bars(datos, x0, col):
            if len(datos)<3: return
            mx = max(datos) or 1
            nb=8; bins=[0]*nb
            for d in datos: bins[min(int(d/mx*nb),nb-1)] += 1
            hm = max(bins) or 1
            bw=300/nb
            for i,c in enumerate(bins):
                h=(c/hm)*150
                g.create_rectangle(x0+i*bw, 200-h, x0+(i+1)*bw-2, 200, fill=col, outline="")
        bars(list(self.hist_i), 30, "#0984e3")
        bars(list(self.hist_t), 390, "#e17055")

    def iniciar(self):
        if self.anim: return
        self.anim = True
        self.btn.config(state="disabled")
        self.vis.clear(); self.inter.clear(); self.tiempos.clear()
        self.hist_i.clear(); self.hist_t.clear()
        self.reloj=0; self.gen=0; self.total=self.var_n.get(); self.hecho=False
        self.txt.delete(1.0, tk.END)
        interes = normal_box_muller(1.0, 0.18)
        self.log("="*48)
        self.log("  MUSEO DE CIENCIAS – TEMA 3 COMPLETO")
        self.log("="*48)
        self.log(f"[3.5 Box-Muller] Factor de interés = {interes:.3f}\n")
        self.prox = exponencial(self.var_lam.get())
        self.paso()

    def paso(self):
        if not self.anim: return
        self.reloj += 0.05
        lam = self.var_lam.get()
        if self.reloj >= self.prox and self.gen < self.total:
            tipo = tipo_visitante()
            t = composicion_tiempo(tipo)
            self.gen += 1
            v = Visitante(self.gen, tipo, t)
            self.vis.append(v)
            inter = exponencial(lam)
            self.inter.append(inter); self.tiempos.append(t)
            self.hist_i.append(inter); self.hist_t.append(t)
            self.prox = self.reloj + inter
            self.log(f"#{self.gen:02d} {tipo:10s} t={self.reloj:5.1f}  visita={t:.2f}")

        for v in self.vis:
            if v.estado == "entrando":
                v.x += 3
                if v.x >= 90: v.estado = "recorriendo"
            elif v.estado == "recorriendo":
                v.restante -= 0.05
                tx = 107 + v.sala*177  # centros de las 4 salas
                if v.x < tx: v.x += 2.2
                elif v.restante <= 0: v.estado = "saliendo"
                elif v.sala < 3 and uniforme() < 0.015: v.sala += 1
            elif v.estado == "saliendo":
                v.x += 4

        self.dibujar_fondo()
        for v in self.vis:
            if v.x < 760:
                r=13
                self.canvas.create_oval(v.x-r,v.y-r,v.x+r,v.y+r, fill=v.color, outline="#2d3436")
                self.canvas.create_text(v.x,v.y, text=str(v.id), fill="white", font=("Arial",7,"bold"))
        self.dibujar_g()
        act = len([v for v in self.vis if v.x < 760])
        self.lbl.config(text=f"t={self.reloj:.1f} | {self.gen}/{self.total} | En museo: {act}")

        if self.gen >= self.total and act == 0:
            self.anim = False
            self.btn.config(state="normal")
            if not self.hecho:
                self.hecho = True
                self.log("\n"+"="*48)
                self.log("[3.6] "+prueba_chi2(self.inter, lam))
                self.log(f"Media inter = {sum(self.inter)/len(self.inter):.3f} (teór {1/lam:.3f})")
                self.log("Simulación terminada. ")
            return
        self.root.after(35, self.paso)

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
