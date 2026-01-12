async function loadNav() {
    const res = await fetch("./navHeader/nav.html");
    const html = await res.text();
    document.getElementById("nav-placeholder").innerHTML = html;

    const page = location.pathname.split("/").pop().replace(".html", "");
    document
        .querySelector(`[data-nav="${page}"]`)
        ?.classList.add("active");
}

loadNav();
