K Learning Assistant Goals

Build a production-ready web-based study platform for `prof-lijar/tiny-company` that helps Korean language learners prepare for the TOPIK exam.

## Core objective

Create a public learning app where users can study TOPIK vocabulary, grammar, reading, writing, and mock tests in one simple, focused platform.

The product should feel useful for real learners, not just like a demo. It should be easy to use, mobile-friendly, and practical for daily study.

## Functional requirements

1. Provide a clear home page explaining what the TOPIK Learning Assistant does.
2. Provide vocabulary study features organized by TOPIK level.
3. Include spaced repetition support for vocabulary review.
4. Provide grammar lessons organized by TOPIK level.
5. Provide reading comprehension practice with questions and answers.
6. Provide writing practice where users can write Korean responses.
7. Add AI-powered writing feedback when available.
8. Provide a mock test simulator that resembles the TOPIK IBT experience.
9. Include a progress tracking dashboard showing:

   * vocabulary progress
   * grammar progress
   * reading practice progress
   * writing practice progress
   * mock test results
10. Include loading, empty, and error states for important screens.
11. Make navigation simple so users can quickly continue studying.

## Product constraints

1. Mobile-friendly and desktop-friendly responsive UI.
2. Keep implementation simple, maintainable, and fast to ship.
3. Use practical defaults; avoid over-engineering.
4. Store study content in a simple structure that can be expanded later.
5. Make the product useful even before advanced backend features are added.
6. Avoid features that require heavy infrastructure unless they are clearly necessary.
7. Prioritize learner experience over technical complexity.

## Content requirements

1. Organize all learning materials by TOPIK level when possible.
2. Use beginner-friendly explanations for grammar.
3. Keep vocabulary entries clear and consistent.
4. Reading practice should include short passages and comprehension questions.
5. Writing practice should include realistic TOPIK-style prompts.
6. Mock tests should be structured enough to feel like exam preparation.

## Technical requirements

1. Use the existing Next.js + TypeScript + Tailwind CSS product structure.
2. Keep reusable UI components in the product component system.
3. Keep data, types, and utilities organized under the product library structure.
4. Ensure the app builds successfully for production deployment.
5. Maintain clean TypeScript types for study content, user progress, and test data.
6. Add basic tests for critical user paths where practical.
7. Keep deployment suitable for Vercel or equivalent platforms.

## Delivery requirements

1. Include README instructions for setup, local run, and deployment.
2. Add or maintain basic CI checks for build, lint, and tests.
3. Ensure the deployed site is publicly accessible.
4. Keep documentation updated when major features or structure change.
5. Make sure the app can be run locally with simple commands.

## Definition of done

1. Deployed site publicly accessible.
2. Home page clearly explains the TOPIK Learning Assistant.
3. Users can study vocabulary by TOPIK level.
4. Users can view grammar lessons by TOPIK level.
5. Users can complete reading comprehension practice.
6. Users can use writing practice and receive feedback when available.
7. Users can take a mock TOPIK-style test.
8. Users can see study progress in a dashboard.
9. The app works on mobile and desktop.
10. Build and test steps pass in CI.
11. README contains clear local development and deployment instructions.
K Learning Assistant Goals

Build a production-ready web-based study platform for `prof-lijar/tiny-company` that helps Korean language learners prepare for the TOPIK exam.

## Core objective

Create a public learning app where users can study TOPIK vocabulary, grammar, reading, writing, and mock tests in one simple, focused platform.

The product should feel useful for real learners, not just like a demo. It should be easy to use, mobile-friendly, and practical for daily study.

## Functional requirements

1. Provide a clear home page explaining what the TOPIK Learning Assistant does.
2. Provide vocabulary study features organized by TOPIK level.
3. Include spaced repetition support for vocabulary review.
4. Provide grammar lessons organized by TOPIK level.
5. Provide reading comprehension practice with questions and answers.
6. Provide writing practice where users can write Korean responses.
7. Add AI-powered writing feedback when available.
8. Provide a mock test simulator that resembles the TOPIK IBT experience.
9. Include a progress tracking dashboard showing:

   * vocabulary progress
   * grammar progress
   * reading practice progress
   * writing practice progress
   * mock test results
10. Include loading, empty, and error states for important screens.
11. Make navigation simple so users can quickly continue studying.

## Product constraints

1. Mobile-friendly and desktop-friendly responsive UI.
2. Keep implementation simple, maintainable, and fast to ship.
3. Use practical defaults; avoid over-engineering.
4. Store study content in a simple structure that can be expanded later.
5. Make the product useful even before advanced backend features are added.
6. Avoid features that require heavy infrastructure unless they are clearly necessary.
7. Prioritize learner experience over technical complexity.

## Content requirements

1. Organize all learning materials by TOPIK level when possible.
2. Use beginner-friendly explanations for grammar.
3. Keep vocabulary entries clear and consistent.
4. Reading practice should include short passages and comprehension questions.
5. Writing practice should include realistic TOPIK-style prompts.
6. Mock tests should be structured enough to feel like exam preparation.

## Technical requirements

1. Use the existing Next.js + TypeScript + Tailwind CSS product structure.
2. Keep reusable UI components in the product component system.
3. Keep data, types, and utilities organized under the product library structure.
4. Ensure the app builds successfully for production deployment.
5. Maintain clean TypeScript types for study content, user progress, and test data.
6. Add basic tests for critical user paths where practical.
7. Keep deployment suitable for Vercel or equivalent platforms.

## Delivery requirements

1. Include README instructions for setup, local run, and deployment.
2. Add or maintain basic CI checks for build, lint, and tests.
3. Ensure the deployed site is publicly accessible.
4. Keep documentation updated when major features or structure change.
5. Make sure the app can be run locally with simple commands.

## Definition of done

1. Deployed site publicly accessible.
2. Home page clearly explains the TOPIK Learning Assistant.
3. Users can study vocabulary by TOPIK level.
4. Users can view grammar lessons by TOPIK level.
5. Users can complete reading comprehension practice.
6. Users can use writing practice and receive feedback when available.
7. Users can take a mock TOPIK-style test.
8. Users can see study progress in a dashboard.
9. The app works on mobile and desktop.
10. Build and test steps pass in CI.
11. README contains clear local development and deployment instructions.
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


