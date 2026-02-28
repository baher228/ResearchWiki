from bs4 import BeautifulSoup

html = """
<p>Intro</p>
<h2>Sec 1</h2>
<p>Text 1</p>
<div class="wiki-figure right"><img src="img1.png"></div>
<h2>Sec 2</h2>
<p>Text 2</p>
"""
soup = BeautifulSoup(html, "html.parser")

# wrap sections
current_section = soup.new_tag("div", attrs={"class": "wiki-section"})
elements = list(soup.body.children) if soup.body else list(soup.children)
print("done")
