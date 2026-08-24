# M4 UI language policy (decision record)

M4’s eventual public interface will use **Mongolian as the default language**. English will be an optional complete interface language. The brand `M4` remains unchanged between languages.

Future user-facing strings must be externalized rather than hard-coded into components. The intended future structure is:

```text
web/locales/mn.json
web/locales/en.json
```

Official Mongolian economic terminology should be preferred over literal machine translation. English terminology may appear in tooltips where it improves discoverability. Equations, data keys, snapshot identifiers and internal code identifiers remain language-neutral. No localization code is implemented in Phase 1A.
