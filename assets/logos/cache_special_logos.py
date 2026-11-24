"""Cache only the five approved historical source images; never substitute a current mark."""
import io
import json
from pathlib import Path
import urllib.request
from PIL import Image

root = Path(__file__).resolve().parent
manifest = json.loads((root / "special-logo-sources.json").read_text())
failed = []
for name, urls in manifest.items():
    target = root / name
    if target.exists():
        with Image.open(target) as im:
            im.verify()
        continue
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; CourtsideArchive/1.0)", "Accept": "image/png,image/*"})
            with urllib.request.urlopen(req, timeout=30) as response:
                raw = response.read(5_000_000)
            with Image.open(io.BytesIO(raw)) as im:
                im.load()
                if min(im.size) < 40:
                    raise ValueError("Unexpectedly small image")
                im = im.convert("RGBA")
                im.thumbnail((500,500))
                im.save(target, "PNG")
            print(f"Cached {name} from {url}", flush=True)
            break
        except Exception as err:
            print(f"{name}: {url}: {err}", flush=True)
    else:
        failed.append(name)
print("Uncached:", failed, flush=True)
if failed:
    raise SystemExit(1)
