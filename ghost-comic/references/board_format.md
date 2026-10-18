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
| `lights` | 光線狀態，`{"night_camp": "Late at night: ...", "morning": "Bright morning: ..."}`；格子用 `light` 指定，句子接在格子 prompt 後面 |
| `pages` | 頁，見下 |

## characters

```json
"me": {
  "name": "我",
  "features": "鳥窩頭＋翹毛、超粗眉、下垂眼",
  "views": "The same character is drawn twice side by side: full body front view on the left, ...",
  "desc": "A 19-year-old Taiwanese university guy, thin, with a huge messy bird's-nest of black hair ...",
  "keywords": ["bird's-nest", "cowlick", "thick eyebrows"],
  "ref_crop": "left"
}
```

- `features`：中文的記憶點，挑版本那張圖的標題，也是檢查 brief 裡逐項對的清單。每個角色至少兩個一眼認得出的特徵（髮型、鼻子、眼睛、臉型、一件固定的衣服），寫進 `desc`，每格 prompt 再重複一次。
- `keywords`：英文的特徵關鍵字；`lint` 會檢查有這個角色的格子，prompt 裡至少出現其中一個。
- `views`：角色卡要畫哪幾個視角。
- `ref_crop`：`refs` 指令從角色卡裁哪一邊當參考圖。預設 `left`（正面）；動物的正面常畫錯毛色時用側面那邊；`none` 不裁。
- `ref_boxes`：自動找的頭部、半身框不準時手動指定，`{"head": [x0, y0, x1, y1]}`，相對於單一視角的比例。
- `animal`：`true` 的角色（狗）不算進人數，也不建議改用頭部裁切。
- `aliases`：台詞和旁白裡對這個角色的其他叫法（`name` 是「媽媽」，旁白寫「我媽」）。`name` 裡的括號也會拆開：「我（舅舅）」算「我」和「舅舅」。
- `intro`：介紹這個角色的那一格的 id。`lint` 要求角色第一次被畫出來的那一格就有他的名字；如果名牌在同一頁的另一格（小寶在 p2 被畫出來，名牌在 p4），設 `intro: "p4"`。介紹的那格必須在同一頁，不然照樣警告。
- `ghost`：`true` 的角色是鬼，不檢查名字：讀者本來就不該知道他是誰。

### 參考圖的三種裁切

`refs` 從挑好的角色卡做三張參考圖：`me`（全身，只留一個視角）、`me:bust`（半身）、`me:head`（頭部）。格子的 `refs` 裡寫 `me:head`、`me:bust`、`me` 或 `me:full`。

- 全身站姿的角色卡會把姿勢一起帶進格子：該坐著吃麵、該特寫的格子都被畫成站著（第二本的 p31、p32 各三次）。特寫用 `:head`，坐著和腰部以上用 `:bust`，只有全身站姿的格子用全身。
- `lint` 會在特寫、坐著的格子用了全身參考時提醒。

## consistency

```json
"consistency": {
  "scene": {"room": "Scene consistency: the living room never changes. ...", "hall": "..."},
  "scale": {"me": "Character scale: the young man is about 175 cm tall and thin; ...", "ama": "..."}
}
```

- `scene`：每個場景寫一次固定格局（家具在哪、門在哪、比例）。格子用 `scene` 欄位指定要接哪一個，**沒寫就不接**。
- `scale`：每個角色的身高和相對比例（「比主角矮一個半頭，頭不比他大」）。格子裡有誰（`cast`，或 refs 裡的角色），就接上誰的。
- 舊的 `scene_refs`（從參考圖推斷場景）只在整份分鏡都沒有任何格子寫 `scene` 時才用，`lint` 會警告。不用它的原因：從帳篷紗網往外看的格子拿營地格當參考，被接上「三頂帳篷一排」，結果畫出從帳篷裡看不到的帳篷。

## lights

```json
"lights": {
  "night_camp": "Late at night: the sky is a slightly lighter flat black than the arrow bamboo ...",
  "tent_inside": "Clean line art, inside a small dark dome tent at night: everything is solid flat black ...",
  "morning": "Bright morning: the sky and the background are plain white with crisp shadows; no black background."
}
```

- 每一段劇情只用一種光線狀態，寫一次、每格用 `light` 指定，不要每格各寫各的。
- 白天狀態一定要寫明背景是白的：A 畫風（少年漫畫線稿）預設愛用平塗黑，第二本的早上、白天格子全變黑。
- 要讓光線前後一致，同一狀態的第一格畫好、挑定後，後面同場景的格子可以用 `panel:<那格>` 當參考；但參考格會連構圖一起帶進來（見 prompting.md），只在鏡位相同時這樣做。

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
| `refs` | 參考圖，依序對應 prompt 裡的 `<image1>`、`<image2>`：角色 id（可加 `:head`、`:bust`）、`scene:<id>`、`panel:<id>`（那格挑定的圖）、`file:<out 底下的路徑>`。每張參考圖都要在 prompt 裡提到，沒提到的照樣會把構圖帶進來 |
| `scene` | 這格接哪個場景的固定格局（`consistency.scene` 的 key），可以是清單；視角跟場景卡不同的格子（從帳篷裡往外看、特寫）不要寫 |
| `light` | 這格的光線狀態（`lights` 的 key） |
| `cast` | 這格畫面裡的角色。沒寫就用 refs 裡的角色；只用文字描述、沒帶參考圖的角色要寫進來，只拿來當花樣參考的（睡衣的碎花）寫 `[]`。人數檢查和比例句都看它 |
| `heads` | 畫面裡的人數，算上不是角色的人（病人、護理站裡的同事）。數字：brief 寫「剛好 N 人」，`lint` 的單人、雙人提醒也照它；一段文字（「一群看不清的病人，不用數」）：brief 照抄，檢查員照描述判。沒寫就是 `cast` 裡的人數。比畫出來的角色還少是錯 |
| `prompt` | 英文。描述畫面看得到的東西，見 prompting.md |
| `n` | 候選張數，預設 2；改動參考圖的格子給 3 |
| `pass` | 用到 `panel:` 參考的格子設 2，第二輪才畫 |
| `screen` | 這格是透過螢幕看到的：加邊框和鏡頭點 |
| `pip` | 螢幕右下角的子畫面，填另一格的 id（例如對方的視訊畫面） |
| `flashback` | 回憶：無框、邊緣暈白 |
| `focus` | 裁切重心 `[x, y]`，預設 `[0.5, 0.5]`。圖的比例跟格子差很多時（2.35:1 的外景放進 3.6:1 的長條），重要的東西被切掉就調它，例如屋頂在上面就用 `[0.5, 0.2]` |
| `mirror` | `true` 時排版前把圖左右翻轉。用在先說話的人被畫在左邊的時候（由右往左讀，他要在右邊）；只能用在畫面裡沒有字、也沒有分左右的特徵（單邊耳環、寫在胸前的字）的圖。候選檔不會被改 |
| `zoom`、`zoom_at` | `zoom` 小於 1 時把圖縮小，貼回同樣大小、用圖四角顏色填滿的底，`zoom_at` 是貼的位置（`[1, 1]` 是右下）。給背景是平塗色的特寫騰出放字的空間（p19 的框蓋住了眼睛）。範圍 0.2 到 1 |
| `continuity` | 這格要跟哪些已選定的格子對得上（id 清單）。`review` 會把它們和 `panel:` 參考、同場景最近的已選定格子一起列進 brief，讓檢查員開圖比對。同一個角色每一格長得一不一樣，另外用 `review --cast` 查 |
| `fill` | 整格塗一個顏色（`"black"`），不送模型畫：停頓、黑暗裡只有聲音的格子 |
| `text` | 字，見下 |
| `sfx` | 狀聲詞 `{"text": "喀", "at": [0.7, 0.3], "size": 0.3, "angle": -12}` |

## text

```json
{"kind": "screen", "text": "你後面那個廁所門，", "pos": "tr", "per_col": 8, "scale": 1.0}
```

- `kind`：
  - `speech`：橢圓框，在場的人說的話。
  - `voice`：黑底白字的橢圓框，看不到是誰在說的聲音（帳篷外叫你名字的那個）。
  - `screen`、`phone`：雙框方形，從螢幕或電話傳來的聲音。
  - `narration`：方框，旁白。
  - `title`：作品標題，白字黑底。
  - `tag`：角色第一次登場的名牌，白字黑底。
- `pos`：放在格子的哪裡，兩個字母，第一個是 `t`（上）、`m`（中）或 `b`（下），第二個是 `r`（右）、`c`（中）或 `l`（左），例如 `tr` 是右上。由右往左讀時，先讀的放 `tr`，後讀的放 `bl`。讀者照「越高越先讀，一樣高就先讀右邊」排框的順序，所以後面的框要放得比前面的低。框要放在說話的人那一側（paneling.md）。
- 同一格裡的框互相蓋住時，`plan` 和 `pages` 會印 `WARN lettering`：p6 的數數被旁白框蓋住，只剩「……」。
- `per_col`：一欄最多幾個字，框放不下會自動再減。
- `\n` 強制換欄，標題用（`一個人在家\n開視訊`）。
- 直排：標點自動換成直排字形，不會落在欄首，開括號不會落在欄尾；長句平均切成兩半，不留單字一欄。
