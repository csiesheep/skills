# 這一輪要調的地方（ghost-story-weitong-v4 → ghost-comic-v2）

2026-11-21 開跑前的檢查，和跑的過程中記下來的。每一條最後要變成兩個 skill 的修改，或明確決定不改。

## 開跑前查到的

| # | 哪裡 | 問題 | 這次怎麼處理 | 要改的 skill |
|---|---|---|---|---|
| 1 | v4 → comic | v4 只產 `story.md` 和 `speakers.md`，沒有劇本，所以 `from_screenplay.py` 用不上；漫畫的 board 只能手寫 | 從 `story.md` 和 `speakers.md` 手寫 board | ghost-comic-v2：加「從 v4 長篇開始」的段落，或寫一個 `from_story.py`，讀 speakers.md 的台詞表 |
| 2 | v4 的長度 | 2,300 到 2,700 字、台詞佔 35 到 45%，照畫約 10 到 12 頁、40 到 50 格；台詞是不加「他說」的口語，漫畫的字框放不下 | 擁有者選「整篇照畫」；台詞要縮，但不能改掉笑點和線索 | ghost-comic-v2：寫明長篇怎麼縮台詞（哪些字可以拿掉、笑點和回收不能動） |
| 3 | 鬼的露出 | v4 的 style.md 說最大驚嚇「不描寫五官」；ghost-comic 預設鬼留白；擁有者這次說「按照故事，可以清楚露臉」 | 照故事：X 光片上的骨頭和玻璃後面的她都可以畫清楚 | 兩個 skill 寫明：v4 的「不寫五官」是文字規則，畫面另外由擁有者決定 |
| 4 | 關卡 | 擁有者這次「只看故事和成品」，可是 ghost-comic 的三個關卡（風格、設計、版面）預設都要擁有者決定 | 角色卡、場景卡、版面由我挑；故事一定先給擁有者看 | ghost-comic-v2：把「擁有者把關卡交給我」寫成一個正式的模式 |
| 5 | GPU 交錯 | v4 的盲測要用 H3 TTS（fair_asr.py），漫畫用 Qwen；同一張 GPU，不要交錯跑 | 先把故事全部做完，再開始畫 | 兩個 skill 都提醒一次 |

## 跑的過程中

- 2026-11-21 擁有者：「好 A」（v4 → comic 用 A：先寫 v3 劇本格式的分鏡稿，再跑 `from_screenplay.py`）；「you can decide everything until the comic is ready」——故事關卡也交給我，ghost-comic 的 step 0（故事先給擁有者看）這次跳過。要寫進 ghost-comic-v2：擁有者可以把「故事關卡」也交出去。
- from_screenplay.py 在這篇（41 格、10 頁、揭露 p33）正常；但劇本裡「**她**（對講機）：」被當成 `speech`，應該是 `voice`（聲音從機器出來）。**ghost-comic 要修：** note 含對講機、電話、廣播、手機時，給 `voice`。角色 id 自動編成 c2、c3、c5，寫 prompt 不好認；建議劇本人物可以帶英文 id。
- 角色卡淡彩（ink_tint tint）：兩個視角上色不一致（我的牛仔褲正面深灰、側面淡藍）。refs 只裁左邊所以這次沒影響；**ink_tint 要修：** prompt 加一句「both views identical colours」。綠色乖乖的淡綠跑到候診區長椅的靠墊上（scene_tint 寫了 green snack packets）。
- lint 把貓也算進 heads；build_board 裡人物數和貓要分開寫，現在用加一處理。
- 第一批檢查（p1–p8，16 張候選）：只有 2 張全對，6 格重畫。重複的問題：牆上告示畫出假字（場景描述沒寫「牆上什麼都不貼」）、候診區格局每格不同、角色卡帶進兩副眼鏡、位置和道具漏畫。**畫風：** 室內格偏「細線淡彩插畫」，乾筆和暈染比外景少——角色卡本身就偏插畫，ghost-comic-v2 要在 sheets 那步要求角色卡也是粗乾筆水墨（現在的 sheet 文字只說 ink wash）。**ghost-comic-v2 要加：** 場景描述預設「牆上不貼任何告示」。
- 第一輪全部檢查（4 位檢查員、p1–p41）：82 張候選只有約 8 張「全對」。檢查員對背景告示、看讀者、道具位置都判不合格；照這個標準重畫會沒完沒了。我把標準分兩級：**劇情要的東西錯了才重畫**（11 格：分割成兩格、阿斌沒肚子痛、籠子不在台上、X 光片畫成房間、鬼是娃娃臉、螢幕不是 X 光、坐姿懸空、貓不在籠裡、手機亂碼），其他 27 格接受。**ghost-comic-v2 要加：** qa_checklist 分「劇情錯（必改）」和「畫面瑕疵（可接受）」兩級，檢查員照兩級回報。
- X 光片格畫成整間 X 光室：因為格子帶了 scene s4，固定格局整段進 prompt。**規則：** 螢幕／底片／監視器的滿版畫面不要給 scene。
- 鬼的角色卡本身是大眼娃娃臉，帶 ghost:head 的格子都會變可愛。揭露格拿掉鬼的參考圖、用文字寫成年人凹陷的臉。**ghost-comic-v2 要加：** 鬼的角色卡就要寫成年人、凹陷、不是娃娃——設計關卡就把可愛臉刷掉。
- 第一位盲讀者讀懂主線（女生是三年前的飼主、灰灰是她的貓），卡在：對話框貼錯人（p3、p19 先說話的人站左邊 → mirror）、日子沒交代（禮拜四、禮拜五）、「我自己提籠子出來」沒說是什麼意思（分鏡稿縮台詞時把「我不記得我有走進倉庫」縮掉了）、手機是誰的。全部用字修，不用 GPU。**ghost-comic-v2 的分鏡稿規則：** 從長篇縮台詞時，反轉的那一句和每個日子的時間標記不能縮掉；from_screenplay.py 可以檢查 brief 的反轉句是否還在某一格。
- 2026-11-22 擁有者看完成品：(1) 字框儘量不要擋住人臉；(2) 有些對話框不知道是誰說的——說話的人不在格子裡就在框下加小臉，一格兩人多框也會搞混；(3) 主角和院長表情都一樣、情緒太少（第 7 頁右上主角沒有害怕）；(4) 「可以幫牠照一下嗎」改「可以幫牠照一下X光嗎」。**已做：** manga.py 加 `who`（尾巴指向說話的人、不在格裡就掛小臉）、`pos: "auto"`（避開臉、照閱讀順序、太擠就整格縮小重排）、每格 `faces`（三位檢查員在 0.1 格線上標）；三位檢查員評 40 張臉有 25 張太平或不對（主角 16/17、院長 7/8），18 格用 repaint 只改臉（每格 2 張、19 GPU 分鐘），全部挑到可用的。**ghost-comic-v2 要記：** 角色卡是 neutral expression，格子會沿用——prompt 要寫漫畫式的表情，選完圖逐臉檢查。

## 影片（2026-11-22 起，ghost-film + ghost-reel）

- 擁有者的決定：長度可超過 3 分鐘、分集；旁白一個聲音＋每個角色一個聲音、不對嘴；用漫畫選定的格，直式 32 格裁 9:16，橫式 9 格（p1 p21 p24 p32 p33 p34 p35 p36 p37）重畫成 9:16；音樂音效照 ghost-film。第一個交付物是約一分鐘的測試。
- 先寫劇本：`film/video_screenplay.md`（`film/count_screenplay.py` 從字數算秒數）。v1 → v2 → v3 存在 `drafts_video/`（v3 即現檔）。分五集：2:39／1:56／2:34／2:16／1:33，約 10:58。
- **ghost-film screenplay_short 的規則，和這份長篇分集怎麼碰在一起：** ①「第 0 秒大標題字」這次不用，照擁有者筆記；第 0 秒是一句旁白加同一句字幕（沒鬼）。②每集開頭不能是片名卡（審稿員：陌生人只看到第二集時會直接滑走），集數改角落小字，第 0 秒用一句具體的話（接上一集最後一句、反轉句重放、院長衝下樓）。③分集的懸念要靠畫面不只靠片尾卡：第一集的結尾補上她第一次出現（只看得到帽緣，不露臉），不然第一集 2:40 都沒有鬼。
- **故事本身的洞，劇本裡用旁白修了，要不要回寫 story_clean 由擁有者決定：** 「自動門一次都沒有開過」和阿斌每晚進出矛盾（改成「她來的那幾次」）；「那三天早上騎車回家」和禮拜五蹲到天亮矛盾（改成禮拜三、禮拜四）；X 光機和 X 光室的位置，乖乖改貼在窗下控制台（候診區這一側）。
- **審稿員會把這些當硬傷，下次寫分鏡稿或劇本時先查：** 監視器拍得到什麼（一台拍不到走廊底和櫃台，要兩台）；「停 3 秒、沒有旁白」下一行不能馬上旁白；對講機的聲音要上字幕；每一個日子和時間碼要在全集裡對得上；片名卡要和「第 0 秒一句話」分開算秒。
- 估秒的偏差：審稿員自己算和腳本差 ±5 秒；腳本沒算到的停格要寫成 [停]，卡要算進去。

### 一分鐘測試 A（2026-11-22，`film/reel/out/test_a_v4/`，61.5 秒，720p 8.6 MB）

- 做法：p1 重畫 9:16（兩輪，各 4 張候選，GPU 約 3 分）→ 聲音候選 14 條（12 分）→ 七段 H3（i2v，29 分）→ 旁白 9＋1 句 ref2va（約 29 分）→ `render.py`（full 約 7 分，`--reuse` 重混）→ `package.py`、`verify.py`、`asr_lines.py`、盲審一位（v2：6/10）。旁白用候選 A 第 2 條（擁有者說「都給你決定」，我只憑辨識讀回和說書調性挑，沒有聽）。
- **圖的比例**：漫畫格 41 張裡只有 22 張接近 9:16（512×1120 三張、544×992 十張、512×992 九張）；十張 800×992（p5 p8 p9 p14 p19 p22 p25 p30 p38 p41）是 4:5，裁 9:16 要切三成寬；橫的 9 張要重畫。skill 說的「32 張直式」要細分。`stills_both.py` 要在 comic 資料夾跑，畫要用 ghost-comic 的 manga.py，不是 film.py（film.py 會換成寫實模型）。
- **重畫要明寫物理位置**：第一輪「水痕」畫到玻璃門外的巷子，會和「沒下雨」的線索衝突；第二輪把「攝影機在門外貼著玻璃、水痕在門內白瓷磚上」寫死才對。
- **spans2.py 的檔名**：`VT_N01_s1_00001` 會被當成「N01_s1」不在 script.json 而整批跳過；要在 script.json 加 `N01_s1`、`N01_s2` 兩個 key，再另寫一個 mkpicks 把最好的一條對回 N01。角色的短句（`欸？` 0.4 秒）用整條檔案當 span。
- **ASR 會騙人**：「灰灰」被聽成「輝輝」，「阿斌」聽成「阿兵」，「坐」聽成「做」；單句窗口對前面有靜音的句子會幻覺出「詞曲 李宗盛」。盲審把它當硬傷，我用 `_vo_only` 量音量和整段辨識證明聲音在（-18 dB），所以不是缺陷。盲審 brief 要寫明「辨識失敗不等於聲音不見，請看音量量測」。
- **H3**：站著看手機的格，第一次他一路走向鏡頭，提示詞加「雙腳一直站在原地不動」後變成鏡頭推近；貓走到她腳邊會變寫實；水痕會自己擴大（對這部片是好的）。一段 5 秒的動作配 12 秒的三句話會出現 2.7 秒的停格，下一輪要給長鏡頭 10 秒的 clip 或把三句話分兩格。
- **片名動畫在亮底看不清**：`title_fx` 1 的白字疊在亮色玻璃上中間幾個字消失；調暗整個鏡頭（lift 1.5–1.8）會讓進出各跳一次亮度（-21／+18）。下一輪：把片名放在畫面暗的下半部，或給片名一塊暗底。
- **結尾卡**：一句超過十個字會被切掉（結尾卡的字不換行）；「測試」的卡不該出現在成品，成品是「下集：…」。
- **盲審 v2（6/10）**：滑走點是第 10 秒（同一張貓放 12 秒）；要補「她搖頭」近景（兩人鏡頭 10.9 秒太長）；開場的貓和灰灰長一樣（刻意，因為她的貓就是灰灰）；字幕「在櫃台滑手機」但畫面他站在門前（漫畫格的站位，旁白改成「站在櫃台前滑手機」）。
- 還沒做：阿斌、院長的聲音；十格 4:5 的裁切逐格看；其餘 8 張橫的格重畫；全片的鏡頭表。

### 2026-11-22 第二輪（擁有者四點意見）：格局、台詞、冷氣、開頭

- **平面圖**：v1 照板子上的文字畫，擁有者說跟很多圖不同；v2 從 41 格圖的多數整理（右前角櫃台、右牆：櫃台→X光室木門＋圓燈→X光窗與控制台→右長椅；左牆長椅與暗窗），擁有者「你決定吧，我們定一個最合理的平面圖，comic先重畫」。只有 p2 p9 p11 p18 p21 p30 偏離（櫃台在左或有冷氣／出風口），重畫（各 4 張）、挑圖、p30 重畫臉、頁面重排（`drafts_comic_plan/` 有舊 board）。ghost-comic-v2 已加 step 0「先畫平面圖」、`floor_plan.py`、`ink_tint.py check` 的平面圖／鏡頭警告、測試。
- **提示詞裡的否定詞**：寫「沒有冷氣」，4 張候選仍有 1–2 張畫出冷氣；只能挑沒有的。
- **polite.py speech 依名稱跳過已有的輸出**：新台詞用舊的名字（`VT_N04`…`N11`）就整批沒有重錄，v5 的旁白其實是舊稿（ASR 讀回「那年夏天，我在巷口…」對上字幕「說是助理…」才發現）。改文字就要換名字，或把舊檔移到 `_old_VT/`。**ref2va 參考句的字會漏進同字的句子**：開場句和參考句（也是開場句）同字，`N01h` 其中一條念出舊稿，多錄幾個種子再挑。
- **ASR 同音字**：阿斌→阿彬／阿兵、灰灰→輝輝／慧慧、牠→他，都不算錯；`asr_lines.py` 的 0.0 要先看讀回的字是不是別句（這次就是別句）。
- **H3 固定鏡頭**：提示詞要寫「不推近、不拉遠、不移動、構圖跟第一幀一樣」，只寫「鏡頭固定」會被推近（兩段動畫第一次都被推近，第二次才固定）。天花板頂端偶爾冒出一條垂線：`zoom` 放大把它切掉。

### 2026-11-22 第三輪：場景一致（平面圖 v4 → 總圖 → 同框修改）

- 擁有者：「平面圖和場景圖不一致」「重畫平面圖，再重畫場景圖」「當然要照 film 的正規做法」。做法：`comic/plan/plan_building.png`（`ghost-comic-v2/scripts/building_plan.py`，照比例的整棟平面圖，九個鏡頭）→ 固定文字塊（`masters3_jobs.py` 的 BIBLE：右前角淺灰櫃台、右牆木門＋圓燈→大玻璃窗→右長椅、左牆暗窗＋左長椅、平的後牆、窗外是 X 光室）→ 每個鏡頭 `fresh_draw.py` 四張總圖，挑一張 → 影片用的圖是總圖的 `edit_stills.py` 同框修改（只放人和貓）→ H3 動畫。
- **平面圖和總圖要互相核對**：v1–v3 的平面圖都和總圖不同（櫃台離門太遠、D 鏡頭畫出玻璃門、窗後畫成辦公室而不是 X 光室、後巷左右相反）。要逐個鏡頭問「這個鏡頭該看到什麼、看不到什麼」，寫進平面圖的圖例和提示詞。
- **模型不理「鏡頭往哪看」**：C 鏡頭（看向右前角、門在左遠處）四次都畫成沿長走道看門，和 A 差不多；沒辦法就接受最接近的一張，並說明。
- **深透視的靜止圖給 H3 會被推近或貓走近鏡頭**：開場貓三個種子都推近；取中段穩定的幾秒。人物小的整間房遠景（修改圖裁近 1.2–2 倍）動畫穩得多。
- 候診區的圖（A/B/C/D/OUT）、`plan/picked/`、`plan/picked_v2/`（舊版）都在 `comic/plan/`；影片用的 7 張修改圖在 `film/reel/fx6/`，動畫 `clips/*_s5x/s6x`，鏡頭表 `make_shots6.py`，版本 `out/test_a_v7/`。
- 還沒做：漫畫其他格改成用總圖修改（目前只重畫了 p2 p9 p11 p18 p21 p30）；阿斌、院長的聲音；十格 4:5 的裁切；橫的 8 格重畫。

### 2026-11-22 完整長片：劇本（`film/long_screenplay.md`，由 `film/build_long_screenplay.py` 產生）

- 擁有者：「重新寫劇本，符合原本故事中的口語」「最後會產生一個長影片，和切成每個小於3分鐘的短影片」。旁白和台詞由程式從 story_clean 取，140 行每行一次、順序不變；新寫的只有開頭句（擁有者給的）和短片開頭句。
- **平面圖 v4 是所有場景圖的鏡像**：門畫在圖下方，面向門時圖右是人的左。審稿員才抓到。v5 把門放圖上方，`building_plan.py` 加 `sees` 用外積檢查每個鏡頭的左右。D、X1 總圖原本就和 A 互相矛盾，水平翻轉。之前我對擁有者說「相符」是錯的。
- 兩輪審稿（留存／按讚／分享）：6/7/6 → 6/7/6。第二輪還抓到鏡頭視角拍不到長椅、監視器拍不到證據、X 光片提早露骨頭、倉庫提早指認籠子。

### 2026-11-22 4 支短片版（`film/long_screenplay_4.md`，`film/build_four.py`）

- 擁有者：「有沒有可能縮成4支」「給我看4支的劇本」。只刪不改寫，刪除線留在劇本裡。切點改成 她第一次開口／這個主意簡直天才／紅燈自己亮了、機器嗶，四支長度平均，比原估的 23% 少刪。秒數假設語速 1.15 倍（還沒試聽）並留 8%。
- 審稿員抓到刪字造成的斷句（「阿斌那句話」接到別人的話、「鐵架⋯就把燈關了」沒主詞、院長沒人告訴就開電腦）：刪字後要再讀一次剩下的句子，不能只看字數。

### 2026-11-22 skill 更新：先平面圖，再場景圖

- 擁有者：「Update the story v4 and comic v2. 特別是先產生平面圖，在產生場景圖。」
- story v4：新增 step 1b（寫文字前先畫平面圖和行蹤表，等「平面圖對」），重講和審稿都要對照它。
- comic v2：step 0 改成 平面圖 → 固定文字和鏡頭 → 每鏡頭一張空場景圖 → 總表確認 → 人物格是場景圖的同框修改。`building_plan.py` 有 draw、jobs、pick、panels；`floor_plan.py` 已由它取代。
- 實測：反向鏡頭 D 照真實左右寫 0/4；由近到遠列物件、畫完鏡像 2/4（另 2 張變成上下兩格）。X1 鏡像 4/4 左右正確。`panels` 在 p12、p9 各 2 張，房間都維持總圖；p9 有 1 張人站錯櫃台那一側。
- 檢查只管左右和視角，不管牆和距離。整本漫畫還沒用這個流程從頭畫過。

### 2026-11-23 長片開工

- 擁有者定案：4 支版劇本 v3，「那隻貓⋯」給「我」；語速 1.15、阿斌 A、院長 A；**「我」就是旁白的聲音**（我一開始另外設了一個聲音，被糾正）。
- 全片配音 `film/vo/full_script.py`：175 句、167 條要錄（每條最多 28 字），她的台詞重複時用同一條。估 3.7 GPU 小時。

## 2026-11-22 聲音選 C

- Owner 聽過 A／B／C 對照後「都選C」：五個角色都用重新演得更有精神的新錄音，混音時再升 1 個半音，1.15 倍速。
- 演出指示要短、用英文。長的中文「有精神」指示讓 H3 把指示念出來（B2、D1 失敗），改短後可用。給 ghost-film 調整時值得寫進去。
- 旁白 113 條用新名稱 `VG_*`（`full_jobs_c.py`），因為 polite 會跳過已存在的名稱。
- 角色對白（54 條）先不錄，等 owner 決定對嘴測試、全部隨影片產生或分開配音。

## 2026-11-22 對嘴測試

- Owner 選「先測一場對嘴」。ghost-film 的正規做法本來就是角色台詞在 H3 clip 內說（SKILL 步驟 2、3），這部一開始把對白排成分開配音是我偏離了 skill，不是沿用。
- 風險：i2v 不吃聲音參考，clip 內的聲音不會是 owner 選的 C 版阿斌／我。測試要讓 owner 同時聽到這個差別。
- 測試：`film/reel/lip_jobs.json`（C master 裁切加兩人）、`prompts/lip01.txt`（14 秒對嘴，2 個 seed）、`prompts/lip01m.txt`（閉嘴，疊 C 版配音）。旁白錄完才跑，H3 與 Qwen 不交錯。

## 2026-11-23 對嘴測試結果

- 14 秒 i2v 三句一鏡：台詞可對，但鏡頭後退、房間變樣，閉嘴版還多出冷氣。
- 14 秒 FL2VA（頭尾同一張圖）：更差，鏡頭突然推近再跳回，最後一句被切掉。寬高要能被 32 整除（720 會報錯，用 576x1024）。
- **可用做法：一人一句的 5 到 7 秒 i2v，全部從同一張圖開始**，8 條房間都穩。H3 句前會念亂語或提示詞（如「台灣國語」），要用字幕時間裁掉，提示詞不要寫語言和語氣形容。
- 「嘴巴閉著、沒有說話」的 clip 音軌仍有亂語，配音版一律靜音使用。
- 旁白 113 條：8 條重錄後 5 條確定可用；「死黨」(L022)、「院貓灰灰」(L024b)、「收在」(L139a) 每條都被 ASR 聽錯，要人耳確認。
- 對照影片：`film/lip_test.mp4`（`reel/make_lip_compare.py`）。

## 2026-11-23 對白：C 版配音，但嘴巴要動

- Owner 先選 B 分開配音，看到做法後補充：「配上影片時，讓角色的嘴巴也要動，不動很奇怪」。
- 做法：每句一段 5 到 7 秒 i2v，從該鏡頭首圖開始，讓說話者說該句；音軌一律靜音，把 C 版配音對到嘴動的時間。嘴型只是節奏接近，不是逐字對嘴。
- 需要嘴動 47 段：阿斌 14、院長 12、我 19、她 2（L086、對講機那段共用一段）。不需要：院長回憶旁白 7 句（畫面沒有他在講話）、她帽子遮臉的 3 次。
- 首圖要檢查說話者的臉看得到。鏡頭 D 的「我」站在櫃台後、靠近攝影機，可能背對鏡頭，這類鏡位要改走位或改用反拍。

### 2026-11-23 嘴動片段驗收（42 段，GPU 約 150 分鐘）

- 實際 42 段，不是 47：同一句拆開錄的併成一段（L034、L042、L062），L045、L072 說話者背對鏡頭不做。
- `clip_check.py` 42 段全過，但逐格看有 8 段壞掉：5 段畫出字幕，2 段鏡頭推近，1 段地上的水變大。**機器檢查抓不到這些，一定要看 strip。**
- 片段音軌不用時，**提示不要引用台詞**。H3 會把引號裡的字畫成字幕或對話框；拿掉後 5 段全部乾淨。
- **不要在提示寫「三腳架」**，H3 真的畫了一支三腳架。
- **8 到 10 秒的片段容易自己推近或長東西**，改提示也救不回來。長句改用同一首圖、同一說話者的 5 到 7 秒穩定片段來回播放（每次回到首幀，沒有跳接）。s16 L042、s23 L062、s24 L069、s45 L105 用這個做法。
- 要看嘴型必須放大說話者的頭（`reel/mouth_sheet.py`），整張縮圖看不出來。最終選擇在 `reel/talk_final.json`。
- 首圖教訓：說話者要看得到臉；阿斌改到鏡頭 A；叫模型「移除」物件可能全部移除（s29 兩個外出籠都不見，要再補一個）；監視器畫面要從 A master 改。

### 2026-11-23 無對白動態片段第一輪失敗（GPU 154 分鐘）

- 提示寫「地上的水漬不變大、不擴散」，H3 在約 40 段裡長出一灘水。**否定句裡提到的東西照樣會被畫出來**，不想要的東西一個字都不要提。
- 「燈輕輕閃」「光線極輕微變化」「天慢慢亮」會造成整段亮度跳動，光線變化改在算繪時做。
- 「往前走」會一路走到鏡頭前變大；要寫「在遠處走一小步」，並寫清楚背對或面對鏡頭。
- 開大批之前，**先拿 3 段試跑看 strip**，這次沒試就花掉 2.5 小時。
- 沒有人物的空景用靜圖加運鏡，比 H3 穩定。
- 第二輪試跑：拿掉水和光線字眼後穩定；但主體是遠處小貓的鏡頭 H3 會自己推到貓臉（s01、s03），貓的鏡頭 s01 s03 s12 s50 s68 改靜圖運鏡。

## Silent motion clips, final count (2026-11-23)
- Pass 3 used the talking-clip look line (「人物在畫面中的大小從頭到尾不變」「人物的腳一直在原地」): 6 of 8 held the frame, against 19 of 26 in pass 2 with the shorter look line. Use this line for every silent clip from the start.
- s26 pushed in on both seeds and s60 turned night into day on both seeds: these two are stills with a camera move.
- clip_check passed s26 pass 3 (a steady push has no jump), so a pass from clip_check does not clear a push-in. Read the strip.
- s40 pass 2 invented a living room for its first 1.4 s, then cut to the right face: offset 1.6 keeps the clip.
- Final: 31 motion clips in film/reel/motion_final.json. The rest are talking clips or stills with a move.

## Long film assembly (2026-11-23, film/longcut/reel)
- make_long.py builds the 68-shot plan from shot_table.json: each talking line plays its own clip from frame 0, cut or ping-ponged ("plates") to the C voice's length; other lines sit on the shot's motion clip or still. Voices: C take, +1 semitone, 1.15x, trimmed to the ASR span.
- render.py `scene` matching across a whole part pulled bright shots to the group median (s65 177 -> 124, day shot s67 darkened). Do not group by part. Set darkness per shot with `lift` from the still's mean instead (DARK in make_long.py).
- msjhbd.ttc draws ⋯ (U+22EF) as a box. Replace it with … before rendering subtitles.
- render.py `end_question` cannot wrap: a 19-character question ran off the 1080 frame. Put long questions on an overlay in two lines.
- X-ray reveals the script times to words (cage only, then hands, then skull) need a drawn camera plate (camera_shot in make_long.py) with the skull masked until its word. A frame_crop push or pull shows everything at once.
- s24: alternating talking clips made the 乖乖 bag jump between table and hand at every cut. Fix: retake the later lines from a frame after the bag is lifted (tk4_s24_*), and start L068 at 1.5 s.
- One sequential render of 10:28 took 1 h 50 m. Four parallel part renders (run_parts.py) took 29 min, then `render.py --reuse` mixes sound over the joined pictures. Two parts reading the same voice wav at once can crash sfx.read_raw (temp file in use): rerun that part alone.
- Shorts: cut_shorts.py joins an opener and card rendered once (make_extras.py) with stretches of the long film. No second render. Lengths 2:37 / 2:38 / 2:58 / 2:38.
- package.py aims every file at 9.3 MB: for the 10:28 long film that is about 25 kb/s of video, unwatchable. The long film's review copy is 720p crf 25 instead (79 MB); the 9.3 MB target only suits videos under 3 minutes.

## Chained segments (owner: 「後面的段落應該要用前段落的尾幾幀當成頭幾幀」)
- Problem: inside one shot, every segment's clip started from the shared still, so each cut snapped back to the first pose. Fix: `longcut/reel/chain.py` generates segment n+1 from the frame segment n actually shows at its cut (after ping-pong mapping), round by round (6 rounds for 30 segments, ~2.7 min per 5 s clip, ~80 min total).
- H3 refuses requests under 5 s ("outside H3's trained range (5-15 s)"); a 4 s request fails instantly.
- 7 s chained clips pushed in (s45b). Keep chained clips at 5 s and ping-pong longer segments.
- Silent beats with a person walking toward camera still pushed in (s16b): a bad link also spoils every later link in the chain, so retake from the break onwards (s16b + s16c).
- clip_check passed both push-ins (light and step numbers looked normal) — the strip sheet is the real check.
- Corridor-perspective start frames pushed in on every seed (s16b 110/112, s45b 110/112/113). What worked: keep a short push as a camera move when the next link is chained from its shown end (s16b, 2 s), and for a long segment play the push once and then ping-pong only the settled last 2 s (s45b, `ch_s45b_s113_hold.mp4`), never a full reverse (it pulls back out).
- Chaining left the timeline unchanged (628.3 s), so bed.wav, extras_v2 and endcard_v1 were reused; long_v5 render 35 min, long_v6 + shorts_v3 cut 7 min. Check: before/after frame pairs at each chained cut all matched (s63b slight drift).

## Polish pass (owner: 「你再打磨一遍」) -> long_v8, shorts_v4
- Review: shot sheet of all 108 segments, loudness (-15.0 LUFS long, LRA 4.1), voice gaps (max 3.3 s at the s40 black), chained cuts.
- Long stills that carry an event can get a synthetic plate instead of H3: s60 (17 s, dean asleep) now has the phone dark -> lit + 2 px shake + buzz.wav during L131b -> dark (`longcut/reel/polish.py`, hooked at the end of make_long.py). Darkening a lit screen by brightness threshold left blobs; filling the convex hull of the screen with a dark glossy colour worked.
- cut_shorts.py now runs alimiter 0.89 on every output (short1 peaked at -0.1 dB before).
- Not done: cat shots s12 and s68 stay stills (H3 pushes in on a small, distant cat).
