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

    const profileLinkForm = document.getElementById("profile-link");
            const profileImage = document.getElementById("profileImage");
            const profileText = document.getElementById("profileText");

            const toggleProfileLinkForm = () => {
                if (profileLinkForm.style.display === "none" || profileLinkForm.style.display === "") {
                    profileLinkForm.style.display = "block";
                } else {
                    profileLinkForm.style.display = "none";
                }
            };

            if (profileImage) {
                profileImage.addEventListener("click", toggleProfileLinkForm);
            }
            if (profileText) {
                profileText.addEventListener("click", toggleProfileLinkForm);
            }

            const createForm = document.getElementById("Create");
            const openCreateFormLink = document.getElementById("openCreateForm");

            const toggleCreateForm = () => {
                if (createForm.style.display === "none" || createForm.style.display === "") {
                    createForm.style.display = "block";
                } else {
                    createForm.style.display = "none";
                }
            };

            if (openCreateFormLink) {
                openCreateFormLink.addEventListener("click", toggleCreateForm);
            }

            const form = document.getElementById('folder-action');
    const toggleFormBtn = document.getElementById('folderFormBtn');

    let isFormVisible = form.style.display === 'block';

    const toggleFormVisibility = () => {
        if (isFormVisible) {
            form.style.display = 'none';
        } else {
            form.style.display = 'block';
        }
        isFormVisible = !isFormVisible;
    };

    toggleFormBtn.addEventListener('click', toggleFormVisibility);

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


