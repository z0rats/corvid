---
title: Email Search
description: Find which mail providers a username is registered at.
---

Checks a username against roughly two dozen mail providers (Gmail, Yandex, Fastmail, and more)
using a mix of SMTP probing, provider APIs, registration-form probing, and headless-browser
checks, streamed over live progress. SMTP and headless-browser checkers are opt-in via settings,
since they need network conditions (outbound TCP/25, a downloaded headless Chromium) that aren't
available in every deployment.
