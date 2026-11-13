/**
 * Tessalynt - Interactive 3D Flashcards Controller
 */
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("flashcardsForm");
  const loadingBox = document.getElementById("flashcardsLoading");
  const flashcardArena = document.getElementById("flashcardArena");
  const generateBtn = document.getElementById("generateFlashcardsBtn");

  // Flashcard elements
  const cardElement = document.getElementById("flashcardElement");
  const cardFrontTag = document.getElementById("cardFrontTag");
  const cardFrontText = document.getElementById("cardFrontText");
  const cardBackTag = document.getElementById("cardBackTag");
  const cardBackText = document.getElementById("cardBackText");
  const currentCardNumEl = document.getElementById("currentCardNum");
  const totalCardsNumEl = document.getElementById("totalCardsNum");
  const cardProgressBar = document.getElementById("cardProgressBar");

  // Action & Navigation buttons
  const prevCardBtn = document.getElementById("prevCardBtn");
  const nextCardBtn = document.getElementById("nextCardBtn");
  const flipCardBtn = document.getElementById("flipCardBtn");
  const shuffleBtn = document.getElementById("shuffleCardsBtn");
  const restartBtn = document.getElementById("restartSessionBtn");
  const markKnownBtn = document.getElementById("markKnownBtn");
  const markRevisionBtn = document.getElementById("markRevisionBtn");
  const exportCardsPdfBtn = document.getElementById("exportCardsPdfBtn");

  // Counters
  const knownCountEl = document.getElementById("knownCount");
  const revisionCountEl = document.getElementById("revisionCount");

  let deck = [];
  let currentIndex = 0;
  let cardStatuses = {}; // { cardId: 'known' | 'revision' }
  let currentMetadata = null;

  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      await triggerFlashcardsGeneration();
    });
  }

  async function triggerFlashcardsGeneration() {
    const payload = {
      subject: document.getElementById("fcSubject").value.trim(),
      topic: document.getElementById("fcTopic").value.trim(),
      count: parseInt(document.getElementById("fcCount").value, 10),
      difficulty: document.getElementById("fcDifficulty").value
    };

    if (!payload.subject || !payload.topic) {
      showToast("Subject and Topic are required.", "error");
      return;
    }

    loadingBox.classList.add("active");
    flashcardArena.style.display = "none";
    generateBtn.disabled = true;

    try {
      const res = await fetch("/api/generate-flashcards", {
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
          showToast(data.message || "Failed to generate flashcards", "error");
        }
        return;
      }

      currentMetadata = data;
      deck = data.flashcards;
      currentIndex = 0;
      cardStatuses = {};
      initFlashcardDeck();
      showToast(`Flashcard deck ready! ${deck.length} cards loaded.`, "success");

    } catch (err) {
      showToast(`Network error: ${err.message}`, "error");
    } finally {
      loadingBox.classList.remove("active");
      generateBtn.disabled = false;
    }
  }

  function initFlashcardDeck() {
    if (!deck || deck.length === 0) return;
    totalCardsNumEl.textContent = deck.length;
    updateCounters();
    displayCard(currentIndex);
    flashcardArena.style.display = "block";
    flashcardArena.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function displayCard(index) {
    const card = deck[index];
    if (!card) return;

    // Reset flip
    cardElement.classList.remove("is-flipped");

    const tag = card.tag || "Concept";
    cardFrontTag.textContent = tag.toUpperCase();
    cardFrontText.textContent = card.front;
    cardBackTag.textContent = tag.toUpperCase();
    cardBackText.textContent = card.back;

    currentCardNumEl.textContent = index + 1;
    const progress = ((index + 1) / deck.length) * 100;
    cardProgressBar.style.width = `${progress}%`;

    // Button states
    prevCardBtn.disabled = index === 0;
    nextCardBtn.disabled = index === deck.length - 1;
  }

  // Flip Card Action
  function toggleFlip() {
    cardElement.classList.toggle("is-flipped");
  }

  cardElement.addEventListener("click", toggleFlip);
  if (flipCardBtn) flipCardBtn.addEventListener("click", toggleFlip);

  // Keyboard navigation
  document.addEventListener("keydown", (e) => {
    if (flashcardArena.style.display !== "block") return;
    if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;

    if (e.code === "Space") {
      e.preventDefault();
      toggleFlip();
    } else if (e.code === "ArrowRight") {
      if (currentIndex < deck.length - 1) {
        currentIndex++;
        displayCard(currentIndex);
      }
    } else if (e.code === "ArrowLeft") {
      if (currentIndex > 0) {
        currentIndex--;
        displayCard(currentIndex);
      }
    }
  });

  if (prevCardBtn) {
    prevCardBtn.addEventListener("click", () => {
      if (currentIndex > 0) {
        currentIndex--;
        displayCard(currentIndex);
      }
    });
  }

  if (nextCardBtn) {
    nextCardBtn.addEventListener("click", () => {
      if (currentIndex < deck.length - 1) {
        currentIndex++;
        displayCard(currentIndex);
      }
    });
  }

  // Shuffle Deck
  if (shuffleBtn) {
    shuffleBtn.addEventListener("click", () => {
      for (let i = deck.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [deck[i], deck[j]] = [deck[j], deck[i]];
      }
      currentIndex = 0;
      displayCard(currentIndex);
      showToast("Deck shuffled!", "info");
    });
  }

  // Mark as Known
  if (markKnownBtn) {
    markKnownBtn.addEventListener("click", () => {
      const card = deck[currentIndex];
      if (!card) return;
      cardStatuses[card.id] = "known";
      updateCounters();
      showToast("Marked as Known ✓", "success");
      if (currentIndex < deck.length - 1) {
        currentIndex++;
        displayCard(currentIndex);
      }
    });
  }

  // Mark as Need Revision
  if (markRevisionBtn) {
    markRevisionBtn.addEventListener("click", () => {
      const card = deck[currentIndex];
      if (!card) return;
      cardStatuses[card.id] = "revision";
      updateCounters();
      showToast("Marked for Revision ⚡", "warning");
      if (currentIndex < deck.length - 1) {
        currentIndex++;
        displayCard(currentIndex);
      }
    });
  }

  function updateCounters() {
    let known = 0;
    let revision = 0;
    Object.values(cardStatuses).forEach((status) => {
      if (status === "known") known++;
      if (status === "revision") revision++;
    });
    knownCountEl.textContent = known;
    revisionCountEl.textContent = revision;
  }

  // Restart Session
  if (restartBtn) {
    restartBtn.addEventListener("click", () => {
      currentIndex = 0;
      cardStatuses = {};
      updateCounters();
      displayCard(0);
      showToast("Session restarted.", "info");
    });
  }

  // Export Flashcards as PDF
  if (exportCardsPdfBtn) {
    exportCardsPdfBtn.addEventListener("click", () => {
      if (!currentMetadata || !deck) return;
      downloadPdfFromApi("flashcards", {
        title: currentMetadata.title,
        subject: currentMetadata.subject,
        topic: currentMetadata.topic,
        flashcards: deck
      });
    });
  }
});
