"""
================================================================================
 SIMULACIÓN - CAFETERÍA
================================================================================
Entorno gráfico con:
  - Animación en tiempo real (clientes llegando, fila, atención)
  - Gráficas en vivo (histogramas de tiempos)
  - Panel de resultados con todos los subtemas del Tema 3

Tema 3 completo:
  3.1 Conceptos básicos
  3.2 VA discretas          → tipo de cliente (Regular / VIP)
  3.3 VA continuas
  3.4.1 Transformada inversa → tiempo entre llegadas (Exponencial)
  3.4.2 Convolución         → pedido complejo = 2 fases (Erlang)
  3.4.3 Composición         → tiempo de atención según tipo
  3.5 Box-Muller            → factor de ánimo del barista (Normal)
  3.6 Pruebas estadísticas  → Chi-cuadrada + resumen
================================================================================
"""

import math
import random
import tkinter as tk
from tkinter import ttk, scrolledtext
from collections import deque

random.seed(42)

# --------------------------------------------------------------------------
# GENERADORES (Tema 3)
# --------------------------------------------------------------------------
def uniforme():
    return random.random()

def exponencial(lam):
    """3.4.1 Transformada inversa → Exponencial
       x = - (1/λ) * ln(1 - R)"""
    return -math.log(1 - uniforme()) / lam


def tipo_cliente():
    """3.2 Variable discreta multinomial (Regular 0.75 / VIP 0.25)"""
    return "VIP" if uniforme() < 0.25 else "Regular"

def erlang_convolucion(k, mu):
    """3.4.2 Convolución → Erlang (suma de k Exponenciales)"""
    return sum(exponencial(mu) for _ in range(k))

def composicion_tiempo_atencion(tipo):
    """3.4.3 Composición: mezcla según tipo de cliente"""
    if tipo == "VIP":
        return exponencial(0.7)                 # más rápido
    # Regular: 30% pedido complejo (Erlang), 70% simple
    if uniforme() < 0.30:
        return erlang_convolucion(2, 0.45)      # 3.4.2 anidado
    return exponencial(0.40)

def normal_box_muller(mu, sigma):
    """3.5 Box-Muller → Normal"""
    u1, u2 = uniforme(), uniforme()
    z = math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * u2)
    return mu + sigma * z

def prueba_chi2(datos, lam, k=6):
    if len(datos) < 12:
        return "Pocos datos para Chi²"
    mx = max(datos)
    ancho = mx / k
    obs = [0] * k
    for d in datos:
        idx = min(int(d / ancho), k - 1)
        obs[idx] += 1
    chi2 = 0.0
    for i in range(k):
        a, b = i * ancho, (i + 1) * ancho
        p = math.exp(-lam * a) - math.exp(-lam * b)
        esp = max(p * len(datos), 1e-6)
        chi2 += (obs[i] - esp) ** 2 / esp
    return f"χ² ≈ {chi2:.3f}  (λ={lam})"

# --------------------------------------------------------------------------
class Cliente:
    def __init__(self, cid, tipo, t_atencion):
        self.id = cid
        self.tipo = tipo
        self.t_atencion = t_atencion
        self.x = 25
        self.y = 310
        self.estado = "llegando"   # llegando | fila | atendido | saliendo
        self.restante = t_atencion
        self.color = "#e67e22" if tipo == "VIP" else "#3498db"

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulación  – Cafetería ")
        self.root.geometry("1280x780")
        self.root.configure(bg="#1e272e")

        # ---- CANVAS animación ----
        self.canvas = tk.Canvas(root, width=720, height=420, bg="#dfe6e9", highlightthickness=0)
        self.canvas.place(x=10, y=10)

        # ---- Gráficas (canvas secundario) ----
        self.canvas_g = tk.Canvas(root, width=720, height=220, bg="#f5f6fa", highlightthickness=1,
                                  highlightbackground="#636e72")
        self.canvas_g.place(x=10, y=440)

        # ---- Panel de resultados ----
        fr = ttk.LabelFrame(root, text=" PANEL DE RESULTADOS  ")
        fr.place(x=740, y=10, width=520, height=650)
        self.txt = scrolledtext.ScrolledText(fr, font=("Consolas", 9), wrap=tk.WORD,
                                             bg="#2d3436", fg="#dfe6e9", insertbackground="white")
        self.txt.pack(fill="both", expand=True, padx=4, pady=4)

        # ---- Controles ----
        ctrl = ttk.Frame(root)
        ctrl.place(x=740, y=670, width=520, height=90)

        ttk.Label(ctrl, text="N clientes:").grid(row=0, column=0, sticky="w")
        self.var_n = tk.IntVar(value=40)
        ttk.Entry(ctrl, textvariable=self.var_n, width=6).grid(row=0, column=1, padx=4)

        ttk.Label(ctrl, text="λ llegadas:").grid(row=0, column=2, sticky="w", padx=(10,0))
        self.var_lam = tk.DoubleVar(value=1.6)
        ttk.Entry(ctrl, textvariable=self.var_lam, width=6).grid(row=0, column=3, padx=4)

        self.btn = ttk.Button(ctrl, text="▶ INICIAR SIMULACIÓN", command=self.iniciar)
        self.btn.grid(row=0, column=4, padx=12)

        self.lbl = ttk.Label(ctrl, text="Listo", font=("Arial", 9))
        self.lbl.grid(row=1, column=0, columnspan=5, sticky="w", pady=6)

        # Estado
        self.clientes = []
        self.inter_llegadas = []
        self.tiempos_atencion = []
        self.reloj = 0.0
        self.prox_llegada = 0.0
        self.gen = 0
        self.total = 40
        self.en_atencion = None
        self.animando = False
        self.hecho = False
        self.hist_inter = deque(maxlen=80)
        self.hist_at = deque(maxlen=80)

        self.dibujar_fondo()
        self.dibujar_graficas()

    def log(self, m):
        self.txt.insert(tk.END, m + "\n")
        self.txt.see(tk.END)

    def dibujar_fondo(self):
        c = self.canvas
        c.delete("all")
        # Mostrador
        c.create_rectangle(520, 60, 700, 180, fill="#6c5ce7", outline="#2d3436", width=2)
        c.create_text(610, 120, text="MOSTRADOR\nBarista", fill="white", font=("Arial", 12, "bold"))
        # Fila
        c.create_rectangle(60, 220, 480, 380, fill="#b2bec3", outline="#636e72", width=2)
        c.create_text(270, 205, text="FILA DE CLIENTES", font=("Arial", 10, "bold"))
        # Entrada
        c.create_rectangle(5, 250, 50, 350, fill="#00b894", outline="#00695c")
        c.create_text(27, 300, text="IN", angle=90, font=("Arial", 9, "bold"), fill="white")

    def dibujar_graficas(self):
        g = self.canvas_g
        g.delete("all")
        g.create_text(180, 15, text="Histograma: tiempos entre llegadas (Exp)", font=("Arial", 9, "bold"))
        g.create_text(540, 15, text="Histograma: tiempos de atención", font=("Arial", 9, "bold"))
        # Ejes
        g.create_line(30, 200, 340, 200, fill="#2d3436")
        g.create_line(30, 30, 30, 200, fill="#2d3436")
        g.create_line(390, 200, 700, 200, fill="#2d3436")
        g.create_line(390, 30, 390, 200, fill="#2d3436")

        def barras(datos, x0, color):
            if len(datos) < 3:
                return
            mx = max(datos) if max(datos) > 0 else 1
            n_bins = 8
            bins = [0] * n_bins
            for d in datos:
                idx = min(int(d / mx * n_bins), n_bins - 1)
                bins[idx] += 1
            hmax = max(bins) if max(bins) > 0 else 1
            bw = 300 / n_bins
            for i, cnt in enumerate(bins):
                h = (cnt / hmax) * 150
                g.create_rectangle(x0 + i * bw, 200 - h, x0 + (i + 1) * bw - 2, 200,
                                   fill=color, outline="")

        barras(list(self.hist_inter), 30, "#0984e3")
        barras(list(self.hist_at), 390, "#e17055")

    def iniciar(self):
        if self.animando:
            return
        self.animando = True
        self.btn.config(state="disabled")
        self.clientes.clear()
        self.inter_llegadas.clear()
        self.tiempos_atencion.clear()
        self.hist_inter.clear()
        self.hist_at.clear()
        self.reloj = 0.0
        self.gen = 0
        self.total = self.var_n.get()
        self.en_atencion = None
        self.hecho = False
        self.txt.delete(1.0, tk.END)

        # 3.5
        animo = normal_box_muller(1.0, 0.12)
        self.log("=" * 48)
        self.log("  CAFETERÍA 'EL RINCÓN' – TEMA 3 COMPLETO")
        self.log("=" * 48)
        self.log(f"[3.5 Box-Muller] Factor de ánimo del barista = {animo:.3f}")
        self.log("Flujo: Ri(0,1) → Generador VA (fórmulas) → Simulación\n")

        self.prox_llegada = exponencial(self.var_lam.get())
        self.paso()

    def paso(self):
        if not self.animando:
            return
        self.reloj += 0.05
        lam = self.var_lam.get()

        # Llegada
        if self.reloj >= self.prox_llegada and self.gen < self.total:
            tipo = tipo_cliente()                              # 3.2
            t_at = composicion_tiempo_atencion(tipo)           # 3.4.3 (+3.4.2)
            self.gen += 1
            cli = Cliente(self.gen, tipo, t_at)
            self.clientes.append(cli)
            inter = exponencial(lam)                           # 3.4.1
            self.inter_llegadas.append(inter)
            self.tiempos_atencion.append(t_at)
            self.hist_inter.append(inter)
            self.hist_at.append(t_at)
            self.prox_llegada = self.reloj + inter
            self.log(f"#{self.gen:02d} {tipo:8s}  t={self.reloj:5.1f}  "
                     f"inter={inter:.2f}  atención={t_at:.2f}")

        # Movimiento
        for cli in self.clientes:
            if cli.estado == "llegando":
                cli.x += 5
                if cli.x >= 80:
                    cli.estado = "fila"
            elif cli.estado == "fila":
                fila = [c for c in self.clientes if c.estado == "fila"]
                if cli in fila:
                    idx = fila.index(cli)
                    cli.x = 90 + idx * 42
                    cli.y = 300
            elif cli.estado == "atendido":
                cli.restante -= 0.05
                if cli.restante <= 0:
                    cli.estado = "saliendo"
            elif cli.estado == "saliendo":
                cli.x += 7
                cli.y -= 3

        if self.en_atencion is None:
            en_fila = [c for c in self.clientes if c.estado == "fila"]
            if en_fila:
                self.en_atencion = en_fila[0]
                self.en_atencion.estado = "atendido"
                self.en_atencion.x = 610
                self.en_atencion.y = 200
        if self.en_atencion and self.en_atencion.estado == "saliendo":
            self.en_atencion = None

        # Dibujar animación
        self.dibujar_fondo()
        for cli in self.clientes:
            if cli.x < 720:
                r = 16
                self.canvas.create_oval(cli.x-r, cli.y-r, cli.x+r, cli.y+r,
                                        fill=cli.color, outline="#2d3436", width=2)
                self.canvas.create_text(cli.x, cli.y, text=str(cli.id),
                                        fill="white", font=("Arial", 8, "bold"))

        # Gráficas en vivo
        self.dibujar_graficas()

        activos = len([c for c in self.clientes if c.x < 720])
        self.lbl.config(text=f"t={self.reloj:.1f} min | Generados {self.gen}/{self.total} | En sistema: {activos}")

        # Fin
        if self.gen >= self.total and self.en_atencion is None and \
           all(c.estado == "saliendo" and c.x > 720 for c in self.clientes):
            self.animando = False
            self.btn.config(state="normal")
            if not self.hecho:
                self.hecho = True
                self.log("\n" + "=" * 48)
                self.log("[3.6] PRUEBA CHI-CUADRADA (tiempos entre llegadas)")
                self.log(prueba_chi2(self.inter_llegadas, lam))
                self.log(f"\nMedia inter-llegadas  = {sum(self.inter_llegadas)/len(self.inter_llegadas):.3f}  (teórica {1/lam:.3f})")
                self.log(f"Media tiempos atención = {sum(self.tiempos_atencion)/len(self.tiempos_atencion):.3f}")
                vip = sum(1 for c in self.clientes if c.tipo == "VIP")
                self.log(f"VIP observados = {vip}/{self.total} = {vip/self.total:.1%}  (teórico 25%)")
                self.log("\n>>> Todos los subtemas del Tema 3 ejecutados.")
                self.log("=" * 48)
            return
        self.root.after(35, self.paso)

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
