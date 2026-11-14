/**
 * Tessalynt - AI Notes Generator Controller
 * Supports 3 learning levels: Beginner Friendly, University Academic, Exam Preparation
 */
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("notesForm");
  const loadingBox = document.getElementById("notesLoading");
  const loadingTitle = document.getElementById("loadingTitle");
  const loadingDesc = document.getElementById("loadingDesc");
  const outputCard = document.getElementById("notesOutput");
  const renderedContent = document.getElementById("renderedNotes");
  const generateBtn = document.getElementById("generateNotesBtn");
  const docTitle = document.getElementById("notesDocTitle");
  const docMeta = document.getElementById("notesDocMeta");
  const levelBadge = document.getElementById("notesLevelBadge");

  // Action buttons
  const copyBtn = document.getElementById("copyNotesBtn");
  const txtBtn = document.getElementById("txtNotesBtn");
  const pdfBtn = document.getElementById("pdfNotesBtn");
  const printBtn = document.getElementById("printNotesBtn");
  const regenBtn = document.getElementById("regenNotesBtn");

  // Learning Level Selection Handling
  const levelCards = document.querySelectorAll(".level-card");
  const levelRadios = document.querySelectorAll('input[name="learningLevel"]');

  levelRadios.forEach(radio => {
    radio.addEventListener("change", () => {
      updateSelectedLevelCard(radio.value);
    });
  });

  function updateSelectedLevelCard(selectedLevel) {
    levelCards.forEach(card => {
      const radio = card.querySelector('input[name="learningLevel"]');
      if (radio && radio.value === selectedLevel) {
        card.classList.add("selected");
        radio.checked = true;
      } else {
        card.classList.remove("selected");
      }
    });
  }

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
    const selectedLevelRadio = document.querySelector('input[name="learningLevel"]:checked');
    const learningLevel = selectedLevelRadio ? selectedLevelRadio.value : "academic";

    const payload = {
      stream: document.getElementById("degreeStream").value.trim(),
      department: document.getElementById("department").value.trim(),
      year: document.getElementById("academicYear").value,
      semester: document.getElementById("semester").value,
      subject: document.getElementById("subject").value.trim(),
      topic: document.getElementById("topic").value.trim(),
      learning_level: learningLevel,
      instructions: document.getElementById("instructions").value.trim()
    };

    if (!payload.subject || !payload.topic) {
      showToast("Please provide both Subject and Topic.", "error");
      return;
    }

    // Dynamic Loading Feedback by Level
    if (loadingTitle && loadingDesc) {
      if (learningLevel === "beginner") {
        loadingTitle.textContent = "Crafting Beginner-Friendly Notes...";
        loadingDesc.textContent = "Google Gemini is structuring your notes with intuitive real-world analogies, plain-English math translations, and step-by-step concepts.";
      } else if (learningLevel === "exam") {
        loadingTitle.textContent = "Compiling University Exam Blueprint...";
        loadingDesc.textContent = "Google Gemini is structuring 2-mark, 5-mark, 8-mark & 16-mark model answers, mark-distribution rubrics, and high-frequency examination traps.";
      } else {
        loadingTitle.textContent = "Synthesizing University Academic Notes...";
        loadingDesc.textContent = "Google Gemini is authoring exhaustive textbook-depth notes with formal definitions, complete mathematical symbol breakdowns, and architectural diagrams.";
      }
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
    docMeta.textContent = `${data.subject} • ${data.topic} • ${data.stream || "Higher Education"}`;
    
    // Level Badge update
    if (levelBadge) {
      const lvl = (data.learning_level || "academic").toLowerCase();
      levelBadge.className = "badge";
      if (lvl === "beginner") {
        levelBadge.classList.add("badge-beginner");
        levelBadge.innerHTML = "🌱 Level 1: Beginner Friendly";
      } else if (lvl === "exam") {
        levelBadge.classList.add("badge-exam");
        levelBadge.innerHTML = "📝 Level 3: Exam Preparation";
      } else {
        levelBadge.classList.add("badge-recommended");
        levelBadge.innerHTML = "🎓 Level 2: University Academic";
      }
    }

    // High-fidelity Markdown, Math, and Diagram rendering
    renderAcademicMarkdown(data.content, renderedContent);

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

  // PDF Download with Learning Level Metadata
  if (pdfBtn) {
    pdfBtn.addEventListener("click", () => {
      if (!currentNotesData) return;
      downloadPdfFromApi("notes", {
        title: currentNotesData.title,
        subject: currentNotesData.subject,
        topic: currentNotesData.topic,
        stream: currentNotesData.stream,
        learning_level: currentNotesData.learning_level || "academic",
        difficulty: currentNotesData.learning_level || "academic",
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
