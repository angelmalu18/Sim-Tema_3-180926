# ============================================================================
# SIMULACIÓN 3 - TRÁFICO EN INTERSECCIÓN (R)
# Tema 3 completo 
# ============================================================================
set.seed(99)

uniforme <- function() runif(1)
exponencial <- function(lambda) -log(1 - uniforme()) / lambda

tipo_vehiculo <- function() {
  u <- uniforme()
  if (u < 0.70) "auto" else if (u < 0.90) "camion" else "moto"
}

erlang_convolucion <- function(k, mu) {
  total <- 0
  for (i in 1:k) total <- total + exponencial(mu)
  total
}

composicion_cruce <- function(tipo) {
  if (tipo == "camion") erlang_convolucion(2, 3.0)
  else if (tipo == "moto") exponencial(10.0)
  else exponencial(8.0)
}

normal_box_muller <- function(mu, sigma) {
  z <- sqrt(-2 * log(uniforme())) * cos(2 * pi * uniforme())
  mu + sigma * z
}

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
    a <- (i-1)*ancho; b <- i*ancho
    p <- exp(-lambda*a) - exp(-lambda*b)
    esp <- max(p * length(datos), 1e-6)
    chi2 <- chi2 + (obs[i] - esp)^2 / esp
    cat(sprintf("Clase [%.2f-%.2f): obs=%d esp=%.2f\n", a, b, obs[i], esp))
  }
  pval <- 1 - pchisq(chi2, df = k - 2)
  cat(sprintf("χ² = %.4f  p-valor = %.4f\n", chi2, pval))
  if (pval > 0.05) cat("No se rechaza H0.\n") else cat("Se rechaza H0.\n")
}

N <- 40; lam <- 5.5
inter <- numeric(0); cruces <- numeric(0); tipos <- character(0)

cat("========================================================\n")
cat("  TRÁFICO EN INTERSECCIÓN – TEMA 3 COMPLETO (R)\n")
cat("========================================================\n")
cat(sprintf("[3.5 Box-Muller] Reacción conductor = %.2f s\n\n",
            normal_box_muller(1.5, 0.4)))

reloj <- 0
for (i in 1:N) {
  inter_i <- exponencial(lam)           # 3.4.1
  reloj <- reloj + inter_i
  tipo <- tipo_vehiculo()               # 3.2
  t_cruce <- composicion_cruce(tipo)    # 3.4.3 (+ 3.4.2 si camión)
  inter <- c(inter, inter_i)
  cruces <- c(cruces, t_cruce)
  tipos <- c(tipos, tipo)
  cat(sprintf("#%02d %-7s  t=%.2f  cruce=%.2fs\n", i, tipo, reloj, t_cruce))
}

cat(sprintf("\nMedia inter-llegadas = %.3f (teórica %.3f)\n", mean(inter), 1/lam))
cat(sprintf("Media tiempos de cruce = %.3f\n", mean(cruces)))
cat("Proporciones de tipos:\n")
print(table(tipos) / N)
cat("(teóricos: auto=0.70, camion=0.20, moto=0.10)\n")

prueba_chi2(inter, lam)
cat("\n>>> Tema 3 completo ejecutado.\n")
