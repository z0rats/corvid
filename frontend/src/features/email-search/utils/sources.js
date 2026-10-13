// The two Email Search tools. mailcat probes a *username* at mail providers; user_scanner takes a
// full address and asks ~150 services whether it has an account (and what the profile says).
export const EMAIL_SOURCES = ['mailcat', 'user_scanner'];

export const isFullEmail = (value) => /^[^@\s]+@[^@\s]+\.[^@\s]{2,}$/.test(value);
