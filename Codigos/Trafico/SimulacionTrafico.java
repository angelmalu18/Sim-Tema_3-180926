/**
 * ============================================================================
 * SIMULACIÓN 3 - TRÁFICO EN INTERSECCIÓN (Java - Swing)
 * Tema 3 completo + animación + panel de resultados
 * ============================================================================
 */
import javax.swing.*;
import java.awt.*;
import java.util.*;

public class SimulacionTrafico extends JFrame {

    static Random rng = new Random(99);
    static double uniforme() { return rng.nextDouble(); }
    static double exponencial(double lam) { return -Math.log(1 - uniforme()) / lam; }
    static String tipoVehiculo() {
        double u = uniforme();
        if (u < 0.70) return "auto";
        if (u < 0.90) return "camion";
        return "moto";
    }
    static double erlang(int k, double mu) {
        double s = 0; for (int i = 0; i < k; i++) s += exponencial(mu); return s;
    }
    static double composicion(String tipo) {
        if (tipo.equals("camion")) return erlang(2, 3.0);
        if (tipo.equals("moto")) return exponencial(10.0);
        return exponencial(8.0);
    }
    static double boxMuller(double mu, double sigma) {
        double z = Math.sqrt(-2*Math.log(uniforme())) * Math.cos(2*Math.PI*uniforme());
        return mu + sigma * z;
    }

    static class Vehiculo {
        int id; String tipo; double x, y, vel; int ancho; Color color;
        Vehiculo(int id, String tipo) {
            this.id = id; this.tipo = tipo;
            this.x = 0; this.y = 200 + (id % 5) * 18;
            this.vel = tipo.equals("camion") ? 2.0 : tipo.equals("auto") ? 3.5 : 4.5;
            this.ancho = tipo.equals("camion") ? 38 : tipo.equals("auto") ? 24 : 14;
            if (tipo.equals("camion")) color = new Color(160, 64, 0);
            else if (tipo.equals("moto")) color = new Color(41, 128, 185);
            else color = new Color(44, 62, 80);
        }
    }

    java.util.List<Vehiculo> vehs = new ArrayList<>();
    java.util.List<Double> inter = new ArrayList<>();
    Map<String, Integer> conteo = new HashMap<>();
    double reloj = 0, prox = 0, lam = 5.5, tSem = 0;
    int gen = 0, total = 40;
    boolean animando = false, hecho = false, verde = true;
    JTextArea log; JPanel panel; JLabel lbl; JButton btn;
    JTextField txtN, txtLam;
    javax.swing.Timer timer;

    public SimulacionTrafico() {
        super("Simulación Tráfico en Intersección ");
        setDefaultCloseOperation(EXIT_ON_CLOSE);
        setSize(1100, 700);
        setLayout(new BorderLayout(6, 6));
        conteo.put("auto", 0); conteo.put("camion", 0); conteo.put("moto", 0);

        panel = new JPanel() {
            protected void paintComponent(Graphics g) {
                super.paintComponent(g);
                Graphics2D g2 = (Graphics2D) g;
                g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                g2.setColor(new Color(93, 109, 126));
                g2.fillRect(0, 150, 720, 140);
                g2.setColor(Color.WHITE);
                for (int x = 0; x < 720; x += 40)
                    g2.drawLine(x, 220, x + 18, 220);
                g2.setColor(new Color(231, 76, 60));
                g2.setStroke(new BasicStroke(3));
                g2.drawLine(360, 150, 360, 290);
                // Semáforo
                g2.setColor(new Color(30, 37, 47));
                g2.fillRect(340, 70, 40, 70);
                g2.setColor(verde ? new Color(46, 204, 113) : new Color(127, 140, 141));
                g2.fillOval(348, 78, 24, 24);
                g2.setColor(verde ? new Color(127, 140, 141) : new Color(231, 76, 60));
                g2.fillOval(348, 108, 24, 24);
                g2.setColor(Color.WHITE);
                g2.drawString("INTERSECCIÓN CON SEMÁFORO", 250, 40);
                for (Vehiculo v : vehs) {
                    if (v.x > 720) continue;
                    g2.setColor(v.color);
                    g2.fillRect((int)v.x, (int)v.y, v.ancho, 14);
                    g2.setColor(Color.WHITE);
                    g2.drawString(String.valueOf(v.id), (int)v.x + 4, (int)v.y + 11);
                }
            }
        };
        panel.setPreferredSize(new Dimension(720, 420));
        panel.setBackground(new Color(44, 62, 80));
        add(panel, BorderLayout.CENTER);

        log = new JTextArea();
        log.setFont(new Font("Monospaced", Font.PLAIN, 11));
        log.setEditable(false);
        log.setBackground(new Color(28, 40, 51));
        log.setForeground(new Color(236, 240, 241));
        JScrollPane sp = new JScrollPane(log);
        sp.setPreferredSize(new Dimension(350, 0));
        sp.setBorder(BorderFactory.createTitledBorder("PANEL DE RESULTADOS (Tema 3)"));
        add(sp, BorderLayout.EAST);

        JPanel ctrl = new JPanel(new FlowLayout(FlowLayout.LEFT));
        ctrl.add(new JLabel("N:")); txtN = new JTextField("40", 4); ctrl.add(txtN);
        ctrl.add(new JLabel("λ:")); txtLam = new JTextField("5.5", 4); ctrl.add(txtLam);
        btn = new JButton("▶ INICIAR"); btn.addActionListener(e -> iniciar()); ctrl.add(btn);
        lbl = new JLabel("Listo"); ctrl.add(lbl);
        add(ctrl, BorderLayout.SOUTH);
        timer = new javax.swing.Timer(35, e -> paso());
    }

    void logMsg(String m) { log.append(m + "\n"); log.setCaretPosition(log.getDocument().getLength()); }

    void iniciar() {
        if (animando) return;
        animando = true; btn.setEnabled(false);
        vehs.clear(); inter.clear();
        conteo.put("auto", 0); conteo.put("camion", 0); conteo.put("moto", 0);
        reloj = 0; gen = 0; hecho = false; verde = true; tSem = 0;
        try { total = Integer.parseInt(txtN.getText().trim());
              lam = Double.parseDouble(txtLam.getText().trim()); } catch (Exception ex) {}
        log.setText("");
        logMsg("================================================");
        logMsg("  TRÁFICO EN INTERSECCIÓN ");
        logMsg("================================================");
        logMsg(String.format("[3.5 Box-Muller] Reacción = %.2f s\n", boxMuller(1.5, 0.4)));
        prox = exponencial(lam);
        timer.start();
    }

    void paso() {
        reloj += 0.04; tSem += 0.04;
        if (tSem > 7.5) { verde = !verde; tSem = 0; }
        if (reloj >= prox && gen < total) {
            String tipo = tipoVehiculo();
            double tc = composicion(tipo);
            gen++;
            conteo.put(tipo, conteo.get(tipo) + 1);
            vehs.add(new Vehiculo(gen, tipo));
            double i = exponencial(lam);
            inter.add(i); prox = reloj + i;
            logMsg(String.format("#%02d %-7s t=%.2f  cruce=%.2fs", gen, tipo, reloj, tc));
        }
        for (Vehiculo v : vehs) {
            if (verde || v.x > 370) v.x += v.vel;
            else if (v.x < 340) v.x += v.vel * 0.25;
        }
        panel.repaint();
        int act = 0; for (Vehiculo v : vehs) if (v.x < 720) act++;
        lbl.setText(String.format("t=%.2f | %d/%d | En vía: %d | %s",
                reloj, gen, total, act, verde ? "VERDE" : "ROJO"));
        if (gen >= total && act == 0) {
            timer.stop(); animando = false; btn.setEnabled(true);
            if (!hecho) {
                hecho = true;
                logMsg("\n================================================");
                double m = 0; for (double d : inter) m += d; m /= inter.size();
                logMsg(String.format("[3.6] Media inter = %.3f (teórica %.3f)", m, 1/lam));
                logMsg("Proporciones:");
                for (String t : new String[]{"auto","camion","moto"})
                    logMsg(String.format("  %s: %d/%d = %.1f%%", t, conteo.get(t), total,
                            100.0 * conteo.get(t) / total));
                logMsg(">>> Tema 3 completo.");
            }
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> new SimulacionTrafico().setVisible(true));
    }
}
