// ============================================================
// app.js — загальна логіка сайту «Сателіт»
// - рендер header/footer з одного джерела (без дублювання);
// - мобільне hamburger-меню;
// - кошик у localStorage;
// Шляхи відносні — сумісно з GitHub Pages (/repo/...).
// ============================================================

import { formatPrice, getProducts } from "./products.js";

const SHOP = {
  name: "Сателіт",
  // Пряме посилання на картку магазину в Google Maps
  mapsUrl: "https://www.google.com/maps/place/%D0%9C%D0%B0%D0%B3%D0%B0%D0%B7%D0%B8%D0%BD+%22%D0%A1%D0%B0%D1%82%D0%B5%D0%BB%D1%96%D1%82%22/@49.0113539,31.3918269,336m/data=!3m1!1e3!4m17!1m8!3m7!1s0x40d17775f1491717:0xab36193c2da13de2!2z0LLRg9C70LjRhtGPINCb0LXQvdGW0L3QsCwgMTAsINCo0L_QvtC70LAsINCn0LXRgNC60LDRgdGM0LrQsCDQvtCx0LvQsNGB0YLRjCwgMjA2MDA!3b1!8m2!3d49.0113634!4d31.3927529!16s%2Fg%2F11p5zj7tl_!3m7!1s0x40d177b040f2557f:0x8bf52c4828e7bc8b!8m2!3d49.0113634!4d31.3927529!9m1!1b1!16s%2Fg%2F11f0333sd3?entry=ttu"
};

// ---------- Header / Footer (єдині для всіх сторінок) ----------

function currentPage() {
  const path = location.pathname.split("/").pop() || "index.html";
  return path === "" ? "index.html" : path;
}

export function renderHeader() {
  const page = currentPage();
  const link = (href, label) => {
    const path = href.split("#")[0];
    const isActive = page === path && !href.includes("#");
    return `<a class="nav-link${isActive ? " active" : ""}" href="${href}">${label}</a>`;
  };

  return `
  <header class="site-header">
    <div class="container header-inner">
      <a class="brand" href="index.html" aria-label="Сателіт — на головну">
        <img src="assets/logo.svg" alt="Логотип магазину Сателіт" class="brand-logo">
        <span class="brand-name">Сателіт</span>
      </a>

      <nav class="main-nav" id="main-nav" aria-label="Головна навігація">
        ${link("index.html", "Головна")}
        ${link("catalog.html", "Каталог")}
        ${link("index.html#sales", "Акції")}
        ${link("index.html#about", "Про нас")}
        ${link("contacts.html", "Контакти")}
        <a class="nav-link nav-icon" href="catalog.html" aria-label="Пошук">🔍</a>
        ${link("cart.html", `<span class="cart-label">Кошик</span><span class="cart-count" id="cart-count">0</span>`)}
        <a class="btn btn-primary btn-login" href="login.html" id="auth-button">Увійти</a>
      </nav>

      <button class="hamburger" id="hamburger" aria-label="Меню" aria-expanded="false">
        <span></span><span></span><span></span>
      </button>
    </div>
  </header>`;
}

export function renderFooter() {
  return `
  <footer class="site-footer">
    <div class="container footer-inner">
      <div class="footer-col">
        <a class="brand brand-footer" href="index.html">
          <img src="assets/logo.svg" alt="Логотип Сателіт" class="brand-logo">
          <span class="brand-name">Сателіт</span>
        </a>
        <p class="footer-tagline">Техніка та електроніка</p>
        <p class="footer-address">Шпола, вул. Леніна, 10<br>Черкаська область, Україна</p>
      </div>
      <div class="footer-col">
        <p class="footer-title">Посилання</p>
        <a href="index.html">Головна</a>
        <a href="catalog.html">Каталог</a>
        <a href="index.html#sales">Акції</a>
        <a href="index.html#about">Про нас</a>
        <a href="contacts.html">Контакти</a>
      </div>
      <div class="footer-col">
        <p class="footer-title">Мапа</p>
        <a href="${SHOP.mapsUrl}" target="_blank" rel="noopener" class="btn btn-outline btn-sm">
          Відкрити в Google Maps
        </a>
      </div>
    </div>
    <div class="footer-bottom container">© Сателіт</div>
  </footer>`;
}

// ---------- Мобільне меню ----------

function initHamburger() {
  const burger = document.getElementById("hamburger");
  const nav = document.getElementById("main-nav");
  if (!burger || !nav) return;
  burger.addEventListener("click", () => {
    const open = nav.classList.toggle("open");
    burger.classList.toggle("open", open);
    burger.setAttribute("aria-expanded", String(open));
  });
}

// ---------- Кошик (localStorage) ----------

const CART_KEY = "satelit_cart_v1";

export function getCart() {
  try {
    return JSON.parse(localStorage.getItem(CART_KEY)) || [];
  } catch {
    return [];
  }
}

export function saveCart(cart) {
  localStorage.setItem(CART_KEY, JSON.stringify(cart));
  updateCartBadge();
}

export function addToCart(product) {
  const cart = getCart();
  const item = cart.find((i) => i.id === product.id);
  if (item) item.qty += 1;
  else cart.push({ id: product.id, name: product.name, price: product.price, qty: 1 });
  saveCart(cart);
}

export function cartTotal() {
  return getCart().reduce((s, i) => s + i.price * i.qty, 0);
}

export function updateCartBadge() {
  const badge = document.getElementById("cart-count");
  if (!badge) return;
  const count = getCart().reduce((s, i) => s + i.qty, 0);
  badge.textContent = String(count);
  badge.classList.toggle("visible", count > 0);
}

// ---------- Рендер карток товарів ----------

export function productCardHTML(p) {
  return `
  <article class="product-card">
    <a href="product.html?id=${encodeURIComponent(p.id)}" class="product-media">
      <img src="${p.image}" alt="${p.name}" loading="lazy">
      ${p.sale ? '<span class="badge badge-sale">Акція</span>' : ""}
    </a>
    <div class="product-info">
      <a class="product-name" href="product.html?id=${encodeURIComponent(p.id)}">${p.name}</a>
      <p class="product-desc">${p.description}</p>
      <div class="product-row">
        <span class="product-price">${formatPrice(p.price)}</span>
        <button class="btn btn-primary btn-sm add-to-cart" data-id="${p.id}">Додати в кошик</button>
      </div>
    </div>
  </article>`;
}

export function bindAddToCartButtons(scope = document) {
  scope.querySelectorAll(".add-to-cart").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const products = await getProducts();
      const p = products.find((x) => x.id === btn.dataset.id);
      if (!p) return;
      addToCart(p);
      btn.textContent = "Додано ✓";
      setTimeout(() => (btn.textContent = "Додати в кошик"), 1200);
    });
  });
}

// ---------- Ініціалізація сторінки ----------

document.addEventListener("DOMContentLoaded", () => {
  const headerMount = document.getElementById("header-mount");
  const footerMount = document.getElementById("footer-mount");
  if (headerMount) headerMount.outerHTML = renderHeader();
  if (footerMount) footerMount.outerHTML = renderFooter();

  initHamburger();
  updateCartBadge();
});
