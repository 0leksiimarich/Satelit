// ============================================================
// products.js — джерело товарів сайту «Сателіт»
// Джерело істини — власний бекенд. DEMO_PRODUCTS — заглушки.
// ============================================================

import { getProductsFromBackend } from "./backend.js";

export const CATEGORIES = [
  { id: "batteries", name: "Батарейки" },
  { id: "tvbox",     name: "TV Box" },
  { id: "antennas",  name: "Антени" },
  { id: "cables",    name: "Кабелі" },
  { id: "accessories", name: "Аксесуари" },
  { id: "other",     name: "Інше" }
];

export const DEMO_PRODUCTS = [
  { id: "demo-tvbox-1", name: "[Приклад] TV Box Android 4K",
    description: "Демонстраційна картка товару. Замінити на реальний товар.",
    price: 1299, category: "tvbox", image: "assets/img-placeholder.svg",
    stock: 0, featured: true, sale: false },
  { id: "demo-battery-1", name: "[Приклад] Батарейки AA, 4 шт.",
    description: "Демонстраційна картка товару. Замінити на реальний товар.",
    price: 59, category: "batteries", image: "assets/img-placeholder.svg",
    stock: 0, featured: true, sale: false },
  { id: "demo-antenna-1", name: "[Приклад] Антена цифрова DVB-T2",
    description: "Демонстраційна картка товару. Замінити на реальний товар.",
    price: 349, category: "antennas", image: "assets/img-placeholder.svg",
    stock: 0, featured: false, sale: false },
  { id: "demo-cable-1", name: "[Приклад] Кабель HDMI 2 м",
    description: "Демонстраційна картка товару. Замінити на реальний товар.",
    price: 149, category: "cables", image: "assets/img-placeholder.svg",
    stock: 0, featured: false, sale: false },
  { id: "demo-acc-1", name: "[Приклад] Пульт універсальний",
    description: "Демонстраційна картка товару. Замінити на реальний товар.",
    price: 199, category: "accessories", image: "assets/img-placeholder.svg",
    stock: 0, featured: false, sale: false },
  { id: "demo-other-1", name: "[Приклад] Подовжувач 3 м",
    description: "Демонстраційна картка товару. Замінити на реальний товар.",
    price: 129, category: "other", image: "assets/img-placeholder.svg",
    stock: 0, featured: false, sale: false }
];

export function formatPrice(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return "—";
  return n.toLocaleString("uk-UA") + " ₴";
}

let cachedProducts = null;

export async function getProducts() {
  if (cachedProducts) return cachedProducts;
  try {
    const list = await getProductsFromBackend();
    if (Array.isArray(list) && list.length > 0) {
      cachedProducts = list;
      return cachedProducts;
    }
  } catch (err) {
    console.warn("Бекенд недоступний, показуємо демо-товари:", err.message);
  }
  cachedProducts = DEMO_PRODUCTS;
  return cachedProducts;
}

export async function getProductById(id) {
  const products = await getProducts();
  return products.find((p) => p.id === id) || null;
}

export function getCategoryName(categoryId) {
  const cat = CATEGORIES.find((c) => c.id === categoryId);
  return cat ? cat.name : "Інше";
}
