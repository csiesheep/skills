"""〈半夜叫我全名的人〉: what each version shows, says and sounds like. Times in seconds."""
COMIC = r"C:/Users/sheep/Pictures/gui_chang_shi/stories/name_call/comic"
TITLE = "半夜叫我全名的人"
NUMBER = None
SEAL = r"C:/Users/sheep/Pictures/gui_chang_shi/brand/avatar/final/avatar_1024.png"

# Sound beds: (from panel, to panel inclusive, bed, gain). Panels in reading order.
BEDS = [
    ("p1", "p10", "wind", 0.6),
    ("p1", "p10", "rustle", 0.25),
    ("p11", "p20", "insects", 0.5),
    ("p11", "p20", "wind", 0.25),
    ("p12", "p18", "drone", 0.45),
    ("p26", "p27", "footsteps", 0.5),
    ("p31", "p33", "drone", 0.35),
]

# ---------------------------------------------------------------- V1 漫動畫
# Per-panel direction: motion, focus override, fx, sfx [(name, at, gain)], hold (extra s), black (s of black before)
V1 = {
    "p1": dict(motion="pan_rtl"),
    "p2": dict(motion="push"),
    "p6": dict(sfx=[("ping", 0.2, 0.6)]),
    "p7": dict(fx=["pulse"], sfx=[("ping", 0.1, 0.7), ("heartbeat", 0.6, 0.5)], hold=0.6),
    "p11": dict(motion="pan_rtl", fx=["night"]),
    "p12": dict(fx=["night", "pulse"], sfx=[("heartbeat", 0.0, 0.55)]),
    "p13": dict(fx=["night", "chroma"], sfx=[("whisper", 0.25, 0.9)], hold=0.4),
    "p14": dict(fx=["night", "pulse"], sfx=[("heartbeat", 0.0, 0.6)]),
    "p15": dict(fx=[], sfx=[("whisper", 0.9, 1.0)], hold=0.6),
    "p16": dict(fx=["night"], motion="pan_rtl"),
    "p17": dict(fx=["night", "pulse"], sfx=[("whisper", 0.1, 1.0), ("riser", 0.8, 0.5)], hold=0.3),
    "p18": dict(motion="snap", fx=["shake", "night"], sfx=[("stinger", 0.0, 1.0)], black=1.0, hold=2.6, duck=True),
    "p19": dict(fx=["night"], sfx=[("rustle", 0.2, 0.5)]),
    "p20": dict(fx=["fadein"]),
    "p27": dict(fx=["darken"]),
    "p29": dict(sfx=[("stinger", 0.1, 0.35)]),
    "p32": dict(fx=["pulse"], sfx=[("heartbeat", 0.0, 0.6)], duck=True, hold=0.5),
    "p33": dict(motion="push", fx=["darken"], sfx=[("zipper", 0.6, 0.8), ("riser", 1.4, 0.5), ("stinger", 3.2, 0.8)], hold=2.0, black=0.6, duck=True),
}

# Cold open: (panel, seconds, text shown, sfx)
HOOK = [
    ("p7", 2.6, None, [("ping", 0.05, 0.8), ("heartbeat", 0.3, 0.5)]),
    ("p13", 1.6, None, [("whisper", 0.1, 1.0)]),
]

# ---------------------------------------------------------------- V2 說書快剪
# (panel, caption with {red}, options). "／" splits a caption into beats on the same picture.
V2 = [
    ("p17", "如果半夜在山上，有人叫你的{全名}——", dict(fx=["night", "pulse"], sfx=[("heartbeat", 0.0, 0.5)])),
    ("p13", "{不要回。}", dict(sfx=[("whisper", 0.0, 1.0)], fx=["night", "chroma", "pulse"])),
    ("TITLE", "", {}),
    ("p2", "去年暑假，我跟同學去爬宜蘭的一座中級山。", {}),
    ("p5", "帶隊的學長，規矩超多。", {}),
    ("p7", "最後一條，他打了大字：／聽到有人叫你全名，{不管多像我們}，都不要回。", dict(fx=["pulse"])),
    ("p8", "小美回了一個白眼。", {}),
    ("p11", "第一晚，我們在山上的平台紮營。", dict(fx=["night"], motion="pan_rtl")),
    ("p12", "凌晨一點，我被吵醒。", dict(fx=["night"], sfx=[("heartbeat", 0.0, 0.5)])),
    ("p13", "「林志偉。」", dict(fx=["night", "chroma"], sfx=[("whisper", 0.1, 1.0)])),
    ("p14", "很標準的國語。有點像學長，／又有點像{我爸}。", dict(fx=["night", "pulse"])),
    ("p15", "一聲，停很久，／又一聲。", dict(sfx=[("whisper", 1.2, 0.9)])),
    ("p16", "我把睡袋拉過頭。{不回。}", dict(fx=["night"])),
    ("p17", "叫到第三聲，我從紗網往外看——", dict(fx=["night", "pulse"], sfx=[("riser", 0.8, 0.5)])),
    ("p18", "", dict(motion="snap", fx=["shake", "night"], sfx=[("stinger", 0.0, 1.0)], hold=1.6, black=0.7, duck=True)),
    ("p18", "{比箭竹還高。}", dict(fx=["night"], motion="static")),
    ("p19", "眨一下眼，只剩箭竹在晃。", dict(fx=["night"], sfx=[("rustle", 0.0, 0.5)])),
    ("p20", "天亮去看，箭竹倒了一片。／像有人在那裡站了{很久}。", {}),
    ("p21", "我很得意：被叫了三次，{一次都沒回}。", {}),
    ("p23", "學長說，他整晚睡死，根本沒出帳篷。", {}),
    ("p27", "那天開始，我們一直{繞回同一棵倒木}。", dict(fx=["darken"])),
    ("p29", "學長滑倒，手肘縫了五針。／大家都說，是我害的。", {}),
    ("p30", "我又沒回。回了我會不記得嗎？", {}),
    ("p31", "上禮拜，跟阿凱吃麵。", {}),
    ("p32", "他放下筷子：／「那天晚上，{你有回啊}。」", dict(fx=["pulse"], sfx=[("heartbeat", 0.0, 0.6)], duck=True)),
    ("p33", "「你坐起來說『在這裡』，自己拉開帳篷，／在外面站了快{十分鐘}。」", dict(fx=["darken"], sfx=[("zipper", 0.2, 0.8), ("stinger", 2.4, 0.8)], duck=True, hold=1.2)),
]

# ---------------------------------------------------------------- V3 電影感
# (panel, seconds, subtitle or None, options). voice=True shows the line as a whisper in the middle of the frame.
V3 = [
    ("p17", 2.6, "林志偉。", dict(voice=True, voice_y=1250, fx=["night"], clip=r"C:/Users/sheep/Pictures/gui_chang_shi/stories/name_call/reels/clips/nc_p17.mp4", sfx=[("whisper", 0.2, 1.0), ("heartbeat", 0.0, 0.4)])),
    ("TITLE", 2.2, None, dict(clip=r"C:/Users/sheep/Pictures/gui_chang_shi/stories/name_call/reels/clips/nc_p1.mp4")),
    ("p1", 3.4, "宜蘭大同鄉，一條中級山。", dict(clip=r"C:/Users/sheep/Pictures/gui_chang_shi/stories/name_call/reels/clips/nc_p1.mp4", clip_offset=2.2)),
    ("p2", 3.6, "去年暑假，我們四個人上山。", {}),
    ("p7", 4.6, None, dict(fx=["pulse"], motion="static", focus=(0.3, 0.62), sfx=[("ping", 0.1, 0.5)])),
    ("p11", 4.2, None, dict(fx=["night"], clip=r"C:/Users/sheep/Pictures/gui_chang_shi/stories/name_call/reels/clips/nc_p11.mp4")),
    ("p12", 3.0, "凌晨一點，我被吵醒。", dict(fx=["night"], sfx=[("heartbeat", 0.0, 0.5)])),
    ("p13", 3.0, "林志偉。", dict(voice=True, fx=["night"], clip=r"C:/Users/sheep/Pictures/gui_chang_shi/stories/name_call/reels/clips/nc_p13.mp4", sfx=[("whisper", 0.3, 1.0)])),
    ("p14", 3.6, "有點像學長，又有點像我爸。", dict(fx=["night", "pulse"])),
    ("p15", 2.2, "林志偉。", dict(voice=True, sfx=[("whisper", 0.4, 1.0)])),
    ("p16", 3.8, "我把睡袋拉過頭，不回。", dict(fx=["night"], motion="pan_rtl")),
    ("p17", 3.4, "第三聲。我往紗網外看。", dict(fx=["night"], clip=r"C:/Users/sheep/Pictures/gui_chang_shi/stories/name_call/reels/clips/nc_p17.mp4", clip_offset=1.4, sfx=[("riser", 1.6, 0.5)])),
    ("p18", 5.0, None, dict(fx=["shake", "night"], clip=r"C:/Users/sheep/Pictures/gui_chang_shi/stories/name_call/reels/clips/nc_p18.mp4", sfx=[("stinger", 0.0, 1.0)], black=1.0, duck=True)),
    ("p19", 3.4, "眨眼，只剩箭竹在晃。", dict(fx=["night"], clip=r"C:/Users/sheep/Pictures/gui_chang_shi/stories/name_call/reels/clips/nc_p19.mp4", sfx=[("rustle", 0.0, 0.5)])),
    ("p20", 3.8, "天亮，那裡的箭竹倒了一片。", dict(fx=["fadein"], clip=r"C:/Users/sheep/Pictures/gui_chang_shi/stories/name_call/reels/clips/nc_p20.mp4")),
    ("p21", 3.0, "「我被叫了三次，一次都沒回。」", {}),
    ("p23", 3.2, "「我整晚睡死，根本沒出帳篷。」", {}),
    ("p26", 3.2, "那天開始，什麼都不順。", dict(motion="pan_down", sfx=[("footsteps", 0.0, 0.6)])),
    ("p29", 3.0, "學長滑倒，縫了五針。", {}),
    ("p31", 3.0, "上禮拜，跟阿凱吃麵。", {}),
    ("p32", 4.2, "「那天晚上，你有回啊。」", dict(fx=["pulse"], sfx=[("heartbeat", 0.0, 0.6)], duck=True)),
    ("p33", 5.6, "「你自己拉開帳篷，在外面站了快十分鐘。」", dict(clip=r"C:/Users/sheep/Pictures/gui_chang_shi/stories/name_call/reels/clips/nc_p33.mp4", fx=["darken"], sfx=[("zipper", 0.3, 0.8), ("riser", 1.2, 0.4), ("stinger", 3.0, 0.8)], black=0.6, duck=True)),
]

# V1 condensed lines: replaces the text of each panel's non-title entries, in order
V1_SAY = {'p1': ['宜蘭大同鄉，一條中級山。'], 'p2': ['去年暑假，我跟同學上山，帶隊的是阿彬學長。'], 'p5': ['阿彬學長', '規矩超多。'], 'p6': ['出發前一晚，學長在群組列了一長串規矩。'], 'p7': ['最後一條，他打大字：', '山上晚上如果聽到有人叫你全名，不管多像我們的聲音，都不要回。'], 'p10': ['隔天在客運上，學長又唸了一次。'], 'p11': ['第一晚，我們在平台紮營。'], 'p14': ['很標準的國語，有點像學長，又有點像我爸。'], 'p16': ['我以為學長在整我，把睡袋拉過頭，不回。', '阿凱在旁邊，沒動靜。'], 'p20': ['天亮去看，箭竹倒了一片，像有人在那站了很久。'], 'p21': ['隔天早上，我很得意。', '我被叫了三次，一次都沒回。'], 'p23': ['我整晚睡死了，根本沒出帳篷。'], 'p24': ['我也有聽到外面有人講話。'], 'p25': ['阿凱收著帳篷，一句話都沒講。'], 'p26': ['那天開始就不順，導航把我們帶進廢棄的產業道路。'], 'p27': ['繞了三個小時，', '這棵倒木我們是不是坐過？'], 'p30': ['大家都說是我害的。', '我又沒回，回了我會不記得嗎？'], 'p31': ['上禮拜跟阿凱吃飯，又聊到這件事。'], 'p33': ['你坐起來說『在這裡』，自己拉開帳篷，', '在外面站了快十分鐘才回來躺下。']}

V1_SKIP = {"p9", "p10", "p28"}
