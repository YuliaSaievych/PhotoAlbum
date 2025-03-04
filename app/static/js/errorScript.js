
document.addEventListener("DOMContentLoaded", function () {
        let errorBox = document.getElementById("error");
        let errorMessage = document.getElementById("error-message");

        if (errorMessage && errorMessage.innerText.trim() !== "") {
            errorBox.style.display = "block";
            setTimeout(() => {
                errorBox.style.display = "none";
            }, 3000);
        }
    });