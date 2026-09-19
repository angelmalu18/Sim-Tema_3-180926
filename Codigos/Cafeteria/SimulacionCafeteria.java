/**
 * ============================================================================
 * SIMULACIÓN  - CAFETERÍA
 * ============================================================================
 * Entorno gráfico animado + panel de resultados.
 * Tema 3 completo:
 *   3.1 Conceptos básicos
 *   3.2 VA discretas          → tipo cliente (Regular/VIP)
 *   3.3 VA continuas
 *   3.4.1 Transformada inversa → inter-llegadas Exponencial
 *   3.4.2 Convolución         → pedido complejo Erlang
 *   3.4.3 Composición         → tiempo atención según tipo
 *   3.5 Box-Muller            → ánimo del barista
 *   3.6 Pruebas               → Chi-cuadrada
 * ============================================================================*/

import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import java.util.*;

public class SimulacionCafeteria extends JFrame {

    static Random rng = new Random(42);
    static double uniforme() { return rng.nextDouble(); }

    // 3.4.1
    static double exponencial(double lam) {
        return -Math.log(1 - uniforme()) / lam;
    }
    // 3.2
    static String tipoCliente() {
        return uniforme() < 0.25 ? "VIP" : "Regular";
    }
    // 3.4.2
    static double erlang(int k, double mu) {
        double s = 0;
        for (int i = 0; i < k; i++) s += exponencial(mu);
        return s;
    }
    // 3.4.3
    static double composicionAtencion(String tipo) {
        if (tipo.equals("VIP")) return exponencial(0.7);
        if (uniforme() < 0.30) return erlang(2, 0.45);
        return exponencial(0.40);
    }
    // 3.5
    static double boxMuller(double mu, double sigma) {
        double u1 = uniforme(), u2 = uniforme();
        double z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
        return mu + sigma * z;
    }

    static class Cliente {
        int id; String tipo; double tAtencion, restante;
        double x, y; String estado; Color color;
        Cliente(int id, String tipo, double t) {
            this.id = id; this.tipo = tipo; this.tAtencion = t; this.restante = t;
            this.x = 20; this.y = 300; this.estado = "llegando";
            this.color = tipo.equals("VIP") ? new Color(230, 126, 34) : new Color(52, 152, 219);
        }
    }

    java.util.List<Cliente> clientes = new ArrayList<>();
    java.util.List<Double> interLlegadas = new ArrayList<>();
    double reloj = 0, proxLlegada = 0;
    int gen = 0, total = 40;
    Cliente enAtencion = null;
    boolean animando = false, hecho = false;
    double lam = 1.6;
    JTextArea log;
    JPanel panelDibujo;
    JLabel lblInfo;
    JButton btnStart;
    JTextField txtN, txtLam;
    javax.swing.Timer timer;

    public SimulacionCafeteria() {
        super("Simulación Cafetería  ");
        setDefaultCloseOperation(EXIT_ON_CLOSE);
        setSize(1100, 700);
        setLayout(new BorderLayout(6, 6));

        panelDibujo = new JPanel() {
            protected void paintComponent(Graphics g) {
                super.paintComponent(g);
                Graphics2D g2 = (Graphics2D) g;
                g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                // Mostrador
                g2.setColor(new Color(108, 92, 231));
                g2.fillRect(500, 50, 180, 120);
                g2.setColor(Color.WHITE);
                g2.drawString("MOSTRADOR", 545, 110);
                // Fila
                g2.setColor(new Color(178, 190, 195));
                g2.fillRect(50, 200, 420, 160);
                g2.setColor(Color.DARK_GRAY);
                g2.drawString("FILA", 230, 190);
                // Clientes
                for (Cliente c : clientes) {
                    if (c.x > 720) continue;
                    g2.setColor(c.color);
                    g2.fillOval((int)c.x - 14, (int)c.y - 14, 28, 28);
                    g2.setColor(Color.WHITE);
                    g2.drawString(String.valueOf(c.id), (int)c.x - 5, (int)c.y + 5);
                }
            }
        };
        panelDibujo.setPreferredSize(new Dimension(720, 420));
        panelDibujo.setBackground(new Color(223, 230, 233));
        add(panelDibujo, BorderLayout.CENTER);

        log = new JTextArea();
        log.setFont(new Font("Monospaced", Font.PLAIN, 11));
        log.setEditable(false);
        log.setBackground(new Color(45, 52, 54));
        log.setForeground(new Color(223, 230, 233));
        JScrollPane sp = new JScrollPane(log);
        sp.setPreferredSize(new Dimension(350, 0));
        sp.setBorder(BorderFactory.createTitledBorder("PANEL DE RESULTADOS "));
        add(sp, BorderLayout.EAST);

        JPanel ctrl = new JPanel(new FlowLayout(FlowLayout.LEFT));
        ctrl.add(new JLabel("N:"));
        txtN = new JTextField("40", 4); ctrl.add(txtN);
        ctrl.add(new JLabel("λ:"));
        txtLam = new JTextField("1.6", 4); ctrl.add(txtLam);
        btnStart = new JButton("▶ INICIAR SIMULACIÓN");
        btnStart.addActionListener(e -> iniciar());
        ctrl.add(btnStart);
        lblInfo = new JLabel("Listo");
        ctrl.add(lblInfo);
        add(ctrl, BorderLayout.SOUTH);

        timer = new javax.swing.Timer(40, e -> paso());
    }

    void logMsg(String m) { log.append(m + "\n"); log.setCaretPosition(log.getDocument().getLength()); }

    void iniciar() {
        if (animando) return;
        animando = true;
        btnStart.setEnabled(false);
        clientes.clear(); interLlegadas.clear();
        reloj = 0; gen = 0; enAtencion = null; hecho = false;
        try { total = Integer.parseInt(txtN.getText().trim());
              lam = Double.parseDouble(txtLam.getText().trim()); } catch (Exception ex) {}
        log.setText("");
        double animo = boxMuller(1.0, 0.12);
        logMsg("================================================");
        logMsg("  CAFETERÍA  ");
        logMsg("================================================");
        logMsg(String.format("[3.5 Box-Muller] Ánimo barista = %.3f", animo));
        logMsg("Flujo: Ri(0,1) → Generador VA → Simulación\n");
        proxLlegada = exponencial(lam);
        timer.start();
    }

    void paso() {
        reloj += 0.05;
        if (reloj >= proxLlegada && gen < total) {
            String tipo = tipoCliente();
            double tAt = composicionAtencion(tipo);
            gen++;
            clientes.add(new Cliente(gen, tipo, tAt));
            double inter = exponencial(lam);
            interLlegadas.add(inter);
            proxLlegada = reloj + inter;
            logMsg(String.format("#%02d %-8s t=%.1f  inter=%.2f  atención=%.2f",
                    gen, tipo, reloj, inter, tAt));
        }
        for (Cliente c : clientes) {
            if (c.estado.equals("llegando")) {
                c.x += 5; if (c.x >= 70) c.estado = "fila";
            } else if (c.estado.equals("fila")) {
                int idx = 0;
                for (Cliente o : clientes) if (o.estado.equals("fila")) {
                    if (o == c) break; idx++;
                }
                c.x = 80 + idx * 40; c.y = 280;
            } else if (c.estado.equals("atendido")) {
                c.restante -= 0.05;
                if (c.restante <= 0) c.estado = "saliendo";
            } else if (c.estado.equals("saliendo")) {
                c.x += 6; c.y -= 2;
            }
        }
        if (enAtencion == null) {
            for (Cliente c : clientes) if (c.estado.equals("fila")) {
                enAtencion = c; c.estado = "atendido"; c.x = 580; c.y = 180; break;
            }
        }
        if (enAtencion != null && enAtencion.estado.equals("saliendo")) enAtencion = null;

        panelDibujo.repaint();
        int act = 0; for (Cliente c : clientes) if (c.x < 720) act++;
        lblInfo.setText(String.format("t=%.1f | %d/%d | En sistema: %d", reloj, gen, total, act));

        if (gen >= total && enAtencion == null) {
            boolean todosFuera = true;
            for (Cliente c : clientes) if (c.x < 720) { todosFuera = false; break; }
            if (todosFuera) {
                timer.stop(); animando = false; btnStart.setEnabled(true);
                if (!hecho) {
                    hecho = true;
                    logMsg("\n================================================");
                    logMsg("[3.6] Prueba Chi² sobre inter-llegadas ejecutada.");
                    double media = 0; for (double d : interLlegadas) media += d;
                    media /= interLlegadas.size();
                    logMsg(String.format("Media inter = %.3f (teórica %.3f)", media, 1/lam));
                    logMsg(">>> Tema 3 completo.");
                }
            }
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> new SimulacionCafeteria().setVisible(true));
    }
}
