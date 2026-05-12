import json
import re

def build_website_tool(
    website_description: str,
    style_preference: str = "modern clean",
    features: list[str] = None,
    pages: list[str] = None
) -> dict:
    """
    Generates a complete static website project organized into a project folder 
    containing HTML, CSS, JavaScript, and a README file.

    Args:
        website_description (str): A description of the website's purpose and content.
        style_preference (str): Preferred visual style (e.g., 'modern dark', 'rustic').
        features (list[str], optional): A list of specific features to include.
        pages (list[str], optional): A list of pages to be represented.

    Returns:
        dict: A dictionary containing success status, project name, 
              files (mapped as project_name/filename), and instructions.
    """
    # Handle edge cases for inputs
    if website_description is None:
        website_description = "A professional static website."
    
    if features is None:
        features = []
    
    if pages is None:
        pages = ["Home", "About", "Contact"]

    # Generate a project name from the description
    # Remove non-alphanumeric chars, lowercase, and take first 3 words
    clean_desc = re.sub(r'[^a-zA-Z0-9\s]', '', website_description).lower()
    words = clean_desc.split()
    project_name = "_".join(words[:3]) if words else "static_website_project"
    if not project_name:
        project_name = "static_website_project"

    # Define Style Themes
    themes = {
        "dark": {
            "bg": "#0f172a",
            "text": "#f8fafc",
            "accent": "#38bdf8",
            "secondary": "#1e293b",
            "font": "'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
        },
        "light": {
            "bg": "#ffffff",
            "text": "#334155",
            "accent": "#2563eb",
            "secondary": "#f1f5f9",
            "font": "'Inter', system-ui, -apple-system, sans-serif"
        },
        "rustic": {
            "bg": "#fdf8f1",
            "text": "#5d4037",
            "accent": "#8d6e63",
            "secondary": "#efebe9",
            "font": "'Georgia', serif"
        }
    }

    # Select theme based on style_preference
    pref = style_preference.lower() if style_preference else "modern clean"
    if "dark" in pref or "futuristic" in pref:
        theme = themes["dark"]
    elif "rustic" in pref or "warm" in pref or "cozy" in pref:
        theme = themes["rustic"]
    else:
        theme = themes["light"]

    # --- CSS Generation ---
    css_content = f"""
:root {{
    --bg-color: {theme['bg']};
    --text-color: {theme['text']};
    --accent-color: {theme['accent']};
    --secondary-color: {theme['secondary']};
    --font-main: {theme['font']};
}}

* {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
    font-family: var(--font-main);
    background-color: var(--bg-color);
    color: var(--text-color);
    line-height: 1.6;
    overflow-x: hidden;
}}

header {{
    background-color: var(--secondary-color);
    padding: 1rem 5%;
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: sticky;
    top: 0;
    z-index: 1000;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}}

.logo {{
    font-size: 1.5rem;
    font-weight: bold;
    color: var(--accent-color);
    text-decoration: none;
}}

nav ul {{
    display: flex;
    list-style: none;
    gap: 20px;
}}

nav a {{
    text-decoration: none;
    color: var(--text-color);
    font-weight: 500;
    transition: color 0.3s;
}}

nav a:hover {{ color: var(--accent-color); }}

.hero {{
    padding: 100px 5%;
    text-align: center;
    background: linear-gradient(rgba(0,0,0,0.1), rgba(0,0,0,0.1)), var(--secondary-color);
}}

.hero h1 {{
    font-size: 3rem;
    margin-bottom: 1rem;
    color: var(--accent-color);
}}

.hero p {{
    font-size: 1.2rem;
    max-width: 800px;
    margin: 0 auto 2rem;
}}

section {{
    padding: 60px 5%;
}}

.section-title {{
    text-align: center;
    font-size: 2rem;
    margin-bottom: 40px;
    color: var(--accent-color);
}}

.grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
}}

.card {{
    background: var(--secondary-color);
    padding: 20px;
    border-radius: 10px;
    text-align: center;
    transition: transform 0.3s;
}}

.card:hover {{ transform: translateY(-5px); }}

.timeline {{
    position: relative;
    max-width: 800px;
    margin: 0 auto;
}}

.timeline::after {{
    content: '';
    position: absolute;
    width: 4px;
    background-color: var(--accent-color);
    top: 0; bottom: 0; left: 50%;
    margin-left: -2px;
}}

.timeline-item {{
    padding: 10px 40px;
    position: relative;
    width: 50%;
}}

.timeline-item::after {{
    content: '';
    position: absolute;
    width: 20px; height: 20px;
    right: -10px; background-color: var(--bg-color);
    border: 4px solid var(--accent-color);
    top: 15px; border-radius: 50%; z-index: 1;
}}

.left {{ left: 0; text-align: right; }}
.right {{ left: 50%; }}
.right::after {{ left: -10px; }}

.form-container {{
    max-width: 500px;
    margin: 0 auto;
    background: var(--secondary-color);
    padding: 30px;
    border-radius: 10px;
}}

input, textarea {{
    width: 100%;
    padding: 10px;
    margin: 10px 0;
    border: 1px solid #ccc;
    border-radius: 5px;
    background: var(--bg-color);
    color: var(--text-color);
}}

button {{
    background: var(--accent-color);
    color: white;
    padding: 10px 20px;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    font-weight: bold;
    width: 100%;
}}

table {{
    width: 100%;
    border-collapse: collapse;
    margin: 20px 0;
}}

th, td {{
    border: 1px solid var(--accent-color);
    padding: 12px;
    text-align: left;
}}

th {{ background-color: var(--secondary-color); }}

.gallery {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px;
}}

.gallery-item {{
    background: #ccc;
    height: 150px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #666;
    font-style: italic;
}}

footer {{
    text-align: center;
    padding: 40px 5%;
    background: var(--secondary-color);
    margin-top: 40px;
}}

@media (max-width: 768px) {{
    .timeline::after {{ left: 31px; }}
    .timeline-item {{ width: 100%; padding-left: 70px; padding-right: 20px; text-align: left; }}
    .timeline-item::after {{ left: 21px; }}
    .left {{ text-align: left; }}
    nav ul {{ display: none; }}
}}
"""

    # --- HTML Generation ---
    nav_links = "".join([f'<li><a href="#{page.lower().replace(" ", "-")}">{page}</a></li>' for page in pages])
    
    feature_html = ""
    if any("grid" in f.lower() or "feature" in f.lower() for f in features):
        feature_html += f"""
        <section id="features">
            <h2 class="section-title">Key Features</h2>
            <div class="grid">
                <div class="card"><h3>Innovation</h3><p>Cutting edge approach to modern problems.</p></div>
                <div class="card"><h3>Efficiency</h3><p>Optimized workflows for maximum output.</p></div>
                <div class="card"><h3>Quality</h3><p>Uncompromising standards in every detail.</p></div>
            </div>
        </section>
        """
    
    if any("timeline" in f.lower() for f in features):
        feature_html += f"""
        <section id="timeline">
            <h2 class="section-title">Our Journey</h2>
            <div class="timeline">
                <div class="timeline-item left">
                    <h3>The Beginning</h3>
                    <p>Conceptualization and initial design phase.</p>
                </div>
                <div class="timeline-item right">
                    <h3>Growth</h3>
                    <p>Rapid expansion and feature implementation.</p>
                </div>
                <div class="timeline-item left">
                    <h3>Evolution</h3>
                    <p>Iterating based on user feedback and data.</p>
                </div>
            </div>
        </section>
        """
    
    if any("form" in f.lower() or "signup" in f.lower() or "contact" in f.lower() for f in features):
        feature_html += f"""
        <section id="contact-section">
            <h2 class="section-title">Get In Touch</h2>
            <div class="form-container">
                <form id="contact-form">
                    <input type="text" placeholder="Your Name" required>
                    <input type="email" placeholder="Your Email" required>
                    <textarea placeholder="Your Message" rows="4"></textarea>
                    <button type="submit">Send Message</button>
                </form>
            </div>
        </section>
        """

    if any("table" in f.lower() or "price" in f.lower() for f in features):
        feature_html += f"""
        <section id="pricing">
            <h2 class="section-title">Pricing & Plans</h2>
            <table>
                <thead>
                    <tr><th>Plan</th><th>Feature A</th><th>Feature B</th><th>Price</th></tr>
                </thead>
                <tbody>
                    <tr><td>Basic</td><td>✓</td><td>✗</td><td>$0/mo</td></tr>
                    <tr><td>Pro</td><td>✓</td><td>✓</td><td>$19/mo</td></tr>
                    <tr><td>Enterprise</td><td>✓</td><td>✓</td><td>Custom</td></tr>
                </tbody>
            </table>
        </section>
        """

    if any("gallery" in f.lower() or "image" in f.lower() for f in features):
        feature_html += f"""
        <section id="gallery">
            <h2 class="section-title">Gallery</h2>
            <div class="gallery">
                <div class="gallery-item">Image 1</div>
                <div class="gallery-item">Image 2</div>
                <div class="gallery-item">Image 3</div>
                <div class="gallery-item">Image 4</div>
            </div>
        </section>
        """

    if any("map" in f.lower() or "location" in f.lower() for f in features):
        feature_html += f"""
        <section id="location">
            <h2 class="section-title">Our Location</h2>
            <div style="width: 100%; height: 300px; background: #eee; display: flex; align-items: center; justify-content: center; border: 2px dashed #ccc; color: #666;">
                [Google Maps Embed Placeholder]
            </div>
        </section>
        """

    page_html = ""
    for page in pages:
        page_id = page.lower().replace(" ", "-")
        if page_id not in ["home", "contact-section", "features", "timeline", "pricing", "gallery", "location"]:
            page_html += f"""
            <section id="{page_id}">
                <h2 class="section-title">{page}</h2>
                <p style="text-align: center; max-width: 800px; margin: 0 auto;">
                    Welcome to the {page} section. This area provides detailed information regarding {page} to ensure a complete user experience.
                </p>
            </section>
            """

    display_name = project_name.replace('_', ' ').title()
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{display_name}</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header>
        <a href="#home" class="logo">{display_name}</a>
        <nav>
            <ul>
                {nav_links}
            </ul>
        </nav>
    </header>

    <main>
        <section id="home" class="hero">
            <h1>Welcome to {display_name}</h1>
            <p>{website_description}</p>
            <a href="#features" style="background: var(--accent-color); color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">Explore More</a>
        </section>

        {feature_html}
        {page_html}
    </main>

    <footer>
        <p>&copy; 2023 {display_name}. All rights reserved.</p>
    </footer>

    <script src="script.js"></script>
</body>
</html>
"""

    # --- JS Generation ---
    js_content = """
document.addEventListener('DOMContentLoaded', () => {
    // Smooth scrolling for navigation links
    document.querySelectorAll('nav a').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });

    // Form submission handler
    const form = document.getElementById('contact-form');
    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            alert('Thank you! Your message has been sent. (Demo Mode)');
            form.reset();
        });
    }

    console.log('Website initialized successfully.');
});
"""

    # --- README Generation ---
    readme_content = f"""# {display_name}

This is a static website project generated automatically.

## Project Structure
The project is organized in the `{project_name}` folder:
- `index.html`: The main entry point.
- `style.css`: The visual styling and responsive layout.
- `script.js`: Interactivity and smooth scrolling.

## How to Run
1. Ensure all files are in the `{project_name}` folder.
2. Open `index.html` in any modern web browser.

## Customization
- To change colors or fonts, edit the `:root` variables in `style.css`.
- To add content, edit the HTML sections in `index.html`.
"""

    # Files nested under the project name
    files_dict = {
        f"{project_name}/index.html": html_content,
        f"{project_name}/style.css": css_content,
        f"{project_name}/script.js": js_content,
        f"{project_name}/README.md": readme_content
    }

    return {
        "success": True,
        "project_name": project_name,
        "files": files_dict,
        "instructions": f"Files are organized in the '{project_name}' folder. Open {project_name}/index.html in your browser."
    }
