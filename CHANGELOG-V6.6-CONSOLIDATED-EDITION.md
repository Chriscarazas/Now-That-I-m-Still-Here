# V6.6 Consolidated Edition

## Publication system
- Added `data/site.json` as the canonical source for navigation and primary plate order.
- Added `scripts/build_site.py` to generate the shared header, footer, breadcrumbs, plate labels, publication metadata, and structured data.
- Standardized the primary plate ledger from Plate 01 through Plate 12.
- Standardized the fixed header and Get the Book action across the full site.

## Editorial and conversion
- Tightened the Home premise copy and simplified the primary action hierarchy to Buy Direct, Read a Sample, and Other Retailers.
- Added an owned sample page containing the opening of the memoir and a clear path into the Book and Buy pages.
- Added book facts, formats, ISBNs, campaign terms, and reader proof near the purchase routes.
- Clarified the Road to 2,000 public record, current total, calculation method, and campaign-linked purchase routes.
- Added funnel event hooks for sample, book, buy, retailer, signed-copy, and subscription actions.

## Owned content and SEO
- Added internal pages for The Diagnosis Ceremony, Losing Your Identity After Loss, and the latest Gazette edition.
- Updated the Writing feed to prefer same-domain preview pages while retaining the Substack source link.
- Expanded Book, Product, Person, Article, CollectionPage, and breadcrumb structured data.
- Corrected the Table of Plates schema and removed duplicate breadcrumb markup.
- Rebuilt the XML and image sitemaps.
- Added responsive AVIF variants for major hero art.

## Visual consistency
- Consolidated hero behavior into full, split, and compact systems.
- Consolidated imagery into cinematic, museum plate, physical artifact, and contact-sheet treatments.
- Restricted Victorian drop caps to narrative prose.
- Standardized edition ornaments, plate captions, paper hierarchy, and metadata.
- Rebuilt the About hero as a true full-bleed cinematic image.
- Rebalanced the Road hero for legibility, contrast, and consistent depth.

## Code cleanup
- Moved the editable stylesheet to `styles/site-source.css`.
- Added `scripts/build_css.cjs` to remove unused selectors, exact duplicate rules, and unused keyframes from the production stylesheet.
- Removed legacy hero, navigation, and drop-cap rule clusters.
- Reduced production CSS from the audited V6.5 baseline of roughly 174 KB, 2,446 lines, 92 media-query blocks, and 343 `!important` declarations to roughly 114 KB, 1,294 lines, 69 media-query blocks, and 125 `!important` declarations.
- Added `scripts/audit_site.py` for HTML, navigation, assets, anchors, structured data, feed, sitemap, email, and stylesheet validation.

## Feed resilience
- Preserved the scheduled Substack refresh workflow.
- Added validation, retries, same-domain preview mapping, atomic cache replacement, and last-known-good preservation.
- Retained static HTML cards as the final fallback.
