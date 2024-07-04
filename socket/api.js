const API_URL = "http://localhost:8000/api";

const createMessage = async ({ token, room, content }) => {
  const res = await fetch(`${API_URL}/message/create-message/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: token,
    },
    body: JSON.stringify({ room_id: room, content }),
  });
  return await res.json();
};

module.exports = { createMessage };
