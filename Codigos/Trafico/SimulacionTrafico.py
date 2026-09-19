"""
================================================================================
 SIMULACIÓN 3 - TRÁFICO EN INTERSECCIÓN
================================================================================
Animación + gráficas en vivo + panel de resultados | Tema 3 completo
Basada en tu versión de tráfico, mejorada.
================================================================================
"""

import math
import random
import tkinter as tk
from tkinter import ttk, scrolledtext
from collections import deque

random.seed(99)

def uniforme():
    return random.random()

def exponencial(lam):
    """3.4.1  x = -(1/λ) ln(1-R)"""
    return -math.log(1 - uniforme()) / lam

def tipo_vehiculo():
    """3.2 Multinomial"""
    u = uniforme()
    if u < 0.70: return "auto"
    if u < 0.90: return "camion"
    return "moto"

def erlang_convolucion(k, mu):
    """3.4.2"""
    return sum(exponencial(mu) for _ in range(k))

def composicion_cruce(tipo):
    """3.4.3"""
    if tipo == "camion": return erlang_convolucion(2, 3.0)
    if tipo == "moto":   return exponencial(10.0)
    return exponencial(8.0)

def normal_box_muller(mu, sigma):
    """3.5"""
    u1, u2 = uniforme(), uniforme()
    z = math.sqrt(-2*math.log(u1)) * math.cos(2*math.pi*u2)
    return mu + sigma * z

def prueba_chi2(datos, lam, k=6):
    if len(datos) < 10: return "Pocos datos"
    mx = max(datos); ancho = mx/k
    obs = [0]*k
    for d in datos: obs[min(int(d/ancho),k-1)] += 1
    chi2 = 0.0
    for i in range(k):
        a,b = i*ancho,(i+1)*ancho
        p = math.exp(-lam*a)-math.exp(-lam*b)
        esp = max(p*len(datos),1e-6)
        chi2 += (obs[i]-esp)**2/esp
    return f"χ² ≈ {chi2:.3f}"

class Vehiculo:
    def __init__(self, cid, tipo, t_cruce):
        self.id = cid
        self.tipo = tipo
        self.t_cruce = t_cruce
        self.x = 0
        self.y = 210 + (cid % 5)*18
        self.vel = 2.0 if tipo=="camion" else 3.5 if tipo=="auto" else 4.5
        self.color = {"auto":"#2c3e50","camion":"#a04000","moto":"#2980b9"}[tipo]
        self.ancho = 38 if tipo=="camion" else 24 if tipo=="auto" else 14

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulación Tráfico en Intersección ")
        self.root.geometry("1280x780")
        self.root.configure(bg="#1a252f")

        self.canvas = tk.Canvas(root, width=720, height=420, bg="#2c3e50", highlightthickness=0)
        self.canvas.place(x=10, y=10)
        self.canvas_g = tk.Canvas(root, width=720, height=220, bg="#f5f6fa",
                                  highlightthickness=1, highlightbackground="#636e72")
        self.canvas_g.place(x=10, y=440)

        fr = ttk.LabelFrame(root, text=" PANEL DE RESULTADOS  ")
        fr.place(x=740, y=10, width=520, height=650)
        self.txt = scrolledtext.ScrolledText(fr, font=("Consolas",9), wrap=tk.WORD,
                                             bg="#1c2833", fg="#ecf0f1")
        self.txt.pack(fill="both", expand=True, padx=4, pady=4)

        ctrl = ttk.Frame(root)
        ctrl.place(x=740, y=670, width=520, height=90)
        ttk.Label(ctrl, text="N:").grid(row=0, column=0)
        self.var_n = tk.IntVar(value=40)
        ttk.Entry(ctrl, textvariable=self.var_n, width=6).grid(row=0, column=1, padx=4)
        ttk.Label(ctrl, text="λ:").grid(row=0, column=2, padx=(8,0))
        self.var_lam = tk.DoubleVar(value=5.5)
        ttk.Entry(ctrl, textvariable=self.var_lam, width=6).grid(row=0, column=3, padx=4)
        self.btn = ttk.Button(ctrl, text="▶ INICIAR", command=self.iniciar)
        self.btn.grid(row=0, column=4, padx=10)
        self.lbl = ttk.Label(ctrl, text="Listo")
        self.lbl.grid(row=1, column=0, columnspan=5, sticky="w", pady=4)

        self.vehs = []
        self.inter = []
        self.conteo = {"auto":0,"camion":0,"moto":0}
        self.hist_i = deque(maxlen=80)
        self.hist_c = deque(maxlen=80)
        self.reloj = 0.0
        self.prox = 0.0
        self.gen = 0
        self.total = 40
        self.anim = False
        self.hecho = False
        self.verde = True
        self.t_sem = 0.0
        self.dibujar_fondo()
        self.dibujar_g()

    def log(self, m):
        self.txt.insert(tk.END, m+"\n"); self.txt.see(tk.END)

    def dibujar_fondo(self):
        c = self.canvas
        c.delete("all")
        c.create_rectangle(0,160,720,300, fill="#5d6d7e", outline="")
        for x in range(0,720,40):
            c.create_line(x,230,x+18,230, fill="white", width=2, dash=(6,6))
        c.create_line(360,160,360,300, fill="#e74c3c", width=3)
        col = "#2ecc71" if self.verde else "#e74c3c"
        c.create_rectangle(340,80,380,145, fill="#1a252f")
        c.create_oval(348,88,372,112, fill=col if self.verde else "#7f8c8d")
        c.create_oval(348,118,372,142, fill="#7f8c8d" if self.verde else col)
        c.create_text(360,40, text="INTERSECCIÓN CON SEMÁFORO", fill="white",
                      font=("Arial",11,"bold"))
        c.create_text(100,380, text="auto=gris  camión=café(Erlang)  moto=azul",
                      fill="#bdc3c7", font=("Arial",8))

    def dibujar_g(self):
        g = self.canvas_g
        g.delete("all")
        g.create_text(180,12, text="Inter-llegadas (Exp)", font=("Arial",9,"bold"))
        g.create_text(540,12, text="Tiempos de cruce", font=("Arial",9,"bold"))
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
                g.create_rectangle(x0+i*bw,200-h, x0+(i+1)*bw-2,200, fill=col, outline="")
        bars(list(self.hist_i), 30, "#0984e3")
        bars(list(self.hist_c), 390, "#e17055")

    def iniciar(self):
        if self.anim: return
        self.anim = True
        self.btn.config(state="disabled")
        self.vehs.clear(); self.inter.clear()
        self.conteo = {"auto":0,"camion":0,"moto":0}
        self.hist_i.clear(); self.hist_c.clear()
        self.reloj=0; self.gen=0; self.total=self.var_n.get()
        self.hecho=False; self.verde=True; self.t_sem=0
        self.txt.delete(1.0, tk.END)
        reac = normal_box_muller(1.5, 0.4)
        self.log("="*48)
        self.log("  TRÁFICO EN INTERSECCIÓN ")
        self.log("="*48)
        self.log(f"[3.5 Box-Muller] Tiempo de reacción = {reac:.2f} s")
        self.log("Flujo: Ri(0,1) → Generador VA → Simulación\n")
        self.prox = exponencial(self.var_lam.get())
        self.paso()

    def paso(self):
        if not self.anim: return
        self.reloj += 0.04
        self.t_sem += 0.04
        if self.t_sem > 7.5:
            self.verde = not self.verde
            self.t_sem = 0.0
        lam = self.var_lam.get()

        if self.reloj >= self.prox and self.gen < self.total:
            tipo = tipo_vehiculo()
            tc = composicion_cruce(tipo)
            self.gen += 1
            self.conteo[tipo] += 1
            v = Vehiculo(self.gen, tipo, tc)
            self.vehs.append(v)
            inter = exponencial(lam)
            self.inter.append(inter)
            self.hist_i.append(inter)
            self.hist_c.append(tc)
            self.prox = self.reloj + inter
            self.log(f"#{self.gen:02d} {tipo:7s} t={self.reloj:5.2f}  cruce={tc:.2f}s")

        for v in self.vehs:
            if self.verde or v.x > 370:
                v.x += v.vel
            elif v.x < 340:
                v.x += v.vel * 0.25

        self.dibujar_fondo()
        for v in self.vehs:
            if v.x < 730:
                self.canvas.create_rectangle(v.x, v.y, v.x+v.ancho, v.y+14,
                                             fill=v.color, outline="white")
                self.canvas.create_text(v.x+v.ancho/2, v.y+7, text=str(v.id),
                                        fill="white", font=("Arial",7,"bold"))
        self.dibujar_g()
        act = len([v for v in self.vehs if v.x < 730])
        self.lbl.config(text=f"t={self.reloj:.2f} | {self.gen}/{self.total} | En vía: {act} | "
                             f"Semáforo: {'VERDE' if self.verde else 'ROJO'}")

        if self.gen >= self.total and act == 0:
            self.anim = False
            self.btn.config(state="normal")
            if not self.hecho:
                self.hecho = True
                self.log("\n"+"="*48)
                self.log("[3.6] "+prueba_chi2(self.inter, lam))
                self.log("\nProporciones observadas:")
                for t,c in self.conteo.items():
                    self.log(f"  {t}: {c}/{self.total} = {c/self.total:.1%}")
                self.log("(teóricos: auto 70%, camión 20%, moto 10%)")
                self.log("\n>>> Tema 3 completo ejecutado.")
            return
        self.root.after(30, self.paso)

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
