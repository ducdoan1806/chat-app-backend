// server.js
const express = require("express");
const http = require("http");
const socketIo = require("socket.io");
const { createMessage } = require("./api");

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
  transports: ["websocket", "polling"],
});

const PORT = process.env.PORT || 3000;

// Serve static files (optional, if you want to serve an HTML file for testing)
app.use(express.static("public"));

// Handle socket connections
io.on("connection", (socket) => {
  socket.on("user-list", (data) => {
    io.emit("user-list", data);
  });
  socket.on("join-room", ({ room, userId }) => {
    socket.join(room);
    socket.userId = userId;
    console.log(`User ${userId} đã tham gia phòng: ${room}`);
  });
  socket.on("send-message", async (data) => {
    const newMessage = await createMessage(data);
    if (newMessage?.status) {
      io.to(data.room).emit("recieve-message", newMessage?.data);
    }
  });
  socket.on("create-room", (data) => {
    io.emit("create-room", data);
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
