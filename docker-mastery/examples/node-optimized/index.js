const http = require("http");
const port = 3000;

http
  .createServer((req, res) => {
    if (req.url === "/health") {
      res.writeHead(200);
      return res.end("ok");
    }
    res.writeHead(200);
    res.end("Hello from an optimized, non-root Node container!\n");
  })
  .listen(port, () => console.log(`listening on ${port}`));
