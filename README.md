# ftl
Faster Than Light Command Line Test Client

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

`ftl view <test_id>`

`ftl del`