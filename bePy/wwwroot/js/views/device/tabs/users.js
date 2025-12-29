export function renderUsers() {
    document.getElementById("detailContent").innerHTML = placeholder("User & Permission");
}
function placeholder(title) {
    return `
        <div class="bg-gray-50 p-6 rounded border text-gray-500 text-center">
            ${title} (Coming soon)
        </div>
    `;
}
