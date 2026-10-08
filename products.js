// ============================================================
// products.js — джерело товарів сайту «Сателіт»
// Джерело істини — таблиця "products" у Supabase
// (структура див. supabase-setup.sql). Якщо Supabase ще не
// підключено або таблиця порожня — використовуємо DEMO_PRODUCTS.
//
// УВАГА: DEMO_PRODUCTS — це ДЕМО-ДАНІ ТИПУ «ПРИКЛАД».
// Це НЕ реальний асортимент магазину «Сателіт».
// ============================================================

import { isSupabaseConfigured, getSupabase } from "./supabase.js";

export const CATEGORIES = [
  { id: "batteries", name: "Батарейки" },
  { id: "tvbox",     name: "TV Box" },
  { id: "antennas",  name: "Антени" },
  { id: "cables",    name: "Кабелі" },
  { id: "accessories", name: "Аксесуари" },
  { id: "other",     name: "Інше" }
];

// Демо-товари. Кожен названий із префіксом "[Приклад]",
// щоб жоден користувач не сприйняв їх як реальні.
export const DEMO_PRODUCTS = [
  {
    id: "demo-tvbox-1",
    name: "[Приклад] TV Box Android 4K",
    description: "Демонстраційна картка товару. Замінити на реальний товар.",
    price: 1299,
    category: "tvbox",
    image: "assets/img-placeholder.svg",
    stock: 0, // 0 = залишок ще не задано (не вигаданий!)
    featured: true,
    sale: false
  },
  {
    id: "demo-battery-1",
    name: "[Приклад] Батарейки AA, 4 шт.",
    description: "Демонстраційна картка товару. Замінити на реальний товар.",
    price: 59,
    category: "batteries",
    image: "assets/img-placeholder.svg",
    stock: 0,
    featured: true,
    sale: false
  },
  {
    id: "demo-antenna-1",
    name: "[Приклад] Антена цифрова DVB-T2",
    description: "Демонстраційна картка товару. Замінити на реальний товар.",
    price: 349,
    category: "antennas",
    image: "assets/img-placeholder.svg",
    stock: 0,
    featured: false,
    sale: false
  },
  {
    id: "demo-cable-1",
    name: "[Приклад] Кабель HDMI 2 м",
    description: "Демонстраційна картка товару. Замінити на реальний товар.",
    price: 149,
    category: "cables",
    image: "assets/img-placeholder.svg",
    stock: 0,
    featured: false,
    sale: false
  },
  {
    id: "demo-acc-1",
    name: "[Приклад] Пульт універсальний",
    description: "Демонстраційна картка товару. Замінити на реальний товар.",
    price: 199,
    category: "accessories",
    image: "assets/img-placeholder.svg",
    stock: 0,
    featured: false,
    sale: false
  },
  {
    id: "demo-other-1",
    name: "[Приклад] Подовжувач 3 м",
    description: "Демонстраційна картка товару. Замінити на реальний товар.",
    price: 129,
    category: "other",
    image: "assets/img-placeholder.svg",
    stock: 0,
    featured: false,
    sale: false
  }
];

// Форматування ціни: тільки гривня (₴), без доларів.
export function formatPrice(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return "—";
  return n.toLocaleString("uk-UA") + " ₴";
}

// Отримання списку товарів.
// Пріоритет: таблиця products у Supabase; якщо недоступно —
// локальні демо-дані (щоб GitHub Pages завжди щось показував).
let cachedProducts = null; // кеш на час перегляду сторінки

export async function getProducts() {
  if (cachedProducts) return cachedProducts;

  if (isSupabaseConfigured) {
    try {
      const sb = await getSupabase();
      const { data, error } = await sb
        .from("products")
        .select("*")
        .order("created_at", { ascending: false });
      if (!error && Array.isArray(data) && data.length > 0) {
        cachedProducts = data;
        return cachedProducts;
      }
    } catch (err) {
      console.warn("Supabase products load failed, fallback to demo:", err);
    }
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
