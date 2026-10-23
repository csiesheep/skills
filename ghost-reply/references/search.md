# Finding posts

Written from the first run (2026-10-19, Traditional Chinese, Taiwan). Search results change daily; when a keyword
stops returning real paranormal posts, note it here.

## Threads

Search URL, with `filter=recent` for today's posts or without it for the top ones:

    https://www.threads.com/search?q=<keyword>&serp_type=default&filter=recent
    https://www.threads.com/search?q=<keyword>&serp_type=default

`get_page_text` reads the results. Results load slowly: wait 6 to 8 seconds, and if only the sidebar comes back,
load the page again. Chrome may show posts translated into English; the original is the post page's tab title.

| Keyword | What came back |
|---|---|
| 靈異經驗 | real experience posts, some weeks old; good for top |
| 靈異故事 | podcasts and creators telling stories; today's posts with `recent` |
| 魔神仔 | mountain stories with long threads |
| 毛毛的 | horror films and games people found scary; popular posts |
| 怪事 | mixed; some mountain and house stories |
| 鬼壓床 | sleep paralysis posts, some pseudo-science; pick the ones asking "有遇過嗎" |
| 講鬼故事 | short videos; the army night-guard post came from here |
| 鬼故事 | mostly metaphors (職場、交友、裝潢鬼故事): skip |
| 撞鬼、阿飄 | mostly metaphors and politics: skip |

Topics that carry ghost talk without the word: 當兵站哨, 大夜班, 宿舍, 一個人住, 搬家, 老家, 醫院, 殯儀館,
恐怖片 titles. A post that asks readers something ("你們當年是哪種") is the best target: its readers are already
replying.

Post URLs come from `find` "timestamp link to the post by <author>" on the results page (href
`/@<author>/post/<code>`). On the post page, the top post's timestamp link is the post itself.

## Instagram

The web hashtag page (`/explore/tags/<tag>/`) failed to load. The keyword search works and shows a grid of popular
posts, not today's:

    https://www.instagram.com/explore/search/keyword/?q=<keyword>

`find` "post links in the results grid" gives `/p/<code>/`. Codes are roughly in time order, so on 2026-10-19 codes
starting `De` were from the last week or two and `Dc`, `Dd` older. Open a post to read its date, likes and comments;
pick ones a few days old that still get comments. Keywords used: 靈異故事.

Accounts found this way (horror picture stories, urban legends) are good fixed-list candidates: their posts get
thousands of likes, and a reply near the top of the comments is seen.

## 2026-10-20 notes

- Threads "Top" for 靈異 returned months-old unrelated posts; the 鬼故事 custom feed in the sidebar returned
  unrelated posts too. `filter=recent` on 靈異經驗 and 魔神仔 found the day's best: chen.kenn (673K views),
  quietnavigator1985's new post, and story replies under hung.c.tsai's 魔神仔 post.
- On a results page, `javascript_tool` with `[...document.querySelectorAll('a[href*="/post/"]')].map(a=>a.getAttribute('href'))`
  lists every post and reply link at once (author in the path); faster than `find` per post.
- Replies under a busy post are their own pages (`/@<replier>/post/<code>`): reply there to land in that comment
  thread.
- Instagram: open the fixed-list accounts' profiles and take the newest post (the first `/p/` link); z.n_.studio
  and banmi.tw each had a post from the last 12 hours with 2,100 likes and 30 to 97 comments. The keyword search
  都市傳說 also surfaced banmi.tw's new post.

## Instagram, the way that worked (2026-10-20, ten posts)

Keyword search (`/explore/search/keyword/?q=`) returns popular posts, mostly weeks or months old; it is good for
finding **accounts**, not today's posts. So:

1. Collect post codes from a few keyword grids (靈異故事, 鬼故事, 恐怖故事, 都市傳說, 怪談, 台灣怪談, 真實靈異,
   靈異, 鬼屋). Page loads clear page variables: keep the codes in `localStorage` between pages.
2. Read every code's stats in one `javascript_tool` call: `fetch('/p/<code>/')` and the page's
   `<meta name="description">` reads "N likes, M comments - <author> on <date>: ...". This names the active
   accounts.
3. Open each promising account's profile and take the post links after the first three (the first three are
   pinned): those are the newest. Read their stats the same way and keep the last few days.
4. Open the shortlisted posts with `get_page_text` for the caption and the top comments; drop off-topic ones (an
   account that mixes horror with army life, mahjong or politics) and ones whose comments are about real harm.

`/api/v1/users/web_profile_info/` answered with a login page; the profile HTML has no post links. Active accounts
found: banmi.tw, z.n_.studio, alicechooooo, 02thinking, hiphop200177, x3laayrwk_. A brand-new post with one comment
(banmi.tw, 02thinking) is the best spot; a days-old post is still worth it when its comments are few or when a top
comment with hundreds of likes can take a reply.

## 2026-10-22 note: Instagram rate limit

Reading about 170 post pages with `fetch('/p/<code>/')`, eight at a time, got HTTP 429 from Instagram after
about 120: first the meta tags came back empty, then every page, profile and post, showed "HTTP ERROR 429" for
the brand's session. Read at most about 40 codes per run, one at a time with a pause, and only the codes that
look new (`De` + a late letter); never re-fetch a batch that came back empty. After a 429, stop for at least
15 minutes.
