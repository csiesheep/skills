# genre.json：一個類型要填的東西

一個類型是一個資料夾，`STORYPIPE_GENRE` 指到它。裡面是 `genre.json` 和 `prompts/`。
程式只認 `genre.json` 的結構，不認任何一個類型的字；鬼故事的字全在 `genres/ghost-story/`。

每個欄位後面給兩個例子：鬼故事（已經做完的）和笑話（草稿，還沒驗證過資料）。

## 最外層

| 欄位 | 意思 | 鬼故事 | 笑話草稿 |
|---|---|---|---|
| `name` | 類型 id，也是權重表裡的 `genre` | `ghost-story` | `joke` |
| `label` | 類型的中文名，報告和 CLI 用 | 鬼故事 | 笑話 |
| `unit` | 一個單位叫什麼，報告用 | 故事 | 笑話 |
| `title_prefix` | 產出標題的開頭（也是假後端的標題） | `[經驗]` | `[笑話]` |
| `better_word` | 盲讀頁的問法「A 比較＿」 | 毛 | 好笑 |
| `is_unit_description` | 標註欄位 `is_story` 的說明：什麼算一個能獨立讀的單位 | 問卦、討論、系列中段都是 false | 轉貼整篇笑話集算 false |

## `source`：來源和訊號

| 欄位 | 意思 | 鬼故事 |
|---|---|---|
| `kind` | 目前只有 `ptt` | `ptt` |
| `board` | 看板 | `marvel` |
| `tags` | 標籤 → 索引檔。百分位在「同標籤、同年份」的母體裡算，所以每個標籤要有自己的索引 | `{"經驗": "data/index/marvel_經驗.jsonl", "翻譯": "data/index/marvel_翻譯.jsonl"}` |
| `default_tag` | 沒標 `source_tag` 的單位算哪個標籤；校準和兩兩比較只用這個標籤 | 經驗 |
| `default_query` | `collect` 指令的預設搜尋 | `經驗 recommend:30` |
| `score_from_year` | 這年之前的文推文太少，不算分數，只進範例池 | 2007 |

## `axes`：類別軸

每個軸標註時選值、統計時算權重、產生時依權重抽。順序就是抽樣順序。

| 欄位 | 意思 |
|---|---|
| `key` | 標註欄位名、權重表的 key |
| `label` | 中文名；規劃書上「場景：…」就是它 |
| `fixed_label` | 使用者指定時，規劃書「使用者指定的欄位」裡的名字；沒給就用 `label` |
| `flag` | CLI 參數名（`--setting`）；`resolve()` 用 key 或 flag 都找得到 |
| `multi` | true 是依序選幾個，第一個是主要的；統計另外算「任一位置」的表 |
| `max_items` | 多值軸最多幾個 |
| `description` | 給標註模型看的欄位說明 |
| `values` | key → 中文標籤；標籤用「：」分開短名和說明，報告只印短名 |
| `aliases` | 使用者的說法 → key；對不到時會用標籤做子字串比對，對到多個就報錯 |
| `detail` | 可有可無：這個軸附帶的一句自由文字（鬼故事的 `setting_detail`），有 `key`、`description`、`max_chars` |
| `plan_notes` | 可有可無：某個值被抽到時，規劃書多加一句提醒（鬼故事的反轉、有解釋） |

鬼故事三個軸：`setting`（22 個場景）、`mechanisms`（15 個機制，多值，最多 3）、`ending`（4 種結尾）。
笑話草稿：`form`（一句話、對話、短故事）、`devices`（諧音、反轉預期、誇張、自嘲…，多值）、`topic`（家庭、職場、動物…）、`ending`（一次、連環、反高潮）。

| 欄位 | 意思 | 鬼故事 |
|---|---|---|
| `pair` | 兩個軸的 key，統計算它們的組合表，抽樣時第二個軸有七成機率照第一個軸的條件抽。第一個要排在第二個前面 | `["setting", "mechanisms"]` |
| `example_axis` | 範例池依這個軸的值各留最多 25 個，錨點提示從同值的範例抽 | `setting` |
| `example_match_axis` | 結構範例從這個軸主要值相同的範例抽 | `mechanisms` |

## `cap`：露出上限

每個類型都要有一個：一個整數刻度，規劃器給寫手一個上限，評審檢查有沒有超過。鬼故事裡它是最有用的約束。

| 欄位 | 鬼故事 | 笑話草稿 |
|---|---|---|
| `key` | `ghost_explicitness` | `offence` |
| `label` | 鬼的露出上限 | 冒犯程度上限 |
| `short` | 鬼露出（報告的短名） | 冒犯 |
| `flag` | `ghost` | `offence` |
| `min` / `max` | 0 / 3 | 0 / 2 |
| `description` | 給標註模型的刻度說明 | 0 無；1 輕微；2 明顯針對群體以外的對象 |
| `levels` | 每一級的短名，盲讀頁和報告用 | 不露面、只有跡象、一瞬間看見、可以清楚看見 |
| `words` | 使用者說法 → 等級 | 不露面=0、間接=1、一瞬間=2、清楚=3 |

## `beats`：節拍

key → 中文名。標註模型給每個節拍佔全文的比例，規劃書換算成字數。鬼故事六拍（正常、小異常、否認、升級、揭露、餘波）；笑話草稿兩拍（鋪陳、笑點）或三拍（鋪陳、誤導、笑點）。

## 自由文字欄位

| 欄位 | 用途 | 鬼故事 |
|---|---|---|
| `anchors` | 清單：讓它像真的細節類型。高分範例的錨點會變成規劃書的提示。有 `key`、`label`、`description`、`max_items`、`max_chars`、`plan_hint` | `realism_anchors`，最多 6 個、每個 15 字 |
| `moment` | 一句話：最關鍵的那一刻 | `scariest_moment`，40 字 |
| `premise` | 一句話前提，不抄原文；高分範例的前提變成規劃書的結構範例 | `one_line_premise`，45 字 |

`max_chars` 同時是 `compare` 指令檢查格式遵守的門檻。

## `voice_markers`

key → 說明。標註模型只勾實際出現的；統計算高低分組的對比；`scare` 拿每一個當特徵。
`translated` 是特別的：`stats --exclude-translated` 和批次報告認得它。沒有可以不給。

## `length`

| 欄位 | 鬼故事 |
|---|---|
| `presets` | 極短 400–700、短 800–1200、中 1500–2500、長 3000–4500、超長 5000–8000 |
| `aliases` | 短篇→短、長篇→長… |
| `min` / `max` | 300 / 12000（使用者能指定的範圍） |
| `sample_clamp` | 沒指定長度時，從高分組 p25–p75 抽再夾到這個範圍：800–4000 |

## 規則、口味、風格

| 欄位 | 意思 | 鬼故事 |
|---|---|---|
| `rule_sets` | 每套規則一個子目錄：`dir` 是 `prompts/` 底下的目錄（根目錄是 `""`），`styles` 是風格檔目錄 | `v2`（根目錄，`styles`）、`restrained`（`restrained/`，風格用 `v1/styles`）、`v1` |
| `tastes` | 口味名 → `rules`、`summary`、`aliases`。第一個是預設 | 直接→v2、留白→restrained |
| `styles` | 清單，每個 `key`、`label`、`aliases`、`summary`；第一個是預設；每個要有 `prompts/<styles 目錄>/<key>.md` | ptt、minimal、humor、oral、literary、report、elder |

## `verdict`：評審的面向

`dims`：欄位名 → 說明，每個 1 到 5 分；程式另外固定加 `overall`（1 到 10）、`passes`、`fix_notes`。
`cap_dim`：哪個面向對應露出上限的處理，校準時單獨看它分不分得開高低分組。
鬼故事：realism、slow_burn、ghost_restraint（cap_dim）、ending、voice。
笑話草稿：setup、punch、offence_restraint（cap_dim）、voice。

評審規則本身在 `prompts/<rule_set>/judge.md`，面向的名字要跟那裡一致。

## `signal`：第二個品質訊號

| 欄位 | 鬼故事 | 笑話草稿 |
|---|---|---|
| `positive_name` / `negative_name` | 毛率 / 虛率 | 笑率 / 冷率 |
| `positive` | 推文裡算正向的 regex：好毛、雞皮疙瘩、可怕… | 哈哈、XD、笑死、笑噴 |
| `negative` | 算負向的 regex：虛、唬爛、小說… | 冷、老梗、看過了、不好笑 |
| `min_comments` | 推文少於這個數不算比例 | 10 |

沒有也行（`scare`、`pairwise` 的第二組配對會跳過），但那就只剩推文數一個訊號，而受歡迎不等於好。

## prompts/ 要有什麼

- `annotate.md`：標註說明，照這份 genre.json 的欄位寫判定規則。只給標題和本文，不給分數。
- `style_guide.md`：寫手規則（預設規則集的）；其他規則集各在自己的子目錄放一份。
- `judge.md`：自我檢查標準，面向跟 `verdict.dims` 一致；每個規則集一份。
- `pairwise_judge.md`：兩兩比較，回 `popular` 和 `scary` 哪篇是 A、B（欄位名沿用鬼故事的，第二題在這個檔裡定義成類型想問的事）。
- `styles/<key>.md`：每種風格一個，告訴寫手這篇的口吻。

## 檢查

`load_genre()` 會擋：別名指到不存在的值、口味用了不存在的規則、`pair` 順序顛倒、`cap.words` 超出範圍、`verdict.cap_dim` 不在 `dims` 裡、少了必要欄位。
改完設定先跑 `py -X utf8 scripts/pipe.py options`，再跑測試；測試裡的 `SecondGenreTest` 是一個完整的小類型範本，可以直接抄。
