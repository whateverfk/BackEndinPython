import { API_URL } from "./config.js";

document.addEventListener("DOMContentLoaded", () => {
    const btn = document.getElementById("loginBtn");

    if (!btn) {
        console.error("Không tìm thấy #loginBtn");
        return;
    }

    btn.addEventListener("click", login);
});

async function login() {
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;

    if (!username || !password) {
        alert("Vui lòng nhập đầy đủ thông tin");
        return;
    }

    const res = await fetch(`${API_URL}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
    });

    if (!res.ok) {
        alert("Sai tài khoản hoặc mật khẩu");
        return;
    }

    const data = await res.json();
    localStorage.setItem("token", data.token);
    window.location.href = "./index.html";
}
