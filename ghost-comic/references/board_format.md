# board.json：分鏡檔格式

工作資料夾裡的 `board.json` 是整本漫畫的唯一來源：頁面怎麼切、每格畫什麼、參考哪些圖、字放哪裡，都在這一份。`assets/example_board.json` 是〈一個人在家開視訊〉的完整範例（7 頁、33 格），新故事從它複製來改最快。

## 最外層

| 欄位 | 意思 |
|---|---|
| `title` | 作品名，第一格的標題字 |
| `story` | 原始故事檔（相對路徑），只是紀錄 |
| `direction` | `rtl`（預設，由右往左，台灣日漫的讀法）或 `ltr` |
| `page` | 頁面尺寸，`[1200, 1700]`，約 B5 比例 |
| `margin` | 外框留白，56 |
| `gutter` | 格間距 `[水平, 垂直]`，`[18, 24]`；垂直比水平寬，讀者才分得出列 |
| `style_options` | 畫風選項，`{"A": {"name", "panel", "sheet"}, ...}`：`panel` 接在每格 prompt 前面，`sheet` 接在角色卡 prompt 前面。`choose style=A` 選定 |
| `characters` | 角色，見下 |
| `scenes` | 場景卡的描述，`{"room": "...", "hall": "..."}`；在 refs 裡寫成 `scene:room` |
| `consistency` | 場景一致和人物比例的固定句子，見下 |
| `pages` | 頁，見下 |

## characters

```json
"me": {
  "name": "我",
  "features": "鳥窩頭＋翹毛、超粗眉、下垂眼",
  "views": "The same character is drawn twice side by side: full body front view on the left, ...",
  "desc": "A 19-year-old Taiwanese university guy, thin, with a huge messy bird's-nest of black hair ...",
  "ref_crop": "left"
}
```

- `features`：中文的記憶點，挑版本那張圖的標題。每個角色至少兩個一眼認得出的特徵（髮型、鼻子、眼睛、臉型、一件固定的衣服），寫進 `desc`，每格 prompt 再重複一次。
- `views`：角色卡要畫哪幾個視角。
- `ref_crop`：`refs` 指令從角色卡裁哪一邊當參考圖。預設 `left`（正面）；動物的正面常畫錯毛色時用側面那邊；`none` 不裁。

## consistency

```json
"consistency": {
  "scene": {"room": "Scene consistency: the living room never changes. ...", "hall": "..."},
  "scale": {"me": "Character scale: the young man is about 175 cm tall and thin; ...", "ama": "..."},
  "scene_refs": {"room": ["scene:room", "panel:p7", "panel:p19", "panel:p2"], "hall": ["scene:hall", "panel:p15", "panel:p8"]}
}
```

- `scene`：每個場景寫一次固定格局（家具在哪、門在哪、比例），之後所有參考到這個場景的格子自動接上這句。
- `scale`：每個角色的身高和相對比例（「比主角矮一個半頭，頭不比他大」）。格子的 refs 裡有誰，就接上誰的。
- `scene_refs`：哪些參考算這個場景。用畫好的格子當場景參考時（光線一致的作法），要把那格加進來，比例句才會跟著接上。

## pages

```json
{"rows": [
  {"h": 0.30, "cells": [{"id": "p9t", "w": 0.60, ...}, {"id": "p10", "w": 0.40, ...}]},
  {"h": 0.70, "cells": [
     {"w": 0.40, "stack": [{"id": "p16", "h": 0.5, ...}, {"id": "p17", "h": 0.5, ...}]},
     {"id": "p18", "w": 0.60, ...}]}
 ],
 "insets": [{"id": "p22", "box": [0.04, 0.73, 0.40, 0.97], ...}]}
```

- 列的 `h` 加起來是 1，列內格子的 `w` 加起來是 1。
- `stack`：一欄裡上下疊的格子，讀完這一欄才讀下一格；左右兩欄的 `h` 切法不同，格線就會錯開。
- `insets`：疊在大格上的小格，`box` 是相對於版心的 `[x0, y0, x1, y1]`。
- 由右往左時，列裡第一格在最右邊。用 `plan` 看編號確認讀的順序。

## 一格

| 欄位 | 意思 |
|---|---|
| `id` | 唯一，`p1`、`p9t` |
| `label` | 中文一句話，草圖上顯示，讓擁有者審分鏡 |
| `refs` | 參考圖，依序對應 prompt 裡的 `<image1>`、`<image2>`：角色 id、`scene:<id>`、`panel:<id>`（那格挑定的圖）、`file:<out 底下的路徑>` |
| `prompt` | 英文。描述畫面看得到的東西，見 prompting.md |
| `n` | 候選張數，預設 2；改動參考圖的格子給 3 |
| `pass` | 用到 `panel:` 參考的格子設 2，第二輪才畫 |
| `screen` | 這格是透過螢幕看到的：加邊框和鏡頭點 |
| `pip` | 螢幕右下角的子畫面，填另一格的 id（例如對方的視訊畫面） |
| `flashback` | 回憶：無框、邊緣暈白 |
| `focus` | 裁切重心 `[x, y]`，預設 `[0.5, 0.5]` |
| `text` | 字，見下 |
| `sfx` | 狀聲詞 `{"text": "喀", "at": [0.7, 0.3], "size": 0.3, "angle": -12}` |

## text

```json
{"kind": "screen", "text": "你後面那個廁所門，", "pos": "tr", "per_col": 8, "scale": 1.0}
```

- `kind`：
  - `speech`：橢圓框，在場的人說的話。
  - `screen`、`phone`：雙框方形，從螢幕或電話傳來的聲音。
  - `narration`：方框，旁白。
  - `title`：作品標題，白字黑底。
  - `tag`：角色第一次登場的名牌，白字黑底。
- `pos`：放在格子的哪裡，兩個字母，第一個是 `t`（上）、`m`（中）或 `b`（下），第二個是 `r`（右）、`c`（中）或 `l`（左），例如 `tr` 是右上。由右往左讀時，先讀的放 `tr`，後讀的放 `bl`。
- `per_col`：一欄最多幾個字，框放不下會自動再減。
- `\n` 強制換欄，標題用（`一個人在家\n開視訊`）。
- 直排：標點自動換成直排字形，不會落在欄首，開括號不會落在欄尾；長句平均切成兩半，不留單字一欄。
