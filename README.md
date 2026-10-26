<img src="https://github.com/user-attachments/assets/25912aba-690a-45e2-a6a9-2b0445e8218f" width="600"/>

[![Python Version](https://img.shields.io/badge/python-3.9+-8400ff)](https://www.python.org) [![License](https://img.shields.io/badge/license-AGPLv3-8400ff.svg)](LICENSE) [![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) [![Tests](https://github.com/blacklanternsecurity/webcap/actions/workflows/tests.yml/badge.svg?branch=stable)](https://github.com/blacklanternsecurity/webcap/actions?query=workflow%3A"tests") [![Codecov](https://codecov.io/gh/blacklanternsecurity/webcap/branch/dev/graph/badge.svg?token=IR5AZBDM5K)](https://codecov.io/gh/blacklanternsecurity/webcap) [![Discord](https://img.shields.io/discord/859164869970362439)](https://discord.com/invite/PZqkgxu5SA)

**WebCap** is an extremely lightweight web screenshot tool. It doesn't require Selenium, Playwright, Puppeteer, or any other browser automation framework; all it needs is a working Chrome installation. Used by [BBOT](https://github.com/blacklanternsecurity/bbot).

### Installation

```bash
pipx install webcap
```

### Web Interface (`webcap server`)

https://github.com/user-attachments/assets/a5dea3fb-fa01-41e7-90cd-67c6efa3d6e5

### Features

WebCap's most unique feature is its ability to capture not only the **fully-rendered DOM**, but also every snippet of **parsed Javascript** (regardless of inline or external), and the **full content** of every HTTP request + response (including Javascript API calls etc.). For convenience, it can output directly to JSON.

### Example Commands

#### Scanning

```bash
# Capture screenshots of all URLs in urls.txt
webcap scan urls.txt -o ./my_screenshots

# Output to JSON, and include the fully-rendered DOM
webcap scan urls.txt --json --dom | jq

# Capture requests and responses
webcap scan urls.txt --json --requests --responses | jq

# Capture javascript
webcap scan urls.txt --json --javascript | jq

# Extract text from screenshots
webcap scan urls.txt --json --ocr | jq
```

#### Server

```bash
# Start the server
webcap server

# Browse to http://localhost:8000
```

# Screenshots

### CLI Interface (`webcap scan`)

![webcap_gif](https://github.com/user-attachments/assets/1eb7270f-e2f4-4d9e-979b-2b571ca20478)

#### Fully-rendered DOM

![image](https://github.com/user-attachments/assets/60dd2a80-f9c3-438e-8f00-f982c356625d)

#### Javascript Capture

![image](https://github.com/user-attachments/assets/6f960bbb-efb6-4294-a1f2-2c6181baa31a)

#### Requests + Responses

![image](https://github.com/user-attachments/assets/0f036384-a465-4579-b70a-b567daaa8113)

#### OCR

![image](https://github.com/user-attachments/assets/cffb268e-8b9b-490c-8949-39e73e73aa8a)

### Full feature list

- [x] Blazing fast screenshots
- [x] Fullscreen capture (entire scrollable page)
- [x] JSON output
- [x] Full DOM extraction
- [x] Javascript extraction (inline + external)
- [ ] Javascript extraction (environment dump)
- [x] Full network logs (incl. request/response bodies)
- [x] Title
- [x] Status code
- [x] Fuzzy (perception) hashing
- [ ] Technology detection
- [x] OCR text extraction
- [x] Web interface


### Webcap as a Python library

```python
import base64
from webcap import Browser

async def main():
    # create a browser instance
    browser = Browser()
    # start the browser
    await browser.start()
    # take a screenshot
    webscreenshot = await browser.screenshot("http://example.com")
    # save the screenshot to a file
    with open("screenshot.png", "wb") as f:
        f.write(webscreenshot.blob)
    # stop the browser
    await browser.stop()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## CLI Usage (--help)

```
 Usage: webcap scan [OPTIONS] URLS                                                            
                                                                                              
 Screenshot URLs                                                                              
                                                                                              
╭─ Arguments ────────────────────────────────────────────────────────────────────────────────╮
│ *    urls      TEXT  URL(s) to capture, or file(s) containing URLs [default: None]         │
│                      [required]                                                            │
╰────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ──────────────────────────────────────────────────────────────────────────────────╮
│ --json    -j                  Output JSON                                                  │
│ --chrome  -c      TEXT        Path to Chrome executable [default: None]                    │
│ --output  -o      OUTPUT_DIR  Output directory                                             │
│                               [default: /home/bls/Downloads/code/webcap/screenshots]       │
│ --help                        Show this message and exit.                                  │
╰────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Screenshots ──────────────────────────────────────────────────────────────────────────────╮
│ --resolution      -r      RESOLUTION  Resolution to capture [default: 1440x900]            │
│ --full-page       -f                  Capture the full page (larger resolution images)     │
│ --no-screenshots                      Only visit the sites; don't capture screenshots      │
│                                       (useful with -j/--json)                              │
╰────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Performance ──────────────────────────────────────────────────────────────────────────────╮
│ --threads  -t      INTEGER  Number of threads to use [default: 15]                         │
│ --timeout  -T      INTEGER  Timeout before giving up on a web request [default: 10]        │
│ --delay            SECONDS  Delay before capturing [default: 3.0]                          │
╰────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ HTTP ─────────────────────────────────────────────────────────────────────────────────────╮
│ --user-agent  -U      TEXT  User agent to use                                              │
│                             [default: Mozilla/5.0 (Windows NT 10.0; Win64; x64)            │
│                             AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0        │
│                             Safari/537.36]                                                 │
│ --headers     -H      TEXT  Additional headers to send in format: 'Header-Name:            │
│                             Header-Value' (multiple supported)                             │
│ --proxy       -p      TEXT  HTTP proxy to use [default: None]                              │
╰────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ JSON (Only apply when -j/--json is used) ─────────────────────────────────────────────────╮
│ --base64        -b                     Output each screenshot as base64                    │
│ --dom           -d                     Capture the fully-rendered DOM                      │
│ --responses     -rs                    Capture the full body of each HTTP response         │
│                                        (including API calls etc.)                          │
│ --requests      -rq                    Capture the full body of each HTTP request          │
│                                        (including API calls etc.)                          │
│ --javascript    -J                     Capture every snippet of Javascript (inline +       │
│                                        external)                                           │
│ --ignore-types                   TEXT  Ignore these filetypes                              │
│                                        [default: Image, Media, Font, Stylesheet]           │
│ --ocr                --no-ocr          Extract text from screenshots [default: no-ocr]     │
╰────────────────────────────────────────────────────────────────────────────────────────────╯
```

## License

Copyright (C) 2024 Black Lantern Security

Licensed under the GNU Affero General Public License v3.0 or later (`AGPL-3.0-or-later`). See [LICENSE](LICENSE).
