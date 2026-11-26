# Brewric/.github

[`profile/README.md`](profile/README.md) is the page at [github.com/Brewric](https://github.com/Brewric).

`tools/build.py` draws the images in `profile/assets`, each in a light and a dark version, from
brewric.com's colours, type and mark. Text in them is drawn as outlines, so it needs DM Sans from
Google Fonts (`DMSans[opsz,wght].ttf`) and fontTools:

```bash
python3 tools/build.py --fonts DIR
```

The benchmark numbers come from `results/published/summary.json` in
[Brewric/benchmarks](https://github.com/Brewric/benchmarks). Change them together.
