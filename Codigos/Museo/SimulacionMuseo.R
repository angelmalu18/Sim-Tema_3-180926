# ============================================================================
# SIMULACIÓN 2 - MUSEO DE CIENCIAS (R)
# Tema 3 completo
# ============================================================================
set.seed(42)

uniforme <- function() runif(1)
exponencial <- function(lambda) -log(1 - uniforme()) / lambda

tipo_visitante <- function() {
  u <- uniforme()
  if (u < 0.45) "Escolar" else if (u < 0.80) "Individual" else "Turista"
}

erlang_convolucion <- function(k, mu) {
  total <- 0
  for (i in 1:k) total <- total + exponencial(mu)
  total
}

composicion_visita <- function(tipo) {
  if (tipo == "Escolar") erlang_convolucion(3, 0.75)
  else if (tipo == "Turista") erlang_convolucion(4, 0.55)
  else exponencial(0.55)
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
}

N <- 35; lam <- 1.4
inter <- numeric(0); visitas <- numeric(0); tipos <- character(0)

cat("========================================================\n")
cat("  MUSEO DE CIENCIAS – TEMA 3 COMPLETO (R)\n")
cat("========================================================\n")
cat(sprintf("[3.5 Box-Muller] Interés = %.3f\n\n", normal_box_muller(1.0, 0.18)))

reloj <- 0
for (i in 1:N) {
  inter_i <- exponencial(lam)
  reloj <- reloj + inter_i
  tipo <- tipo_visitante()
  t_vis <- composicion_visita(tipo)
  inter <- c(inter, inter_i)
  visitas <- c(visitas, t_vis)
  tipos <- c(tipos, tipo)
  cat(sprintf("#%02d %-10s  t=%.2f  visita=%.2f\n", i, tipo, reloj, t_vis))
}

cat(sprintf("\nMedia inter = %.3f (teórica %.3f)\n", mean(inter), 1/lam))
cat(sprintf("Media visita = %.3f\n", mean(visitas)))
print(table(tipos) / N)
prueba_chi2(inter, lam)
cat("\n>>> Tema 3 completo.\n")
