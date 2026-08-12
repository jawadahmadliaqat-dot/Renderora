import os
import sys
import subprocess
import uuid
import glob
import shutil
import re
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

# 1. Environment Variables Configuration
load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://127.0.0.1:8000/auth/google/callback")

# Directory Setup
MEDIA_DIR = "media"
OUTPUT_VIDEOS_DIR = os.path.join(MEDIA_DIR, "videos")
OUTPUT_PLOTS_DIR = os.path.join(MEDIA_DIR, "plots")

os.makedirs(OUTPUT_VIDEOS_DIR, exist_ok=True)
os.makedirs(OUTPUT_PLOTS_DIR, exist_ok=True)

# 2. Security Configuration & Inspector
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
    """Inspects code for dangerous operations before execution."""
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, code, re.IGNORECASE):
            return False, f"⚠️ Security Alert: Dangerous code pattern detected (`{pattern}`)."
    return True, ""


# 3. FastAPI Initialization
app = FastAPI(
    title="Renderora API & Animation Studio",
    description="Unified backend supporting FastAPI endpoints and Gradio Web UI for Manim & Matplotlib rendering.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static media hosting
app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")


class CodeRequest(BaseModel):
    code: str


# ==========================================
# 4. FastAPI Endpoints
# ==========================================

@app.get("/", response_class=HTMLResponse)
def serve_home():
    """Serves index.html or fallback landing page."""
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    return HTMLResponse(
        "<h1>⚡ Welcome to Renderora API</h1>"
        "<p>Gradio UI Studio is live at <a href='/studio'>/studio</a></p>",
        status_code=200
    )


# --- Google OAuth Routes ---
@app.get("/auth/google")
def login_google():
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="GOOGLE_CLIENT_ID is not configured in .env")
    
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
        raise HTTPException(status_code=400, detail="Failed to fetch access token from Google.")
    
    user_info_res = requests.get(
        "https://www.googleapis.com/oauth2/v1/userinfo",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    user_info = user_info_res.json()
    
    name = user_info.get("name", "User")
    picture = user_info.get("picture", "")
    
    return RedirectResponse(url=f"http://127.0.0.1:8000/?name={name}&picture={picture}")


# --- Rendering Endpoints ---
@app.post("/render")
def render_manim_or_animation_code(req: CodeRequest):
    """Renders either Matplotlib Animations or Manim Code."""
    safe, msg = is_safe(req.code)
    if not safe:
        raise HTTPException(status_code=400, detail=msg)

    job_id = str(uuid.uuid4())[:8]
    work_dir = f"temp_{job_id}"
    os.makedirs(work_dir, exist_ok=True)
    
    script_filename = os.path.join(work_dir, "script.py")
    is_matplotlib_animation = "animation.FuncAnimation" in req.code or "matplotlib.animation" in req.code
    
    try:
        if is_matplotlib_animation:
            output_video_path = os.path.join(OUTPUT_VIDEOS_DIR, f"anim_{job_id}.mp4")
            safe_out_path = output_video_path.replace("\\", "/")
            
            forced_prefix = (
                "import matplotlib\n"
                "matplotlib.use('Agg')\n"
                "import matplotlib.pyplot as plt\n"
                "import numpy as np\n"
                "import matplotlib.animation as animation\n\n"
            )
            
            animation_injection = (
                f"\n\n# Auto-injected saver\n"
                f"if 'ani' in locals():\n"
                f"    ani.save(r'{safe_out_path}', writer='ffmpeg', fps=30)\n"
                f"elif 'anim' in locals():\n"
                f"    anim.save(r'{safe_out_path}', writer='ffmpeg', fps=30)\n"
            )
            
            modified_code = forced_prefix + req.code + animation_injection
            with open(script_filename, "w", encoding="utf-8") as f:
                f.write(modified_code)
                
            cmd = [sys.executable, script_filename]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                raise HTTPException(status_code=400, detail=result.stderr or result.stdout)
                
            if not os.path.exists(output_video_path):
                raise HTTPException(status_code=500, detail="Animation executed, but MP4 video was not created. Ensure FFmpeg is installed.")
                
            video_url = f"http://127.0.0.1:8000/{safe_out_path}"
            return {"success": True, "video_url": video_url}

        else:
            # Manim Engine Rendering
            with open(script_filename, "w", encoding="utf-8") as f:
                f.write(req.code)
                
            cmd = ["manim", "-ql", "--media_dir", work_dir, script_filename]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                raise HTTPException(status_code=400, detail=result.stderr or result.stdout)
                
            matched_files = glob.glob(os.path.join(work_dir, "**", "*.mp4"), recursive=True)
            if not matched_files:
                raise HTTPException(status_code=500, detail="Manim rendered, but output MP4 file was not found.")
            
            final_video_path = os.path.join(OUTPUT_VIDEOS_DIR, f"manim_{job_id}.mp4")
            shutil.copy(matched_files[0], final_video_path)
            
            safe_final_path = final_video_path.replace("\\", "/")
            video_url = f"http://127.0.0.1:8000/{safe_final_path}"
            return {"success": True, "video_url": video_url}

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Rendering timed out (Limit: 60s).")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


@app.post("/render-plot")
def render_matplotlib_plot(req: CodeRequest):
    """Renders Static Matplotlib 2D/3D Plots."""
    safe, msg = is_safe(req.code)
    if not safe:
        raise HTTPException(status_code=400, detail=msg)

    job_id = str(uuid.uuid4())[:8]
    script_filename = f"temp_plot_{job_id}.py"
    output_image_path = os.path.join(OUTPUT_PLOTS_DIR, f"plot_{job_id}.png")
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
        cmd = [sys.executable, script_filename]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            raise HTTPException(status_code=400, detail=result.stderr or result.stdout)
            
        if not os.path.exists(output_image_path):
            raise HTTPException(status_code=500, detail="Plot script executed, but image file was not generated.")
            
        image_url = f"http://127.0.0.1:8000/{safe_img_path}"
        return {"success": True, "image_url": image_url}
        
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Plot generation timed out.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(script_filename):
            os.remove(script_filename)


# ==========================================
# 5. Gradio Web Interface
# ==========================================

def render_video_gradio(code: str):
    """Adapter function tailored for Gradio block UI."""
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
            return None, f"⚠️ Manim Error:\n{error_msg}"

        mp4_files = glob.glob(os.path.join(work_dir, "**", "*.mp4"), recursive=True)
        if not mp4_files:
            return None, "❌ Video generate nahi hui. Class name check karein (Scene se inherit hona chahiye)."

        video_path = max(mp4_files, key=os.path.getctime)
        final_path = os.path.join(OUTPUT_VIDEOS_DIR, f"gradio_{job_id}.mp4")
        shutil.copy(video_path, final_path)

        return final_path, "✅ Video Rendered Successfully!"

    except subprocess.TimeoutExpired:
        return None, "⏱️ Timeout: Rendering 50 seconds se zyada legayi. Code chhota karein."
    except Exception as e:
        return None, f"❌ Unexpected Error: {str(e)}"
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


with gr.Blocks(
    title="Renderora Studio",
    theme=gr.themes.Soft(primary_hue="indigo")
) as demo:
    
    gr.Markdown("""
    # ⚡ Renderora
    ### Cloud Animation & Plot Studio
    Apna Manim Code neeche paste karein aur Render dabayein.
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
            render_btn = gr.Button("🚀 Render Video", variant="primary", size="lg")

        with gr.Column(scale=1):
            video_output = gr.Video(label="Output Animation")
            status = gr.Textbox(label="Status", interactive=False, lines=3)

    render_btn.click(
        fn=render_video_gradio,
        inputs=code_input,
        outputs=[video_output, status]
    )

    gr.Markdown("---\nMade with ❤️ | Renderora Studio Engine")


# 6. Mount Gradio to FastAPI at `/studio`
app = gr.mount_gradio_app(app, demo, path="/studio")


# ==========================================
# 7. Execution Entrypoint
# ==========================================
if __name__ == "__main__":
    print("🚀 Starting Renderora Application...")
    print("📍 FastAPI Endpoints: http://127.0.0.1:8000")
    print("📍 Gradio Interactive UI: http://127.0.0.1:8000/studio")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)