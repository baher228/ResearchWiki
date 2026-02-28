from bs4 import BeautifulSoup

html = """
<p><img src="1.png" alt="fig1"></p>
<p><img src="2b.png" alt="fig2b"><img src="2c.png" alt="fig2c"></p>
"""
soup = BeautifulSoup(html, "html.parser")

images = soup.find_all('img')
grouped_images = []

current_group = []
for img in images:
    if not current_group:
        current_group.append(img)
    else:
        prev_img = current_group[-1]
        p_curr = img.find_parent('p')
        p_prev = prev_img.find_parent('p')
        
        if p_curr and p_prev and p_curr == p_prev:
            current_group.append(img)
        elif p_curr and p_prev:
            curr_node = p_prev.next_sibling
            while curr_node and curr_node != p_curr:
                if curr_node.name and curr_node.name != 'br':
                    break
                curr_node = curr_node.next_sibling
            if curr_node == p_curr:
                current_group.append(img)
            else:
                grouped_images.append(current_group)
                current_group = [img]
        else:
            grouped_images.append(current_group)
            current_group = [img]
if current_group:
    grouped_images.append(current_group)

for group in grouped_images:
    insertion_node = group[0].find_parent('p') or group[0]
    
    # Optional parent wrapper if multiple
    if len(group) > 1:
        group_div = soup.new_tag("div", attrs={"class": "wiki-figure-group", "style": "display: flex; justify-content: center; gap: 1em; flex-wrap: wrap; margin: 1.5em auto;"})
        insertion_node.insert_before(group_div)
        container = group_div
    else:
        container = None
        
    for img in group:
        p = img.find_parent('p')
        img_width = 100 # mock
        style = f"width: {img_width}px;" if img_width else "width: max-content;"
        figure_div = soup.new_tag("div", attrs={"class": "wiki-figure center", "style": style})
        
        if container:
            container.append(figure_div)
            # clear figure margins for flex item
            figure_div['style'] += " margin: 0;"
        else:
            insertion_node.insert_before(figure_div)
            
        figure_div.append(img.extract())
        alt_text = img.get('alt', '').strip()
        if alt_text:
            caption_div = soup.new_tag("div", attrs={"class": "wiki-caption"})
            caption_div.string = alt_text
            figure_div.append(caption_div)
            
        if p and not p.get_text(strip=True) and not p.find('img'):
            p.decompose()

print(soup.prettify())
