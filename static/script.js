// DOM Elements
const textModeBtn = document.getElementById('textModeBtn');
const imageModeBtn = document.getElementById('imageModeBtn');
const textInputContainer = document.getElementById('textInputContainer');
const imageInputContainer = document.getElementById('imageInputContainer');
const textInput = document.getElementById('textInput');
const imageInput = document.getElementById('imageInput');
const imageUploadArea = document.getElementById('imageUploadArea');
const imagePreview = document.getElementById('imagePreview');
const checkBtn = document.getElementById('checkBtn');
const inputSection = document.getElementById('inputSection');
const resultSection = document.getElementById('resultSection');
const resultCard = document.getElementById('resultCard');
const checkAnotherBtn = document.getElementById('checkAnotherBtn');

let currentMode = 'text';
let currentImageData = null;

// Mode switching
textModeBtn.addEventListener('click', () => {
    currentMode = 'text';
    textModeBtn.classList.add('active');
    imageModeBtn.classList.remove('active');
    textInputContainer.style.display = 'block';
    imageInputContainer.style.display = 'none';

});

imageModeBtn.addEventListener('click', () => {
    currentMode = 'image';
    imageModeBtn.classList.add('active');
    textModeBtn.classList.remove('active');
    textInputContainer.style.display = 'none';
    imageInputContainer.style.display = 'block';

});

// Image upload
imageInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            currentImageData = e.target.result;
            imagePreview.src = currentImageData;
            imagePreview.style.display = 'block';
            imageUploadArea.querySelector('svg').style.display = 'none';
            imageUploadArea.querySelector('span').style.display = 'none';
        };
        reader.readAsDataURL(file);
    }
});

// Check item button
checkBtn.addEventListener('click', async () => {
    const input = currentMode === 'text' ? textInput.value.trim() : currentImageData;

    if (!input) return;

    checkBtn.disabled = true;
    checkBtn.textContent = 'Analyzing...';

    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 2000));

    const result = analyzeBiosecurityItem(input, currentMode);
    displayResult(result);

    inputSection.style.display = 'none';
    resultSection.style.display = 'block';

    checkBtn.disabled = false;
    checkBtn.textContent = 'Check Item';
});

// Check another button
checkAnotherBtn.addEventListener('click', () => {
    inputSection.style.display = 'block';
    resultSection.style.display = 'none';
    textInput.value = '';
    currentImageData = null;
    imagePreview.style.display = 'none';
    imagePreview.src = '';
    imageUploadArea.querySelector('svg').style.display = 'block';
    imageUploadArea.querySelector('span').style.display = 'block';
});

// Biosecurity analysis logic HARD CODE
function analyzeBiosecurityItem(input, type) {
    const itemText = type === 'text' ? input.toLowerCase() : 'food item from image';

    const biconRules = {
        meat: {
            keywords: ['meat', 'beef', 'pork', 'chicken', 'lamb', 'duck', 'sausage', 'jerky', 'bacon'],
            decision: 'prohibited',
            categories: ['Meat and meat products', 'Animal products'],
            riskFactors: ['May contain foot-and-mouth disease', 'Risk of African swine fever', 'Not heat-treated to Australian standards'],
            reason: 'Fresh, dried, or processed meat products are prohibited unless commercially prepared and sealed with specific treatments approved by Australian authorities.',
        },
        dairy: {
            keywords: ['milk', 'cheese', 'yogurt', 'butter', 'cream', 'dairy'],
            decision: 'declare',
            categories: ['Dairy products', 'Animal products'],
            riskFactors: ['May contain animal pathogens', 'Unpasteurized products pose higher risk'],
            reason: 'Most dairy products must be declared. Commercially packaged and shelf-stable dairy may be allowed, but fresh dairy is often prohibited.',
        },
        fruit: {
            keywords: ['fruit', 'apple', 'orange', 'banana', 'mango', 'strawberry', 'grape'],
            decision: 'prohibited',
            categories: ['Fresh fruit and vegetables', 'Plant products'],
            riskFactors: ['May harbor fruit flies', 'Risk of plant diseases', 'Could introduce invasive species'],
            reason: 'Fresh fruits are prohibited due to biosecurity risks including pests and diseases that could harm Australian agriculture.',
        },
        vegetable: {
            keywords: ['vegetable', 'tomato', 'lettuce', 'carrot', 'potato', 'onion'],
            decision: 'prohibited',
            categories: ['Fresh fruit and vegetables', 'Plant products'],
            riskFactors: ['May carry soil-borne diseases', 'Risk of plant pests', 'Could introduce invasive species'],
            reason: 'Fresh vegetables are prohibited due to risks of introducing pests and diseases harmful to Australian ecosystems.',
        },
        seeds: {
            keywords: ['seed', 'grain', 'bean', 'lentil', 'chickpea', 'rice (uncooked)', 'quinoa'],
            decision: 'declare',
            categories: ['Seeds and grains', 'Plant products'],
            riskFactors: ['May introduce invasive plant species', 'Could carry plant diseases', 'Risk of contamination'],
            reason: 'Seeds and grains must be declared. Some commercially packaged varieties may be allowed, but many require inspection or are prohibited.',
        },
        processedFood: {
            keywords: ['chips', 'crackers', 'cookies', 'chocolate', 'candy', 'instant noodles', 'packaged snacks'],
            decision: 'allowed',
            categories: ['Commercially prepared foods', 'Processed products'],
            riskFactors: [],
            reason: 'Commercially manufactured and packaged snack foods are generally allowed as they pose minimal biosecurity risk.',
        },
        traditionalFood: {
            keywords: ['bánh tráng', 'rice paper', 'dried shrimp', 'fish sauce', 'dried fish', 'fried shallot', 'chili oil'],
            decision: 'declare',
            categories: ['Traditional Asian foods', 'Seafood products', 'Condiments'],
            riskFactors: ['May contain animal products', 'Complex ingredients require inspection', 'Dried seafood needs verification'],
            reason: 'Traditional foods with multiple ingredients should be declared. Items like rice paper are usually allowed, but those with seafood or animal products need inspection.',
        },
        honey: {
            keywords: ['honey', 'honeycomb', 'bee product', 'royal jelly'],
            decision: 'prohibited',
            categories: ['Bee products', 'Animal products'],
            riskFactors: ['May contain bee diseases', 'Risk of American foulbrood', 'Could harm Australian bee populations'],
            reason: 'Honey and bee products are prohibited unless they meet strict import conditions and are commercially prepared.',
        },
        nuts: {
            keywords: ['nut', 'peanut', 'almond', 'cashew', 'walnut', 'pistachio'],
            decision: 'declare',
            categories: ['Nuts and nut products', 'Plant products'],
            riskFactors: ['May carry plant diseases', 'Could contain soil or pests'],
            reason: 'Nuts must be declared. Commercially roasted and packaged nuts are often allowed, but raw nuts may be prohibited.',
        },
        egg: {
            keywords: ['egg', 'dried egg', 'egg powder'],
            decision: 'prohibited',
            categories: ['Egg products', 'Animal products'],
            riskFactors: ['Risk of avian influenza', 'May contain salmonella', 'Could spread poultry diseases'],
            reason: 'Fresh and dried eggs are prohibited unless commercially processed and meeting Australian standards.',
        },
    };

    // Find matching rule
    for (const [category, rules] of Object.entries(biconRules)) {
        for (const keyword of rules.keywords) {
            if (itemText.includes(keyword)) {
                const userReports = {
                    allowed: Math.floor(Math.random() * 50) + 10,
                    declared: Math.floor(Math.random() * 80) + 20,
                    confiscated: Math.floor(Math.random() * 30),
                };

                const total = userReports.allowed + userReports.declared + userReports.confiscated;
                const checkProbability = Math.round(((userReports.declared + userReports.confiscated) / total) * 100);

                return {
                    item: input.substring(0, 100),
                    decision: rules.decision,
                    categories: rules.categories,
                    riskFactors: rules.riskFactors,
                    reason: rules.reason,
                    userReports,
                    checkProbability,
                };
            }
        }
    }

    // Default case
    return {
        item: input.substring(0, 100),
        decision: 'declare',
        categories: ['General goods'],
        riskFactors: ['Unidentified item requires inspection'],
        reason: 'This item could not be automatically categorized. We recommend declaring it at customs for inspection to ensure compliance with biosecurity regulations.',
        userReports: {
            allowed: 15,
            declared: 42,
            confiscated: 8,
        },
        checkProbability: 77,
    };
}

// Display result
function displayResult(result) {
    const decisionConfig = {
        allowed: {
            icon: '<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>',
            title: 'Likely Allowed',
            boxClass: 'result-box-green',
        },
        prohibited: {
            icon: '<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#dc2626" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>',
            title: 'Prohibited',
            boxClass: 'result-box-red',
        },
        declare: {
            icon: '<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
            title: 'Must Declare',
            boxClass: 'result-box-amber',
        },
    };

    const config = decisionConfig[result.decision];

    let html = `
        <div class="result-header">
            <div class="result-icon">${config.icon}</div>
            <div style="flex: 1;">
                <div class="result-title">${config.title}</div>
                <div class="result-item">${result.item}</div>
            </div>
        </div>

        <div class="result-content">
            <div class="result-box ${config.boxClass}">
                <h3>Reason</h3>
                <p>${result.reason}</p>
            </div>
    `;

    if (result.categories.length > 0) {
        html += `
            <div class="result-section">
                <h3>BICON Categories Matched</h3>
                <div class="category-tags">
                    ${result.categories.map(cat => `<span class="category-tag">${cat}</span>`).join('')}
                </div>
            </div>
        `;
    }

    if (result.riskFactors.length > 0) {
        html += `
            <div class="result-section">
                <h3>Risk Factors Identified</h3>
                <ul class="risk-list">
                    ${result.riskFactors.map(factor => `<li>${factor}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    if (result.userReports) {
        html += `
            <div class="result-section">
                <div class="community-reports">
                    <div class="community-header">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"></circle>
                            <line x1="12" y1="16" x2="12" y2="12"></line>
                            <line x1="12" y1="8" x2="12.01" y2="8"></line>
                        </svg>
                        <h3>Community Reports (Similar Items)</h3>
                    </div>
                    <div class="report-grid">
                        <div class="report-item">
                            <div class="report-number green">${result.userReports.allowed}</div>
                            <div class="report-label">Allowed</div>
                        </div>
                        <div class="report-item">
                            <div class="report-number amber">${result.userReports.declared}</div>
                            <div class="report-label">Declared</div>
                        </div>
                        <div class="report-item">
                            <div class="report-number red">${result.userReports.confiscated}</div>
                            <div class="report-label">Confiscated</div>
                        </div>
                    </div>
                    ${result.checkProbability ? `
                        <div class="probability-section">
                            <span class="probability-label">Estimated check probability: </span>
                            <span><strong>${result.checkProbability}%</strong></span>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    html += '</div>';

    resultCard.innerHTML = html;
}



    
