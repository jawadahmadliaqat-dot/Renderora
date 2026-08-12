<p align="center">
  <img src="https://readme-typing-svg.herokuapp.com?font=Righteous&color=6366F1&size=48&center=true&vCenter=true&width=700&lines=Renderora;Cloud+Animation+Platform" alt="Renderora" />
</p>

<p align="center">
  <strong>A modern, browser-based cloud platform for rendering Manim & Matplotlib math animations and plots in real time.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Manim-Animation-FF69B4?style=for-the-badge" alt="Manim" />
  <img src="https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white" alt="Tailwind CSS" />
  <img src="https://img.shields.io/badge/Chart.js-FF6384?style=for-the-badge&logo=chartdotjs&logoColor=white" alt="Chart.js" />
</p>

---

## 📌 Table of Contents
- [About Renderora](#-about-renderora)
- [Key Features](#-key-features)
- [Web Interface Preview](#-web-interface-preview)
- [Built-In Templates](#-built-in-templates)
- [Tech Stack](#-tech-stack)
- [System Architecture](#-system-architecture)
- [Getting Started](#-getting-started)
- [API Endpoints](#-api-endpoints)
- [Disclaimer & License](#-disclaimer--license)

---

## ⚡ About Renderora

**Renderora** is a light-speed, full-featured cloud animation platform. It provides developers, mathematicians, and educators with an in-browser code studio to write Python-based **Manim** scene code, **Matplotlib** figures/animations, and interactive **Chart.js** data feeds—rendering video/image outputs via a powerful FastAPI backend service.

---

## ✨ Key Features

- **💻 In-Browser Studio:** Integrated dark-themed editor featuring live line numbering, syntax updates, and quick execution (`Ctrl + Enter`).
- **🎬 Dual Rendering Pipeline:** Automatically routes requests to render **MP4 videos** (Manim & Matplotlib `FuncAnimation`) or **PNG plots**.
- **📊 Interactive Live Charts:** Built-in JS chart execution powered by Chart.js with real-time parameter controls (Frequency/Amplitude tweak sliders).
- **📂 Preset Templates:** Instant starter templates ranging from simple geometric shapes to stickman animations, math equations, sine waves, and particle hearts.
- **📱 Fully Responsive UI:** Tailored mobile and desktop layout with tab switches between editor and preview modes.
- **🔐 Integrated OAuth:** Built-in Google Single Sign-On flow (`/auth/google`) for user authentication before triggering render tasks.
- **💾 Local State & Export:** Auto-saves draft code directly to `localStorage` and provides direct high-speed download links for final rendered media.

---

## 📸 Web Interface Preview

<p align="center">
  <img src="https://via.placeholder.com/800x420.png?text=Renderora+Cloud+Animation+Studio" width="100%" alt="Renderora Interface" />
</p>

---

## 📂 Built-In Templates

Renderora comes pre-packed with sample codes for fast prototyping:

| Template | Type | Description |
| :--- | :--- | :--- |
| **Circle** | Manim | Basic expanding pink circle scene |
| **Square → Circle** | Manim | Smooth shape transformation animation |
| **Math Formula** | Manim | LaTeX equation rendering ($e^{i\pi} + 1 = 0$) |
| **Stickman** | Manim | Animated walking stick figure scene |
| **Sine Wave** | Matplotlib | High-contrast static plot render |
| **Anim Wave** | Matplotlib | Animated wave using `FuncAnimation` |
| **Live Chart** | Chart.js | Real-time browser-rendered interactive line chart |
| **Particle Heart** | Matplotlib | Animated beating heart particle effect |

---

## 💻 Tech Stack

### Frontend
- **HTML5 & Vanilla JavaScript** (ES6+)
- **Tailwind CSS** (via CDN for sleek dark UI)
- **Chart.js** (for client-side real-time data visualization)

### Backend
- **Python 3.9+**
- **FastAPI** (Async Web Framework)
- **Manim Community Edition** (Math animation engine)
- **Matplotlib & NumPy** (Plotting and array calculations)

---

## 🏗️ System Architecture
