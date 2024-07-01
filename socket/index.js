// server.js
const express = require("express");
const http = require("http");
const socketIo = require("socket.io");

const app = express();
const server = http.createServer(app);
const io = socketIo(server);

const PORT = process.env.PORT || 3000;

// Serve static files (optional, if you want to serve an HTML file for testing)
app.use(express.static("public"));

// Handle socket connections
io.on("connection", (socket) => {
  socket.on("user-list", (data) => {
    io.emit("user-list", data);
  });
  socket.on("room", (data) => {
    io.emit("room", data);
  });
  // Handle disconnections
  socket.on("disconnect", () => {
    console.log("A user disconnected");
  });
});

// Start the server
server.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});
