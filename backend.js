// ============================================================
// backend.js — клієнт «Сателіт Backend» (власна заміна Firebase/Supabase)
// ============================================================

export const API_URL = "https://satelit-backend.onrender.com"; // ← впишіть URL з Render

const TOKEN_KEY = "satelit_token_v1";

export function isBackendConfigured() {
  return !API_URL.includes("ВАШ");
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}
export function setToken(t) {
  if (t) localStorage.setItem(TOKEN_KEY, t);
  else localStorage.removeItem(TOKEN_KEY);
}

async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  const token = getToken();
  if (token) headers["Authorization"] = "Bearer " + token;
  let resp;
  try {
    resp = await fetch(API_URL + path, { ...options, headers });
  } catch (err) {
    throw new Error("NETWORK");
  }
  let body = {};
  try { body = await resp.json(); } catch {}
  if (!resp.ok) {
    const e = new Error(body.detail || "SERVER");
    e.status = resp.status;
    throw e;
  }
  return body;
}

export async function sendOtp(email, purpose) {
  // purpose: "register" | "login" — надсилає одноразовий код на пошту
  return api("/api/auth/otp/send", {
    method: "POST",
    body: JSON.stringify({ email, purpose })
  });
}

export async function signUpWithEmail(email, password, name, phone, code) {
  const data = await api("/api/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, name, phone, code })
  });
  setToken(data.token);
  return data.user;
}

export async function signInWithEmail(email, password, code = "") {
  const data = await api("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password, code })
  });
  setToken(data.token);
  return data.user;
}

export async function signOutUser() {
  setToken(null);
  try { await api("/api/auth/logout", { method: "POST" }); } catch {}
}

export async function getCurrentUser() {
  if (!getToken()) return null;
  try {
    const data = await api("/api/auth/me");
    return data.user;
  } catch {
    setToken(null);
    return null;
  }
}

export async function getProductsFromBackend() {
  const data = await api("/api/products");
  return data.products || [];
}

export async function createOrder(order) {
  return api("/api/orders", { method: "POST", body: JSON.stringify(order) });
}

export async function getMyOrders() {
  const data = await api("/api/orders");
  return data.orders || [];
}

export function translateAuthError(err) {
  if (!err) return "Сталася помилка авторизації. Спробуйте ще раз пізніше.";
  if (err.message === "NETWORK")
    return "Сервер недоступний. Перевірте інтернет або повторіть спробу пізніше.";
  if (typeof err.message === "string" && /[А-Яа-яЄєІіЇїҐґ]/.test(err.message))
    return err.message; // сервер уже повертає зрозуміле українською
  console.error("Auth error:", err);
  return "Сталася помилка авторизації. Спробуйте ще раз пізніше.";
}

// ---------- Пошта служби підтримки та імпорт товарів (адмін) ----------
export const SUPPORT_EMAIL = "satelit-magazin@ukr.net";

export async function importProductsTable(file, useAi = true) {
  const form = new FormData();
  form.append("file", file);
  const token = getToken();
  let resp;
  try {
    resp = await fetch(`${API_URL}/api/admin/products/import?use_ai=${useAi ? 1 : 0}`, {
      method: "POST",
      headers: token ? { Authorization: "Bearer " + token } : {},
      body: form
    });
  } catch {
    throw new Error("NETWORK");
  }
  let body = {};
  try { body = await resp.json(); } catch {}
  if (!resp.ok) {
    const e = new Error(body.detail || "SERVER");
    e.status = resp.status;
    throw e;
  }
  return body;
}
