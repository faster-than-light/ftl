# BugCatcher
Command Line Test Client by Faster Than Light

#### Usage

```
bugcatcher [-h] [--project PROJECT] [--endpoint ENDPOINT] [--async]
       [--sid SID] [--extension EXTENSIONS]
       command [items [items ...]]
```

Retrieve a SID from the BugCatcher <a href="https://bugcatcher.fasterthanlight.dev" target="_blank">web app</a> and use it directly.

`bugcatcher --project "Master" --sid 5EX3c6FNWMAv3AiIsFMGOhnMidNyDkarskyzddFq push *`

Or store some environmental variables.

```
export FTL_SID=5EX3c6FNWMAv3AiIsFMGOhnMidNyDkarskyzddFq
export FTL_PROJECT="Master"
```

Then minimize your `bugcatcher` commands.

`bugcatcher push *`

`bugcatcher test`

`bugcatcher view <test_id>`

`bugcatcher del`