import requests
import re
import shutil
import click


FTP_RESOURCE_RE = re.compile(r'tileSources: \["([^"]+\.json)"\]')
FTP_RESOURCE_UP_RE = re.compile(r'tileSources:.+\\\"url\\\":\\\"([^\\]+)\\\"')
SMT_IDSID_RE = re.compile(r"data-idsid=\"([^\"]+)")


def save(image_name: str, url: str):
    """ Save the image at [url] at the path [image_name]
    """
    res = requests.get(url, stream=True)
    if res.status_code == 200:
        with open(image_name, 'wb') as f:
            shutil.copyfileobj(res.raw, f)
        click.echo(click.style(f"[ ] [x] Image saved {image_name}", fg="green"))
    else:
        click.echo(click.style(f"XXXXX Image Couldn\'t be retrieved", fg="red"))


def download_fromthepage(page: str):
    """ Downloads the page at [page]'s url and save the image found in this page.
    """
    print(f"[ ] Taking care of {page}")
    data = requests.get(page)

    iiif_matches = FTP_RESOURCE_RE.findall(data.text)
    upload_matches = FTP_RESOURCE_UP_RE.findall(data.text)

    if iiif_matches:
        for match in iiif_matches:
            click.echo(f"[ ] [x] Found IIIF JSON at {match}")
            j = requests.get(match).json()
            link = f"{j['@id']}/full/{j['width']},/0/default.jpg"
            click.echo(f"[ ] [x] Maximum image size {j['width']} / {j['height']}")
            click.echo(f"[ ] [x] Image link {link}")
            save(j["@id"].split("/")[-1] + ".jpg", link)
    elif upload_matches:
        click.echo("[ ] [x] Found uploaded image")
        for match in upload_matches:
            if match.startswith("/"):
                match = f"https://fromthepage.com/{match}"
            save(match.split("/")[-1], match)
    else:
        click.echo(click.style("[ ] [ ] Found NOTHING", fg="red"))

    click.echo(f"[x] Done : {page}")


def download_smithonian(page: str):
    """ Downloads the page at [page]'s url and save the image found in this page.
    """
    click.echo(f"[ ] Taking care of {page}")
    data = requests.get(page)

    json_match = SMT_IDSID_RE.findall(data.text)
    if json_match:
        for match in json_match:
            click.echo(f"[ ] [x] Found Smithonian JSON ID at {match}")
            j = requests.get(f"https://ids.si.edu/ids/dynamic?id={match}&format=dzi_json").json()["Image"]
            link = f"https://ids.si.edu/ids/iiif/{match}/full/{j['Size']['Height']},/0/default.jpg"
            click.echo(f"[ ] [x] Maximum image size {j['Size']['Height']} / {j['Size']['Width']}")
            click.echo(f"[ ] [x] Image link {link}")
            save(f"{match}.jpg", link)
    else:
        click.echo(click.style("[ ] [ ] Found NOTHING", fg="red"))

    click.echo(f"[x] Done : {page}")


def iter_input(args, mode="fromthepage"):
    """ Parse the list of things to download: can be text files (.txt extension)
            or FromThePage urls
    """
    if mode == "fromthepage":
        download = download_fromthepage
    else:
        download = download_smithonian

    for arg in args:
        if arg.endswith(".txt"):
            with open(arg) as f:
                click.echo(f"--- Parsing {arg} ---")
                for line in f:
                    if line.strip():
                        download(line.strip())
        else:
            download(arg)


@click.command()
@click.argument("source", nargs=-1)
@click.option("--mode", type=click.Choice(["fromthepage", "smithonian"]),
                show_default=True, help="Website used", default="fromthepage")
def cli(source, mode):
    """ Download images from FromThePage or other similar websites by providing URL of transcriptions, such as :

    > python dlftpage.py https://fromthepage.com/stanforduniversityarchives/jls/memorials-1905/display/43950

    Or by providing a text file with a list of URL (one per line, see source.txt)

    > python dlftpage.py source.txt
    """
    iter_input(source, mode=mode)


if __name__ == "__main__":
    cli()


