# AI-Generated Books Web Platform Goals

Build a production-ready website for `prof-lijar/ai-generated-books-web` that hosts and lets users read books from:
`https://github.com/prof-lijar/ai-generated-books`

## Core objective

Create a public web app where visitors can browse available books and read each book in an in-browser PDF viewer.

## Functional requirements

1. Source books from the `ai-generated-books` repository.
2. Provide a books library page showing all available books.
3. For each book, provide a dedicated reader page with embedded PDF viewing.
4. PDF viewer must support:
   - next/previous page navigation
   - zoom in/out
   - fit to width
   - download PDF
   - open PDF in new tab
5. Add search/filter on the library page by title and/or filename.
6. Include loading, empty, and error states for robustness.

## Product constraints

1. Mobile-friendly and desktop-friendly responsive UI.
2. Keep implementation simple, maintainable, and fast to ship.
3. Use practical defaults; avoid over-engineering.
4. Ensure PDFs are served in a way that works reliably in production.

## Delivery requirements

1. Include README instructions for setup, local run, and deployment.
2. Add basic CI checks and tests for critical paths.
3. Deploy-ready output (suitable for Vercel/Netlify/Fly or equivalent).

## Definition of done

1. Deployed site publicly accessible.
2. Library page lists books from the source repository.
3. Selecting a book opens a working in-browser PDF viewer.
4. Build and test steps pass in CI.
