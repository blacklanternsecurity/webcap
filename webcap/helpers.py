import re
import asyncio
import logging
import traceback
from pathlib import Path
from contextlib import suppress
from urllib.parse import urlparse

wap_id = "gppongmhjkpfnbhagpmjfkannfbllamg"


log = logging.getLogger(__name__)


async def task_pool(fn, all_args, threads=10, global_kwargs=None):
    if global_kwargs is None:
        global_kwargs = {}

    tasks = {}
    try:
        all_args = list(all_args)

        def new_task():
            with suppress(IndexError):
                arg = all_args.pop(0)
                task = asyncio.create_task(fn(arg, **global_kwargs))
                tasks[task] = arg

        for _ in range(threads):
            new_task()

        while tasks:
            try:
                log.debug(f"Waiting for {len(tasks)} tasks to complete")
                done, pending = await asyncio.wait(set(tasks.keys()), return_when=asyncio.FIRST_COMPLETED, timeout=1.0)
                log.debug(f"asyncio.wait returned with {len(done)} done tasks and {len(pending)} pending tasks")
            except asyncio.TimeoutError:
                log.debug(f"no tasks completed in the last second")
                continue
            log.debug(f"{len(done)} tasks done, {len(pending)} tasks pending")
            for task in done:
                arg = tasks.pop(task)
                try:
                    result = task.result()
                    yield arg, result
                except Exception as e:
                    log.error(f"Error in task {arg}: {e}")
                    log.debug(traceback.format_exc())
                new_task()
    except (KeyboardInterrupt, asyncio.CancelledError):
        for task in tasks:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await asyncio.wait_for(task, timeout=0.01)


def str_or_file_list(l):
    """
    Chains together list elements into a unified list, including the contents of any elements that are files.
    """
    if not isinstance(l, (list, tuple, set)):
        l = [l]
    final_list = {}
    for entry in l:
        f = str(entry).strip()
        f_path = Path(f)
        if f_path.exists() and not f_path.is_dir():
            with open(f_path, "r") as f:
                for line in f:
                    final_list[line.strip()] = None
        else:
            final_list[f] = None

    return list(final_list)


def validate_urls(urls):
    for url in urls:
        parsed_url = urlparse(url)
        if (not parsed_url.netloc) or (parsed_url.scheme not in ["http", "https"]):
            log.warning(f"skipping invalid URL: {url}")
            continue
        yield url


sub_regex = re.compile(r"[^a-zA-Z0-9_\.-]")
sub_regex_multiple = re.compile(r"\-+")


def sanitize_filename(filename):
    """
    Sanitizes a filename by replacing non-alphanumeric characters with underscores.
    """
    filename = str(filename)
    filename = sub_regex.sub("-", filename)
    # collapse multiple underscores
    filename = sub_regex_multiple.sub("-", filename).strip("-")
    filename = str(truncate_filename(filename, 240))
    return filename


# async def download_wap(chrome_version, output_dir):
#     ext_dir = Path(output_dir) / chrome_version
#     # if the file exists and it's younger than 1 month, return it
#     if ext_dir.is_dir() and ext_dir.stat().st_mtime > time.time() - (60 * 60 * 24 * 30):
#         print(f"Using cached WAP for Chrome {chrome_version}")
#         return ext_dir

#     shutil.rmtree(ext_dir, ignore_errors=True)

#     # otherwise go download it
#     ext_url = f"https://clients2.google.com/service/update2/crx?response=redirect&prodversion={chrome_version}&acceptformat=crx2,crx3&x=id%3D{wap_id}%26installsource%3Dondemand%26uc"
#     # get .crx file and write to file
#     async with httpx.AsyncClient(follow_redirects=True) as client:
#         response = await client.get(ext_url)
#         print(f"Downloading WAP for Chrome {chrome_version}, response: {response}")
#         # return None if it's not a successful response
#         if not str(getattr(response, "status_code", 0)).startswith("2"):
#             return

#         # unzip the crx file
#         # make bytesio from response.content
#         with zipfile.ZipFile(io.BytesIO(response.content), "r") as zip_ref:
#             zip_ref.extractall(ext_dir)

#         # remove open() calls
#         for file in ("index", "popup"):
#             file_path = ext_dir / "js" / f"{file}.js"
#             if file_path.is_file():
#                 with open(file_path, "r") as f:
#                     content = f.read()
#                 content = content.replace(" open(", " console.log(")
#                 with open(file_path, "w") as f:
#                     f.write(content)

#         return ext_dir


def get_exception_chain(e):
    """
    Retrieves the full chain of exceptions leading to the given exception.

    Args:
        e (BaseException): The exception for which to get the chain.

    Returns:
        list[BaseException]: List of exceptions in the chain, from the given exception back to the root cause.

    Examples:
        >>> try:
        ...     raise ValueError("This is a value error")
        ... except ValueError as e:
        ...     exc_chain = get_exception_chain(e)
        ...     for exc in exc_chain:
        ...         print(exc)
        This is a value error
    """
    exception_chain = []
    current_exception = e
    while current_exception is not None:
        exception_chain.append(current_exception)
        current_exception = getattr(current_exception, "__context__", None)
    return exception_chain


def in_exception_chain(e, exc_types):
    """
    Given an Exception and a list of Exception types, returns whether any of the specified types are contained anywhere in the Exception chain.

    Args:
        e (BaseException): The exception to check
        exc_types (list[Exception]): Exception types to consider intentional cancellations. Default is KeyboardInterrupt

    Returns:
        bool: Whether the error is the result of an intentional cancellaion

    Examples:
        >>> try:
        ...     raise ValueError("This is a value error")
        ... except Exception as e:
        ...     if not in_exception_chain(e, (KeyboardInterrupt, asyncio.CancelledError)):
        ...         raise
    """
    return any(isinstance(_, exc_types) for _ in get_exception_chain(e))


def is_cancellation(e):
    return in_exception_chain(e, (KeyboardInterrupt, asyncio.CancelledError))


def repr_params(params):
    return f"{', '.join(f'{k}={repr(v)}' for k, v in params.items())}"


def truncate_filename(file_path, max_length=255):
    """
    Truncate the filename while preserving the file extension to ensure the total path length does not exceed the maximum length.

    Args:
        file_path (str): The original file path.
        max_length (int): The maximum allowed length for the total path. Default is 255.

    Returns:
        pathlib.Path: A new Path object with the truncated filename.

    Raises:
        ValueError: If the directory path is too long to accommodate any filename within the limit.

    Example:
        >>> truncate_filename('/path/to/example_long_filename.txt', 20)
        PosixPath('/path/to/example.txt')
    """
    p = Path(file_path)
    directory, stem, suffix = p.parent, p.stem, p.suffix

    max_filename_length = max_length - len(suffix)

    if max_filename_length <= 0:
        raise ValueError("The directory path is too long to accommodate any filename within the limit.")

    if len(stem) > max_filename_length:
        truncated_stem = stem[:max_filename_length]
    else:
        truncated_stem = stem

    new_path = directory / (truncated_stem + suffix)
    return new_path


def color_status_code(status_code):
    """
    This function takes an HTTP status code as input and returns it in bold with a specific color based on the first digit of the status code.

    Args:
        status_code (int or str): An HTTP status code represented as either an integer or string.

    Returns:
        str: A colored string representation of the status code, indicating its severity level.

    """
    status_code = str(status_code)
    if status_code == "404":
        color = "orchid"
    elif status_code.startswith("2"):
        color = "bright_green"
    elif status_code.startswith("3"):
        color = "purple"
    elif status_code.startswith("4"):
        color = "red"
    else:
        color = "orange1"
    return f"[bold {color}]{status_code}[/bold {color}]"
