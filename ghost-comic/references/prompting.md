# 畫格子的 prompt：規則和踩過的坑

模型是本機 ComfyUI 上的 Qwen Image 2.1（int8），編碼器 qwen3vl 8B，15 步、CFG 1、euler/simple。參考圖從 `images.image_1..n` 進去，prompt 裡用 `<image1>`、`<image2>` 指它們。以下每一條都是〈一個人在家開視訊〉實際發生過的事。

## 每格 prompt 的組成

1. 畫風前綴（`style_options` 選中的 `panel`），程式自動接。
2. 鏡位：wide shot、medium shot、close-up、從誰的位置看（`from the laptop's webcam position`）。
3. 場景和光線：`Same room, camera angle and lighting as <image3>: late at night, only the floor lamp is on, the walls, ceiling and window are solid flat black ...`
4. 角色和動作：寫畫面上看得到的姿勢和相對位置。
5. 保持外觀：`Keep his bird's-nest hair with the tall cowlick, very thick eyebrows and grey hoodie exactly as in <image1>.` 每格都重複記憶點。
6. 人數：只有一個人的格子加 `Only one person in the frame.`
7. 場景一致、人物比例：程式從 `consistency` 自動接。

## 坑和修法

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

## 時間（RTX 3090）

- 一張圖 1024 上下：沒有參考圖約 23 到 36 秒，有一到兩張參考圖約 47 到 115 秒。
- 角色卡、場景卡 1536×1024，一次出 3 版約 2 分鐘。
- 〈一個人在家開視訊〉7 頁 33 格，連同畫風比較、角色和場景各 3 版、重畫，GPU 共約 81 分鐘：畫風比較 5.5 分鐘、卡 28 分鐘、格子 47 分鐘。照這份規則一次寫對的話，格子大約可以省下一半。
