import subprocess
import shutil
import json
import os
import re
import sys
import time
import datetime
import argparse
from moviepy import AudioFileClip, VideoClip, CompositeVideoClip, ImageClip, ColorClip
from PIL import Image, ImageStat
import numpy as np

# Config Defaults (Can be overridden by args)
VIDEO_SIZE = (1080, 1920)
LOG_FILE = None

def log(message, data=None, type_="INFO"):
    print(f"[{type_}] {message}")
    if LOG_FILE:
        try:
            timestamp = datetime.datetime.now().isoformat()
            with open(LOG_FILE, 'a') as f:
                f.write(f"\n## [VIDEO_GEN:{type_}] {message}\n")
                f.write(f"**Time**: {timestamp}\n")
                if data:
                    f.write("### Data\n")
                    f.write(f"```json\n{json.dumps(data, indent=2, ensure_ascii=False)}\n```\n")
                f.write("---\n")
        except Exception as e:
            print(f"Log Error: {e}")

def write_status(song_id, status, message, video_url=None, error=None):
    status_file = f"videos/{song_id}_status.json"
    data = {
        "status": status,
        "message": message,
        "updated": str(datetime.datetime.now())
    }
    if video_url: data["video_url"] = video_url
    if error: data["error"] = str(error)
    
    with open(status_file, "w") as f:
        json.dump(data, f)

def get_theme_colors(image_path):
    try:
        img = Image.open(image_path)
        img_small = img.resize((150, 150))
        result = img_small.quantize(colors=10)
        palette = result.getpalette()
        
        colors = [tuple(palette[i:i+3]) for i in range(0, len(palette), 3)][:10]
        
        def get_saturation(rgb):
            r,g,b = rgb
            mx = max(r,g,b)
            mn = min(r,g,b)
            if mx == mn: return 0
            return (mx-mn)/mx
            
        sorted_by_sat = sorted(colors, key=get_saturation, reverse=True)
        highlight = sorted_by_sat[0]
        if sum(highlight) < 300: 
            highlight = (255, 220, 100)
            
        stat = ImageStat.Stat(img_small)
        avg_color = stat.mean[:3]
        bg = tuple([int(c * 0.2) for c in avg_color])
        
        return bg, highlight
        return bg, highlight
    except Exception as e:
        log(f"Warning: Color extraction failed ({e}), using defaults.", type_="WARNING")
        return (20, 20, 30), (255, 220, 0)

def rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))

def normalize(text):
    return re.sub(r'[^a-zA-Z0-9\u0a00-\u0a7f\u0900-\u097f]', '', text).lower()

def generate_video(song_id, title="Baby Song", output_path=None, s_audio=None, s_image=None, s_lyrics=None, log_file=None, language=None):
    global LOG_FILE
    if log_file: LOG_FILE = log_file
    
    log(f"🎬 Starting Karaoke Generation for {song_id} ('{title}')...", data={
        "output_path": output_path,
        "audio": s_audio,
        "image": s_image,
        "lyrics": s_lyrics
    })
    write_status(song_id, "processing", "Starting video generation...")
    
    # Paths (Defaults)
    json_path = f"lyrics/{song_id}.json"
    txt_path = f"lyrics/{song_id}.txt" 
    audio_path = f"audios/{song_id}.mp3"
    image_path = f"photos/{song_id}.jpg"
    
    if s_lyrics: 
        txt_path = s_lyrics
        base = os.path.splitext(s_lyrics)[0]
        json_path = base + ".json"
        
    if s_audio: audio_path = s_audio
    if s_image: image_path = s_image
    
    if not output_path:
        output_path = f"videos/{song_id}_HQ.mp4"
        
    # Check inputs
    if not os.path.exists(audio_path):
        log(f"Error: Missing audio file for {song_id}", type_="ERROR")
        write_status(song_id, "failed", "Missing audio file", error="Audio file not found")
        return

    # 1. Colors
    bg_rgb, highlight_rgb = get_theme_colors(image_path)
    highlight_hex = rgb_to_hex(highlight_rgb)
    log(f"🎨 Theme: BG={bg_rgb}, Highlight={highlight_hex}")

    # 2. Get Audio Duration
    try:
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration
        audio_clip.close() # Re-open later
    except Exception as e:
        log(f"Error reading audio duration: {e}", type_="WARNING")
        duration = 60 # Fallback

    # 3. Load Data
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        words = json_data['data']['alignedWords']
    except:
        log("Error: Invalid JSON lyrics data.", type_="ERROR")
        write_status(song_id, "failed", "Invalid lyrics data", error="JSON parse error")
        return
        
    with open(txt_path, 'r', encoding='utf-8') as f:
        # Strip structural tags like [Chorus], (Verse 1), etc.
        raw_lines = []
        for l in f.readlines():
            cleaned = re.sub(r'\[.*?\]|\(.*?\)', '', l).strip()
            if cleaned:
                raw_lines.append(cleaned)

        norm_lines = [normalize(l) for l in raw_lines]

    # 4. Alignment Logic (Strict Forward, Local Only)
    word_to_line = [-1] * len(words)
    curr_line_idx = 0
    drift_state = False # If true, we are in a repetition/unknown section
    
    i = 0
    while i < len(words):
        probe_str = ""
        # Lookahead window for word matching (chunk of 3 words)
        for k in range(3):
            if i + k < len(words): probe_str += normalize(words[i+k]['word'])
        
        if not probe_str:
            i += 1; continue
            
        # Candidates: Current line, next line, next+1
        candidates = [curr_line_idx]
        if curr_line_idx + 1 < len(norm_lines): candidates.append(curr_line_idx + 1)
        if curr_line_idx + 2 < len(norm_lines): candidates.append(curr_line_idx + 2)
        
        best_match_idx = -1
        best_score = 0
        
        for c_idx in candidates:
            if probe_str in norm_lines[c_idx]:
                score = len(probe_str)
                # Removed forward bias (* 2.0) to prevent skipping the first line
                if score > best_score: best_score = score; best_match_idx = c_idx
        
        if best_match_idx != -1:
            # Match found!
            curr_line_idx = best_match_idx
            word_to_line[i] = curr_line_idx
            drift_state = False
        else:
            # No match found in expected window
            # If we were already drifting, stay drifting (-1)
            # If we were locked on a line, check if this word is just a filler OR a true drift
            # For simplicity: strict forward mode means if it's not in candidates, it's drift.
            # But we be careful not to flicker on single words.
            # Let's say if it doesn't match current or next, it's -1.
            word_to_line[i] = -1
            
        i += 1
        
    timeline = []
    current_block = None
    
    # Compress timeline
    for i, w in enumerate(words):
        line_idx = word_to_line[i]
        if current_block is None: 
            current_block = {"line": line_idx, "start": w['startS'], "end": w['endS']}
        else:
            if line_idx == current_block["line"]: 
                current_block["end"] = w['endS']
            else: 
                timeline.append(current_block)
                current_block = {"line": line_idx, "start": w['startS'], "end": w['endS']}
    if current_block: timeline.append(current_block)

    # 5. Pre-render & Paragraph Grouping
    # Parse Paragraphs from raw text file (double newline structure)
    paragraphs = []
    current_para = []
    
    log("🎨 Pre-rendering paragraphs...", data={"paragraphs_count": len(paragraphs)})
    write_status(song_id, "processing", "Pre-rendering lyrics...")
    
    # Re-read raw file to respect double newlines
    with open(txt_path, 'r', encoding='utf-8') as f:
        file_content = f.read()
    
    # Split by double newline to find paragraph blocks
    raw_para_blocks = file_content.split('\n\n')
    
    # Map linear line indices to paragraphs
    global_line_idx = 0
    for block in raw_para_blocks:
        raw_block_lines = [l.strip() for l in block.split('\n') if l.strip()]
        
        # Apply EXACT same filtering as earlier to keep indices in sync
        clean_block_lines = []
        for l in raw_block_lines:
            cleaned = re.sub(r'\[.*?\]|\(.*?\)', '', l).strip()
            if cleaned:
                clean_block_lines.append(cleaned)
                
        if not clean_block_lines: continue
        
        para_indices = []
        for _ in clean_block_lines:
            para_indices.append(global_line_idx)
            global_line_idx += 1
        paragraphs.append(para_indices)

    # Pre-render lines
    temp_dir = f"temp_gen_{song_id}"
    if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    RENDER_SCRIPT = os.path.join("utils", "render_line_coretext.py")
    
    line_images = []
    
    log(f"Rendering {len(raw_lines)} lines to images...")
    t_start_lines = time.time()
    
    for i, txt in enumerate(raw_lines):
        w_path = os.path.join(temp_dir, f"l{i}_w.png")
        g_path = os.path.join(temp_dir, f"l{i}_g.png")
        # Generate generic white and highlight images
        subprocess.check_call([sys.executable, RENDER_SCRIPT, txt, w_path, "--color", "#FFFFFF", "--width", "850", "--fontsize", "50", "--language", str(language)])
        subprocess.check_call([sys.executable, RENDER_SCRIPT, txt, g_path, "--color", highlight_hex, "--width", "850", "--fontsize", "50", "--language", str(language)])
        im = Image.open(w_path); h = im.height; im.close()
        line_images.append({'w': w_path, 'g': g_path, 'h': h})
    log(f"✅ Line rendering complete. (Took {time.time() - t_start_lines:.1f}s)")
        
    title_path = os.path.join(temp_dir, "title.png")
    subprocess.check_call([sys.executable, RENDER_SCRIPT, title, title_path, "--color", highlight_hex, "--fontsize", "70", "--width", "900", "--language", str(language)])

    loaded_imgs = {}
    def get_imgs(idx):
        if idx not in loaded_imgs:
            l = line_images[idx]
            loaded_imgs[idx] = (Image.open(l['w']).convert("RGBA"), Image.open(l['g']).convert("RGBA"))
        return loaded_imgs[idx]

    def make_frame(get_frame_t):
        t = get_frame_t
        
        # 1. Find Active Line
        active_idx = -1
        for seg in timeline:
            if seg['start'] <= t <= seg['end']: 
                active_idx = seg['line']
                break
        
        # 2. Find Active Paragraph
        visible_lines = []
        highlight_idx = active_idx # Can be -1
        
        found_para = False
        
        if active_idx != -1:
            for para in paragraphs:
                if active_idx in para:
                    visible_lines = para
                    found_para = True
                    break
        
        # State persistence: If drift/no-match, keep showing LAST matched paragraph
        if not found_para:
            # Find the last valid line before this time
            last_idx = 0
            for seg in timeline:
                if seg['end'] < t and seg['line'] != -1:
                    last_idx = seg['line']
            
            # Show that paragraph
            for para in paragraphs:
                if last_idx in para:
                    visible_lines = para
                    break
            
            highlight_idx = -1 # No highlight during drift

        W, H = VIDEO_SIZE
        frame_img = Image.new('RGBA', (W, H), (0,0,0,0))
        
        # 3. Layout: Center the visible paragraph block
        if visible_lines:
            total_h = sum([line_images[ali]['h'] for ali in visible_lines]) + (len(visible_lines)-1)*40
            start_y = (H - total_h) / 2 + 300 # Lower half offset
            
            curr_y = start_y
            for idx in visible_lines:
                w_img, g_img = get_imgs(idx)
                src = g_img if idx == highlight_idx else w_img
                
                # Center horizontally
                x_pos = (W - w_img.width) // 2
                frame_img.alpha_composite(src, (x_pos, int(curr_y)))
                curr_y += line_images[idx]['h'] + 40
                
        return np.array(frame_img)

    text_clip = VideoClip(make_frame, duration=duration)
    audio = AudioFileClip(audio_path)
    
    if os.path.exists(output_path): os.remove(output_path)
    
    bg = ColorClip(size=VIDEO_SIZE, color=bg_rgb, duration=duration)
    
    title_clip = (ImageClip(title_path)
                  .with_position(('center', 100))
                  .with_duration(duration))
                  
    cover = (ImageClip(image_path)
             .resized(width=600)
             .with_position(('center', 250))
             .with_duration(duration))
     
    # Text clip sits on top. Position is handled inside make_frame relative to full canvas
    final = CompositeVideoClip([bg, title_clip, cover, text_clip], size=VIDEO_SIZE).with_audio(audio)
    
    log(f"Rendering {output_path}...", data={"codec": "libx264", "fps": 24})
    write_status(song_id, "processing", "Rendering video (this takes a while)...")
    temp_output = output_path + ".temp.mp4"
    if os.path.exists(temp_output): os.remove(temp_output)
    
    try:
        t_start_render = time.time()
        final.write_videofile(temp_output, fps=24, codec='libx264', audio_codec='aac')
        log(f"✅ Video encoding complete. (Took {time.time() - t_start_render:.1f}s)")
        
        # Atomic rename to final path
        if os.path.exists(output_path): os.remove(output_path)
        if os.path.exists(output_path): os.remove(output_path)
        os.rename(temp_output, output_path)
        log("✅ Done (Atomic Rename)")
        write_status(song_id, "completed", "Video generated successfully!", video_url=output_path)
        
    except Exception as e:
        log(f"❌ Render failed: {e}", type_="ERROR")
        write_status(song_id, "failed", "Render failed", error=e)
        if os.path.exists(temp_output): os.remove(temp_output)
        sys.exit(1)
    finally:
        if os.path.exists(temp_output):
             try:
                 os.remove(temp_output)
             except: pass
    
    # Cleanup
    shutil.rmtree(temp_dir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("song_id")
    parser.add_argument("--title", default="Baby Song")
    parser.add_argument("--output", default=None)
    parser.add_argument("--audio", default=None)
    parser.add_argument("--image", default=None)
    parser.add_argument("--lyrics", default=None)
    parser.add_argument("--log_file", default=None)
    parser.add_argument("--language", default=None)
    
    args = parser.parse_args()
    
    generate_video(
        args.song_id, 
        title=args.title, 
        output_path=args.output,
        s_audio=args.audio,
        s_image=args.image,
        s_lyrics=args.lyrics,
        log_file=args.log_file,
        language=args.language
    )
