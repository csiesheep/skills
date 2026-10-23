# Finding posts

From the runs of 2026-10-22 (china_life on Threads; covervote on Threads and Instagram). Taiwan, Traditional
Chinese. Results change daily: when a keyword stops working, write it down here.

## Threads

    https://www.threads.com/search?q=<keyword>&serp_type=default&filter=recent   (today's)
    https://www.threads.com/search?q=<keyword>&serp_type=default                 (top)

Wait 7 to 8 s, scroll down 10 ticks, wait 3 s, then read every hit in one call:

```js
(()=>{const out=[];const seen=new Set();document.querySelectorAll('a[href*="/post/"] time').forEach(t=>{const a=t.closest('a');const h=a.getAttribute('href');if(seen.has(h))return;seen.add(h);let c=a;for(let i=0;i<12&&c;i++){c=c.parentElement;if(c&&c.innerText&&c.innerText.length>60&&c.querySelectorAll('time').length===1)break}out.push(h+' @'+t.getAttribute('datetime').slice(2,10)+' :: '+(c?c.innerText:'').replace(/\n+/g,' | ').slice(0,160))});return out.join('\n')})()
```

Each line is `/@author/post/<code> @yy-mm-dd :: author | age | text | likes | replies`. Several searches fit
in one `browser_batch` (navigate, wait, scroll, wait, extract, repeated).

**Open the post before drafting.** The search line is cut at 160 characters. On 2026-10-22 @stayywhy's line read
「想讓長輩認識某候選人，但說服只會讓他們反感」; the full post went on to a plan to binge videos on the elders'
phones so the algorithm would push them. The user approved a reply on the short version. Read the whole post, and
put anything that changes the picture in the list you show the user.

| Game | Keyword | What came back |
|---|---|---|
| covervote | 說服長輩 (recent) | mostly marriage pressure; a few election ones, partisan |
| covervote | 長輩 投票 | partisan posts and poll analysis: skip |
| covervote | 跟爸媽聊政治 (top) | good: people regretting arguments with parents, some months old |
| covervote | 說服爸媽 投票 (top) | good: @yuuib__ asking how to get a friend to vote |
| covervote | 政見 比較 (recent) | all campaign attacks: skip |
| covervote | 長輩 政治 (recent) | party accounts and attacks: skip |
| china_life | see the 2026-10-22 engagement file | 中國歷史, 網頁遊戲 gave the two posted replies |

## Instagram

Keyword search returns a grid of popular posts, mostly weeks or months old, and for election words it is
**mostly campaign material, news, Japanese and Malaysian election posts, and anti-scam notices** (2026-10-22: five
keywords gave one usable post). Expect few hits; broaden to neutral topics (選舉看政見) rather than forcing a
reply under an unfit post.

    https://www.instagram.com/explore/search/keyword/?q=<keyword>

Read the grid's captions without opening each post: `fetch('/p/<code>/')` and decode the
`og:description` meta ("N likes, M comments - author on Month D, YYYY: caption"):

```js
const ta=document.createElement('textarea');const ids=[...new Set([...document.querySelectorAll('a[href*="/p/"],a[href*="/reel/"]')].map(a=>a.getAttribute('href').split('/').filter(Boolean).pop()))].slice(0,20);const out=[];for(const id of ids){const h=await (await fetch('/p/'+id+'/')).text();const m=h.match(/<meta property="og:description" content="([^"]*)"/);ta.innerHTML=m?m[1]:'?';out.push(id+' :: '+ta.value.replace(/\n+/g,' | ').slice(0,110))};out.join('\n')
```

**Rate limit**: about 120 such fetches in a row got HTTP 429 for the whole session (ghost-reply, 2026-10-22). Read
at most about 40 per run and stop for 15 minutes after a 429. Codes starting `De` were the last two weeks in
October 2026.

The comment box is `find` "Add a comment textarea"; the Post button is `find` "Post button for comment" (its
coordinates move when the page scrolls). Check the typed text with `document.querySelector('textarea').value`
before pressing Post.
