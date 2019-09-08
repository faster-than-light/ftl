# ftl
Faster Than Light Command Line Test Client

#### Usage

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