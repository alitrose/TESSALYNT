/**
 * Tessalynt - Global JavaScript Utilities & API Key Management
 */

// Mobile Navigation Toggle
document.addEventListener("DOMContentLoaded", () => {
  const toggleBtn = document.getElementById("navToggle");
  const navMenu = document.getElementById("navMenu");
  if (toggleBtn && navMenu) {
    toggleBtn.addEventListener("click", () => {
      navMenu.classList.toggle("open");
    });
  }

  // Check API Status on load
  checkApiStatus();

  // Settings Modal setup
  setupSettingsModal();
});

// Toast Notification System
function showToast(message, type = "info") {
  let container = document.getElementById("toastContainer");
  if (!container) {
    container = document.createElement("div");
    container.id = "toastContainer";
    container.className = "toast-container";
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  
  let iconSvg = "";
  if (type === "success") {
    iconSvg = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>`;
  } else if (type === "error") {
    iconSvg = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#EF4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>`;
  } else {
    iconSvg = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6366F1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>`;
  }

  toast.innerHTML = `${iconSvg} <span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Copy to Clipboard Helper
async function copyToClipboard(text, successMessage = "Copied to clipboard!") {
  try {
    await navigator.clipboard.writeText(text);
    showToast(successMessage, "success");
  } catch (err) {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand("copy");
    document.body.removeChild(textarea);
    showToast(successMessage, "success");
  }
}

// Check Gemini API Configuration Status
async function checkApiStatus() {
  const badge = document.getElementById("apiStatusBadge");
  const text = document.getElementById("apiStatusText");
  if (!badge) return;

  try {
    const res = await fetch("/api/status");
    const data = await res.json();
    if (data.configured) {
      badge.classList.add("active");
      badge.classList.remove("warning");
      if (text) text.textContent = data.model ? `Gemini Active (${data.model})` : "Gemini Connected";
    } else {
      badge.classList.remove("active");
      badge.classList.add("warning");
      if (text) text.textContent = "API Key Needed";
    }
  } catch (e) {
    badge.classList.remove("active");
    if (text) text.textContent = "Status Check Failed";
  }
}

// Settings Modal
function setupSettingsModal() {
  const openBtns = document.querySelectorAll(".open-settings-modal");
  const modal = document.getElementById("settingsModal");
  const closeBtn = document.getElementById("closeSettingsModal");
  const saveBtn = document.getElementById("saveKeyBtn");
  const clearBtn = document.getElementById("clearKeyBtn");
  const keyInput = document.getElementById("settingsApiKeyInput");

  if (!modal) return;

  openBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      modal.classList.add("active");
    });
  });

  if (closeBtn) {
    closeBtn.addEventListener("click", () => {
      modal.classList.remove("active");
    });
  }

  modal.addEventListener("click", (e) => {
    if (e.target === modal) modal.classList.remove("active");
  });

  if (saveBtn && keyInput) {
    saveBtn.addEventListener("click", async () => {
      const key = keyInput.value.trim();
      if (!key) {
        showToast("Please enter an API key", "error");
        return;
      }
      saveBtn.disabled = true;
      saveBtn.textContent = "Verifying...";
      try {
        const res = await fetch("/api/set-session-key", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ api_key: key })
        });
        const data = await res.json();
        if (res.ok) {
          showToast(data.message, "success");
          modal.classList.remove("active");
          keyInput.value = "";
          checkApiStatus();
        } else {
          showToast(data.message || "Failed to verify key", "error");
        }
      } catch (err) {
        showToast("Error connecting to server", "error");
      } finally {
        saveBtn.disabled = false;
        saveBtn.textContent = "Save & Verify";
      }
    });
  }

  if (clearBtn) {
    clearBtn.addEventListener("click", async () => {
      try {
        await fetch("/api/set-session-key", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ api_key: "" })
        });
        showToast("Session key cleared. Defaulting to .env", "info");
        checkApiStatus();
      } catch (err) {
        showToast("Failed to clear session key", "error");
      }
    });
  }
}

// Download PDF Helper via POST blob
async function downloadPdfFromApi(exportType, payload) {
  const btn = event?.currentTarget;
  const originalText = btn ? btn.innerHTML : "";
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner" style="width:14px;height:14px;border-width:2px;margin:0;display:inline-block;vertical-align:middle;"></span> Generating PDF...`;
  }

  try {
    const res = await fetch("/api/export-pdf", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ export_type: exportType, ...payload })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.message || "PDF generation failed");
    }

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `Tessalynt_${exportType}_${Date.now()}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    showToast("PDF downloaded successfully!", "success");
  } catch (err) {
    showToast(`PDF Error: ${err.message}`, "error");
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = originalText;
    }
  }
}

// Download TXT Helper
async function downloadTxtFromApi(title, subject, topic, content) {
  try {
    const res = await fetch("/api/export-txt", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, subject, topic, content })
    });
    if (!res.ok) throw new Error("TXT export failed");

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `Tessalynt_${(topic || "notes").replace(/\s+/g, "_")}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    showToast("TXT notes downloaded!", "success");
  } catch (err) {
    showToast(`TXT Export Error: ${err.message}`, "error");
  }
}

// Simple Markdown Renderer for client-side display
function renderSimpleMarkdown(md) {
  if (!md) return "";
  let html = md
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^#### (.*$)/gim, '<h4>$1</h4>')
    .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/gim, '<em>$1</em>')
    .replace(/`([^`]+)`/gim, '<code>$1</code>')
    .replace(/^\> (.*$)/gim, '<blockquote>$1</blockquote>')
    .replace(/^\- (.*$)/gim, '<li>$1</li>')
    .replace(/^\* (.*$)/gim, '<li>$1</li>')
    .replace(/<\/li>\n<li>/gim, '</li><li>')
    .replace(/\n{2,}/gim, '</p><p>')
    .replace(/\n/gim, '<br>');

  return `<p>${html}</p>`;
}
