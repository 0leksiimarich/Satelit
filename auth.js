// ============================================================
// auth.js — авторизація сайту «Сателіт» через власний бекенд
// Email + одноразовий код з пошти. Без Google.
// ============================================================

import {
  sendOtp, signUpWithEmail, signInWithEmail, signOutUser, getCurrentUser,
  getMyOrders, translateAuthError, isBackendConfigured
} from "./backend.js";

export { signOutUser, getCurrentUser, getMyOrders, isBackendConfigured };
export { translateAuthError };

export async function requestCode(email, purpose) {
  return sendOtp(email, purpose);   // purpose: "register" | "login"
}

export async function register
