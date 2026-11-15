"""ghost-film voiceover with the H3 T8 speech nodes (local, no TTS service).
py -X utf8 speak.py <jobs.json>   jobs: [{"name", "text", "voice", "acting", "emotion", "intensity", "seconds", "seed", "ref"?}]
Built from custom_nodes/minimax-h3-audio-T8/examples/speech_described_api.json; output in
ComfyUI/output/ghost_film_vo/<name>_*.flac"""
import json, sys, urllib.request, urllib.error
from pathlib import Path
jobs = json.load(open(sys.argv[1], encoding="utf8"))
for j in jobs:
    g = {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": j.get("unet", "minimax_h3_fl2va_pruned_int8_convrot.safetensors"), "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_32b_h3_ultra_uncensored_heretic_int8_convrot.safetensors", "type": "minimax", "device": "default"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_video_vae_fp16.safetensors"}},
        "4": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_audio_vae_fp32.safetensors"}},
        "5": {"class_type": "MiniMaxH3VoiceProfileT8", "inputs": {
            "voice_mode": "reference_voice" if j.get("ref") else "described_voice", "speaker_id": j.get("speaker", "narrator"),
            "voice_description": j["voice"], "language": "Chinese", "rights_confirmed": bool(j.get("ref")),
            "reference_start_seconds": 0.0, "reference_duration_seconds": 0.0, "highpass_60hz": True, "peak_limit_minus_3_dbfs": True}},
        "6": {"class_type": "MiniMaxH3SpeechPlanT8", "inputs": {
            "text": j["text"], "language": "Chinese", "acting_direction": j.get("acting", "low, calm, close to the microphone"),
            "emotion": j.get("emotion", "uneasy"), "emotion_intensity": j.get("intensity", 0.5), "space": j.get("space", "close"),
            "chunking": "single_segment", "target_units": 18, "max_units": 60, "voice_profile": ["5", 0]}},
        "7": {"class_type": "MiniMaxH3SpeechStudioT8", "inputs": {
            "segment_index": 0, "seed": j.get("seed", 1), "render_seconds": j.get("seconds", 8.0), "resolution": 32, "steps": j.get("steps", 20),
            "sampler_name": "res_multistep", "scheduler": "simple", "shift_video": 12.0, "shift_audio": 3.0,
            "trim_mode": "conservative_energy", "verify_mode": "off", "asr_model_directory": "", "asr_language": "Chinese",
            "min_similarity": 0.85, "unload_asr_after_verify": True, "speaker_check_mode": "off", "speaker_model_directory": "",
            "min_speaker_similarity": 0.86, "unload_speaker_after_verify": True, "peak_limit_dbfs": -1.0,
            "release_policy": "clear_execution_cache",
            "model": ["1", 0], "clip": ["2", 0], "video_vae": ["3", 0], "audio_vae": ["4", 0],
            "voice_profile": ["5", 0], "speech_plan": ["6", 0]}},
        "8": {"class_type": "SaveAudio", "inputs": {"audio": ["7", 0], "filename_prefix": f"ghost_film_vo/{j['name']}"}},
    }
    if j.get("ref"):
        g["9"] = {"class_type": "LoadAudio", "inputs": {"audio": j["ref"]}}
        g["5"]["inputs"]["reference_audio"] = ["9", 0]
    req = urllib.request.Request("http://127.0.0.1:8188/prompt", data=json.dumps({"prompt": g}).encode(), headers={"Content-Type": "application/json"})
    try:
        print(j["name"], urllib.request.urlopen(req).read().decode())
    except urllib.error.HTTPError as e:
        print(j["name"], "ERR", e.read().decode()[:1500]); break
