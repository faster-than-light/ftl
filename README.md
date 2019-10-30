# ftl
Faster Than Light Command Line Test Client

[![PyPI version](https://badge.fury.io/py/bugcatcher.svg)](https://badge.fury.io/py/bugcatcher)
[![Build Status](https://travis-ci.org/faster-than-light/ftl.svg?branch=master)](https://travis-ci.org/faster-than-light/ftl)
[![License: GPL v2](https://img.shields.io/badge/License-GPL%20v2-blue.svg)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html)

[![Issues](https://img.shields.io/github/issues/faster-than-light/ftl)](https://github.com/faster-than-light/ftl/issues)
![Forks](https://img.shields.io/github/forks/faster-than-light/ftl)
![Stars](https://img.shields.io/github/stars/faster-than-light/ftl)

### Installation

#### Installing with PIP
`pip install bugcatcher`

Installing with PIP creates a console script for `ftl` to run BugCatcher.

#### Installing from the GitHub Repository

Download or clone this repository to your drive. Then use PIP to install the local package by going to its directory in your console and typing: `pip install .`

### Usage

```
ftl [-h] [--project PROJECT] [--endpoint ENDPOINT] [--async]
       [--sid SID] [--extension EXTENSIONS]
       command [items [items ...]]
```

Retrieve a SID from the BugCatcher <a href="https://bugcatcher.fasterthanlight.dev" target="_blank">web app</a> and use it directly.

`ftl --project "Master" --sid 5EX3c6FNWMAv3AiIsFMGOhnMidNyDkarskyzddFq push *`

Or store some environmental variables.

```
export STL_INTERNAL_SID=5EX3c6FNWMAv3AiIsFMGOhnMidNyDkarskyzddFq
export FTL_PROJECT="Master"
```

Then minimize your `ftl` commands.

`ftl push *`

`ftl test`

`ftl view <test_id> --json`

`ftl del`