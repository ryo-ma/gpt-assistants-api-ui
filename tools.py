import subprocess


# example function
def geocode(address):
    address_replace = address.replace("\n", "").replace("\r", "")
    result = subprocess.run(
        (f'echo "{address_replace}" | abrg -'),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
    ).stdout
    print(result)
    return result


TOOL_MAP = {"geocode": geocode}
