# Shellui Marketplace threat model

Shellui Marketplace 0.9 is a public catalog. Listings are free. The service does not take payment and does not hold a session for directory visitors. Staff curate apps in Django admin.

## Catalog poisoning

A third party must not be able to publish an official app, a navigation item, or an `auth` capability by calling the API. The public API is read-only. `is_official`, capabilities, and the navigation template are staff fields.

Mitigations:

- Only `published` apps are returned. Unlisted apps are 404.
- On the way out, the service validates the navigation template again. A `javascript:` URL, an extra field, or `safeForAuthToken` on a third-party app withholds that app.
- The `auth` capability is rejected in model validation and in the admin form unless the app is official. The public payload drops `auth` unless the app is official, and it sets `safeForAuthToken` only when that capability is present.

Tests: `CatalogPoisoningTests` in `apps/catalog/tests/test_security.py`.

## Malicious navigation templates

`shellui add` copies `url`, `path`, `official`, and `safeForAuthToken` into `shellui.config.json`. A bad template could point the shell at an unexpected origin or ask for the session token.

Mitigations:

- The template is a fixed set of keys: `label`, `path`, `url`, `icon`, and optional `safeForAuthToken`.
- `url` is https. `http://localhost` is allowed only when `DEBUG` is true.
- Paths cannot contain `..`. Labels are plain text.
- `safeForAuthToken` requires an official app and the `auth` capability.
- Icons are an icon name, a site-relative path, or an https URL. Uploaded files are png, jpeg, webp, or gif (Django `ImageField`).

Tests: `UrlValidationTests`, `CapabilityValidationTests`, and `test_poisoned_navigation_url_is_withheld`.

## Stats spam

Install posts are public so the directory can ping them. A client could inflate counts.

Mitigations:

- Active installs are unique per app and subject hash. Repeating a post does not add another event.
- Anonymous subjects are `sha256(origin + install id)`. Signed-in subjects are `sha256(user sub)` from an Identity JWT verified by `shellui-django` (`decode_identity_rs256_jwt`). A bad token is 401, not an anonymous install.
- Posts without a Bearer token or an `installId` are accepted and not counted (`dedupe_key_required`), matching the directory client, which sends `{}`.
- Each IP is rate limited (default 30 per minute). The cache key is a hash of the address.
- The body must be `application/json` and may only contain `installId`. These two views are the only CSRF-exempt JSON posts.
- `Origin`, when present, must be `https://host[:port]`. Localhost http origins require `DEBUG`.

Tests: `StatsSpamAndPiiTests`.

## PII

Install stats do not need to know who someone is.

Mitigations:

- Rows store `subject_hash`, kind (`user` or `anonymous`), the app, and timestamps. They do not store the IP, the Origin header, the install id, the token, or the user id.
- Logs record the app slug and the kind, not the subject.
- Sentry is initialized with `send_default_pii=False`.
- Gunicorn access logs drop request headers, so an Authorization token is not written.

Tests: `test_anonymous_pings_dedupe_and_do_not_store_pii` and `test_signed_in_installs_dedupe_on_the_subject_hash`.
