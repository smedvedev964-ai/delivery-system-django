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

    const updateProductControl = (form, quantity) => {
        const csrf = form.querySelector('[name="csrfmiddlewaretoken"]')?.value || "";
        const next = form.querySelector('[name="next"]')?.value || window.location.pathname;
        const productName = form.dataset.productName || "блюдо";
        form.replaceChildren();
        const csrfInput = document.createElement("input");
        csrfInput.type = "hidden";
        csrfInput.name = "csrfmiddlewaretoken";
        csrfInput.value = csrf;
        const nextInput = document.createElement("input");
        nextInput.type = "hidden";
        nextInput.name = "next";
        nextInput.value = next;
        form.append(csrfInput, nextInput);

        const makeButton = (action, label, ariaLabel) => {
            const button = document.createElement("button");
            button.type = "submit";
            button.name = "action";
            button.value = action;
            button.textContent = label;
            button.setAttribute("aria-label", ariaLabel);
            return button;
        };
        if (quantity > 0) {
            form.append(makeButton("decrement", "−", `Уменьшить количество: ${productName}`));
            const count = document.createElement("span");
            count.setAttribute("aria-live", "polite");
            count.textContent = quantity;
            form.append(count);
        }
        form.append(makeButton("increment", "+", quantity ? `Добавить ещё: ${productName}` : `Добавить ${productName} в корзину`));
    };

    document.addEventListener("submit", async (event) => {
        const form = event.target.closest("form[data-cart-control]");
        if (!form) return;
        event.preventDefault();
        if (form.dataset.pending === "true") return;
        form.dataset.pending = "true";
        form.classList.add("is-pending");
        const action = event.submitter?.value || "increment";
        const body = new FormData(form);
        body.set("action", action);
        try {
            const response = await fetch(form.action, {
                method: "POST",
                body,
                headers: { "X-Requested-With": "XMLHttpRequest", "Accept": "application/json" },
                credentials: "same-origin",
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || "Не удалось обновить корзину.");
            document.querySelectorAll(`[data-cart-control][data-product-id="${data.product_id}"]`).forEach((control) => {
                updateProductControl(control, data.quantity);
            });
            const sidebar = document.querySelector("#cart-sidebar");
            if (sidebar && data.sidebar_html) sidebar.outerHTML = data.sidebar_html;
            const cartLink = document.querySelector(".cart-icon-link");
            if (cartLink) {
                cartLink.querySelector(".cart-dot")?.remove();
                if (data.cart_has_items) {
                    const dot = document.createElement("span");
                    dot.className = "cart-dot";
                    dot.setAttribute("aria-hidden", "true");
                    cartLink.append(dot);
                }
            }
        } catch (error) {
            let notice = form.querySelector(".cart-control-error");
            if (!notice) {
                notice = document.createElement("span");
                notice.className = "cart-control-error";
                notice.setAttribute("role", "alert");
                form.append(notice);
            }
            notice.textContent = error.message;
        } finally {
            form.dataset.pending = "false";
            form.classList.remove("is-pending");
        }
    });
});
