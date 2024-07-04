// server.js
const express = require("express");
const http = require("http");

const app = express();
const server = http.createServer(app);
const socketIo = require("socket.io")(server, { cors: { origin: "*" } });

const PORT = process.env.PORT || 3000;

// Serve static files (optional, if you want to serve an HTML file for testing)
app.use(express.static("public"));

// Handle socket connections
socketIo.on("connection", (socket) => {
  socket.on("user-list", (data) => {
    socketIo.emit("user-list", data);
  });
  socket.on("join-room", ({ room, userId }) => {
    socket.join(room);
    socket.userId = userId;
    console.log(`User ${userId} đã tham gia phòng: ${room}`);
  });
  socket.on("send-message", (data) => {
    console.log("data: ", data);
    socketIo.to(data.room).emit("recieve-message", {
      userId: data.userId,
      message: data.message,
    });
  });
  socket.on("create-room", (data) => {
    socketIo.emit("create-room", data);
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
