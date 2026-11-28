"use strict";

document.addEventListener("DOMContentLoaded", () => {
    // Прокручивается вся страница, а не отдельная внутренняя колонка меню.
    if (window.location.hash === "#menu") {
        const menu = document.querySelector("#menu");

        if (menu) {
            window.requestAnimationFrame(() => {
                menu.scrollIntoView({
                    behavior: "smooth",
                    block: "start",
                });
            });
        }
    }

    // Плавно отправляем форму сортировки без блокировки выбранного значения.
    document.querySelectorAll(".sort-form select").forEach((select) => {
        select.addEventListener("change", () => {
            const form = select.form;

            if (form) {
                form.classList.add("is-submitting");
                form.requestSubmit();
            }
        });
    });
});
