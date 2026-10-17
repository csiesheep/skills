# 畫格子的 prompt：規則和踩過的坑

模型是本機 ComfyUI 上的 Qwen Image 2.1（int8），編碼器 qwen3vl 8B，15 步、CFG 1、euler/simple。參考圖從 `images.image_1..n` 進去，prompt 裡用 `<image1>`、`<image2>` 指它們。以下每一條都是實際發生過的事，大多來自〈一個人在家開視訊〉，括號裡註明的來自後兩本。

## 每格 prompt 的組成

1. 畫風前綴（`style_options` 選中的 `panel`），程式自動接。
2. 鏡位：wide shot、medium shot、close-up、從誰的位置看（`from the laptop's webcam position`）。
3. 場景和光線：`Same room, camera angle and lighting as <image3>: late at night, only the floor lamp is on, the walls, ceiling and window are solid flat black ...`
4. 角色和動作：寫畫面上看得到的姿勢和相對位置。
5. 保持外觀：`Keep his bird's-nest hair with the tall cowlick, very thick eyebrows and grey hoodie exactly as in <image1>.` 每格都重複記憶點。
6. 人數：只有一個人的格子加 `Only one person in the frame.`
7. 場景一致、人物比例：程式從 `consistency` 自動接。

## 坑和修法

這張表裡能用字面判斷的，`manga.py lint` 都會檢查（`panels` 也會先跑，有錯就不畫）：全身構圖抱胸、沒在 prompt 裡提到的參考圖、特寫和坐著的格子用全身參考、頭部裁切配上害怕或不笑的表情、坐在沙發或椅子上又帶場景參考、wall of、招牌海報、dim 和 lit by、顏色字、halfway、reflection、單人格沒寫 Only one person、角色特徵沒重複、角色第一次出場那格沒有名字、`panel:` 參考的輪次、不存在的 scene 或 light。排版時 `plan` 和 `pages` 會警告同一格裡互相蓋住的文字框。判斷不了的（同一人畫兩次、手的數量、大小）留給獨立檢查（qa_checklist.md）；讀者看不看得懂留給讀者檢查（reader_check.md）。

| 發生了什麼 | 原因 | 修法 |
|---|---|---|
| 小芳的視訊格畫成兩個全身的她並排站著；主角也被畫成兩個 | 角色卡上本來就有正面和側面兩隻，模型連「兩個人」一起照抄 | `refs` 指令只裁正面那一半當參考；prompt 加 `Only one person in the frame` |
| 視訊畫面畫成全身站姿 | 角色卡是全身，模型照抄姿勢 | `head and shoulders only, as seen by her laptop's webcam, not a full body` |
| 客廳場景卡畫成棕色沙發、粉紅拖鞋，顏色跟著跑進格子 | prompt 有顏色字 | 參考圖一律轉灰階，頁面也轉灰階；prompt 不寫顏色字（pink、brown、bluish） |
| 「dim living room, lit by the laptop」畫成灰濛濛的寫實光影，跟線稿畫風不合 | dim、glow、lit by 這類字會拉出寫實光影 | 改寫成 `The room is solid flat black; he is drawn in clean white line art, lit only by the laptop screen` |
| 「坐下坐到一半」畫成跳過沙發、坐到茶几上 | 抽象的動作描述 | 寫畫面上的位置：`standing on the floor between the sofa and the coffee table, the coffee table in the foreground, knees bent, bottom just above the cushion. He is not on the table` |
| 「黑螢幕映出他的臉」畫成他整個人站在筆電前 | 同上；加了 `Only one person` 反而鼓勵畫出一個人 | 不帶角色參考，寫 `the black screen fills the whole frame. In the glossy black glass, a faint white reflection of a face ... nobody outside the screen` |
| 第 1 頁和第 3 頁的客廳是白牆，其他客廳格是黑的 | 參考的是白天版的場景卡 | 每個光線狀態先挑定一格廣角，之後的格子拿它當場景參考（`panel:p7`、`panel:p19`），這些格子放第二輪 |
| 揭露那格的阿嬤比主角還大、臉畫得很清楚 | 沒有寫比例 | `consistency.scale` 寫死身高；那格加 `her head is no bigger than his head, she stays behind the sofa back, never closer to the camera than he is`，臉要克制就寫 `her face is in deep flat black shadow: only the outline of her ears and hair and a faint glint of two eyes` |
| 結尾那格的告示牌長出亂碼中文 | prompt 提到 sign、poster | 不提任何會有字的東西；畫風前綴已經有 `No text, no letters` |
| 帶主角參考圖的群眾格，隊伍裡多一個長得像他的人 | 參考圖的身分漏到別人身上 | 把其他人的長相寫出來（綁馬尾的女生、戴棒球帽的高個子），加 `He is the only person who looks like <image1>` |
| 正面坐姿的狗一直畫成白狗，三次修正只成功一半 | 模型對狗的正面偏好淺色 | 角色卡只用側面那隻當參考（`ref_crop`），毛色在 prompt 裡寫清楚 |
| 客廳場景卡前景多一雙人的膝蓋 | 「from the eye level of a seated person」 | 用編輯修掉：`Keep this room exactly the same ... Remove only the two knees`；場景卡 prompt 加 `nobody in it` |
| 有編輯指令的格子（同構圖加一個人、只改椅子方向）一次對的比例不高 | | 這種格子給 `n: 3`；同構圖加人（走廊加阿嬤）三張都成功，改物件方向兩張成功一張 |
| 寫實的預設畫風被擁有者退回（「太寫實」） | | 開始前先跑 `styles`，給三種畫風範例選；選定後才畫角色卡 |
| 從帳篷紗網往外看的格子冒出三頂帳篷（〈半夜叫我全名的人〉） | 那格被列進 `consistency.scene_refs.camp`，營地格局那句（三頂帳篷一排）被自動接上 | 視角跟場景卡不同的格子不要列進 `scene_refs`；換成在 prompt 裡寫明畫面裡只有什麼（`no tents, no dead tree`） |
| 「a wall of arrow bamboo」畫成帳篷前一道水泥牆 | wall 被照字面畫 | 寫 `thin dark bamboo stalks`、`no walls, no buildings, no fences` |
| 用參考格鎖場景，結果連參考格裡的人和構圖一起搬過來（四個人走過倒木 → 小美出現兩次；整個營地遠景 → 該是帳篷特寫的格子也變遠景） | 參考格整張進去，模型照抄 | 要的是場景不是構圖時，用沒有人的場景卡，不用畫好的格子；特寫格乾脆不帶參考，用文字寫 |
| 角色卡是站姿，該坐著吃麵、該特寫的格子他都站著（三次） | 參考圖的姿勢被照抄 | 用頭部、半身裁切（`akai:head`、`akai:bust`）：重畫三張都坐著，也穿回角色卡上的拉鍊外套（用全身參考時臉變漫畫化、衣服變毛衣） |
| 阿凱的特寫背後一直多一張桌子和凳子（六張全中，prompt 寫了 no tables 也一樣） | 帶了麵店場景卡當參考，場景卡上的桌凳被搬進背景；場景格局句也寫了桌子和凳子 | 特寫不帶場景參考、不寫 `scene`，背景用文字寫（`behind him only the tiled wall, the wall fan and the dark doorway`）；`lint` 會警告特寫帶場景參考 |
| A 畫風的早上、白天格子背景變全黑 | 線稿畫風預設愛用平塗黑 | 白天格子加 `Bright morning: the sky and the background are plain white; no black background` |
| 學長雙手抱胸，兩隻手又從身體兩側垂下來，一共四隻手（擁有者抓到的） | 抱胸加全身構圖，模型把垂手的姿勢也畫上去 | 抱胸的格子取到腰部為止（waist-up），寫 `each hand tucked under the opposite upper arm; he has exactly two arms and two hands, and nothing hangs at his sides`；挑圖時數手 |
| 揭露的黑影比箭竹矮 | 沒寫比例 | `so tall that its head and shoulders rise clearly above the tops of the bamboo`；最後一格同位置換成主角時寫 `the bamboo rises well above his head` |
| 嚇到的那格，老二還在咧嘴笑（〈跟外甥玩捉迷藏〉，5 張有 4 張）；媽媽該低頭抿嘴，兩張都直視鏡頭微笑 | 頭部裁切就是角色卡上那張臉，表情一起帶進來 | 換成 `:bust`，表情寫成五官動作：`eyebrows raised and pulled together, eyes wide open, a drop of cold sweat ... Nobody smiles`；重畫 3 張全對。`lint` 會警告頭部裁切配上害怕、哭、不笑的字 |
| 舅舅坐沙發的格子，3 張有 2 張坐到茶几上（上一本也有一次） | 帶了客廳場景卡，模型把人放在卡的正中間，那裡是茶几 | 坐著的格子不帶場景參考，用文字寫座位：`facing a long wooden sofa ... He sits deep on the sofa, his back against its backrest; a low glass coffee table stands empty in the foreground`；重畫 3 張都坐在沙發上。`lint` 會警告 |
| 「同一個鏡頭」的揭露格，深色衫櫥 3 張全變成白色，小寶睜眼看鏡頭 | 同構圖編輯只鎖了鏡位，物件的顏色和人的狀態沒寫 | 每個要保持的東西都寫出來：`The wardrobe keeps its very dark, almost black wood and small brass handles exactly as in <image2>`、`eyes closed, drawn as two soft curved lines`；重畫 4 張的衫櫥全對 |
| 兩人對話的格子，由右往左讀時先讀到回答（p11、p15） | 先說話的人被畫在左邊 | prompt 寫明先說話的人站在右邊；圖已經畫好、畫面裡沒有字的話，格子設 `mirror: true` 左右翻轉 |

## 時間（RTX 3090）

- 一張圖 1024 上下：沒有參考圖約 23 到 36 秒，有一到兩張參考圖約 47 到 115 秒。
- 角色卡、場景卡 1536×1024，一次出 3 版約 2 分鐘。
- 〈一個人在家開視訊〉7 頁 33 格，連同畫風比較、角色和場景各 3 版、重畫，GPU 共約 81 分鐘：畫風比較 5.5 分鐘、卡 28 分鐘、格子 47 分鐘。照這份規則一次寫對的話，格子大約可以省下一半。
- 〈跟外甥玩捉迷藏〉7 頁 28 格，每格都交給獨立檢查，被退回重畫 24 次：GPU 共約 100 分鐘，畫風 3.6 分鐘、卡 22 分鐘、格子 74 分鐘（167 張圖）。檢查員共跑 8 批，每批 4 到 30 分鐘，可以跟 GPU 同時跑。
