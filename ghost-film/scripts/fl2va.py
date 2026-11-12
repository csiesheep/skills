"""One H3 shot pinned at both ends (T8 long-video chain, task FL2VA): the first frame and the last frame are given, H3 fills the
motion between. Use it when image-to-video keeps doing the wrong action (upper_bunk: i2v made him fall forward toward the
camera five times; with a last frame of the empty chair and the stretched dead legs, FL2VA made him fall backward while the legs
came down). From <story>/film/reel:
    py -X utf8 fl2va.py <chain_id> <first.png> <last.png> <prompt.txt> [seconds=6] [seed] [width=576] [height=1024]
The prompt file holds the timed beats ([0s-2s] ...) and the sound in one paragraph; the look line is added in front.
Output: ComfyUI/output/minimax_h3_t8_long_video/<chain_id>/assembled/*.mp4. A chain_id can be used once; take a new one per try.
The render window must be on H3's 17n+5 frame grid (124, 141, 158 ...): seconds 6 -> 158."""
import json, math, sys, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path.home() / ".claude" / "skills" / "ghost-comic" / "scripts"))
import comfy  # noqa: E402
a = sys.argv[1:]
chain_id, first_p, last_p, prompt_p = a[:4]
sec = float(a[4]) if len(a) > 4 else 6.0
seed = int(a[5]) if len(a) > 5 else 20261107
W, H = (int(a[6]), int(a[7])) if len(a) > 7 else (576, 1024)
window = 17 * math.ceil((sec * 24 + 10 - 5) / 17) + 5
LOOK = ("寫實港片電影感，35mm 底片顆粒，固定機位鏡頭完全不動，畫面維持跟第一幀一樣的色調和亮度，畫面中沒有任何文字。")
SEG = Path(prompt_p).read_text(encoding="utf-8").strip()
first = comfy.upload(Path(first_p)); last = comfy.upload(Path(last_p))
g = {
 "1": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_video_vae_fp16.safetensors"}},
 "2": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_audio_vae_fp32.safetensors"}},
 "3": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_32b_h3_ultra_uncensored_heretic_int8_convrot.safetensors", "type": "minimax", "device": "default"}},
 "4": {"class_type": "UNETLoader", "inputs": {"unet_name": "minimax_h3_fused_refdelta_r1024_turbo8_mystic07_int8_convrot.safetensors", "weight_dtype": "default"}},
 "6": {"class_type": "MiniMaxH3LongVideoBackgroundStartT8", "inputs": {"chain_id": chain_id, "execution_mode": "auto_accept_and_continue", "max_retries": 1, "retry_delay_seconds": 2, "release_policy": "clear_execution_cache"}},
 "7": {"class_type": "MiniMaxH3LongVideoOrchestratorT8", "inputs": {"chain_id": ["6", 0], "total_duration_seconds": sec, "render_window_frames": window, "context_frames": 22,
       "global_prompt": LOOK, "segment_prompts_json": json.dumps([LOOK + SEG], ensure_ascii=False), "base_seed": seed,
       "seed_policy": "increment", "steps": 4, "shift_video": 12, "shift_audio": 3, "sampler_name": "dual_clock_euler", "scheduler": "native_flow"}},
 "8": {"class_type": "MiniMaxH3LongVideoAcceptedContextLoadT8", "inputs": {"chain_id": ["7", 0], "segment_index": ["7", 1]}},
 "20": {"class_type": "LoadImage", "inputs": {"image": first}},
 "22": {"class_type": "LoadImage", "inputs": {"image": last}},
 "9": {"class_type": "MiniMaxH3LongVideoConditioningT8", "inputs": {"model": ["4", 0], "clip": ["3", 0], "video_vae": ["1", 0], "audio_vae": ["2", 0], "context": ["8", 0],
       "segment_index": ["7", 1], "context_frames": ["7", 3], "context_audio": "video_and_audio", "prompt": ["7", 10], "width": W, "height": H, "length": ["7", 2],
       "task_type": "FL2VA", "audio_mode": "native", "audio_denoise_strength": 0.35, "add_source_as_reference": False, "prompt_primary_audio_ordinal": 0,
       "strict_prompt_tags": True, "ref_image_size": "match", "reference_video_policy": "official_2_to_15s", "first_frame": ["20", 0], "last_frame": ["22", 0]}},
 "10": {"class_type": "MiniMaxH3DualClockSamplerT8", "inputs": {"model": ["9", 0], "av_latent": ["9", 2], "steps": ["7", 16], "shift_video": ["7", 17], "shift_audio": ["7", 18], "sampler_name": ["7", 19], "scheduler": ["7", 20]}},
 "11": {"class_type": "RandomNoise", "inputs": {"noise_seed": ["7", 11]}},
 "12": {"class_type": "BasicGuider", "inputs": {"model": ["10", 0], "conditioning": ["9", 1]}},
 "13": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["11", 0], "guider": ["12", 0], "sampler": ["10", 1], "sigmas": ["10", 2], "latent_image": ["9", 2]}},
 "14": {"class_type": "MiniMaxH3AVDecodeT8", "inputs": {"av_latent": ["13", 0], "video_vae": ["1", 0], "audio_vae": ["2", 0]}},
 "15": {"class_type": "MiniMaxH3OutputTrimT8", "inputs": {"frames": ["14", 0], "start_seconds": ["7", 4], "duration_seconds": ["7", 5], "fps": 24, "audio": ["14", 1]}},
 "16": {"class_type": "MiniMaxH3LongVideoCandidateSaveT8", "inputs": {"frames": ["15", 0], "audio": ["15", 1], "av_latent": ["13", 0], "chain_id": ["7", 0], "segment_index": ["7", 1],
       "timeline_start_seconds": ["7", 6], "save_context": ["7", 8], "parent_candidate_id": ["8", 2], "parent_manifest_revision": ["8", 3], "candidate_id": "",
       "model_id": "h3_fused_refdelta_int8_nolora", "sampling_summary": ["7", 21], "prompt": ["9", 4], "seed": ["7", 11], "bit_depth": 8, "crf": 18}},
 "17": {"class_type": "MiniMaxH3LongVideoAutoQueueT8", "inputs": {"candidate_json_path": ["16", 0], "job_id": ["6", 2], "auto_accept": ["6", 1], "replace_policy": "reject_existing",
       "strict_chain_identity": True, "compose_when_complete": True, "filename_prefix": f"ghost_film/{chain_id}", "audio_seam_policy": "cosine_bridge", "bridge_ms": 5, "crf": 18}},
}
req = urllib.request.Request("http://127.0.0.1:8188/prompt", data=json.dumps({"prompt": g}).encode(), headers={"Content-Type": "application/json"})
try:
    print(urllib.request.urlopen(req).read().decode())
except urllib.error.HTTPError as e:
    print(e.read().decode()[:2000])
