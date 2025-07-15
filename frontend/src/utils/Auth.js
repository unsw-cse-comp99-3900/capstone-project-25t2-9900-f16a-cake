export const Auth = {
  save: (token, user) => {
    localStorage.setItem("token", token);
    localStorage.setItem("role", user.role);
    localStorage.setItem("subrole", user.subrole ?? "none");
    localStorage.setItem("username", user.username);
  },
  clear: () => {
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    localStorage.removeItem("subrole");
    localStorage.removeItem("username");
  },
  getToken: () => localStorage.getItem("token"),
  getRole: () => localStorage.getItem("role"),
  getSubrole: () => localStorage.getItem("subrole"),
  getUsername: () => localStorage.getItem("username"),
}; 


// 1. 前端登录时给后端的数据格式
// [用户名, 密码, 角色(staff/admin)]
// 2. 后端返回的格式 (依旧不明确)
// [登录状态, token, 用户信息(id, username, role, subrole)]
// {
//     "success": true,
//     "token": "eyJhbGciOiJIUzI1NiIsInR...",
//     "user": {
//         "id": 123,
//         "username": "admin1",
//         "role": "admin",
//         "subrole": null
//     }
// }
// 3. 前端保存的数据格式
// [token, role, subrole, username]