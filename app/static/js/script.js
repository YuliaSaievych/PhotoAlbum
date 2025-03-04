function copyToClipboard() {
    var copyText = document.querySelector("input");
    copyText.select();
    document.execCommand("copy");
    alert("Посилання скопійоване!");
};
document.addEventListener('DOMContentLoaded', function() {
    const recoverBtn = document.getElementById('recoverBtn');
    const recoverForm = document.getElementById('recoverForm');

    if (recoverBtn && recoverForm) {
        recoverBtn.addEventListener('click', function() {
            recoverForm.style.display = recoverForm.style.display === 'none' ? 'block' : 'none';
        });
    }
});

document.getElementById("openRecoverForm").addEventListener("click", function(event) {
        let form = document.getElementById("recoverForm");
        form.style.display = "block";
        event.stopPropagation();
    });

    document.addEventListener("click", function(event) {
        let form = document.getElementById("recoverForm");
        if (form.style.display === "block" && !form.contains(event.target) && event.target.id !== "openRecoverForm") {
            form.style.display = "none";
        }
    });

