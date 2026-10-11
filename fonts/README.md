# Profile typography

The profile uses Geist for display type, Inter for body copy, and Geist Mono for small metadata. Text is converted to SVG paths so GitHub renders the chosen typefaces consistently without loading remote fonts.

The original, unmodified font files come from [Google Fonts](https://github.com/google/fonts/tree/bd8f81ddb5c74d5c8897b36ad88b440266245103/ofl):

- [Geist](https://github.com/google/fonts/tree/bd8f81ddb5c74d5c8897b36ad88b440266245103/ofl/geist), licensed under [SIL OFL 1.1](Geist-OFL.txt).
- [Inter](https://github.com/google/fonts/tree/bd8f81ddb5c74d5c8897b36ad88b440266245103/ofl/inter), licensed under [SIL OFL 1.1](Inter-OFL.txt).
- [Geist Mono](https://github.com/google/fonts/tree/bd8f81ddb5c74d5c8897b36ad88b440266245103/ofl/geistmono), licensed under [SIL OFL 1.1](GeistMono-OFL.txt).

To regenerate the visual assets:

```sh
python -m pip install -r scripts/requirements.txt
python scripts/build_header.py
python scripts/update_stats.py
```
