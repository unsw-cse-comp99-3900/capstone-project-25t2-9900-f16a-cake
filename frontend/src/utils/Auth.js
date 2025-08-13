export const Auth = {
  save: (token, user) => {
    localStorage.setItem("token", token);
    localStorage.setItem("role", user.role);
    localStorage.setItem("subrole", user.subrole ?? "none");
    localStorage.setItem("username", user.username);
    localStorage.setItem("user_id", user.id);
  },
  clear: () => {
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    localStorage.removeItem("subrole");
    localStorage.removeItem("username");
    localStorage.removeItem("user_id");
    localStorage.removeItem("ai_session_id");
  },
  getToken: () => localStorage.getItem("token"),
  getRole: () => localStorage.getItem("role"),
  getSubrole: () => localStorage.getItem("subrole"),
  getUsername: () => localStorage.getItem("username"),
  getUserId: () => localStorage.getItem("user_id"),
};