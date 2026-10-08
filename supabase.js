// ============================================================
// supabase.js — підключення Supabase (бекенд сайту «Сателіт»)
// ------------------------------------------------------------
// Supabase замінює Firebase: авторизація (email/пароль + Google),
// таблиця products (каталог) і таблиця orders (замовлення).
//
// НЕБЕЗПЕКА: сюди вставляється ТІЛЬКИ anon-ключ.
// service_role key і Google Client Secret — НИКОЛИ у фронтенді!
// Реальний захист даних — Row Level Security (supabase-setup.sql).
// ============================================================

export const SUPABASE_URL = "https://ncxsjavfvugkttfmcitr.supabase.co";
export const SUPABASE_ANON_KEY =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5jeHNqYXZmdnVna3R0Zm1jaXRyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTE0MjEwODMsImV4cCI6MjEwNjk5NzA4M30.AAMVaAHLgFtCft-BJHIwjdiyfQTwoooKs-cdj-Cozak";

// Ключі OAuth Google (створюються на console.cloud.google.com):
// CLIENT_ID — публічний, можна у фронтенді.
// SECRET — тільки в налаштуваннях Supabase, НІКОЛИ сюди!
export const GOOGLE_CLIENT_ID = "ВСТАВТЕ_GOOGLE_CLIENT_ID"; // ...apps.googleusercontent.com

// Прапорець: чи реальні дані вже вставлено.
export const isSupabaseConfigured =
  !SUPABASE_URL.includes("ВСТАВТЕ") && !SUPABASE_ANON_KEY.includes("ВСТАВТЕ");

// Динамічне підключення SDK через CDN (стабільно для GitHub Pages,
// не потребує npm/збірки). Версія зафіксована.
async function initSupabase() {
  if (!isSupabaseConfigured) return null;
  try {
    const mod = await import(
      "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm"
    );
    return mod.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
  } catch (err) {
    console.error("Supabase init failed:", err);
    return null;
  }
}

// Єдиний «прохід» до клієнта для всіх модулів.
export const supabaseReady = initSupabase();

// Зручна обгортка: отримати клієнт або помилку «не підключено».
export async function getSupabase() {
  const client = await supabaseReady;
  if (!client) throw new Error("DEMO_MODE");
  return client;
}
