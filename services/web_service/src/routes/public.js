function registerPublicRoutes({ match, renderHtml, redirect, notFound }) {
  match("GET", "/", () => redirect("/auth/login"));
  match("GET", "/auth/login", () => renderHtml("login", { title: "Iniciar Sesión — Hotel Magnifique" }));
  match("GET", "/auth/register", () => renderHtml("register", { title: "Registrar — Hotel Magnifique" }));
  match("GET", "/game/no-game", () => renderHtml("no-game", { title: "Sin partida activa — Hotel Magnifique" }));
  return notFound;
}

module.exports = { registerPublicRoutes };
