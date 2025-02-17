function toggleMenu() {
    var menu = document.getElementById('myMenu');
    menu.style.display = (menu.style.display === 'block') ? 'none' : 'block';
}

document.addEventListener('click', function (event) {
    var menu = document.getElementById('myMenu');
    var modals = document.querySelectorAll('.modal');

    // Close modals when clicking outside
    if (!event.target.closest('.modal-content') && !event.target.closest('.icon.menu')) {
        modals.forEach(function (modal) {
            if (modal.style.display === 'block') {
                modal.style.display = 'none';
            }
        });
    }

    // Close menu when clicking outside
    if (!event.target.closest('.menu') && !event.target.closest('#myMenu')) {
        menu.style.display = 'none';
    }
});

const letters = document.querySelectorAll('.letter');

letters.forEach(letter => {
    // Randomize rotation
    const randomRotation = Math.random() * 30 - 15; // between -15 and 15 degrees
    letter.style.transform = `rotate(${randomRotation}deg)`;
});