import os
import sys
import subprocess
import uuid
import glob
import shutil
import re
import time
import threading
import requests
from typing import Tuple

import gradio as gr
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn

# ==========================================
# 1. Environment Variables
# ==========================================
load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")
REDIRECT_URI = os.getenv("REDIRECT_URI", f"{BASE_URL}/auth/google/callback")

# ==========================================
# 2. Self-Ping Keep-Alive Bot (Prevents Render Sleep)
# ==========================================
def keep_alive_bot():
    # Production URL ko ping karega
    target_url = os.getenv("BASE_URL", "https://renderora.onrender.com")
    interval = 720  # 12 minutes delay (Render sleeps after 15 mins)

    print(f"🤖 Keep-Alive Bot initialized! Target: {target_url}")
    time.sleep(30)  # Initial wait server start hone ke liye

    while True:
        try:
            res = requests.get(target_url, timeout=10)
            print(f"⏰ [Keep-Alive Ping Success] Status Code: {res.status_code}")
        except Exception as e:
            print(f"⚠️ [Keep-Alive Ping Failed]: {e}")
        
        time.sleep(interval)

# Background thread mein bot start
threading.Thread(target=keep_alive_bot, daemon=True).start()

# ==========================================
# 3. Directory Setup
# ==========================================
MEDIA_DIR = "media"
OUTPUT_VIDEOS_DIR = os.path.join(MEDIA_DIR, "videos")
OUTPUT_PLOTS_DIR = os.path.join(MEDIA_DIR, "plots")

os.makedirs(OUTPUT_VIDEOS_DIR, exist_ok=True)
os.makedirs(OUTPUT_PLOTS_DIR, exist_ok=True)

# ==========================================
# 4. Security Check
# ==========================================
DANGEROUS_PATTERNS = [
    r"os\.(system|popen|remove|rmdir|unlink)",
    r"subprocess",
    r"shutil\.(rmtree|move|copy)",
    r"eval\s*\(",
    r"exec\s*\(",
    r"__import__",
    r"open\s*\([^)]*['\"]w",
    r"rm\s+-rf",
    r"sys\.(exit|modules)",
    r"import\s+socket",
    r"import\s+requests",
    r"while\s+True",
]

def is_safe(code: str) -> Tuple[bool, str]:
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, code, re.IGNORECASE):
            return False, f"Security Alert: Dangerous code pattern detected (`{pattern}`)."
    return True, ""

# ==========================================
# 5. FastAPI App Setup
# ==========================================
app = FastAPI(
    title="Renderora API & Animation Studio",
    description="Backend for Manim & Matplotlib rendering",
    version="2.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")

class CodeRequest(BaseModel):
    code: str
    quality: str = "LOW"
# ==========================================
# 6. Favicon Routes (Fixes Tab Icon Issue)
# ==========================================
@app.get('/favicon.ico', include_in_schema=False)
@app.get('/favicon.svg', include_in_schema=False)
async def favicon():
    favicon_path = os.path.join(MEDIA_DIR, "favicon.svg")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    raise HTTPException(status_code=404, detail="Favicon file not found in media folder")
# ==========================================
# 6. Home Route
# ==========================================
@app.get("/", response_class=HTMLResponse)
def serve_home():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    return HTMLResponse(
        "<h1>Renderora API</h1>"
        "<p>Gradio UI available at <a href='/studio'>/studio</a></p>"
    )

# ==========================================
# 7. Google OAuth
# ==========================================
@app.get("/auth/google")
def login_google():
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="GOOGLE_CLIENT_ID is not configured")
    
    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?response_type=code"
        f"&client_id={GOOGLE_CLIENT_ID}&redirect_uri={REDIRECT_URI}"
        f"&scope=openid%20email%20profile"
    )
    return RedirectResponse(url=google_auth_url)

@app.get("/auth/google/callback")
def auth_google_callback(code: str):
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    token_res = requests.post(token_url, data=data)
    token_json = token_res.json()
    
    access_token = token_json.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Failed to get access token")
    
    user_info_res = requests.get(
        "https://www.googleapis.com/oauth2/v1/userinfo",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    user_info = user_info_res.json()
    
    name = user_info.get("name", "User")
    picture = user_info.get("picture", "")
    
    return RedirectResponse(url=f"{BASE_URL}/?name={name}&picture={picture}")

# ==========================================
# 8. Main Render Endpoint
# ==========================================
@app.post("/render")
def render_code(req: CodeRequest):
    safe, msg = is_safe(req.code)
    if not safe:
        raise HTTPException(status_code=400, detail=msg)

    job_id = str(uuid.uuid4())[:8]
    work_dir = f"temp_{job_id}"
    os.makedirs(work_dir, exist_ok=True)
    
    script_filename = os.path.join(work_dir, "script.py")
    is_matplotlib_animation = "FuncAnimation" in req.code or "matplotlib.animation" in req.code
    
    try:
        # ---------- Matplotlib Animation ----------
        if is_matplotlib_animation:
            filename = f"anim_{job_id}.mp4"
            output_video_path = os.path.join(OUTPUT_VIDEOS_DIR, filename)
            safe_out_path = output_video_path.replace("\\", "/")
            
            forced_prefix = (
                "import matplotlib\n"
                "matplotlib.use('Agg')\n"
                "import matplotlib.pyplot as plt\n"
                "import numpy as np\n"
                "import matplotlib.animation as animation\n\n"
            )
            
            animation_injection = (
                f"\n\n"
                f"if 'ani' in locals():\n"
                f"    ani.save(r'{safe_out_path}', writer='ffmpeg', fps=30)\n"
                f"elif 'anim' in locals():\n"
                f"    anim.save(r'{safe_out_path}', writer='ffmpeg', fps=30)\n"
            )
            
            modified_code = forced_prefix + req.code + animation_injection
            
            with open(script_filename, "w", encoding="utf-8") as f:
                f.write(modified_code)
                
            result = subprocess.run(
                [sys.executable, script_filename],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                raise HTTPException(status_code=400, detail=result.stderr or result.stdout)
                
            if not os.path.exists(output_video_path):
                raise HTTPException(status_code=500, detail="Animation ran but MP4 was not created. Check FFmpeg.")
            
            print(f"✅ Matplotlib animation saved: {output_video_path}")
            
            return {
                "success": True,
                "video_url": f"/media/videos/{filename}"
            }

        # ---------- Manim Rendering ----------
        else:
            with open(script_filename, "w", encoding="utf-8") as f:
                f.write(req.code)

            quality_flag = "-qh" if req.quality == "HIGH" else "-ql"

            result = subprocess.run(
                ["manim", quality_flag, "--media_dir", work_dir, "-o", f"output_{job_id}", script_filename],
                capture_output=True,
                text=True,
                timeout=90
            )

            print("===== MANIM STDOUT =====")
            print(result.stdout[-1000:] if result.stdout else "No stdout")
            print("===== MANIM STDERR =====")
            print(result.stderr[-1000:] if result.stderr else "No stderr")

            if result.returncode != 0:
                raise HTTPException(status_code=400, detail=result.stderr or result.stdout)

            matched_files = glob.glob(os.path.join(work_dir, "**", "*.mp4"), recursive=True)
            print("Found MP4 files:", matched_files)

            if not matched_files:
                raise HTTPException(status_code=500, detail="Manim finished but no MP4 file was found.")

            filename = f"manim_{job_id}.mp4"
            final_video_path = os.path.abspath(os.path.join(OUTPUT_VIDEOS_DIR, filename))

            shutil.copy2(matched_files[0], final_video_path)

            if not os.path.exists(final_video_path):
                raise HTTPException(status_code=500, detail=f"Copy failed. File not found at {final_video_path}")

            print(f"✅ Video successfully saved at: {final_video_path}")

            return {
                "success": True,
                "video_url": f"/media/videos/{filename}"
            }

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Rendering timed out (limit 90s).")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

# ==========================================
# 9. Static Plot Endpoint
# ==========================================
@app.post("/render-plot")
def render_plot(req: CodeRequest):
    safe, msg = is_safe(req.code)
    if not safe:
        raise HTTPException(status_code=400, detail=msg)

    job_id = str(uuid.uuid4())[:8]
    script_filename = f"temp_plot_{job_id}.py"
    filename = f"plot_{job_id}.png"
    output_image_path = os.path.join(OUTPUT_PLOTS_DIR, filename)
    safe_img_path = output_image_path.replace("\\", "/")
    
    forced_prefix = (
        "import matplotlib\n"
        "matplotlib.use('Agg')\n"
        "import matplotlib.pyplot as plt\n"
        "import numpy as np\n\n"
    )
    
    modified_code = forced_prefix + req.code + f"\n\nplt.savefig(r'{safe_img_path}', bbox_inches='tight')\nplt.close()"
    
    with open(script_filename, "w", encoding="utf-8") as f:
        f.write(modified_code)
        
    try:
        result = subprocess.run(
            [sys.executable, script_filename],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            raise HTTPException(status_code=400, detail=result.stderr or result.stdout)
            
        if not os.path.exists(output_image_path):
            raise HTTPException(status_code=500, detail="Plot script ran but image was not created.")
        
        print(f"✅ Plot saved: {output_image_path}")
        
        return {
            "success": True,
            "image_url": f"/media/plots/{filename}"
        }
        
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Plot generation timed out.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(script_filename):
            os.remove(script_filename)

# ==========================================
# 10. Gradio Interface
# ==========================================
def render_video_gradio(code: str):
    safe, message = is_safe(code)
    if not safe:
        return None, message

    job_id = str(uuid.uuid4())[:8]
    work_dir = f"temp_gradio_{job_id}"
    os.makedirs(work_dir, exist_ok=True)
    scene_file = os.path.join(work_dir, "scene.py")

    with open(scene_file, "w", encoding="utf-8") as f:
        f.write(code)

    try:
        result = subprocess.run(
            ["manim", "-ql", "--media_dir", work_dir, scene_file],
            capture_output=True,
            text=True,
            timeout=50,
            cwd=work_dir
        )

        if result.returncode != 0:
            error_msg = result.stderr[-800:] if result.stderr else "Unknown Manim error"
            return None, f"Manim Error:\n{error_msg}"

        mp4_files = glob.glob(os.path.join(work_dir, "**", "*.mp4"), recursive=True)
        if not mp4_files:
            return None, "Video not generated. Make sure your class inherits from Scene."

        video_path = max(mp4_files, key=os.path.getctime)
        final_path = os.path.join(OUTPUT_VIDEOS_DIR, f"gradio_{job_id}.mp4")
        shutil.copy2(video_path, final_path)

        return final_path, "Video Rendered Successfully!"

    except subprocess.TimeoutExpired:
        return None, "Timeout: Rendering took more than 50 seconds."
    except Exception as e:
        return None, f"Unexpected Error: {str(e)}"
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

with gr.Blocks(title="Renderora Studio") as demo:
    gr.Markdown("""
    # Renderora
    ### Cloud Animation & Plot Studio
    Paste your Manim code below and click Render.
    """)

    with gr.Row():
        with gr.Column(scale=1):
            code_input = gr.Code(
                language="python",
                lines=18,
                label="Manim Code",
                value="""from manim import *

class MyScene(Scene):
    def construct(self):
        text = Text("Hello from Renderora!").scale(1.5)
        self.play(Write(text))
        self.wait(1)
"""
            )
            render_btn = gr.Button("Render Video", variant="primary", size="lg")

        with gr.Column(scale=1):
            video_output = gr.Video(label="Output Animation")
            status = gr.Textbox(label="Status", interactive=False, lines=3)

    render_btn.click(
        fn=render_video_gradio,
        inputs=code_input,
        outputs=[video_output, status]
    )

    gr.Markdown("---\nMade with love | Renderora Studio")

app = gr.mount_gradio_app(app, demo, path="/studio")

# ==========================================
# 11. Start Server
# ==========================================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"Starting Renderora Server on Port {port}...")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
