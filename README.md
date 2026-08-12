
<p align="center">
  <img src="https://readme-typing-svg.herokuapp.com?font=Righteous&color=6366F1&size=50&center=true&vCenter=true&width=750&lines=Renderora;Cloud-Native+Animation+%26+Plotting+Platform" alt="Renderora" />
</p>

<p align="center">
  <strong>A high-performance, containerized cloud platform for real-time Manim math animations, Matplotlib plots, and dynamic interactive charts.</strong>
</p>

<p align="center">
  <a href="https://renderora.onrender.com">
    <img src="https://img.shields.io/badge/Live_Demo-https%3A%2F%2Frenderora.onrender.com-6366F1?style=for-the-badge&logo=render&logoColor=white" alt="Live Demo" />
  </a>
  <a href="https://github.com/jawadahmadliaqat-dot/Renderora">
    <img src="https://img.shields.io/github/stars/jawadahmadliaqat-dot/Renderora?style=for-the-badge&color=f1c40f" alt="Stars" />
  </a>
  <img src="https://img.shields.io/badge/Docker-Supported-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker" />
  <img src="https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
</p>

---

## 📌 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Live Demo & Cloud Access](#-live-demo--cloud-access)
- [System Architecture](#-system-architecture)
- [Core Templates & Examples](#-core-templates--examples)
- [Tech Stack](#-tech-stack)
- [REST API Specification](#-rest-api-specification)
- [Local Development & Docker Setup](#-local-development--docker-setup)
- [Deployment Guide](#-deployment-guide)
- [Troubleshooting & Performance](#-troubleshooting--performance)
- [Contributing](#-contributing)
- [License](#-license)

---

## ⚡ Overview

**Renderora** is an end-to-end cloud-native studio designed for students, educators, software engineers, and content creators. It eliminates the hassle of configuring complex local LaTeX, FFmpeg, and Python environments by shifting video rendering and mathematical plotting into an accessible web platform.

Powered by a containerized **FastAPI** backend and an **in-browser Monaco-style editor**, users can seamlessly write **Manim (Community Edition)** code, synthesize **Matplotlib** graphics, or manipulate real-time **Chart.js** telemetry feeds.

---

## ✨ Key Features

- **🌐 Live Cloud Rendering Engine:** Offloads resource-heavy mathematical video encoding (Manim) and image generation (Matplotlib) to cloud servers.
- **🐳 Fully Containerized (Docker):** Bundles FFmpeg, Cairo, LaTeX dependencies, and Python runtimes for deterministic execution across environments.
- **👨‍💻 Modern Web Editor Studio:**
  - Dynamic line numbering & scroll-sync.
  - Quick render shortcut (`Ctrl + Enter` / `Cmd + Enter`).
  - Auto-persisting draft storage via `localStorage`.
  - Mobile-responsive layout switching between Editor & Preview viewports.
- **📊 Real-time Interactive Control Panel:** Live parameter sliders (Frequency, Amplitude) bound to dynamic client-side telemetry rendering via Chart.js.
- **🔑 Google OAuth Single Sign-On:** Pre-integrated authentication pipeline to manage access controls before dispatching heavy computation workloads.
- **📥 One-Click Export:** Native streaming media previews with instant high-speed file download handlers for MP4 videos and PNG figures.

---

## 🚀 Live Demo & Cloud Access

The platform is deployed and live on Render Cloud Infrastructure:

- **🌐 Web Platform App:** [https://renderora.onrender.com](https://renderora.onrender.com)
- **📚 Interactive API Docs (Swagger):** [https://renderora.onrender.com/docs](https://renderora.onrender.com/docs)
- **📖 Alternative Docs (ReDoc):** [https://renderora.onrender.com/redoc](https://renderora.onrender.com/redoc)

> 💡 **Free Instance Notice:** The server instance automatically spins down during periods of inactivity. If accessing after a pause, please allow **30–50 seconds** for the cloud container to initialize.

---

## 🏗️ System Architecture
