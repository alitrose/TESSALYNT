/**
 * Tessalynt - AI Notes Generator Controller
 */
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("notesForm");
  const loadingBox = document.getElementById("notesLoading");
  const outputCard = document.getElementById("notesOutput");
  const renderedContent = document.getElementById("renderedNotes");
  const generateBtn = document.getElementById("generateNotesBtn");
  const docTitle = document.getElementById("notesDocTitle");
  const docMeta = document.getElementById("notesDocMeta");

  // Action buttons
  const copyBtn = document.getElementById("copyNotesBtn");
  const txtBtn = document.getElementById("txtNotesBtn");
  const pdfBtn = document.getElementById("pdfNotesBtn");
  const printBtn = document.getElementById("printNotesBtn");
  const regenBtn = document.getElementById("regenNotesBtn");

  let currentNotesData = null;

  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      await triggerGeneration();
    });
  }

  if (regenBtn) {
    regenBtn.addEventListener("click", async () => {
      await triggerGeneration();
    });
  }

  async function triggerGeneration() {
    const payload = {
      stream: document.getElementById("degreeStream").value.trim(),
      department: document.getElementById("department").value.trim(),
      year: document.getElementById("academicYear").value,
      semester: document.getElementById("semester").value,
      subject: document.getElementById("subject").value.trim(),
      topic: document.getElementById("topic").value.trim(),
      instructions: document.getElementById("instructions").value.trim()
    };

    if (!payload.subject || !payload.topic) {
      showToast("Please provide both Subject and Topic.", "error");
      return;
    }

    // UI state
    loadingBox.classList.add("active");
    outputCard.classList.remove("active");
    generateBtn.disabled = true;

    try {
      const res = await fetch("/api/generate-notes", {
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
          showToast(data.message || "Failed to generate notes", "error");
        }
        return;
      }

      currentNotesData = data;
      renderNotes(data);
      showToast("Academic study notes generated & saved to library!", "success");

    } catch (err) {
      showToast(`Network error: ${err.message}`, "error");
    } finally {
      loadingBox.classList.remove("active");
      generateBtn.disabled = false;
    }
  }

  function renderNotes(data) {
    docTitle.textContent = data.title;
    docMeta.textContent = `${data.subject} • ${data.topic} • ${data.stream || "Academic Level"}`;
    renderedContent.innerHTML = renderSimpleMarkdown(data.content);
    outputCard.classList.add("active");
    outputCard.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  // Copy button
  if (copyBtn) {
    copyBtn.addEventListener("click", () => {
      if (!currentNotesData) return;
      copyToClipboard(currentNotesData.content, "Study notes copied to clipboard!");
    });
  }

  // TXT Download
  if (txtBtn) {
    txtBtn.addEventListener("click", () => {
      if (!currentNotesData) return;
      downloadTxtFromApi(
        currentNotesData.title,
        currentNotesData.subject,
        currentNotesData.topic,
        currentNotesData.content
      );
    });
  }

  // PDF Download
  if (pdfBtn) {
    pdfBtn.addEventListener("click", () => {
      if (!currentNotesData) return;
      downloadPdfFromApi("notes", {
        title: currentNotesData.title,
        subject: currentNotesData.subject,
        topic: currentNotesData.topic,
        stream: currentNotesData.stream,
        content: currentNotesData.content
      });
    });
  }

  // Print
  if (printBtn) {
    printBtn.addEventListener("click", () => {
      window.print();
    });
  }
});
