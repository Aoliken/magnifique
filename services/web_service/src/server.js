const http = require("http");
const fs = require("fs");
const path = require("path");

const { registerPublicRoutes } = require("./routes/public");

const PORT = Number(process.env.PORT || 5003);
const OWNER_HEADER = "X-Magnifique-Web-Service";
const OWNER_VALUE = "web-service";
const VIEWS_DIR = path.join(__dirname, "..", "views");
const PUBLIC_DIR = path.join(__dirname, "..", "public");

function renderTemplate(viewName, locals = {}) {
  const filePath = path.join(VIEWS_DIR, `${viewName}.ejs`);
  const template = fs.readFileSync(filePath, "utf-8");
  return template.replace(/<%=\s*(\w+)\s*%>/g, (_, key) => String(locals[key] ?? ""));
}

function respondHtml(res, statusCode, viewName, locals) {
  res.writeHead(statusCode, {
    "Content-Type": "text/html; charset=utf-8",
    [OWNER_HEADER]: OWNER_VALUE,
  });
  res.end(renderTemplate(viewName, locals));
}

function respondRedirect(res, location) {
  res.writeHead(302, {
    Location: location,
    [OWNER_HEADER]: OWNER_VALUE,
  });
  res.end("");
}

function serveStatic(res, relativePath) {
  const filePath = path.join(PUBLIC_DIR, relativePath);
  if (!fs.existsSync(filePath)) {
    return false;
  }

  res.writeHead(200, {
    "Content-Type": "text/css; charset=utf-8",
    [OWNER_HEADER]: OWNER_VALUE,
  });
  res.end(fs.readFileSync(filePath, "utf-8"));
  return true;
}

const routes = [];

function match(method, pathname, handler) {
  routes.push({ method, pathname, handler });
}

registerPublicRoutes({
  match,
  renderHtml: (viewName, locals) => ({ type: "html", viewName, locals }),
  redirect: (location) => ({ type: "redirect", location }),
  notFound: { type: "not-found" },
});

const server = http.createServer((req, res) => {
  const url = new URL(req.url, `http://${req.headers.host || `127.0.0.1:${PORT}`}`);

  if (req.method !== "GET") {
    res.writeHead(405, { [OWNER_HEADER]: OWNER_VALUE });
    res.end("Method Not Allowed");
    return;
  }

  const route = routes.find((candidate) => candidate.method === req.method && candidate.pathname === url.pathname);
  if (route) {
    const outcome = route.handler();
    if (outcome.type === "redirect") {
      respondRedirect(res, outcome.location);
      return;
    }
    if (outcome.type === "html") {
      respondHtml(res, 200, outcome.viewName, outcome.locals);
      return;
    }
  }

  if (url.pathname.startsWith("/public/") && serveStatic(res, url.pathname.replace("/public/", ""))) {
    return;
  }

  if (route && route.type === "not-found") {
    res.writeHead(404, {
      "Content-Type": "text/plain; charset=utf-8",
      [OWNER_HEADER]: OWNER_VALUE,
    });
    res.end("Not Found");
    return;
  }

  res.writeHead(404, {
    "Content-Type": "text/plain; charset=utf-8",
    [OWNER_HEADER]: OWNER_VALUE,
  });
  res.end("Not Found");
});

server.listen(PORT, "0.0.0.0", () => {
  process.stdout.write(`web-service listening on ${PORT}\n`);
});
