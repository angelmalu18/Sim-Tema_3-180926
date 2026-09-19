/**
 * ============================================================================
 * SIMULACIÓN 2 - MUSEO DE CIENCIAS (Java - Swing)
 * Tema 3 completo + animación + panel de resultados
 * ============================================================================
 */
import javax.swing.*;
import java.awt.*;
import java.util.*;

public class SimulacionMuseo extends JFrame {

    static Random rng = new Random(42);
    static double uniforme() { return rng.nextDouble(); }
    static double exponencial(double lam) { return -Math.log(1 - uniforme()) / lam; }
    static String tipoVisitante() {
        double u = uniforme();
        if (u < 0.45) return "Escolar";
        if (u < 0.80) return "Individual";
        return "Turista";
    }
    static double erlang(int k, double mu) {
        double s = 0; for (int i = 0; i < k; i++) s += exponencial(mu); return s;
    }
    static double composicion(String tipo) {
        if (tipo.equals("Escolar")) return erlang(3, 0.75);
        if (tipo.equals("Turista")) return erlang(4, 0.55);
        return exponencial(0.55);
    }
    static double boxMuller(double mu, double sigma) {
        double z = Math.sqrt(-2*Math.log(uniforme())) * Math.cos(2*Math.PI*uniforme());
        return mu + sigma * z;
    }

    static class Visitante {
        int id; String tipo; double restante; double x, y; String estado; int sala; Color color;
        Visitante(int id, String tipo, double t) {
            this.id = id; this.tipo = tipo; this.restante = t;
            this.x = 15; this.y = 320; this.estado = "entrando"; this.sala = 0;
            if (tipo.equals("Escolar")) color = new Color(231, 76, 60);
            else if (tipo.equals("Turista")) color = new Color(243, 156, 18);
            else color = new Color(52, 152, 219);
        }
    }

    java.util.List<Visitante> vis = new ArrayList<>();
    java.util.List<Double> inter = new ArrayList<>();
    double reloj = 0, prox = 0, lam = 1.4;
    int gen = 0, total = 35;
    boolean animando = false, hecho = false;
    JTextArea log; JPanel panel; JLabel lbl; JButton btn;
    JTextField txtN, txtLam;
    javax.swing.Timer timer;

    public SimulacionMuseo() {
        super("Simulación Museo de Ciencias ");
        setDefaultCloseOperation(EXIT_ON_CLOSE);
        setSize(1100, 700);
        setLayout(new BorderLayout(6, 6));

        panel = new JPanel() {
            protected void paintComponent(Graphics g) {
                super.paintComponent(g);
                Graphics2D g2 = (Graphics2D) g;
                g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                String[] salas = {"Sala 1\nDinos", "Sala 2\nEspacio", "Sala 3\nRobots", "Sala 4\nEnergía"};
                for (int i = 0; i < 4; i++) {
                    int x = 60 + i * 160;
                    g2.setColor(new Color(189, 195, 199));
                    g2.fillRect(x, 40, 140, 120);
                    g2.setColor(Color.DARK_GRAY);
                    g2.drawString(salas[i].split("\n")[0], x + 35, 90);
                    g2.drawString(salas[i].split("\n")[1], x + 40, 110);
                }
                g2.setColor(new Color(178, 190, 195));
                g2.fillRect(40, 250, 640, 140);
                for (Visitante v : vis) {
                    if (v.x > 700) continue;
                    g2.setColor(v.color);
                    g2.fillOval((int)v.x - 12, (int)v.y - 12, 24, 24);
                    g2.setColor(Color.WHITE);
                    g2.drawString(String.valueOf(v.id), (int)v.x - 4, (int)v.y + 4);
                }
            }
        };
        panel.setPreferredSize(new Dimension(720, 420));
        panel.setBackground(new Color(236, 240, 241));
        add(panel, BorderLayout.CENTER);

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
        ctrl.add(new JLabel("N:")); txtN = new JTextField("35", 4); ctrl.add(txtN);
        ctrl.add(new JLabel("λ:")); txtLam = new JTextField("1.4", 4); ctrl.add(txtLam);
        btn = new JButton("▶ INICIAR"); btn.addActionListener(e -> iniciar()); ctrl.add(btn);
        lbl = new JLabel("Listo"); ctrl.add(lbl);
        add(ctrl, BorderLayout.SOUTH);
        timer = new javax.swing.Timer(40, e -> paso());
    }

    void logMsg(String m) { log.append(m + "\n"); log.setCaretPosition(log.getDocument().getLength()); }

    void iniciar() {
        if (animando) return;
        animando = true; btn.setEnabled(false);
        vis.clear(); inter.clear(); reloj = 0; gen = 0; hecho = false;
        try { total = Integer.parseInt(txtN.getText().trim());
              lam = Double.parseDouble(txtLam.getText().trim()); } catch (Exception ex) {}
        log.setText("");
        logMsg("================================================");
        logMsg("  MUSEO DE CIENCIAS  ");
        logMsg("================================================");
        logMsg(String.format("[3.5 Box-Muller] Interés = %.3f\n", boxMuller(1.0, 0.18)));
        prox = exponencial(lam);
        timer.start();
    }

    void paso() {
        reloj += 0.05;
        if (reloj >= prox && gen < total) {
            String tipo = tipoVisitante();
            double t = composicion(tipo);
            gen++;
            vis.add(new Visitante(gen, tipo, t));
            double i = exponencial(lam);
            inter.add(i); prox = reloj + i;
            logMsg(String.format("#%02d %-10s t=%.1f  visita=%.2f", gen, tipo, reloj, t));
        }
        for (Visitante v : vis) {
            if (v.estado.equals("entrando")) {
                v.x += 3; if (v.x >= 80) v.estado = "recorriendo";
            } else if (v.estado.equals("recorriendo")) {
                v.restante -= 0.05;
                double tx = 130 + v.sala * 160;
                if (v.x < tx) v.x += 2.2;
                else if (v.restante <= 0) v.estado = "saliendo";
                else if (v.sala < 3 && uniforme() < 0.015) v.sala++;
            } else if (v.estado.equals("saliendo")) {
                v.x += 4;
            }
        }
        panel.repaint();
        int act = 0; for (Visitante v : vis) if (v.x < 700) act++;
        lbl.setText(String.format("t=%.1f | %d/%d | En museo: %d", reloj, gen, total, act));
        if (gen >= total && act == 0) {
            timer.stop(); animando = false; btn.setEnabled(true);
            if (!hecho) {
                hecho = true;
                logMsg("\n================================================");
                double m = 0; for (double d : inter) m += d; m /= inter.size();
                logMsg(String.format("[3.6] Media inter = %.3f (teórica %.3f)", m, 1/lam));
                logMsg(">>> Tema 3 completo.");
            }
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> new SimulacionMuseo().setVisible(true));
    }
}
