import io
import re
import time
import httpx
import shutil
import asyncio
import inspect
import zipfile
from pathlib import Path
from contextlib import suppress

wap_id = "gppongmhjkpfnbhagpmjfkannfbllamg"


async def task_pool(fn, all_args, threads=10, global_kwargs=None):
    if global_kwargs is None:
        global_kwargs = {}

    tasks = {}
    all_args = list(all_args)

    def new_task():
        with suppress(IndexError):
            arg = all_args.pop(0)
            task = asyncio.create_task(fn(arg, **global_kwargs))
            tasks[task] = arg

    for _ in range(threads):  # Start initial batch of tasks
        new_task()

    while tasks:  # While there are tasks pending
        # Wait for the first task to complete
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            arg = tasks.pop(task)
            result = task.result()
            yield arg, result
            new_task()


def str_or_file_list(l):
    """
    Chains together list elements into a unified list, including the contents of any elements that are files.
    """
    if not isinstance(l, (list, tuple, set)):
        l = [l]
    final_list = {}
    for entry in l:
        f = str(entry).strip()
        f_path = Path(f).resolve()
        if f_path.is_file():
            with open(f_path, "r") as f:
                for line in f:
                    final_list[line.strip()] = None
        else:
            final_list[f] = None

    return list(final_list)


sub_regex = re.compile(r"[^a-zA-Z0-9_\.-]")
sub_regex_multiple = re.compile(r"\-+")


def sanitize_filename(filename):
    """
    Sanitizes a filename by replacing non-alphanumeric characters with underscores.
    """
    filename = sub_regex.sub("-", filename)
    # collapse multiple underscores
    filename = sub_regex_multiple.sub("-", filename)
    return filename


def get_keyword_args(fn):
    """
    Inspects a function and returns a dictionary of keyword arguments.
    """
    signature = inspect.signature(fn)
    keyword_args = {
        name: param.default
        for name, param in signature.parameters.items()
        if param.default is not param.empty and name != "self"
    }
    return keyword_args


async def download_wap(chrome_version, output_dir):
    ext_dir = Path(output_dir) / chrome_version
    # if the file exists and it's younger than 1 month, return it
    if ext_dir.is_dir() and ext_dir.stat().st_mtime > time.time() - (60 * 60 * 24 * 30):
        print(f"Using cached WAP for Chrome {chrome_version}")
        return ext_dir

    shutil.rmtree(ext_dir, ignore_errors=True)

    # otherwise go download it
    ext_url = f"https://clients2.google.com/service/update2/crx?response=redirect&prodversion={chrome_version}&acceptformat=crx2,crx3&x=id%3D{wap_id}%26installsource%3Dondemand%26uc"
    # get .crx file and write to file
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(ext_url)
        print(f"Downloading WAP for Chrome {chrome_version}, response: {response}")
        # return None if it's not a successful response
        if not str(getattr(response, "status_code", 0)).startswith("2"):
            return

        # unzip the crx file
        # make bytesio from response.content
        with zipfile.ZipFile(io.BytesIO(response.content), "r") as zip_ref:
            zip_ref.extractall(ext_dir)

        # remove open() calls
        for file in ("index", "popup"):
            file_path = ext_dir / "js" / f"{file}.js"
            if file_path.is_file():
                with open(file_path, "r") as f:
                    content = f.read()
                content = content.replace(" open(", " console.log(")
                with open(file_path, "w") as f:
                    f.write(content)

        return ext_dir
