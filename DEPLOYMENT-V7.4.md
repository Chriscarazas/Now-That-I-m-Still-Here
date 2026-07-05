# V7.4 Deployment Instructions

## GitHub Pages deployment

1. Back up the currently deployed repository or create a release branch.
2. Replace the repository contents with the contents of this V7.4 package.
3. Confirm that `CNAME` still contains the intended custom domain.
4. Commit the files.
5. Push to the branch configured for GitHub Pages, normally `main`.
6. In GitHub, open **Settings → Pages** and confirm the correct source branch and root directory.
7. Allow GitHub Pages to publish, then open `https://chriscarazas.com` in a private browser window.

## Post-deployment checks

Run these checks after the new build is live:

- Hard-refresh the homepage so `site.css?v=7.4` and `site.js?v=7.4` load.
- Resize the browser slowly through 1440, 1100, 900, 800, 701, 700, 560, and 390 px.
- Confirm each art hero keeps its artwork within the hero.
- Open the mobile menu and test outside click, link selection, Escape, and widening beyond 900 px.
- Confirm Katie handwriting and the capital J are fully visible.
- Confirm field notes do not overlap captions or buttons.
- Confirm the footer email opens `mailto:chris@chriscarazas.com`.
- Test Book, Buy, Writing, Gazette, Reviews, Podcasts, About, Sample, Press, Katie Archive, Meet Katie, and Meet Shadow routes.
- Run a Lighthouse mobile audit for performance, accessibility, best practices, and SEO.
- Submit the existing sitemap in Google Search Console if the deployment changes indexed metadata.

## Local validation

From the project root:

```bash
python3 scripts/audit_site.py
python3 -m http.server 8000
```

Then open `http://localhost:8000`.
