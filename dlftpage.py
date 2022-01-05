import requests
import re
import shutil


RESOURCE_RE = re.compile(r'tileSources: \["([^"]+\.json)"\]')
RESOURCE_UP_RE = re.compile(r'tileSources:.+\\\"url\\\":\\\"([^\\]+)\\\"')


def save(image_name: str, url: str):
    """ Save the image at [url] at the path [image_name]
    """
    res = requests.get(url, stream=True)
    if res.status_code == 200:
        with open(image_name, 'wb') as f:
            shutil.copyfileobj(res.raw, f)
        print(f"[ ] [x] Image saved {image_name}")
    else:
        print('XXXXX Image Couldn\'t be retrieved')


def download(page: str):
    """ Downloads the page at [page]'s url and save the image found in this page.
    """
    print(f"[ ] Taking care of {page}")
    data = requests.get(page)

    iiif_matches = RESOURCE_RE.findall(data.text)
    upload_matches = RESOURCE_UP_RE.findall(data.text)

    if iiif_matches:
        for match in iiif_matches:
            print(f"[ ] [x] Found IIIF JSON at {match}")
            j = requests.get(match).json()
            link = f"{j['@id']}/full/{j['width']},/0/default.jpg"
            print(f"[ ] [x] Maximum image size {j['width']} / {j['height']}")
            print(f"[ ] [x] Image link {link}")
            save(j["@id"].split("/")[-1] + ".jpg", link)
    elif upload_matches:
        print("[ ] [x] Found uploaded image")
        for match in upload_matches:
            if match.startswith("/"):
                match = f"https://fromthepage.com/{match}"
            save(match.split("/")[-1], match)
    else:
        print("[ ] [ ] Found NOTHING")

    print(f"[x] Done : {page}")


def iter_input(*args):
    """ Parse the list of things to download: can be text files (.txt extension)
            or FromThePage urls
    """
    for arg in args:
        if arg.endswith(".txt"):
            with open(arg) as f:
                print(f"--- Parsing {arg} ---")
                for line in f:
                    if line.strip():
                        download(line.strip())
        else:
            download(arg)


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1:
        print("ERROR: Please text files with one FromThePage link per line or provide link directly")
        print("eg. python dlftpage.py "
              "https://fromthepage.com/stanforduniversityarchives/jls/memorials-1905/display/43950")
    else:
        iter_input(*sys.argv[1:])


