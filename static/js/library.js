/**
 * Tessalynt - Study Materials Library Controller
 */
document.addEventListener("DOMContentLoaded", () => {
  const grid = document.getElementById("libraryGrid");
  const searchInput = document.getElementById("librarySearch");
  const filterPills = document.querySelectorAll(".filter-pill-btn");
  const emptyState = document.getElementById("libraryEmptyState");

  // Preview Modal Elements
  const viewerModal = document.getElementById("materialViewerModal");
  const closeViewerBtn = document.getElementById("closeViewerModal");
  const viewerTitle = document.getElementById("viewerTitle");
  const viewerMeta = document.getElementById("viewerMeta");
  const viewerBody = document.getElementById("viewerBody");
  const viewerPdfBtn = document.getElementById("viewerPdfBtn");
  const viewerTxtBtn = document.getElementById("viewerTxtBtn");
  const viewerDeleteBtn = document.getElementById("viewerDeleteBtn");

  let activeType = "all";
  let activeSearch = "";
  let loadedMaterials = [];
  let currentViewingItem = null;

  // Initialize load
  fetchMaterials();

  // Search input debounced
  if (searchInput) {
    let timeout = null;
    searchInput.addEventListener("input", () => {
      clearTimeout(timeout);
      timeout = setTimeout(() => {
        activeSearch = searchInput.value.trim();
        fetchMaterials();
      }, 300);
    });
  }

  // Filter Pills
  filterPills.forEach((btn) => {
    btn.addEventListener("click", () => {
      filterPills.forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      activeType = btn.getAttribute("data-type");
      fetchMaterials();
    });
  });

  async function fetchMaterials() {
    try {
      const url = `/api/materials?type=${encodeURIComponent(activeType)}&search=${encodeURIComponent(activeSearch)}`;
      const res = await fetch(url);
      const data = await res.json();
      loadedMaterials = data.materials || [];
      renderMaterialsGrid(loadedMaterials);
    } catch (err) {
      showToast("Error loading library items", "error");
    }
  }

  function renderMaterialsGrid(items) {
    grid.innerHTML = "";
    if (!items || items.length === 0) {
      emptyState.style.display = "block";
      return;
    }
    emptyState.style.display = "none";

    items.forEach((item) => {
      const card = document.createElement("div");
      card.className = "material-card";

      const typeBadgeClass = getTypeBadgeClass(item.material_type);
      const typeLabel = item.material_type.toUpperCase();

      card.innerHTML = `
        <div>
          <div class="material-card-header">
            <span class="badge ${typeBadgeClass}">${typeLabel}</span>
            <span style="font-size:0.75rem;color:var(--text-dim);">${item.created_at.split(' ')[0]}</span>
          </div>
          <h4 class="material-card-title">${escapeHtml(item.title)}</h4>
          <div class="material-card-meta">
            ${escapeHtml(item.subject)} &bull; ${escapeHtml(item.topic)}
            ${item.stream ? `&bull; ${escapeHtml(item.stream)}` : ''}
          </div>
        </div>
        <div class="material-card-actions">
          <button class="btn btn-secondary btn-sm open-view-btn" data-id="${item.id}">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
            Open
          </button>
          <div style="display:flex;gap:0.35rem;">
            <button class="btn btn-ghost btn-sm quick-pdf-btn" data-id="${item.id}" title="Download PDF">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
            </button>
            <button class="btn btn-ghost btn-sm quick-del-btn" data-id="${item.id}" style="color:var(--danger);" title="Delete">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
            </button>
          </div>
        </div>
      `;
      grid.appendChild(card);
    });

    // Attach listeners
    grid.querySelectorAll(".open-view-btn").forEach((btn) => {
      btn.addEventListener("click", () => openViewer(parseInt(btn.getAttribute("data-id"), 10)));
    });

    grid.querySelectorAll(".quick-pdf-btn").forEach((btn) => {
      btn.addEventListener("click", () => handleQuickPdf(parseInt(btn.getAttribute("data-id"), 10)));
    });

    grid.querySelectorAll(".quick-del-btn").forEach((btn) => {
      btn.addEventListener("click", () => handleDelete(parseInt(btn.getAttribute("data-id"), 10)));
    });
  }

  function getTypeBadgeClass(type) {
    switch (type) {
      case "notes": return "badge-primary";
      case "revision": return "badge-warning";
      case "mcq": return "badge-secondary";
      case "flashcards": return "badge-success";
      default: return "badge-primary";
    }
  }

  // Open Viewer Modal
  async function openViewer(id) {
    const item = loadedMaterials.find((m) => m.id === id);
    if (!item) return;

    currentViewingItem = item;
    viewerTitle.textContent = item.title;
    viewerMeta.textContent = `${item.material_type.toUpperCase()} • ${item.subject} • ${item.topic} • ${item.created_at}`;

    if (item.material_type === "notes" || item.material_type === "revision") {
      viewerBody.innerHTML = `<div class="rendered-content">${renderSimpleMarkdown(item.content_text)}</div>`;
      viewerTxtBtn.style.display = "inline-flex";
    } else if (item.material_type === "mcq") {
      viewerTxtBtn.style.display = "none";
      const questions = item.content_json || [];
      let qHtml = `<div style="display:flex;flex-direction:column;gap:1rem;">`;
      questions.forEach((q, idx) => {
        qHtml += `
          <div class="mcq-question-card" style="margin-bottom:0;">
            <div class="mcq-prompt"><b>Q${idx + 1}.</b> ${escapeHtml(q.question)}</div>
            <div style="font-size:0.875rem;margin:0.5rem 0;color:#CBD5E1;">
              <div>A) ${escapeHtml(q.options?.A || '')}</div>
              <div>B) ${escapeHtml(q.options?.B || '')}</div>
              <div>C) ${escapeHtml(q.options?.C || '')}</div>
              <div>D) ${escapeHtml(q.options?.D || '')}</div>
            </div>
            <div style="font-size:0.85rem;color:var(--success);font-weight:600;">Correct: Option (${q.correct_answer})</div>
            <div style="font-size:0.8rem;color:var(--text-muted);margin-top:4px;"><b>Explanation:</b> ${escapeHtml(q.explanation)}</div>
          </div>
        `;
      });
      qHtml += `</div>`;
      viewerBody.innerHTML = qHtml;
    } else if (item.material_type === "flashcards") {
      viewerTxtBtn.style.display = "none";
      const cards = item.content_json || [];
      let cHtml = `<div style="display:grid;grid-template-columns:1fr;gap:0.75rem;">`;
      cards.forEach((c, idx) => {
        cHtml += `
          <div style="background:rgba(255,255,255,0.03);border:1px solid var(--border-subtle);border-radius:var(--radius-md);padding:1rem;">
            <div style="font-size:0.75rem;color:var(--primary);font-weight:700;">CARD ${idx + 1} &bull; ${(c.tag || 'CONCEPT').toUpperCase()}</div>
            <div style="font-weight:600;margin:0.25rem 0 0.5rem;color:#FFFFFF;">Q: ${escapeHtml(c.front)}</div>
            <div style="font-size:0.9rem;color:#CBD5E1;border-top:1px dashed var(--border-subtle);padding-top:0.4rem;">${escapeHtml(c.back)}</div>
          </div>
        `;
      });
      cHtml += `</div>`;
      viewerBody.innerHTML = cHtml;
    }

    viewerModal.classList.add("active");
  }

  if (closeViewerBtn) {
    closeViewerBtn.addEventListener("click", () => {
      viewerModal.classList.remove("active");
    });
  }

  viewerModal.addEventListener("click", (e) => {
    if (e.target === viewerModal) viewerModal.classList.remove("active");
  });

  // Modal PDF Download
  if (viewerPdfBtn) {
    viewerPdfBtn.addEventListener("click", () => {
      if (!currentViewingItem) return;
      handleExportItem(currentViewingItem);
    });
  }

  // Modal TXT Download
  if (viewerTxtBtn) {
    viewerTxtBtn.addEventListener("click", () => {
      if (!currentViewingItem) return;
      downloadTxtFromApi(
        currentViewingItem.title,
        currentViewingItem.subject,
        currentViewingItem.topic,
        currentViewingItem.content_text
      );
    });
  }

  // Modal Delete
  if (viewerDeleteBtn) {
    viewerDeleteBtn.addEventListener("click", async () => {
      if (!currentViewingItem) return;
      await handleDelete(currentViewingItem.id);
      viewerModal.classList.remove("active");
    });
  }

  function handleQuickPdf(id) {
    const item = loadedMaterials.find((m) => m.id === id);
    if (item) handleExportItem(item);
  }

  function handleExportItem(item) {
    if (item.material_type === "notes") {
      downloadPdfFromApi("notes", {
        title: item.title,
        subject: item.subject,
        topic: item.topic,
        stream: item.stream,
        content: item.content_text
      });
    } else if (item.material_type === "revision") {
      downloadPdfFromApi("revision", {
        title: item.title,
        subject: item.subject,
        topic: item.topic,
        content: item.content_text
      });
    } else if (item.material_type === "mcq") {
      downloadPdfFromApi("mcq_key", {
        title: item.title,
        subject: item.subject,
        topic: item.topic,
        difficulty: item.difficulty || "Standard",
        questions: item.content_json
      });
    } else if (item.material_type === "flashcards") {
      downloadPdfFromApi("flashcards", {
        title: item.title,
        subject: item.subject,
        topic: item.topic,
        flashcards: item.content_json
      });
    }
  }

  async function handleDelete(id) {
    const confirmed = confirm("Are you sure you want to delete this study material?");
    if (!confirmed) return;

    try {
      const res = await fetch(`/api/materials/${id}`, { method: "DELETE" });
      if (res.ok) {
        showToast("Material deleted", "info");
        fetchMaterials();
      } else {
        showToast("Failed to delete item", "error");
      }
    } catch (err) {
      showToast("Network error deleting item", "error");
    }
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
