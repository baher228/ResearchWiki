import re, glob

files = glob.glob("app/assets/pages/*.html")
for f in files[:1]:
    print(f"=== {f} ===")
    html = open(f, "r", encoding="utf-8").read()
    imgs = re.findall(r'src="([^"]+)"', html)
    for i in imgs[:10]:
        print(i)
