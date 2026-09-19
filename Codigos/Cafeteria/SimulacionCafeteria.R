# ============================================================================
# SIMULACIÓN 1 - CAFETERÍA "EL RINCÓN" (R - consola)
# Tema 3 completo
# ============================================================================
# 3.1 Conceptos básicos
# 3.2 VA discretas          → tipo cliente (Regular/VIP)
# 3.3 VA continuas
# 3.4.1 Transformada inversa → x = -(1/λ) * ln(1-R)   Exponencial
# 3.4.2 Convolución         → Erlang = suma de k Exp
# 3.4.3 Composición         → tiempo atención según tipo
# 3.5 Box-Muller            → Normal
# 3.6 Pruebas               → Chi-cuadrada
# ============================================================================

set.seed(42)

uniforme <- function() runif(1)

# 3.4.1 Transformada inversa Exponencial
# x = -(1/λ) * ln(1 - R)     (también se usa -ln(R)/λ)
exponencial <- function(lambda) {
  -log(1 - uniforme()) / lambda
}

# 3.2 Variable discreta multinomial
tipo_cliente <- function() {
  if (uniforme() < 0.25) "VIP" else "Regular"
}

# 3.4.2 Convolución → Erlang
erlang_convolucion <- function(k, mu) {
  total <- 0
  for (i in 1:k) total <- total + exponencial(mu)
  total
}

# 3.4.3 Composición
composicion_atencion <- function(tipo) {
  if (tipo == "VIP") {
    exponencial(0.7)
  } else if (uniforme() < 0.30) {
    erlang_convolucion(2, 0.45)   # pedido complejo
  } else {
    exponencial(0.40)
  }
}

# 3.5 Box-Muller
normal_box_muller <- function(mu, sigma) {
  u1 <- uniforme(); u2 <- uniforme()
  z <- sqrt(-2 * log(u1)) * cos(2 * pi * u2)
  mu + sigma * z
}

# 3.6 Chi-cuadrada
prueba_chi2 <- function(datos, lambda, k = 6) {
  ancho <- max(datos) / k
  obs <- integer(k)
  for (d in datos) {
    idx <- min(floor(d / ancho) + 1, k)
    obs[idx] <- obs[idx] + 1
  }
  chi2 <- 0
  cat("\n=== 3.6 Prueba Chi-cuadrada ===\n")
  for (i in 1:k) {
    a <- (i - 1) * ancho; b <- i * ancho
    p <- exp(-lambda * a) - exp(-lambda * b)
    esp <- max(p * length(datos), 1e-6)
    chi2 <- chi2 + (obs[i] - esp)^2 / esp
    cat(sprintf("Clase [%.2f-%.2f): obs=%d esp=%.2f\n", a, b, obs[i], esp))
  }
  gl <- k - 2
  pval <- 1 - pchisq(chi2, df = gl)
  cat(sprintf("χ² = %.4f  gl = %d  p-valor = %.4f\n", chi2, gl, pval))
  if (pval > 0.05) cat("No se rechaza H0 (ajuste razonable).\n")
  else cat("Se rechaza H0.\n")
}

# --- Motor de simulación ---
N <- 40
lam <- 1.6
inter <- numeric(0)
atenciones <- numeric(0)
tipos <- character(0)

cat("========================================================\n")
cat("  CAFETERÍA '' (R)\n")
cat("========================================================\n")
cat(sprintf("[3.5 Box-Muller] Ánimo barista = %.3f\n", normal_box_muller(1.0, 0.12)))
cat("Flujo: Ri(0,1) → Generador VA (fórmulas) → Simulación\n\n")

reloj <- 0
for (i in 1:N) {
  inter_i <- exponencial(lam)          # 3.4.1
  reloj <- reloj + inter_i
  tipo <- tipo_cliente()               # 3.2
  t_at <- composicion_atencion(tipo)   # 3.4.3 (+ 3.4.2)
  inter <- c(inter, inter_i)
  atenciones <- c(atenciones, t_at)
  tipos <- c(tipos, tipo)
  cat(sprintf("#%02d %-8s  t=%.2f  inter=%.2f  atención=%.2f\n",
              i, tipo, reloj, inter_i, t_at))
}

cat("\n--- Resumen ---\n")
cat(sprintf("Media inter-llegadas  = %.3f  (teórica 1/λ = %.3f)\n",
            mean(inter), 1/lam))
cat(sprintf("Media tiempos atención = %.3f\n", mean(atenciones)))
cat("Proporción VIP:\n")
print(table(tipos) / N)

prueba_chi2(inter, lam)

cat("\n>>> Tema 3 completo ejecutado.\n")
