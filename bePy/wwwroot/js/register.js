import { API_URL } from "./config.js";
async function register() {
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;
    const password2 = document.getElementById("password2").value;

    if (!username || !password) {
        alert("Vui lòng nhập đầy đủ thông tin");
        return;
    }

    if (password !== password2) {
        alert("Mật khẩu không khớp");
        return;
    }

    const res = await fetch(`${API_URL}/api/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
    });

    if (!res.ok) {
        const text = await res.text();
        alert(text);
        return;
    }

    const data = await res.json();
    localStorage.setItem("token", data.token);

    window.location.href = "./index.html";
}
document.addEventListener("DOMContentLoaded", () => {
    const btn = document.getElementById("btnDangky");

    if (!btn) {
        console.error("Không tìm thấy #btnDangky");
        return;
    }

    btn.addEventListener("click", register);
});

