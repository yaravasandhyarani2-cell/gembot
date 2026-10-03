# Chatbox-X

[![chatbox-x](https://img.shields.io/badge/Ollama-gemma4%3Ae2b-blue)](https://github.com/yaravasandhyarani2-cell/chatbox-x)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Chatbox-X** is a local AI chatbot web application built with **Next.js 14**, **Tailwind CSS**, and **TypeScript** that connects to local **Ollama** running **`gemma4:e2b`** with real-time text streaming.

---

## 🚀 Quick Start

### 1. Prerequisites
Ensure Ollama is installed and running with the model:
```bash
ollama run gemma4:e2b
```

### 2. Install & Run
```bash
cd chatbox-x
npm install
npm run dev
```
Visit **http://localhost:3000** in your browser.

---

## 🐙 Push to GitHub
```bash
cd chatbox-x
git init
git add -A
git commit -m "feat: complete Chatbox-X app with Ollama gemma4:e2b streaming"
git branch -M main
git remote add origin https://github.com/yaravasandhyarani2-cell/chatbox-x.git
git push -u origin main
```
