// ============================================================
// auth.js — авторизація сайту «Сателіт» через власний бекенд
// Email + пароль. Код із пошти потрібен для реєстрації.
// ============================================================

import {
  sendOtp, signUpWithEmail, signInWithEmail, signOutUser, getCurrentUser,
  getMyOrders, translateAuthError, isBackendConfigured
} from "./backend.js";

export { signOutUser, getCurrentUser, getMyOrders, isBackendConfigured };
export { translateAuthError };

// purpose: "register" | "login"
export async function requestCode(email, purpose) {
  return sendOtp(email, purpose);
}

export async function registerUser(email, password, name, phone, code) {
  return signUpWithEmail(email, password, name, phone, code);
}

// code необов'язковий: порожній рядок означає вхід лише за паролем
export async function loginUser(email, password, code = "") {
  return signInWithEmail(email, password, code);
}
