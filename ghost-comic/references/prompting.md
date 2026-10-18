# 畫格子的 prompt：規則和踩過的坑

模型是本機 ComfyUI 上的 Qwen Image 2.1（int8），編碼器 qwen3vl 8B，15 步、CFG 1、euler/simple。參考圖從 `images.image_1..n` 進去，prompt 裡用 `<image1>`、`<image2>` 指它們。以下每一條都是實際發生過的事，大多來自〈一個人在家開視訊〉，括號裡註明的來自後面幾本。

## 每格 prompt 的組成

1. 畫風前綴（`style_options` 選中的 `panel`），程式自動接。
2. 鏡位：wide shot、medium shot、close-up、從誰的位置看（`from the laptop's webcam position`）。
3. 場景和光線：`Same room, camera angle and lighting as <image3>: late at night, only the floor lamp is on, the walls, ceiling and window are solid flat black ...`
4. 角色和動作：寫畫面上看得到的姿勢和相對位置。
5. 保持外觀：`Keep his bird's-nest hair with the tall cowlick, very thick eyebrows and grey hoodie exactly as in <image1>.` 每格都重複記憶點。
6. 人數：只有一個人的格子加 `Only one person in the frame.`
7. 場景一致、人物比例：程式從 `consistency` 自動接。

## 坑和修法

這張表裡能用字面判斷的，`manga.py lint` 都會檢查（`panels` 也會先跑，有錯就不畫）：全身構圖抱胸、沒在 prompt 裡提到的參考圖、特寫和坐著的格子用全身參考、頭部裁切配上害怕或不笑的表情、坐在沙發或椅子上又帶場景參考、有人的格子帶場景參考、`heads` 比畫出來的角色少、wall of、招牌海報、dim 和 lit by、顏色字、halfway、reflection、單人格沒寫 Only one person、角色特徵沒重複、角色第一次出場那格沒有名字、`panel:` 參考的輪次、不存在的 scene 或 light。排版時 `plan` 和 `pages` 會警告同一格裡互相蓋住的文字框。判斷不了的（同一人畫兩次、手的數量、大小）留給獨立檢查（qa_checklist.md）；讀者看不看得懂留給讀者檢查（reader_check.md）。

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
| 走廊和護理站的格子帶了場景卡，人畫得很小，或乾脆沒有人（〈三個人〉p2、p7）；要監視器俯角的格子畫成平視的大廳（〈電梯〉p12、p22） | 場景卡是空景，模型照抄它的構圖和鏡位，人只能塞在邊上 | 有人的格子不帶場景卡，用文字寫地方（`a long hospital corridor, a row of doors on the left ...`）；要鎖場景就用已選定、裡面有人的同場景格子。只有跟場景卡同一個視角的遠景才帶，prompt 寫 `wide shot`。`lint` 會警告 |
| 阿嬤、王伯伯每一格都盯著讀者看；阿嬤躺在病床上還坐得直挺挺，王伯伯一手插口袋（〈三個人〉） | 角色卡是正面、看鏡頭、站姿，參考圖把視線和姿勢一起帶進來 | 視線寫成頭的方向：`in profile, her head turned toward the door`、`looking down at the bed, not at the viewer`；姿勢寫成身體的位置：`lying back against the raised bed, shoulders sunk into the pillow` |
| 為了甩掉角色卡的姿勢，阿嬤的特寫改成只用文字畫，表情對了，臉卻不是她（〈三個人〉p30，擁有者抓到的：「奶奶不像」） | 文字只寫得出特徵，臉型和五官要靠參考圖 | 主要角色的特寫保留 `:head` 或 `:bust`，表情用五官動作寫出來蓋過角色卡上的表情；只用文字畫的格子限於遠景、背影、臉在陰影裡。重畫 4 張，挑的那張臉對了 |
| 監視器要畫成一條直線的兩格（〈三個人〉p5、p32）畫成波浪線 | 每格都接的一段共用句寫了 `monitors show wavy lines`，跟這兩格自己的 prompt 打架；獨立檢查抓到的 | 共用的句子只放畫風和「不要什麼」（no text、no writing anywhere），不描述畫面內容；內容只寫在各格自己的 prompt |
| 「電梯裡擠了十個人」「背後貼著三個人」數不準，重畫幾次都多一個或少一個（〈電梯〉p25、p27） | 模型數不準五個以上的人，人一多就亂 | 不要讓劇情靠數人頭：用背影擋、人群出框、只畫到肩膀；非數不可的，畫面裡只放三個以內，其他交給旁白。格子的 `heads` 寫成描述（「一群看不清的人，不用數」），檢查員就照描述判 |
| 王伯伯點滴架上的收音機、林先生拉著衣角的手，四次整格編輯和一次局部重畫都畫不出來（〈三個人〉p29） | 細節太小，或那個組合模型就是畫不出來 | 先試下一列的 `repaint`；還不行，就回到故事原文，把這個細節寫進旁白或對話（「老阿伯的點滴架上綁一台收音機」），不要再燒 GPU |
| 多了一圈玉項圈（〈三個人〉p30）、弟弟頭髮是黑的（p34）、阿嬤招手的手不對（p37）、要改成保全制服的襯衫三次整格編輯都沒變（〈電梯〉p27）；整格重畫還會連對的地方一起變 | 整格編輯對小地方不敏感 | `manga.py repaint p34_1 --box x0,y0,x1,y1 --prompt "his hair under the knitted hat is white"`：把那一塊裁出來、放大到 1024 上下再改、縮回去羽化貼上，原圖不動，結果是新的候選。框要比要改的東西大一圈，邊緣十分之一是過渡帶。上面四個都是這樣修好的，每次 3 到 4 張約 1.3 到 2.3 分鐘 |
| 弟弟在 p35、p36 是白頭髮，p34 是黑的；阿嬤的特寫臉不像她（〈三個人〉，兩個都是擁有者抓到的，逐格檢查都過了） | 逐格檢查只看那一格對不對，看不到同一個人在兩格長得不一樣；選定的角色卡 boy_2 本身就是黑髮，跟擁有者要的不一樣 | 選角色卡時就對照故事和擁有者說的外觀；所有格子選完、排頁之前跑 `review --cast all`，每個角色一份 brief，把他出現的每一格和角色卡放在一起，交給檢查員比（qa_checklist.md 的跨格檢查） |

## 時間（RTX 3090）

- 一張圖 1024 上下：沒有參考圖約 23 到 36 秒，有一到兩張參考圖約 47 到 115 秒。
- 角色卡、場景卡 1536×1024，一次出 3 版約 2 分鐘。
- 下面的分鐘數都是 `out/log.jsonl` 的 `exec_s` 加總，是 GPU 真的在畫的時間。`wall_s` 還包含在 ComfyUI 佇列裡排隊的時間，好幾批一起送的時候會重複算（〈三個人〉wall 加起來 284 分鐘，實際 147 分鐘）；`status` 報的是 exec。
- 〈一個人在家開視訊〉7 頁 33 格，連同畫風比較、角色和場景各 3 版、重畫和修正回合：GPU 共約 97 分鐘（150 張圖），畫風比較 6 分鐘、卡 28 分鐘、格子 64 分鐘。
- 〈半夜叫我全名的人〉6 頁 32 格：約 71 分鐘（157 張圖），卡 14 分鐘、格子 54 分鐘。
- 〈跟外甥玩捉迷藏〉7 頁 28 格，每格都交給獨立檢查，被退回重畫 24 次：約 91 分鐘（167 張圖），畫風 3 分鐘、卡 22 分鐘、格子 66 分鐘。檢查員共跑 8 批，每批 4 到 30 分鐘，可以跟 GPU 同時跑。
- 〈阿嬤說我後面跟了三個人〉10 頁 37 格，9 個角色：約 147 分鐘（246 張圖），畫風 3 分鐘、卡 24 分鐘、格子 112 分鐘、局部重畫 7 分鐘。
- 〈代班那台電梯一直超載〉7 頁畫完才給擁有者看故事，整本放棄：約 104 分鐘白畫。故事先給擁有者看（SKILL.md 第 0 步）。
