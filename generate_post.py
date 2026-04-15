import anthropic
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import json
import os
import subprocess

SITE_URL = "https://topicallyrandom.github.io/Jablog"
JABLON_SEARCHES = [
    "https://www.samueljablon.com",
    "https://brooklynrail.org/?s=jablon",
]

def scrape_jablon_news():
    print("Searching for Sam Jablon news...")
    results = []
    try:
        r = requests.get("https://www.samueljablon.com", timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text(separator="\n", strip=True)[:2000]
        results.append(f"FROM samueljablon.com:\n{text}")
    except Exception as e:
        print(f"Jablon site error: {e}")

    try:
        r = requests.get("https://www.artsy.net/artist/samuel-jablon", timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text(separator="\n", strip=True)[:1500]
        results.append(f"FROM artsy.net:\n{text}")
    except Exception as e:
        print(f"Artsy error: {e}")

    return "\n\n".join(results) if results else "No live data retrieved."

def read_past_posts():
    past = []
    if not os.path.exists("posts"):
        return past
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    for fname in files[:12]:
        try:
            with open(f"posts/{fname}", "r") as f:
                soup = BeautifulSoup(f.read(), "html.parser")
                title = soup.find("h1")
                body = soup.find("div", class_="body")
                meta = soup.find("div", class_="post-meta")
                if title and body:
                    past.append({
                        "date": meta.get_text(strip=True) if meta else fname,
                        "title": title.get_text(strip=True),
                        "excerpt": body.get_text(separator=" ", strip=True)[:600]
                    })
        except Exception as e:
            print(f"Could not read {fname}: {e}")
    return past

def count_posts():
    try:
        files = [f for f in os.listdir("posts") if f.endswith(".html")]
        return len(files) + 1
    except:
        return 1

def generate_post(jablon_context, today_str, past_posts, dispatch_num):
    print("Generating Jablog post...")
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    past_context = ""
    if past_posts:
        past_context = "PAST JABLOG POSTS (reference these — agree, contradict, spiral, callback, become increasingly self-aware):\n\n"
        for p in past_posts:
            past_context += f"Date: {p['date']}\nTitle: {p['title']}\nExcerpt: {p['excerpt']}\n\n"

    # Escalating instability based on dispatch number
    if dispatch_num < 20:
        tone = "enthusiastic and earnest, clearly a fan but still mostly coherent. Occasionally a thought runs long."
    elif dispatch_num < 50:
        tone = "increasingly obsessive. Some posts are at strange hours. References to previous posts starting to appear. The writer is starting to wonder about themselves."
    elif dispatch_num < 100:
        tone = "deeply unhinged devotion, 3am energy, conspiracy-adjacent theories about Jablon's work and its significance, self-referential loops, occasional all-caps. Still brilliant but clearly something has happened to this person."
    else:
        tone = "full conspiracy mode. The blog has become self-aware. The writer believes Jablon's paintings contain encoded messages. References previous posts as sacred texts. The word LUCK appears too often. The writer and Jablon have merged somehow."

    prompt = f"""Today is {today_str}. This is dispatch number {dispatch_num} of Jablog — an obsessive fan blog entirely devoted to Sam Jablon (b. 1986, Binghamton NY), New York painter and poet whose work oscillates between legibility and illegibility, who was mentored by Anne Waldman, Amiri Baraka, Vito Acconci and Bob Holman, who got his MFA at Brooklyn College (where they told him to stop making word paintings and he didn't), whose recent show "Luck or Else" is at Morgan Presents, and whose paintings include titles like: Luck, Easy Lover, Oy Vey, Mischief, Pleasure, Or Else, Don't Panic, Desire, Endless Passion, Innocent Culprit, Emit Time, Good Ol Days, VICIOUSSS, Joker Lover Devil, Time, Linger Longer, Fine As Wine, Loving It, Unstung.

Here is whatever was found about Jablon online today (use it if relevant, ignore if stale):
{jablon_context}

{past_context}

The tone for this dispatch should be: {tone}

Write a blog post that:
- Is entirely about Sam Jablon — his paintings, his practice, his words, his significance, his palette, the specific canvases, the poems, the mentors, the shows
- Draws on real details: the specific painting titles, dimensions, exhibitions, institutions, the Brooklyn Rail reviews, the BOMB Magazine piece, the Wall Street Journal review
- If past posts exist, references them with increasing self-awareness — the blog is becoming a document of its own obsession
- Uses the specific escalating tone described above
- Never uses bullet points — only flowing, sometimes runaway prose
- Is between 600-900 words
- The title should feel like something the writer typed quickly and did not reconsider

Return ONLY a JSON object with no markdown, no backticks:
{{
  "title": "the post title",
  "subtitle": "a one-sentence subtitle",
  "body_html": "the full post body as HTML — only <p> tags and <em> for italics. No other tags except <a href=\\"url\\"> for links."
}}"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)

def build_post_html(post_data, date_str, dispatch_num):
    title = post_data["title"]
    subtitle = post_data["subtitle"]
    body_html = post_data["body_html"]
    body_html = body_html.replace("<p>", '<p class="first-p">', 1).replace('class="first-p"', 'class="first-p"', 1)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — Jablog</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IM+Fell+English:ital@0;1&family=Inconsolata:wght@300;400;700&family=Crimson+Text:ital,wght@0,400;0,600;1,400;1,600&display=swap" rel="stylesheet">
<style>
  *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
  :root{{--bg:#f9f6ef;--ink:#1a1814;--red:#8b1a1a;--faded:#9a9488;--rule:#ccc8be}}
  body{{background:var(--bg);color:var(--ink);font-family:'Crimson Text',serif;font-size:19px;line-height:1.7;min-height:100vh}}
  .masthead{{text-align:center;padding:2.5rem 2rem 1.5rem;border-bottom:1px solid var(--rule)}}
  .masthead::before{{content:'';display:block;height:4px;background:repeating-linear-gradient(90deg,var(--ink) 0,var(--ink) 8px,transparent 8px,transparent 16px);margin-bottom:2rem}}
  .blog-title{{font-family:'IM Fell English',serif;font-size:clamp(3rem,10vw,6rem);line-height:.85;letter-spacing:-.03em}}
  .blog-title span{{color:var(--red);font-style:italic}}
  .masthead a{{text-decoration:none;color:inherit}}
  article{{max-width:660px;margin:0 auto;padding:3rem 2rem 6rem}}
  .post-meta{{font-family:'Inconsolata',monospace;font-size:.68rem;letter-spacing:.14em;text-transform:uppercase;color:var(--faded);margin-bottom:1.5rem}}
  h1{{font-family:'IM Fell English',serif;font-size:clamp(1.8rem,4vw,2.6rem);line-height:1.1;margin-bottom:.6rem;font-weight:400}}
  .subtitle{{font-family:'Crimson Text',serif;font-style:italic;font-size:1.15rem;color:var(--faded);margin-bottom:2.5rem;line-height:1.4}}
  hr{{border:none;border-top:1px solid var(--rule);margin:2rem 0}}
  .body p{{margin-bottom:1.5rem;font-size:1.05rem;line-height:1.75}}
  .body p.first-p::first-letter{{font-family:'IM Fell English',serif;font-size:4.5rem;font-weight:400;float:left;line-height:.75;margin:.05em .08em 0 0;color:var(--red)}}
  .body a{{color:var(--red);text-decoration:none;border-bottom:1px solid var(--red)}}
  .body em{{font-style:italic}}
  .back{{display:inline-block;margin-top:3rem;font-family:'Inconsolata',monospace;font-size:.7rem;letter-spacing:.1em;text-transform:uppercase;color:var(--faded);text-decoration:none;border-bottom:1px solid var(--rule);padding-bottom:2px}}
  .back:hover{{color:var(--red);border-color:var(--red)}}
  footer{{text-align:center;padding:2rem;font-family:'Inconsolata',monospace;font-size:.62rem;letter-spacing:.1em;color:var(--faded);border-top:1px solid var(--rule)}}
</style>
</head>
<body>
<div class="masthead">
  <a href="../index.html"><div class="blog-title">Jab<span>log</span></div></a>
</div>
<article>
  <div class="post-meta">{date_str} &nbsp;·&nbsp; Dispatch No. {dispatch_num}</div>
  <h1>{title}</h1>
  <p class="subtitle">{subtitle}</p>
  <hr>
  <div class="body">{body_html}</div>
  <a href="../index.html" class="back">&larr; All dispatches</a>
</article>
<footer>Jablog &mdash; Words on the Painter of Words &mdash; {SITE_URL}</footer>
</body>
</html>"""

def update_index(date_str, slug, title, time_str):
    with open("index.html", "r") as f:
        content = f.read()

    new_item = f"""    <div class="post-row">
      <div class="post-time">{date_str} &nbsp;·&nbsp; {time_str}</div>
      <div><a href="posts/{slug}.html" class="post-title-link">{title}</a></div>
    </div>
"""
    marker = "<!-- NEW POSTS GO HERE -->"
    content = content.replace(marker, marker + "\n" + new_item)
    with open("index.html", "w") as f:
        f.write(content)

def main():
    now = datetime.now(timezone.utc)
    today_str = now.strftime("%B %d, %Y")
    slug = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%-I:%M%p").lower()
    date_short = now.strftime("%b %d")

    if os.path.exists(f"posts/{slug}.html"):
        print(f"Post for {slug} already exists. Skipping.")
        return

    jablon_context = scrape_jablon_news()
    past_posts = read_past_posts()
    dispatch_num = count_posts()

    print(f"Dispatch #{dispatch_num}, {len(past_posts)} past posts loaded.")

    post_data = generate_post(jablon_context, today_str, past_posts, dispatch_num)

    os.makedirs("posts", exist_ok=True)
    post_html = build_post_html(post_data, today_str, dispatch_num)
    with open(f"posts/{slug}.html", "w") as f:
        f.write(post_html)
    print(f"Written posts/{slug}.html")

    update_index(date_short, slug, post_data["title"], time_str)
    print("Updated index.html")

    subprocess.run(["git", "config", "user.email", "action@github.com"])
    subprocess.run(["git", "config", "user.name", "Jablog Bot"])
    subprocess.run(["git", "add", f"posts/{slug}.html", "index.html"])
    subprocess.run(["git", "commit", "-m", f"Dispatch {dispatch_num}: {today_str}"])
    subprocess.run(["git", "push"])
    print("Pushed!")

if __name__ == "__main__":
    main()
