# Tech Stack: orchast_agent Documentation Website

## Chosen Stack
- **Static Site Generator**: [MkDocs](https://www.mkdocs.org/)
- **Theme**: [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- **Deployment**: GitHub Actions $\rightarrow$ GitHub Pages
- **Content Format**: Markdown

## Justification
1. **Simplicity**: MkDocs uses a single configuration file (`mkdocs.yml`) and standard Markdown files for content, making it extremely easy for contributors to add documentation without knowing HTML/CSS or complex frameworks.
2. **Professionalism**: The Material theme is widely recognized as one of the best documentation themes available, providing excellent search, navigation, and responsive design out-of-the-box.
3. **GitHub Pages Integration**: MkDocs has native support for GitHub Pages (`gh-pages` branch), and automation via GitHub Actions is straightforward.
4. **Performance**: As a static site generator, it produces lightweight HTML files that load nearly instantaneously.
5. **Consistency**: Since the project likely uses Python, using a Python-based documentation tool (MkDocs) keeps the toolchain consistent.

## Tooling & Commands
- **Installation**: `pip install mkdocs-material`
- **Local Preview**: `mkdocs serve`
- **Build Site**: `mkdocs build`
- **Deployment**: `mkdocs gh-deploy` (or via GitHub Action)
