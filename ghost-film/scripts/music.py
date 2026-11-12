"""ACE-Step 1.5 score for the reel (API form of ghost-reel/assets/ace_m1.json). py -X utf8 music.py name seed seconds"""
import json, sys, urllib.request
name, seed, sec = sys.argv[1], int(sys.argv[2]), float(sys.argv[3])
TAGS = ("cinematic horror film score, 1990s Hong Kong horror movie, slow and sparse, a low cello drone, a few detuned "
        "felt piano notes far apart, a faint out-of-tune music box, soft breathy string harmonics, tense silence between "
        "notes, very dark, intimate, no drums, no beat, no vocals, instrumental")
g = {
 "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "acestep_v1.5_turbo.safetensors", "weight_dtype": "default"}},
 "2": {"class_type": "DualCLIPLoader", "inputs": {"clip_name1": "qwen_0.6b_ace15.safetensors", "clip_name2": "qwen_1.7b_ace15.safetensors", "type": "ace", "device": "default"}},
 "3": {"class_type": "VAELoader", "inputs": {"vae_name": "ace_1.5_vae.safetensors"}},
 "4": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["1", 0], "shift": 3}},
 "5": {"class_type": "TextEncodeAceStepAudio1.5", "inputs": {"clip": ["2", 0], "tags": TAGS, "lyrics": "[Instrumental]", "seed": seed,
       "bpm": 60, "duration": sec, "timesignature": "4", "language": "en", "keyscale": "D minor", "generate_audio_codes": True,
       "cfg_scale": 2.0, "temperature": 0.85, "top_p": 0.9, "top_k": 0, "min_p": 0.0}},
 "6": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["5", 0]}},
 "7": {"class_type": "EmptyAceStep1.5LatentAudio", "inputs": {"seconds": sec, "batch_size": 1}},
 "8": {"class_type": "KSampler", "inputs": {"model": ["4", 0], "positive": ["5", 0], "negative": ["6", 0], "latent_image": ["7", 0],
       "seed": seed, "steps": 8, "cfg": 1, "sampler_name": "euler", "scheduler": "simple", "denoise": 1}},
 "9": {"class_type": "VAEDecodeAudio", "inputs": {"samples": ["8", 0], "vae": ["3", 0]}},
 "10": {"class_type": "SaveAudio", "inputs": {"audio": ["9", 0], "filename_prefix": f"ghost_film_music/{name}"}},
}
req = urllib.request.Request("http://127.0.0.1:8188/prompt", data=json.dumps({"prompt": g}).encode(), headers={"Content-Type": "application/json"})
try:
    print(urllib.request.urlopen(req).read().decode())
except urllib.error.HTTPError as e:
    print(e.read().decode()[:1500])
