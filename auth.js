// ============================================================
// auth.js — Supabase Authentication для сайту «Сателіт»
// Справжня авторизація: email/пароль + офіційний Google OAuth
// через Supabase (redirect-флоу). Жодних фальшивих кнопок.
// Доки supabase.js не містить реальних ключів, усі функції
// кидають помилку "DEMO_MODE" — сторінки показують сумне
// українське повідомлення замість падіння.
// ============================================================

import { getSupabase, isSupabaseConfigured } from "./supabase.js";

// Переклад технічних помилок Supabase на людську українську.
// Користувач НИКОЛИ не бачить stack trace чи англійський код помилки.
export function translateAuthError(err) {
  const raw = (err && (err.message || err.error_description || "")) || "";
  const m = raw.toLowerCase();
  if (m.includes("invalid login credentials"))
    return "Неправильна email-адреса або пароль.";
  if (m.includes("email not confirmed"))
    return "Email ще не підтверджено. Перевірте пошту.";
  if (m.includes("already registered") || m.includes("already exists"))
    return "Ця email-адреса вже використовується.";
  if (m.includes("user not found"))
    return "Користувача з такою адресою не знайдено.";
  if (m.includes("rate limit") || m.includes("too many"))
    return "Забагато спроб. Зачекайте трохи та повторіть.";
  if (m.includes("password"))
    return "Пароль не відповідає вимогам (мінімум 6 символів).";
  console.error("Auth error:", err); // технічна інформація — лише в консоль
  return "Сталася помилка авторизації. Спробуйте ще раз пізніше.";
}

// ---------- Публічний API (використовують login/register/account) ----------

export async function signUpWithEmail(email, password) {
  const sb = await getSupabase(); // кине DEMO_MODE, якщо не налаштовано
  const { data, error } = await sb.auth.signUp({ email, password });
  if (error) throw error;
  return data;
}

export async function signInWithEmail(email, password) {
  const sb = await getSupabase();
  const { data, error } = await sb.auth.signInWithPassword({ email, password });
  if (error) throw error;
  return data;
}

// Офіційний Google sign-in через Supabase. Після входу
// Supabase повертає на auth/callback.html.
export async function signInWithGoogle() {
  const sb = await getSupabase();
  const base = window.location.origin + window.location.pathname.replace(/[^/]*$/, "");
  const { error } = await sb.auth.signInWithOAuth({
    provider: "google",
    options: { redirectTo: base + "auth/callback.html" }
  });
  if (error) throw error;
  // Якщо все гаразд — браузер зараз перейде на Google.
}

export async function signOutUser() {
  if (!isSupabaseConfigured) return;
  const sb = await getSupabase().catch(() => null);
  if (!sb) return;
  await sb.auth.signOut();
}

// Поточний користувач (null, якщо не ввійшов або демо-режим).
export async function getCurrentUser() {
  if (!isSupabaseConfigured) return null;
  const sb = await getSupabase().catch(() => null);
  if (!sb) return null;
  const { data } = await sb.auth.getSession();
  return data.session ? data.session.user : null;
}

// Підписка на зміни стану входу: callback(user|null).
export function onAuthChange(callback) {
  if (!isSupabaseConfigured) {
    callback(null);
    return () => {};
  }
  let unsubscribe = () => {};
  getSupabase()
    .then((sb) => {
      const { data } = sb.auth.onAuthStateChange((_event, session) => {
        callback(session ? session.user : null);
      });
      unsubscribe = data.subscription ? data.subscription.unsubscribe : () => {};
    })
    .catch(() => callback(null));
  return () => unsubscribe();
}
