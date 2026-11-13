/**
 * Tessalynt - Interactive MCQ Quiz Controller
 */
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("mcqForm");
  const loadingBox = document.getElementById("mcqLoading");
  const quizSection = document.getElementById("quizSection");
  const questionsContainer = document.getElementById("questionsContainer");
  const submitQuizBtn = document.getElementById("submitQuizBtn");
  const generateBtn = document.getElementById("generateMcqBtn");
  const quizMetaTitle = document.getElementById("quizMetaTitle");
  const quizMetaDetails = document.getElementById("quizMetaDetails");

  // Results & Exports
  const resultsCard = document.getElementById("quizResultsCard");
  const finalScoreEl = document.getElementById("finalScore");
  const finalPercentageEl = document.getElementById("finalPercentage");
  const performanceMessageEl = document.getElementById("performanceMessage");
  const retryQuizBtn = document.getElementById("retryQuizBtn");
  const downloadPaperPdfBtn = document.getElementById("downloadPaperPdfBtn");
  const downloadKeyPdfBtn = document.getElementById("downloadKeyPdfBtn");

  let currentMcqData = null;
  let userAnswers = {}; // { questionId: 'A' | 'B' | 'C' | 'D' }
  let isQuizSubmitted = false;

  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      await triggerMcqGeneration();
    });
  }

  async function triggerMcqGeneration() {
    const payload = {
      subject: document.getElementById("mcqSubject").value.trim(),
      topic: document.getElementById("mcqTopic").value.trim(),
      count: parseInt(document.getElementById("mcqCount").value, 10),
      difficulty: document.getElementById("mcqDifficulty").value
    };

    if (!payload.subject || !payload.topic) {
      showToast("Subject and Topic are required.", "error");
      return;
    }

    loadingBox.classList.add("active");
    quizSection.style.display = "none";
    resultsCard.style.display = "none";
    generateBtn.disabled = true;
    userAnswers = {};
    isQuizSubmitted = false;

    try {
      const res = await fetch("/api/generate-mcq", {
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
          showToast(data.message || "Failed to generate MCQs", "error");
        }
        return;
      }

      currentMcqData = data;
      renderQuiz(data);
      showToast(`Generated ${data.questions.length} questions. Good luck!`, "success");

    } catch (err) {
      showToast(`Network error: ${err.message}`, "error");
    } finally {
      loadingBox.classList.remove("active");
      generateBtn.disabled = false;
    }
  }

  function renderQuiz(data) {
    quizMetaTitle.textContent = data.title;
    quizMetaDetails.textContent = `${data.subject} • ${data.topic} • ${data.difficulty} Difficulty • ${data.questions.length} Questions`;
    questionsContainer.innerHTML = "";
    userAnswers = {};
    isQuizSubmitted = false;

    data.questions.forEach((q, idx) => {
      const qCard = document.createElement("div");
      qCard.className = "mcq-question-card";
      qCard.id = `qCard_${q.id}`;

      let optionsHtml = "";
      ["A", "B", "C", "D"].forEach((optKey) => {
        const optText = q.options[optKey] || "";
        optionsHtml += `
          <button type="button" class="mcq-option-btn" data-qid="${q.id}" data-opt="${optKey}">
            <span class="mcq-option-key">${optKey}</span>
            <span class="mcq-option-text">${escapeHtml(optText)}</span>
          </button>
        `;
      });

      qCard.innerHTML = `
        <div class="mcq-prompt">
          <span style="color:var(--primary);margin-right:4px;">Q${idx + 1}.</span> ${escapeHtml(q.question)}
        </div>
        <div class="mcq-options-grid" id="optGrid_${q.id}">
          ${optionsHtml}
        </div>
        <div class="mcq-explanation-box" id="explBox_${q.id}">
          <div style="font-weight:700;margin-bottom:4px;color:var(--accent-cyan);">Detailed Explanation:</div>
          <div>${escapeHtml(q.explanation)}</div>
        </div>
      `;
      questionsContainer.appendChild(qCard);
    });

    // Option click listeners
    const optionButtons = questionsContainer.querySelectorAll(".mcq-option-btn");
    optionButtons.forEach((btn) => {
      btn.addEventListener("click", () => {
        if (isQuizSubmitted) return; // Locked after submit
        const qid = btn.getAttribute("data-qid");
        const opt = btn.getAttribute("data-opt");

        // Deselect sibling buttons
        const grid = document.getElementById(`optGrid_${qid}`);
        grid.querySelectorAll(".mcq-option-btn").forEach((b) => b.classList.remove("selected"));

        btn.classList.add("selected");
        userAnswers[qid] = opt;
      });
    });

    quizSection.style.display = "block";
    resultsCard.style.display = "none";
    submitQuizBtn.style.display = "inline-flex";
    quizSection.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  // Submit Quiz & Evaluate
  if (submitQuizBtn) {
    submitQuizBtn.addEventListener("click", () => {
      if (!currentMcqData || isQuizSubmitted) return;

      const totalQuestions = currentMcqData.questions.length;
      const answeredCount = Object.keys(userAnswers).length;

      if (answeredCount < totalQuestions) {
        const confirmSubmit = confirm(
          `You have answered ${answeredCount} of ${totalQuestions} questions. Do you still want to submit?`
        );
        if (!confirmSubmit) return;
      }

      isQuizSubmitted = true;
      evaluateQuiz();
    });
  }

  function evaluateQuiz() {
    let score = 0;
    const total = currentMcqData.questions.length;

    currentMcqData.questions.forEach((q) => {
      const qid = q.id;
      const userChoice = userAnswers[qid];
      const correctChoice = q.correct_answer;
      const grid = document.getElementById(`optGrid_${qid}`);
      const explBox = document.getElementById(`explBox_${qid}`);

      // Lock buttons
      grid.querySelectorAll(".mcq-option-btn").forEach((b) => {
        b.classList.add("locked");
        const opt = b.getAttribute("data-opt");
        if (opt === correctChoice) {
          b.classList.add("correct-answer");
        } else if (opt === userChoice && userChoice !== correctChoice) {
          b.classList.add("wrong-answer");
        }
      });

      if (userChoice === correctChoice) {
        score++;
      }

      // Show explanation
      explBox.classList.add("show");
    });

    const percentage = Math.round((score / total) * 100);
    finalScoreEl.textContent = `${score} / ${total}`;
    finalPercentageEl.textContent = `${percentage}%`;

    let msg = "";
    if (percentage >= 85) {
      msg = "🌟 Outstanding Performance! You have demonstrated exceptional mastery of this topic.";
    } else if (percentage >= 70) {
      msg = "🎉 Great job! You have solid comprehension. Review the explanations below for full perfection.";
    } else if (percentage >= 50) {
      msg = "📚 Good effort! A quick revision of the concepts below will elevate your exam scores.";
    } else {
      msg = "💡 Needs Focus. Study the detailed answers and try the quiz again to master the material.";
    }
    performanceMessageEl.textContent = msg;

    resultsCard.style.display = "block";
    submitQuizBtn.style.display = "none";
    resultsCard.scrollIntoView({ behavior: "smooth", block: "start" });
    showToast(`Quiz completed! You scored ${score}/${total} (${percentage}%)`, "success");
  }

  // Retry Quiz
  if (retryQuizBtn) {
    retryQuizBtn.addEventListener("click", () => {
      if (!currentMcqData) return;
      renderQuiz(currentMcqData);
    });
  }

  // Export Question Paper PDF (No answers)
  if (downloadPaperPdfBtn) {
    downloadPaperPdfBtn.addEventListener("click", () => {
      if (!currentMcqData) return;
      downloadPdfFromApi("mcq_paper", {
        title: currentMcqData.title,
        subject: currentMcqData.subject,
        topic: currentMcqData.topic,
        difficulty: currentMcqData.difficulty,
        questions: currentMcqData.questions
      });
    });
  }

  // Export Answer Key PDF (With answers & explanations)
  if (downloadKeyPdfBtn) {
    downloadKeyPdfBtn.addEventListener("click", () => {
      if (!currentMcqData) return;
      downloadPdfFromApi("mcq_key", {
        title: currentMcqData.title,
        subject: currentMcqData.subject,
        topic: currentMcqData.topic,
        difficulty: currentMcqData.difficulty,
        questions: currentMcqData.questions
      });
    });
  }

  function escapeHtml(str) {
    if (!str) return "";
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
});
