/**
 * Tessalynt - Quick Revision Controller
 */
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("revisionForm");
  const loadingBox = document.getElementById("revisionLoading");
  const outputCard = document.getElementById("revisionOutput");
  const renderedContent = document.getElementById("renderedRevision");
  const generateBtn = document.getElementById("generateRevisionBtn");
  const docTitle = document.getElementById("revisionDocTitle");
  const docMeta = document.getElementById("revisionDocMeta");

  const copyBtn = document.getElementById("copyRevisionBtn");
  const txtBtn = document.getElementById("txtRevisionBtn");
  const pdfBtn = document.getElementById("pdfRevisionBtn");
  const regenBtn = document.getElementById("regenRevisionBtn");

  let currentRevisionData = null;

  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      await triggerRevisionGeneration();
    });
  }

  if (regenBtn) {
    regenBtn.addEventListener("click", async () => {
      await triggerRevisionGeneration();
    });
  }

  async function triggerRevisionGeneration() {
    const payload = {
      subject: document.getElementById("revSubject").value.trim(),
      topic: document.getElementById("revTopic").value.trim(),
      level: document.getElementById("revLevel").value.trim(),
      focus: document.getElementById("revFocus").value.trim()
    };

    if (!payload.subject || !payload.topic) {
      showToast("Subject and Topic are required for revision generation.", "error");
      return;
    }

    loadingBox.classList.add("active");
    outputCard.classList.remove("active");
    generateBtn.disabled = true;

    try {
      const res = await fetch("/api/generate-revision", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const data = await res.json();

      if (!res.ok) {
        if (data.error === "KEY_MISSING") {
          showToast(data.message, "error");
          document.getElementById("settingsModal")?.classList.add("active");
        } else {
          showToast(data.message || "Failed to generate revision", "error");
        }
        return;
      }

      currentRevisionData = data;
      renderRevision(data);
      showToast("Quick revision sheet generated & saved!", "success");

    } catch (err) {
      showToast(`Network error: ${err.message}`, "error");
    } finally {
      loadingBox.classList.remove("active");
      generateBtn.disabled = false;
    }
  }

  function renderRevision(data) {
    docTitle.textContent = data.title;
    docMeta.textContent = `${data.subject} • ${data.topic} • Last-Minute Exam Sprint`;
    renderedContent.innerHTML = renderSimpleMarkdown(data.content);
    outputCard.classList.add("active");
    outputCard.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  if (copyBtn) {
    copyBtn.addEventListener("click", () => {
      if (!currentRevisionData) return;
      copyToClipboard(currentRevisionData.content, "Revision sheet copied to clipboard!");
    });
  }

  if (txtBtn) {
    txtBtn.addEventListener("click", () => {
      if (!currentRevisionData) return;
      downloadTxtFromApi(
        currentRevisionData.title,
        currentRevisionData.subject,
        currentRevisionData.topic,
        currentRevisionData.content
      );
    });
  }

  if (pdfBtn) {
    pdfBtn.addEventListener("click", () => {
      if (!currentRevisionData) return;
      downloadPdfFromApi("revision", {
        title: currentRevisionData.title,
        subject: currentRevisionData.subject,
        topic: currentRevisionData.topic,
        content: currentRevisionData.content
      });
    });
  }
});
