
// DOM refs 
const textModeBtn = document.getElementById('textModeBtn');
const imageModeBtn = document.getElementById('imageModeBtn');
const textInputContainer = document.getElementById('textInputContainer');
const imageInputContainer = document.getElementById('imageInputContainer');
const textInput = document.getElementById('textInput');
const imageInput = document.getElementById('imageInput');
const imagePreview = document.getElementById('imagePreview');
const imageUploadArea = document.getElementById('imageUploadArea');
const checkBtn = document.getElementById('checkBtn');
const checkAnotherBtn = document.getElementById('checkAnotherBtn');
const inputSection = document.getElementById('inputSection');
const resultSection = document.getElementById('resultSection');
const resultCard = document.getElementById('resultCard');

let currentMode = 'text';
let selectedFile = null;

function setMode(mode) {
  [textModeBtn, imageModeBtn].forEach(b => b.classList.remove('active'));
  [textInputContainer, imageInputContainer].forEach(el => {
    el.style.display = 'none';
  });

  currentMode = mode;

  if (mode === 'text') {
    textModeBtn.classList.add('active');
    textInputContainer.style.display = 'block';
  } else if (mode === 'image') {
    imageModeBtn.classList.add('active');
    imageInputContainer.style.display = 'block';
  }
}

textModeBtn.addEventListener('click', () => setMode('text'));
imageModeBtn.addEventListener('click', () => setMode('image'));

imageInput.addEventListener('change', e => {
  const file = e.target.files[0];
  if (!file) return;
  selectedFile = file;
  const reader = new FileReader();
  reader.onload = ev => {
    imagePreview.src = ev.target.result;
    imagePreview.style.display = 'block';
  };
  reader.readAsDataURL(file);
});

// Drag-and-drop
imageUploadArea.addEventListener('dragover', e => {
  e.preventDefault();
  imageUploadArea.style.borderColor = 'var(--green-mid)';
  imageUploadArea.style.background = 'var(--green-light)';
});
imageUploadArea.addEventListener('dragleave', () => {
  imageUploadArea.style.borderColor = '';
  imageUploadArea.style.background = '';
});
imageUploadArea.addEventListener('drop', e => {
  e.preventDefault();
  imageUploadArea.style.borderColor = '';
  imageUploadArea.style.background = '';
  const file = e.dataTransfer.files[0];
  if (file && file.type.startsWith('image/')) {
    selectedFile = file;
    const reader = new FileReader();
    reader.onload = ev => {
      imagePreview.src = ev.target.result;
      imagePreview.style.display = 'block';
    };
    reader.readAsDataURL(file);
  }
});

checkBtn.addEventListener('click', runCheck);

async function runCheck() {
  if (currentMode === 'text') {
    const text = textInput.value.trim();
    if (!text) { shake(textInput); return; }
    await submitText(text);

  } else if (currentMode === 'image') {
    if (!selectedFile) { shake(imageUploadArea); return; }
    await submitImage(selectedFile);
  }
}

async function submitText(text) {
  showLoading();
  try {
    const res = await fetch('/check-text', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    showResult(data);
  } catch (err) {
    showError(err.message);
  }
}

async function submitImage(file) {
  showLoading();
  try {
    const formData = new FormData();
    formData.append('image', file);
    const res = await fetch('/analyze', { method: 'POST', body: formData });
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    showResult(data);
  } catch (err) {
    showError(err.message);
  }
}

function showLoading() {
  inputSection.style.display = 'none';
  resultSection.style.display = 'block';
  resultCard.innerHTML = `
    <div class="loading-state">
      <div class="loading-spinner"></div>
      <p class="loading-text">Checking against biosecurity rules…</p>
      <small>This may take a few seconds</small>
    </div>`;
}

function showResult(data) {
  inputSection.style.display = 'none';
  resultSection.style.display = 'block';
  resultCard.innerHTML = buildResultHTML(data);
  resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function showError(message) {
  inputSection.style.display = 'none';
  resultSection.style.display = 'block';
  resultCard.innerHTML = `
    <div class="result-error">
      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <line x1="12" y1="8" x2="12" y2="12"/>
        <line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
      <h4>Something went wrong</h4>
      <p>${escHtml(message)}</p>
    </div>`;
}

checkAnotherBtn.addEventListener('click', () => {
  resultSection.style.display = 'none';
  inputSection.style.display = 'block';
  // Reset state
  textInput.value = '';
  selectedFile = null;
  imagePreview.src = '';
  imagePreview.style.display = 'none';
  imageInput.value = '';
  setMode('text');
  inputSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
});

const VERDICT_CONFIG = {
  BRING_IT: {
    label: 'Safe to Bring',
    sublabel: 'This item appears to meet Australian biosecurity requirements.',
    icon: `<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>`,
    headerClass: 'verdict-header--bring',
    badgeClass: 'verdict-badge--bring',
  },
  DECLARE_IT: {
    label: 'Declare at Border',
    sublabel: 'You can bring this, but you MUST declare it at the biosecurity counter on arrival.',
    icon: `<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
    headerClass: 'verdict-header--declare',
    badgeClass: 'verdict-badge--declare',
  },
  DONT_BRING: {
    label: 'Do Not Bring',
    sublabel: 'This item is prohibited and will be confiscated or destroyed at the border.',
    icon: `<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`,
    headerClass: 'verdict-header--dont',
    badgeClass: 'verdict-badge--dont',
  },
};

function buildResultHTML(data) {
  const verdict = data.overall_verdict || 'DECLARE_IT';
  const cfg = VERDICT_CONFIG[verdict] || VERDICT_CONFIG.DECLARE_IT;

  // Product name / barcode header
  const productLine = data.product_name
    ? `<span class="result-product-name">${escHtml(data.product_name)}</span>`
    : '';
  const barcodeLine = data.barcode
    ? `<span class="result-barcode">Barcode: ${escHtml(data.barcode)}</span>`
    : '';

  // Ingredients chips
  const ingredientChips = (data.ingredients_raw || []).length > 0
    ? `<div class="ingredients-section">
         <h5>Detected Ingredients</h5>
         <div class="ingredient-chips">
           ${(data.ingredients_raw || []).map(i => `<span class="chip">${escHtml(i)}</span>`).join('')}
         </div>
       </div>`
    : '';

  // Category tags
  const activeCats = Object.entries(data.categories || {})
    .filter(([, v]) => v)
    .map(([k]) => k);

  const categoryTags = activeCats.length > 0
    ? `<div class="categories-section">
         <h5>Item Categories</h5>
         <div class="category-tags">
           ${activeCats.map(c => `<span class="cat-tag">${escHtml(c)}</span>`).join('')}
         </div>
       </div>`
    : '';

  // Key concerns
  const concerns = (data.key_concerns || []);
  const concernsHTML = concerns.length > 0
    ? `<div class="concerns-section">
         <h5>Key Points</h5>
         <ul class="concerns-list">
           ${concerns.map(c => `<li>${escHtml(c)}</li>`).join('')}
         </ul>
       </div>`
    : '';

  // Rules applied
  const rules = (data.rules_applied || []);
  const rulesHTML = rules.length > 0
    ? `<div class="rules-section">
         <h5>Relevant Rules</h5>
         ${rules.map(r => `
           <div class="rule-item rule-item--${(r.verdict || '').toLowerCase()}">
             <div class="rule-item-header">
               <span class="rule-verdict-dot rule-dot--${(r.verdict || '').toLowerCase()}"></span>
               <span class="rule-item-name">${formatRuleName(r.item)}</span>
               <span class="rule-verdict-label rule-verdict--${(r.verdict || '').toLowerCase()}">${formatVerdict(r.verdict)}</span>
             </div>
             <p class="rule-reason">${escHtml(r.reason || '')}</p>
           </div>`).join('')}
       </div>`
    : '';

  // Source badge
  const sourceBadge = data.source
    ? `<div class="source-badge">Source: ${formatSource(data.source)}</div>`
    : '';

  return `
    <div class="result-verdict-card">
      <div class="verdict-header ${cfg.headerClass}">
        <div class="verdict-icon-wrap">${cfg.icon}</div>
        <div>
          <div class="verdict-label-text">${cfg.label}</div>
          <div class="verdict-sub">${cfg.sublabel}</div>
        </div>
      </div>

      <div class="result-body">
        ${productLine || barcodeLine
      ? `<div class="result-meta">${productLine}${barcodeLine}</div>`
      : ''}

        ${data.verdict_reason
      ? `<p class="verdict-reason-text">${escHtml(data.verdict_reason)}</p>`
      : ''}

        ${concernsHTML}
        ${categoryTags}
        ${ingredientChips}
        ${rulesHTML}
        ${sourceBadge}
      </div>
    </div>`;
}

function formatRuleName(item) {
  return (item || '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function formatVerdict(v) {
  return { BRING_IT: 'Bring It', DECLARE_IT: 'Declare', DONT_BRING: "Don't Bring" }[v] || v;
}

function formatSource(s) {
  return {
    open_food_facts: 'Open Food Facts',
    gemini: 'Gemini AI (image)',
    gemini_fallback_after_barcode: 'Gemini AI (barcode fallback)',
    text_input: 'Text description',
    barcode_unknown: 'Barcode (product not found in database)',
  }[s] || s;
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function shake(el) {
  el.style.animation = 'none';
  requestAnimationFrame(() => {
    el.style.animation = 'shake 0.4s ease';
  });
}

function showToast(msg) {
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.textContent = msg;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

setMode('text');
resultSection.style.display = 'none';