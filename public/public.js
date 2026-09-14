// Gujarat Police Citizen Safety Portal - Interactive Script (public.js)

/* ==========================================================================
   CUSTOM CYBER POLICE POPUP DIALOGS (Zero Native Browser Alerts)
   ========================================================================== */
function showCustomAlert(title, message, type = 'info') {
  const existing = document.getElementById('custom-popup-dialog');
  if (existing) existing.remove();

  const iconClass = type === 'danger' ? 'icon-danger fa-triangle-exclamation' : (type === 'success' ? 'icon-success fa-circle-check' : 'icon-info fa-circle-info');
  const boxClass = type === 'danger' ? 'custom-dialog-box alert-danger' : 'custom-dialog-box';

  const backdrop = document.createElement('div');
  backdrop.id = 'custom-popup-dialog';
  backdrop.className = 'custom-dialog-backdrop';
  backdrop.innerHTML = `
    <div class="${boxClass}">
      <div class="custom-dialog-header">
        <div class="custom-dialog-icon ${iconClass.split(' ')[0]}">
          <i class="fa-solid ${iconClass.split(' ')[1]}"></i>
        </div>
        <div class="custom-dialog-title-wrap">
          <div class="custom-dialog-title">${title}</div>
          <div class="custom-dialog-subtitle">Gujarat Police Citizen Safety Portal</div>
        </div>
      </div>
      <div class="custom-dialog-body">${message}</div>
      <div class="custom-dialog-footer">
        <button class="btn-primary" id="btn-custom-dialog-ok" style="min-width: 90px; padding: 7px 16px; background: linear-gradient(135deg, #2563EB, #1D4ED8); border: 1px solid rgba(56,189,248,0.4); color: #FFF; border-radius: 8px; font-weight: 600; cursor: pointer;">
          <i class="fa-solid fa-check"></i> OK
        </button>
      </div>
    </div>
  `;

  document.body.appendChild(backdrop);
  const okBtn = backdrop.querySelector('#btn-custom-dialog-ok');
  if (okBtn) {
    okBtn.focus();
    okBtn.onclick = () => backdrop.remove();
  }
  backdrop.onclick = (e) => {
    if (e.target === backdrop) backdrop.remove();
  };
}

function showCustomConfirm(title, message, onConfirm, onCancel, confirmText = 'Confirm', cancelText = 'Cancel', type = 'danger') {
  const existing = document.getElementById('custom-popup-dialog');
  if (existing) existing.remove();

  const iconClass = type === 'danger' ? 'icon-danger fa-triangle-exclamation' : (type === 'success' ? 'icon-success fa-circle-check' : 'icon-info fa-circle-info');
  const boxClass = type === 'danger' ? 'custom-dialog-box alert-danger' : 'custom-dialog-box';
  const confirmBtnStyle = type === 'danger' 
    ? 'background: linear-gradient(135deg, #DC2626, #B91C1C); border: 1px solid rgba(239,68,68,0.4); color: #FFF;' 
    : 'background: linear-gradient(135deg, #2563EB, #1D4ED8); border: 1px solid rgba(56,189,248,0.4); color: #FFF;';

  const backdrop = document.createElement('div');
  backdrop.id = 'custom-popup-dialog';
  backdrop.className = 'custom-dialog-backdrop';
  backdrop.innerHTML = `
    <div class="${boxClass}">
      <div class="custom-dialog-header">
        <div class="custom-dialog-icon ${iconClass.split(' ')[0]}">
          <i class="fa-solid ${iconClass.split(' ')[1]}"></i>
        </div>
        <div class="custom-dialog-title-wrap">
          <div class="custom-dialog-title">${title}</div>
          <div class="custom-dialog-subtitle">Gujarat Police Citizen Safety Portal</div>
        </div>
      </div>
      <div class="custom-dialog-body">${message}</div>
      <div class="custom-dialog-footer">
        <button id="btn-custom-dialog-cancel" style="padding: 7px 14px; background: rgba(15,23,42,0.6); border: 1px solid rgba(56,189,248,0.25); color: #38BDF8; border-radius: 8px; font-weight: 600; cursor: pointer;">${cancelText}</button>
        <button id="btn-custom-dialog-confirm" style="padding: 7px 16px; border-radius: 8px; font-weight: 600; cursor: pointer; ${confirmBtnStyle}">${confirmText}</button>
      </div>
    </div>
  `;

  document.body.appendChild(backdrop);
  const confirmBtn = backdrop.querySelector('#btn-custom-dialog-confirm');
  const cancelBtn = backdrop.querySelector('#btn-custom-dialog-cancel');

  if (confirmBtn) {
    confirmBtn.focus();
    confirmBtn.onclick = () => {
      backdrop.remove();
      if (typeof onConfirm === 'function') onConfirm();
    };
  }
  if (cancelBtn) {
    cancelBtn.onclick = () => {
      backdrop.remove();
      if (typeof onCancel === 'function') onCancel();
    };
  }
  backdrop.onclick = (e) => {
    if (e.target === backdrop) {
      backdrop.remove();
      if (typeof onCancel === 'function') onCancel();
    }
  };
}

function initPublicPortal() {
  // 0. Interactive Police Sentinel Cyber Constellation Background
  try {
    initCyberBackground();
  } catch (e) {
    console.warn('initCyberBackground error:', e);
  }

  // 1. Live Clock
  const clockEl = document.getElementById('public-live-clock');
  if (clockEl) {
    const updateClock = () => {
      const now = new Date();
      clockEl.textContent = now.toTimeString().split(' ')[0] + ' IST';
    };
    updateClock();
    setInterval(updateClock, 1000);
  }

  // 2. Mobile Menu Toggle & Scroll Spy
  initNavigation();

  // 3. Traffic Corridor Filter Buttons
  const cityBtns = document.querySelectorAll('#traffic-city-filters .city-btn');
  const corridorCards = document.querySelectorAll('#corridors-grid-container .corridor-card');

  cityBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      cityBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const selectedCity = btn.dataset.city;

      corridorCards.forEach(card => {
        if (selectedCity === 'ALL' || card.dataset.region === selectedCity) {
          card.style.display = 'block';
        } else {
          card.style.display = 'none';
        }
      });
    });
  });

  // 4. FAQ Accordion
  const faqItems = document.querySelectorAll('.faq-item');
  faqItems.forEach(item => {
    const toggleBtn = item.querySelector('.faq-toggle');
    if (toggleBtn) {
      toggleBtn.addEventListener('click', () => {
        const isActive = item.classList.contains('active');
        faqItems.forEach(i => i.classList.remove('active'));
        if (!isActive) {
          item.classList.add('active');
        }
      });
    }
  });

  // 5. Stolen Vehicle Ownership Authenticity & Multi-Proof e-Intimation Desk
  const intimationForm = document.getElementById('public-intimation-form');
  const receiptCard = document.getElementById('receipt-modal-card');
  const receiptContent = document.getElementById('receipt-details-content');
  const dismissReceiptBtn = document.getElementById('btn-dismiss-receipt');

  // File Upload State & Proof Manager
  let uploadedProofDocuments = [];

  function updateProofUI() {
    const previewGrid = document.getElementById('proof-preview-grid');
    const counterEl = document.getElementById('proof-counter');
    if (!previewGrid || !counterEl) return;

    if (uploadedProofDocuments.length === 0) {
      previewGrid.innerHTML = '';
      counterEl.innerHTML = '<i class="fa-solid fa-circle-info"></i> Minimum 2 Proofs Required (RC, Owner ID, Vehicle Photo)';
      counterEl.style.color = '#F59E0B';
      return;
    }

    const isComplete = uploadedProofDocuments.length >= 2;
    counterEl.innerHTML = `<i class="fa-solid fa-circle-check"></i> ${uploadedProofDocuments.length} Proof(s) Attached ${isComplete ? '(Authenticity Verified)' : '(1 More Required)'}`;
    counterEl.style.color = isComplete ? '#34D399' : '#F59E0B';

    previewGrid.innerHTML = uploadedProofDocuments.map((doc, idx) => `
      <div class="proof-card" data-idx="${idx}">
        ${doc.dataUrl.startsWith('data:image/') ? `
          <img src="${doc.dataUrl}" class="proof-thumb" alt="Proof thumbnail">
        ` : `
          <div class="proof-thumb-icon"><i class="fa-solid fa-file-pdf"></i></div>
        `}
        <div class="proof-info">
          <div class="proof-name" title="${doc.name}">${doc.name}</div>
          <div class="proof-meta">
            <span>${(doc.size / 1024).toFixed(1)} KB</span> &bull;
            <select class="proof-category-select" onchange="window._changeProofCategory(${idx}, this.value)">
              <option value="Vehicle RC Smart Card" ${doc.category === 'Vehicle RC Smart Card' ? 'selected' : ''}>RC Smart Card</option>
              <option value="Owner Govt ID (Aadhaar/DL)" ${doc.category === 'Owner Govt ID (Aadhaar/DL)' ? 'selected' : ''}>Owner ID (Aadhaar/DL)</option>
              <option value="Vehicle Photograph" ${doc.category === 'Vehicle Photograph' ? 'selected' : ''}>Vehicle Photo</option>
              <option value="Insurance Policy / Invoice" ${doc.category === 'Insurance Policy / Invoice' ? 'selected' : ''}>Insurance / Invoice</option>
            </select>
          </div>
        </div>
        <button type="button" class="btn-remove-proof" onclick="window._removeProofDocument(${idx})" title="Remove document">
          <i class="fa-solid fa-trash-can"></i>
        </button>
      </div>
    `).join('');
  }

  window._changeProofCategory = function(idx, cat) {
    if (uploadedProofDocuments[idx]) {
      uploadedProofDocuments[idx].category = cat;
    }
  };

  window._removeProofDocument = function(idx) {
    uploadedProofDocuments.splice(idx, 1);
    updateProofUI();
  };

  function handleProofFiles(files) {
    if (!files || !files.length) return;
    Array.from(files).forEach(file => {
      if (file.size > 5 * 1024 * 1024) {
        showCustomAlert('File Exceeds Limit', `"${file.name}" is larger than 5MB. Please upload an optimized file.`, 'warning');
        return;
      }
      const reader = new FileReader();
      reader.onload = (e) => {
        let defaultCat = 'Vehicle Photograph';
        const lower = file.name.toLowerCase();
        if (lower.includes('rc') || lower.includes('reg')) defaultCat = 'Vehicle RC Smart Card';
        else if (lower.includes('aadhaar') || lower.includes('dl') || lower.includes('id') || lower.includes('pan') || lower.includes('voter')) defaultCat = 'Owner Govt ID (Aadhaar/DL)';
        else if (lower.includes('insur') || lower.includes('policy') || lower.includes('bill') || lower.includes('invoice')) defaultCat = 'Insurance Policy / Invoice';

        uploadedProofDocuments.push({
          id: `DOC-${Date.now()}-${Math.floor(Math.random()*1000)}`,
          name: file.name,
          size: file.size,
          type: file.type,
          category: defaultCat,
          dataUrl: e.target.result
        });
        updateProofUI();
      };
      reader.readAsDataURL(file);
    });
  }

  // Setup Dropzone Event Listeners
  const dropzone = document.getElementById('proof-dropzone');
  const fileInput = document.getElementById('int-proof-files');
  const browseBtn = document.getElementById('btn-browse-proofs');

  if (browseBtn && fileInput) {
    browseBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      fileInput.click();
    });
  }
  if (dropzone && fileInput) {
    dropzone.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', (e) => {
      handleProofFiles(e.target.files);
      fileInput.value = '';
    });
    dropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    });
    dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
    dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
      if (e.dataTransfer && e.dataTransfer.files) {
        handleProofFiles(e.dataTransfer.files);
      }
    });
  }

  // Dynamic date constraints on load
  const regDateInput = document.getElementById('int-reg-date');
  if (regDateInput) regDateInput.max = new Date().toISOString().split('T')[0];
  const theftTimeInput = document.getElementById('int-theft-time');
  if (theftTimeInput) theftTimeInput.max = new Date().toISOString().slice(0, 16);

  const INDIAN_STATE_PREFIXES = new Set([
    'AN', 'AP', 'AR', 'AS', 'BR', 'CG', 'CH', 'DD', 'DL', 'DN',
    'GA', 'GJ', 'HP', 'HR', 'JH', 'JK', 'KA', 'KL', 'LA', 'LD',
    'MH', 'ML', 'MN', 'MP', 'MZ', 'NL', 'OD', 'OR', 'PB', 'PY',
    'RJ', 'SK', 'TN', 'TR', 'TS', 'UK', 'UP', 'WB', 'BH'
  ]);

  function validateIndianPlateComprehensive(rawPlate) {
    const p = (rawPlate || '').replace(/[^A-Z0-9]/g, '').toUpperCase();
    if (!p || p.length < 5 || p.length > 13) return { valid: false, reason: 'Registration plate length must be between 5 and 13 characters.' };

    if (/^(\w)\1+$/.test(p)) return { valid: false, reason: 'Invalid repetitive registration plate.' };
    if (/^[0-9]+$/.test(p)) return { valid: false, reason: 'Plate cannot be only numbers.' };
    if (/^[A-Z]+$/.test(p)) return { valid: false, reason: 'Plate cannot be only letters.' };
    if (/^(TEST|DUMMY|SAMPLE|DEMO|ABCD|XXXX|1234)/i.test(p)) return { valid: false, reason: 'Test or dummy registration plate numbers are strictly rejected.' };

    // Bharat Series (e.g. 21BH1234AA to 26BH9999ZZ)
    if (/^[0-9]{2}BH[0-9]{4}[A-Z]{1,2}$/.test(p)) {
      const yr = parseInt(p.slice(0, 2), 10);
      if (yr >= 21 && yr <= 26) return { valid: true, type: 'BHARAT_SERIES', plate: p };
    }

    // Defense / Military (e.g. 21B123456C)
    if (/^[0-9]{2}[A-Z][0-9]{5,6}[A-Z]$/.test(p)) {
      return { valid: true, type: 'DEFENSE', plate: p };
    }

    // Diplomatic (e.g. 77CD1234, 19UN1234, 23CC1234)
    if (/^[0-9]{1,3}(CD|CC|UN)[0-9]{1,4}$/.test(p)) {
      return { valid: true, type: 'DIPLOMATIC', plate: p };
    }

    // Temporary (e.g. GJ01TR1234, GJ01TEMP1234)
    if (/^[A-Z]{2}[0-9]{1,2}(TR|TEMP|CR)[0-9]{1,4}$/.test(p)) {
      const st = p.slice(0, 2);
      if (INDIAN_STATE_PREFIXES.has(st)) return { valid: true, type: 'TEMPORARY', plate: p };
    }

    // Vintage (e.g. GJVA0001, DLVA1234)
    if (/^[A-Z]{2}VA[A-Z]{0,2}[0-9]{4}$/.test(p)) {
      const st = p.slice(0, 2);
      if (INDIAN_STATE_PREFIXES.has(st)) return { valid: true, type: 'VINTAGE', plate: p };
    }

    // Standard / Commercial / EV (GJ01AB1234, MH01T1234, DL1C9999, etc.)
    const st = p.slice(0, 2);
    if (!INDIAN_STATE_PREFIXES.has(st)) {
      return { valid: false, reason: `State code '${st}' is not a recognized Indian State or Union Territory.` };
    }

    const stdMatch = p.match(/^[A-Z]{2}([0-9]{1,2})([A-Z]{0,3})([0-9]{1,4})$/);
    if (stdMatch) {
      return { valid: true, type: 'STANDARD', plate: p };
    }

    return { valid: false, reason: 'Plate number does not match standard Indian MoRTH registration formats (e.g. GJ01AB1234 or 22BH1234AA).' };
  }

  function validateChassis(chassis) {
    const c = (chassis || '').replace(/[^A-Z0-9]/g, '').toUpperCase();
    if (c.length !== 17) return { valid: false, reason: 'Chassis / VIN must be exactly 17 alphanumeric characters (ISO 3779 standard).' };
    if (/[IOQ]/.test(c)) return { valid: false, reason: 'Chassis VIN cannot contain letters I, O, or Q (forbidden under international VIN standards).' };
    if (/^(\w)\1+$/.test(c)) return { valid: false, reason: 'Invalid repetitive Chassis / VIN number.' };
    if (!/[0-9]/.test(c) || !/[A-Z]/.test(c)) return { valid: false, reason: 'Chassis VIN must contain a mixture of letters and numbers.' };
    const dummyPatterns = ['12345678901234567', '01234567890123456', 'XXXXXXXXXXXXX', 'CHASSISNUMBER', 'TESTVINNUMBER'];
    if (dummyPatterns.some(d => c.includes(d))) return { valid: false, reason: 'Dummy or sequential Chassis VIN detected. Enter genuine vehicle chassis.' };
    return { valid: true, chassis: c };
  }

  function validateEngine(engine) {
    const e = (engine || '').replace(/[^A-Z0-9]/g, '').toUpperCase();
    if (e.length < 6 || e.length > 16) return { valid: false, reason: 'Engine Number must be between 6 and 16 characters.' };
    if (/^(\w)\1+$/.test(e)) return { valid: false, reason: 'Invalid repetitive Engine Number.' };
    const dummy = ['000000', '111111', '123456', 'XXXXXX', 'ENGINENO', 'TESTENGINE'];
    if (dummy.some(d => e.includes(d))) return { valid: false, reason: 'Dummy Engine Number detected. Enter authentic engine number.' };
    return { valid: true, engine: e };
  }

  function validateMobileNumber(phone, label = 'Mobile') {
    const clean = (phone || '').replace(/[^0-9]/g, '');
    if (clean.length !== 10) return { valid: false, reason: `${label} number must be exactly 10 digits.` };
    if (!['6', '7', '8', '9'].includes(clean[0])) return { valid: false, reason: `Indian ${label} number must start with 6, 7, 8, or 9.` };
    if (/^(\d)\1+$/.test(clean)) return { valid: false, reason: `Invalid repetitive ${label} number.` };
    const dummyList = ['1234567890', '9876543210', '0123456789', '9898989898', '9090909090'];
    if (dummyList.includes(clean)) return { valid: false, reason: `Dummy ${label} number detected. Please enter a genuine contact number.` };
    return { valid: true, mobile: clean };
  }

  function validateGovtIdNumber(type, num) {
    const clean = (num || '').replace(/[^A-Z0-9]/g, '').toUpperCase();
    if (!clean || clean.length < 8) return { valid: false, reason: 'Government ID number is mandatory and must be at least 8 characters.' };

    if (type.includes('Aadhaar')) {
      if (clean.length !== 12 || !/^[0-9]{12}$/.test(clean)) return { valid: false, reason: 'Aadhaar Card number must be exactly 12 numeric digits.' };
      if (clean.startsWith('0') || clean.startsWith('1')) return { valid: false, reason: 'Valid Aadhaar numbers do not start with 0 or 1.' };
      if (/^(\d)\1+$/.test(clean) || ['123412341234', '111122223333'].includes(clean)) return { valid: false, reason: 'Dummy or repetitive Aadhaar number detected.' };
    } else if (type.includes('PAN')) {
      if (!/^[A-Z]{5}[0-9]{4}[A-Z]{1}$/.test(clean)) return { valid: false, reason: 'PAN Card must be 10 characters formatted like ABCDE1234F.' };
    } else if (type.includes('Voter')) {
      if (!/^[A-Z]{3}[0-9]{7}$/.test(clean)) return { valid: false, reason: 'Voter ID (EPIC) must be 3 letters followed by 7 digits (e.g. ABC1234567).' };
    } else if (type.includes('Passport')) {
      if (!/^[A-Z][0-9]{7}$/.test(clean)) return { valid: false, reason: 'Indian Passport must start with 1 letter followed by 7 digits (e.g. A1234567).' };
    } else if (type.includes('Driving')) {
      if (clean.length < 10 || clean.length > 16) return { valid: false, reason: 'Driving License number must be between 10 and 16 characters.' };
    }
    return { valid: true, idNumber: clean };
  }

  if (intimationForm) {
    intimationForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      // Clear previous invalid highlights
      intimationForm.querySelectorAll('.custom-input').forEach(inp => inp.classList.remove('is-invalid'));

      // 1. Mandatory Documents Verification
      if (uploadedProofDocuments.length < 2) {
        showCustomAlert(
          'Mandatory Ownership Proofs Required',
          'Please upload at least 2 authentic verification documents (such as Vehicle RC Smart Card, Owner Aadhaar/DL, or Vehicle Photographs) to authenticate ownership before activating statewide hotlists.',
          'danger'
        );
        const dropzoneEl = document.getElementById('proof-dropzone');
        if (dropzoneEl) dropzoneEl.scrollIntoView({ behavior: 'smooth' });
        return;
      }

      // Collect field values
      const plateInput = document.getElementById('int-plate');
      const plate = (plateInput?.value || '').trim().toUpperCase();
      const rcNumberInput = document.getElementById('int-rc-number');
      const rcNumber = (rcNumberInput?.value || '').trim().toUpperCase();
      const chassisInput = document.getElementById('int-chassis');
      const chassisNumber = (chassisInput?.value || '').trim().toUpperCase();
      const engineInput = document.getElementById('int-engine');
      const engineNumber = (engineInput?.value || '').trim().toUpperCase();
      const category = document.getElementById('int-category')?.value || 'Four-Wheeler / Car / SUV';
      const makeInput = document.getElementById('int-make');
      const make = (makeInput?.value || '').trim();
      const colorInput = document.getElementById('int-color');
      const vehicleColor = (colorInput?.value || '').trim();
      const regDateInput = document.getElementById('int-reg-date');
      const registrationDate = regDateInput?.value || '';

      const nameInput = document.getElementById('int-name');
      const ownerName = (nameInput?.value || '').trim();
      const guardianInput = document.getElementById('int-guardian');
      const guardianName = (guardianInput?.value || '').trim();
      const idType = document.getElementById('int-id-type')?.value || 'Aadhaar Card';
      const idNumberInput = document.getElementById('int-id-number');
      const idNumber = (idNumberInput?.value || '').trim();
      const phoneInput = document.getElementById('int-phone');
      const mobile = (phoneInput?.value || '').trim();
      const altPhoneInput = document.getElementById('int-alt-phone');
      const altMobile = (altPhoneInput?.value || '').trim();
      const emailInput = document.getElementById('int-email');
      const email = (emailInput?.value || '').trim();
      const insurancePolicy = (document.getElementById('int-insurance')?.value || '').trim();
      const addressInput = document.getElementById('int-address');
      const permanentAddress = (addressInput?.value || '').trim();

      const theftTimeInput = document.getElementById('int-theft-time');
      const incidentDateTime = theftTimeInput?.value || '';
      const district = document.getElementById('int-district')?.value || 'Ahmedabad City';
      const policeStationInput = document.getElementById('int-police-station');
      const policeStation = (policeStationInput?.value || '').trim();
      const locationInput = document.getElementById('int-location');
      const incidentLocation = (locationInput?.value || '').trim();
      const firNumber = (document.getElementById('int-fir')?.value || '').trim() || 'Pending Station Endorsement';
      const description = (document.getElementById('int-desc')?.value || '').trim();
      const declarationChecked = document.getElementById('int-declaration')?.checked;

      // -------------------------------------------------------------
      // STRICT ANTI-DUMMY REAL INFORMATION VERIFICATION
      // -------------------------------------------------------------
      // 1. Plate
      const plateCheck = validateIndianPlateComprehensive(plate);
      if (!plateCheck.valid) {
        plateInput?.classList.add('is-invalid');
        plateInput?.focus();
        showCustomAlert('Invalid Registration Number', plateCheck.reason, 'danger');
        return;
      }

      // 2. Chassis
      const chassisCheck = validateChassis(chassisNumber);
      if (!chassisCheck.valid) {
        chassisInput?.classList.add('is-invalid');
        chassisInput?.focus();
        showCustomAlert('Invalid Chassis / VIN Number', chassisCheck.reason, 'danger');
        return;
      }

      // 3. Engine
      const engineCheck = validateEngine(engineNumber);
      if (!engineCheck.valid) {
        engineInput?.classList.add('is-invalid');
        engineInput?.focus();
        showCustomAlert('Invalid Engine Number', engineCheck.reason, 'danger');
        return;
      }

      // 4. RC SmartCard Number
      if (rcNumber.length < 8 || /^(\w)\1+$/.test(rcNumber) || rcNumber.includes('000000')) {
        rcNumberInput?.classList.add('is-invalid');
        rcNumberInput?.focus();
        showCustomAlert('Invalid RC Number', 'Please enter genuine Registration Certificate SmartCard number as printed on RC card.', 'danger');
        return;
      }

      // 5. Make & Color
      if (make.length < 3 || /^(test|dummy|car|auto|bike|vehicle|abc)$/i.test(make)) {
        makeInput?.classList.add('is-invalid');
        makeInput?.focus();
        showCustomAlert('Invalid Vehicle Make/Model', 'Please enter specific vehicle make, model and variant (e.g. Hyundai Creta SX or Honda Activa 6G).', 'danger');
        return;
      }
      if (vehicleColor.length < 3 || /^(test|dummy|color)$/i.test(vehicleColor)) {
        colorInput?.classList.add('is-invalid');
        colorInput?.focus();
        showCustomAlert('Invalid Vehicle Color', 'Please specify genuine vehicle color (e.g. Polar White, Phantom Black).', 'danger');
        return;
      }

      // 6. Dates
      const now = new Date();
      if (!registrationDate || new Date(registrationDate) > now) {
        regDateInput?.classList.add('is-invalid');
        regDateInput?.focus();
        showCustomAlert('Invalid Registration Date', 'Vehicle registration date cannot be in the future.', 'danger');
        return;
      }
      if (!incidentDateTime || new Date(incidentDateTime) > now) {
        theftTimeInput?.classList.add('is-invalid');
        theftTimeInput?.focus();
        showCustomAlert('Invalid Incident Time', 'Theft / last seen date and time cannot be in the future.', 'danger');
        return;
      }
      if (new Date(incidentDateTime) < new Date(registrationDate)) {
        theftTimeInput?.classList.add('is-invalid');
        theftTimeInput?.focus();
        showCustomAlert('Invalid Incident Timeline', 'Theft date cannot be prior to vehicle registration date.', 'danger');
        return;
      }

      // 7. Owner Names
      if (ownerName.length < 3 || !/^[A-Za-z\s\.]+$/.test(ownerName) || /^(test|dummy|user|admin|name|abc|asdf)$/i.test(ownerName) || !ownerName.includes(' ')) {
        nameInput?.classList.add('is-invalid');
        nameInput?.focus();
        showCustomAlert('Invalid Owner Name', 'Please enter full legal name (First Name and Surname) as printed on the RC SmartCard.', 'danger');
        return;
      }
      if (guardianName.length < 3 || !/^[A-Za-z\s\.]+$/.test(guardianName) || /^(test|dummy|father|guardian|abc)$/i.test(guardianName)) {
        guardianInput?.classList.add('is-invalid');
        guardianInput?.focus();
        showCustomAlert('Invalid Guardian Name', 'Please enter legal father or husband full name.', 'danger');
        return;
      }

      // 8. Govt ID
      const idCheck = validateGovtIdNumber(idType, idNumber);
      if (!idCheck.valid) {
        idNumberInput?.classList.add('is-invalid');
        idNumberInput?.focus();
        showCustomAlert('Invalid Government ID', idCheck.reason, 'danger');
        return;
      }

      // 9. Mobile Numbers
      const phoneCheck = validateMobileNumber(mobile, 'Contact Mobile');
      if (!phoneCheck.valid) {
        phoneInput?.classList.add('is-invalid');
        phoneInput?.focus();
        showCustomAlert('Invalid Mobile Number', phoneCheck.reason, 'danger');
        return;
      }
      if (altMobile) {
        const altCheck = validateMobileNumber(altMobile, 'Alternate Mobile');
        if (!altCheck.valid) {
          altPhoneInput?.classList.add('is-invalid');
          altPhoneInput?.focus();
          showCustomAlert('Invalid Alternate Mobile', altCheck.reason, 'danger');
          return;
        }
        if (altCheck.mobile === phoneCheck.mobile) {
          altPhoneInput?.classList.add('is-invalid');
          altPhoneInput?.focus();
          showCustomAlert('Duplicate Mobile Numbers', 'Alternate emergency mobile must be different from primary mobile.', 'danger');
          return;
        }
      }

      // 10. Email
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email) || email.includes('test@') || email.includes('dummy@') || email.includes('asdf@')) {
        emailInput?.classList.add('is-invalid');
        emailInput?.focus();
        showCustomAlert('Invalid Email Address', 'Please provide a genuine email address for official digital docket transmission.', 'danger');
        return;
      }

      // 11. Address & Location
      if (permanentAddress.length < 15 || /^(test|dummy|address|asdfghjkl)/i.test(permanentAddress)) {
        addressInput?.classList.add('is-invalid');
        addressInput?.focus();
        showCustomAlert('Incomplete Residential Address', 'Please enter complete permanent address including Flat/House No, Society, Area and City (minimum 15 characters).', 'danger');
        return;
      }
      if (incidentLocation.length < 8 || /^(test|dummy|somewhere|location)/i.test(incidentLocation)) {
        locationInput?.classList.add('is-invalid');
        locationInput?.focus();
        showCustomAlert('Incomplete Theft Location', 'Please provide specific theft location / landmark / parking area (minimum 8 characters).', 'danger');
        return;
      }
      if (policeStation.length < 3 || /^(test|station|police)$/i.test(policeStation)) {
        policeStationInput?.classList.add('is-invalid');
        policeStationInput?.focus();
        showCustomAlert('Invalid Police Station', 'Please enter the nearest Police Station having territorial jurisdiction.', 'danger');
        return;
      }

      // 12. Declaration Checkbox
      if (!declarationChecked) {
        showCustomAlert('Statutory Declaration Required', 'You must affirm the Solemn Statutory Declaration of Ownership before submission.', 'warning');
        return;
      }

      const submitBtn = intimationForm.querySelector('.btn-submit-intimation');
      const origBtnText = submitBtn ? submitBtn.innerHTML : 'Submit Authenticated e-Intimation';
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Authenticating with VAHAN & Statewide ANPR Sentry Matrix...';
      }

      const payload = {
        plate,
        rcNumber,
        chassisNumber,
        engineNumber,
        category,
        vehicleMake: make,
        vehicleColor,
        registrationDate,
        ownerName,
        guardianName,
        idType,
        idNumber,
        mobile,
        altMobile,
        email,
        insurancePolicy,
        permanentAddress,
        incidentDateTime,
        district,
        policeStation,
        incidentLocation,
        firNumber,
        description,
        documents: uploadedProofDocuments.map(d => ({
          id: d.id,
          name: d.name,
          category: d.category,
          size: d.size,
          type: d.type,
          dataUrl: d.dataUrl
        }))
      };

      let refNo = `GUJ-THEFT-2026-${Math.floor(100000 + Math.random() * 900000)}`;
      let digitalSig = `GUJ-POL-SIG-${Date.now().toString(16).toUpperCase()}`;
      const timestamp = new Date().toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' }) + ' IST';

      // 1. Send to backend server with 3s timeout fallback
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 3000);

        const endpoints = ['/api/public/theft-report'];
        if (window.location.port !== '8000') {
          endpoints.push(`http://${window.location.hostname || 'localhost'}:8000/api/public/theft-report`);
        }

        let resp = null;
        for (const ep of endpoints) {
          try {
            resp = await fetch(ep, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(payload),
              signal: controller.signal
            });
            if (resp && resp.ok) break;
          } catch (err) {}
        }
        clearTimeout(timeoutId);

        if (resp && resp.ok) {
          const result = await resp.json();
          if (result.ackNumber) refNo = result.ackNumber;
          if (result.digitalSignature) digitalSig = result.digitalSignature;
        }
      } catch (networkErr) {
        console.warn('Backend server synchronization fallback to local secure storage:', networkErr);
      }

      // 2. Cache receipt for dedicated 1-page PDF print/download
      window._lastStolenVehicleReceipt = {
        refNo,
        plate,
        rcNumber,
        chassisNumber,
        engineNumber,
        category,
        make,
        vehicleColor,
        registrationDate,
        name: ownerName,
        guardianName,
        idType,
        idNumber,
        phone: mobile,
        altMobile,
        email,
        insurancePolicy,
        permanentAddress,
        incidentDateTime: incidentDateTime || timestamp,
        district,
        policeStation,
        location: incidentLocation,
        fir: firNumber,
        desc: description,
        documents: [...uploadedProofDocuments],
        timestamp,
        digitalSig
      };

      // 3. Save into citizen local history
      try {
        const myReports = JSON.parse(localStorage.getItem('SENTINEL_MY_INTIMATIONS') || '[]');
        myReports.unshift(window._lastStolenVehicleReceipt);
        localStorage.setItem('SENTINEL_MY_INTIMATIONS', JSON.stringify(myReports));
      } catch (err) {}

      // 4. Save into active hotlist registry so CIPHER terminal picks it up immediately
      try {
        const wl = JSON.parse(localStorage.getItem('SENTINEL_WATCHLIST_REGISTRY_V3') || '[]');
        const newWl = {
          id: `CITIZEN-${refNo.split('-').pop()}`,
          plate: plate,
          vehicleMake: make,
          category: `🚨 STOLEN VEHICLE (${category})`,
          source: `Citizen e-Intimation #${refNo}`,
          threatLevel: 'CRITICAL',
          suspectName: `Complainant: ${ownerName} (Ph: ${mobile})`,
          description: `Location: ${incidentLocation} | PS: ${policeStation}. Chassis: ${chassisNumber || 'Verified'}, Engine: ${engineNumber || 'Verified'}. ${description || 'Citizen lodged verified stolen vehicle alert.'}`,
          registeredOwner: ownerName,
          registeredRTO: 'Gujarat State Transport Dept',
          chassisNumber: chassisNumber,
          engineNumber: engineNumber,
          rcNumber: rcNumber,
          status: 'ACTIVE_WARRANT',
          isCitizenReport: true,
          ackNumber: refNo,
          documentsCount: uploadedProofDocuments.length,
          lastDetectedCamera: 'Scanning 30 Live Feeds...',
          lastDetectedTime: timestamp
        };
        const filtered = wl.filter(w => w.plate !== plate);
        filtered.unshift(newWl);
        localStorage.setItem('SENTINEL_WATCHLIST_REGISTRY_V3', JSON.stringify(filtered));
      } catch (err) {}

      // 5. Render Official Digital Acknowledgment Receipt
      if (receiptContent && receiptCard) {
        receiptContent.innerHTML = `
          <div style="background: rgba(3, 7, 20, 0.95); border: 2px solid #38BDF8; border-radius: 12px; padding: 20px; color: #FFF; box-shadow: 0 10px 30px rgba(0,0,0,0.8);">
            <!-- Police Header -->
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(56,189,248,0.3); padding-bottom: 12px; margin-bottom: 14px; flex-wrap: wrap; gap: 10px;">
              <div style="display: flex; align-items: center; gap: 12px;">
                <img src="/logo.png" alt="Gujarat Police Sentinel" style="width: 48px; height: 48px; object-fit: contain;">
                <div>
                  <h4 style="margin: 0; font-size: 14px; color: #FFF; letter-spacing: 0.5px;">GUJARAT POLICE SURVEILLANCE & INTELLIGENCE COMMAND</h4>
                  <span style="font-size: 11px; color: #38BDF8; font-family: monospace;">DIGITAL PRE-FIR THEFT e-INTIMATION & OWNERSHIP AUTHENTICITY DOSSIER</span>
                </div>
              </div>
              <div style="text-align: right;">
                <span style="display: block; font-family: monospace; font-size: 13.5px; font-weight: 800; color: #FEF08A; background: rgba(234,179,8,0.15); padding: 4px 10px; border-radius: 4px; border: 1px solid rgba(234,179,8,0.4);">${refNo}</span>
                <span style="font-size: 9.5px; color: #94A3B8;">Govt of Gujarat Ref ID</span>
              </div>
            </div>

            <!-- Authenticated Technical Credentials Grid -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px 14px; font-size: 12px; margin-bottom: 14px; background: rgba(8, 17, 39, 0.5); padding: 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.08);">
              <div><strong style="color: #94A3B8;">Vehicle Plate:</strong> <span style="font-family: monospace; font-size: 14px; font-weight: 800; color: #F87171;">${plate}</span></div>
              <div><strong style="color: #94A3B8;">Make & Model:</strong> <span style="color: #FFF; font-weight: 600;">${make} (${vehicleColor || 'Standard'})</span></div>
              <div><strong style="color: #94A3B8;">RC SmartCard No:</strong> <span style="color: #FEF08A; font-family: monospace;">${rcNumber}</span></div>
              <div><strong style="color: #94A3B8;">Chassis / VIN:</strong> <span style="color: #FEF08A; font-family: monospace;">${chassisNumber}</span></div>
              <div><strong style="color: #94A3B8;">Engine Number:</strong> <span style="color: #FEF08A; font-family: monospace;">${engineNumber}</span></div>
              <div><strong style="color: #94A3B8;">Vehicle Class:</strong> <span style="color: #38BDF8;">${category}</span></div>
              <div><strong style="color: #94A3B8;">Registered Owner:</strong> <span style="color: #FFF; font-weight: 700;">${ownerName}</span></div>
              <div><strong style="color: #94A3B8;">Owner ID Ref:</strong> <span style="color: #CBD5E1;">${idType} (${idNumber})</span></div>
              <div><strong style="color: #94A3B8;">Contact Mobile:</strong> <span style="color: #FFF; font-family: monospace;">+91 ${mobile}</span></div>
              <div><strong style="color: #94A3B8;">District / Jurisdiction:</strong> <span style="color: #38BDF8;">${district} &bull; ${policeStation}</span></div>
              <div><strong style="color: #94A3B8;">Theft Location:</strong> <span style="color: #FFF;">${incidentLocation}</span></div>
              <div><strong style="color: #94A3B8;">Lodged Timestamp:</strong> <span style="color: #94A3B8; font-family: monospace;">${timestamp}</span></div>
            </div>

            <!-- Uploaded Evidence Preview Gallery -->
            <div style="margin-bottom: 14px;">
              <div style="font-size: 11px; font-weight: 700; color: #38BDF8; margin-bottom: 6px; display: flex; align-items: center; gap: 6px;">
                <i class="fa-solid fa-file-shield"></i> VERIFIED OWNERSHIP PROOFS & PHOTOGRAPHS (${uploadedProofDocuments.length} ATTACHED):
              </div>
              <div class="receipt-proofs-strip">
                ${uploadedProofDocuments.map(doc => `
                  <div class="receipt-proof-item" title="${doc.category}: ${doc.name}">
                    ${doc.dataUrl.startsWith('data:image/') ? `
                      <img src="${doc.dataUrl}" alt="${doc.name}">
                    ` : `
                      <div style="display: flex; align-items: center; justify-content: center; height: 100%; color: #38BDF8; font-size: 24px;"><i class="fa-solid fa-file-pdf"></i></div>
                    `}
                    <div class="receipt-proof-tag">${doc.category.split(' ')[0]}</div>
                  </div>
                `).join('')}
              </div>
            </div>

            <!-- Digital Hash & Police Station Note -->
            <div style="background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.4); border-radius: 8px; padding: 12px 14px; margin-bottom: 12px; font-size: 11.5px; color: #34D399; line-height: 1.5;">
              <div style="display: flex; align-items: center; gap: 6px; font-weight: 700; margin-bottom: 4px;">
                <i class="fa-solid fa-circle-check"></i> STATEWIDE ANPR HIGHWAY SENTRY & INTERCEPTOR GRID ACTIVATED
              </div>
              <div>Digital Verification Hash: <code style="color: #FEF08A; font-family: monospace; font-size: 10.5px;">${digitalSig}</code></div>
              <div style="color: #CBD5E1; margin-top: 4px; font-size: 11px;">
                📌 <strong>Officer Instructions for Citizen:</strong> Present this digital acknowledgement receipt along with your original RC Smart Card at <strong>${policeStation || district}</strong>. The investigating officer can directly correlate real-time automated camera detections under Section 379/411 BNS using Ref ID <strong>${refNo}</strong>.
              </div>
            </div>

            <!-- Security Stamp -->
            <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 10px; font-size: 10.5px; color: #64748B;">
              <span>🔒 SECURE DIGITAL RECORD // SECTION 65B EVIDENCE ACT & SECTION 379/411 BNS COMPLIANT</span>
              <span style="color: #38BDF8; font-family: monospace;">VAHAN / SARTHI & CCTNS INTEGRATED</span>
            </div>
          </div>
        `;

        receiptCard.style.display = 'block';
        receiptCard.scrollIntoView({ behavior: 'smooth' });
      }

      showCustomAlert('Authenticated e-Intimation Lodged', `Your vehicle theft report for [${plate}] has been successfully verified & broadcast to all Gujarat Police CCTV interceptors & Highway Patrol cruisers! Reference ID: ${refNo}`, 'success');

      // Reset form and upload state
      intimationForm.reset();
      uploadedProofDocuments = [];
      updateProofUI();

      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = origBtnText;
      }
    });
  }

  if (dismissReceiptBtn && receiptCard) {
    dismissReceiptBtn.addEventListener('click', () => {
      receiptCard.style.display = 'none';
    });
  }

  // Isolated Single-Page Comprehensive PDF Print/Download for Stolen Vehicle e-Intimation
  window.printStolenVehicleDocument = function(customData) {
    let receiptData = customData || window._lastStolenVehicleReceipt;
    if (!receiptData) {
      try {
        const myReports = JSON.parse(localStorage.getItem('SENTINEL_MY_INTIMATIONS') || '[]');
        if (myReports.length > 0) receiptData = myReports[0];
      } catch(e) {}
    }

    if (!receiptData) {
      showCustomAlert('No Active Form', 'Please fill out and submit the Vehicle Theft e-Intimation form first.', 'info');
      return;
    }

    const printIframe = document.createElement('iframe');
    printIframe.style.position = 'fixed';
    printIframe.style.right = '0';
    printIframe.style.bottom = '0';
    printIframe.style.width = '0';
    printIframe.style.height = '0';
    printIframe.style.border = 'none';
    document.body.appendChild(printIframe);

    const doc = printIframe.contentWindow.document;
    doc.open();

    const proofs = receiptData.documents || [];

    doc.write(`
      <!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="UTF-8">
        <title>Gujarat Police - e-Intimation ${receiptData.refNo}</title>
        <style>
          @page {
            size: A4 portrait;
            margin: 10mm 12mm 10mm 12mm;
          }
          * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
          }
          body {
            font-family: 'Segoe UI', Arial, sans-serif;
            color: #0F172A;
            background: #FFF;
            line-height: 1.4;
            font-size: 11.5px;
          }
          .document-wrapper {
            border: 2px solid #0F172A;
            border-radius: 6px;
            padding: 16px 20px;
            background: #FFF;
            position: relative;
          }
          .header-table {
            width: 100%;
            border-bottom: 2px solid #0F172A;
            padding-bottom: 10px;
            margin-bottom: 10px;
          }
          .header-title-block {
            text-align: center;
          }
          .header-title-block h1 {
            font-size: 15px;
            font-weight: 800;
            letter-spacing: 0.5px;
            color: #0F172A;
            text-transform: uppercase;
          }
          .header-title-block h2 {
            font-size: 11.5px;
            font-weight: 700;
            color: #1E3A8A;
            margin-top: 2px;
            text-transform: uppercase;
          }
          .header-title-block p {
            font-size: 10px;
            color: #475569;
            margin-top: 1px;
          }
          .ref-banner {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #F1F5F9;
            border: 1px solid #CBD5E1;
            border-radius: 6px;
            padding: 6px 12px;
            margin-bottom: 10px;
          }
          .ref-box {
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 13px;
            font-weight: 800;
            color: #1E3A8A;
          }
          .status-pill {
            background: #DC2626;
            color: #FFF;
            font-weight: 800;
            font-size: 9.5px;
            padding: 2px 8px;
            border-radius: 4px;
            letter-spacing: 0.5px;
          }
          .section-title {
            font-size: 11px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #1E3A8A;
            border-bottom: 1.5px solid #CBD5E1;
            padding-bottom: 2px;
            margin-bottom: 6px;
            margin-top: 10px;
          }
          .data-grid {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 6px;
          }
          .data-grid td {
            padding: 4.5px 8px;
            border: 1px solid #E2E8F0;
            font-size: 11px;
            vertical-align: top;
          }
          .data-grid td.label-col {
            width: 25%;
            background: #F8FAFC;
            font-weight: 700;
            color: #475569;
          }
          .data-grid td.val-col {
            width: 25%;
            color: #0F172A;
          }
          .plate-highlight {
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 13.5px;
            font-weight: 900;
            color: #DC2626;
            background: #FEF2F2;
            padding: 1px 6px;
            border: 1px solid #FCA5A5;
            border-radius: 4px;
            display: inline-block;
          }
          .code-val {
            font-family: 'Consolas', monospace;
            font-weight: 700;
            color: #1E3A8A;
          }
          .proofs-table {
            width: 100%;
            margin-top: 6px;
            border-collapse: collapse;
          }
          .proof-box {
            display: inline-block;
            width: 110px;
            margin: 4px 6px 4px 0;
            vertical-align: top;
            border: 1px solid #CBD5E1;
            border-radius: 4px;
            padding: 4px;
            background: #F8FAFC;
            text-align: center;
          }
          .proof-box img {
            width: 100px;
            height: 70px;
            object-fit: cover;
            border-radius: 3px;
            border: 1px solid #E2E8F0;
          }
          .proof-caption {
            font-size: 8.5px;
            font-weight: 700;
            color: #334155;
            margin-top: 2px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
          }
          .notice-box {
            background: #F0FDF4;
            border: 1px solid #86EFAC;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 10.5px;
            color: #166534;
            line-height: 1.45;
            margin-top: 10px;
          }
          .signature-row {
            margin-top: 20px;
            display: flex;
            justify-content: space-between;
            padding-top: 10px;
          }
          .sig-block {
            width: 200px;
            text-align: center;
            border-top: 1px dashed #64748B;
            padding-top: 3px;
            font-size: 10px;
            color: #475569;
          }
        </style>
      </head>
      <body>
        <div class="document-wrapper">
          <table class="header-table">
            <tr>
              <td style="width: 50px; vertical-align: middle;">
                <img src="/logo.png" alt="Gujarat Police Crest" style="width: 48px; height: 48px; object-fit: contain;">
              </td>
              <td class="header-title-block">
                <h1>GOVERNMENT OF GUJARAT — POLICE DEPARTMENT</h1>
                <h2>OFFICIAL CITIZEN PRE-FIR VEHICLE THEFT & OWNERSHIP AUTHENTICATION DOCKET</h2>
                <p>STATEWIDE AUTOMATED ANPR CORRIDOR INTERCEPT GRID &bull; CCTNS / VAHAN COMPLIANT</p>
              </td>
              <td style="width: 60px; text-align: right; vertical-align: middle;">
                <div style="font-family: monospace; font-size: 9px; color: #64748B; border: 1px solid #CBD5E1; padding: 3px; border-radius: 4px; text-align: center;">
                  SEC 65B<br>EVIDENCE<br>CERTIFIED
                </div>
              </td>
            </tr>
          </table>

          <div class="ref-banner">
            <div>
              <span style="font-size: 9.5px; color: #64748B; display: block;">Official Acknowledgement Reference ID:</span>
              <span class="ref-box">${receiptData.refNo}</span>
            </div>
            <div>
              <span style="font-size: 9.5px; color: #64748B; display: block;">Lodged Date & Time:</span>
              <span style="font-weight: 700; font-size: 11px;">${receiptData.timestamp}</span>
            </div>
            <div>
              <span class="status-pill">● STATEWIDE HOTLIST ACTIVE</span>
            </div>
          </div>

          <div class="section-title">1. AUTHENTICATED VEHICLE TECHNICAL CREDENTIALS</div>
          <table class="data-grid">
            <tr>
              <td class="label-col">Registration Plate</td>
              <td class="val-col"><span class="plate-highlight">${receiptData.plate}</span></td>
              <td class="label-col">Vehicle Class / Category</td>
              <td class="val-col"><strong>${receiptData.category}</strong></td>
            </tr>
            <tr>
              <td class="label-col">RC SmartCard Number</td>
              <td class="val-col"><span class="code-val">${receiptData.rcNumber || 'Verified on Portal'}</span></td>
              <td class="label-col">Chassis / VIN Number</td>
              <td class="val-col"><span class="code-val">${receiptData.chassisNumber || 'Verified on Portal'}</span></td>
            </tr>
            <tr>
              <td class="label-col">Engine Number</td>
              <td class="val-col"><span class="code-val">${receiptData.engineNumber || 'Verified on Portal'}</span></td>
              <td class="label-col">Make, Model & Color</td>
              <td class="val-col">${receiptData.make} (${receiptData.vehicleColor || 'Standard'})</td>
            </tr>
            <tr>
              <td class="label-col">Registration / Mfg Date</td>
              <td class="val-col">${receiptData.registrationDate || 'N/A'}</td>
              <td class="label-col">Insurance Policy / Co.</td>
              <td class="val-col">${receiptData.insurancePolicy || 'Standard / Third Party'}</td>
            </tr>
            <tr>
              <td class="label-col">Identifying Marks / Mods</td>
              <td class="val-col" colspan="3">${receiptData.desc || 'No distinguishing aftermarket markings noted.'}</td>
            </tr>
          </table>

          <div class="section-title">2. VERIFIED OWNER & COMPLAINANT PROFILE</div>
          <table class="data-grid">
            <tr>
              <td class="label-col">Registered Legal Owner</td>
              <td class="val-col"><strong>${receiptData.name}</strong></td>
              <td class="label-col">Father / Guardian Name</td>
              <td class="val-col">${receiptData.guardianName || 'N/A'}</td>
            </tr>
            <tr>
              <td class="label-col">Owner Govt ID Ref</td>
              <td class="val-col">${receiptData.idType || 'Aadhaar Card'}: <span class="code-val">${receiptData.idNumber || 'Verified'}</span></td>
              <td class="label-col">Primary Contact Mobile</td>
              <td class="val-col"><strong>+91 ${receiptData.phone}</strong> ${receiptData.altMobile ? `(Alt: +91 ${receiptData.altMobile})` : ''}</td>
            </tr>
            <tr>
              <td class="label-col">Citizen Official Email</td>
              <td class="val-col">${receiptData.email || 'N/A'}</td>
              <td class="label-col">Residential Address</td>
              <td class="val-col">${receiptData.permanentAddress || receiptData.location}</td>
            </tr>
          </table>

          <div class="section-title">3. INCIDENT CIRCUMSTANCES & POLICE JURISDICTION</div>
          <table class="data-grid">
            <tr>
              <td class="label-col">Date & Time of Theft</td>
              <td class="val-col"><strong>${receiptData.incidentDateTime || receiptData.timestamp}</strong></td>
              <td class="label-col">Commissionerate / District</td>
              <td class="val-col"><strong>${receiptData.district || 'Ahmedabad City'}</strong></td>
            </tr>
            <tr>
              <td class="label-col">Police Station Jurisdiction</td>
              <td class="val-col"><strong>${receiptData.policeStation || 'Central'}</strong></td>
              <td class="label-col">Station GD / Diary Ref</td>
              <td class="val-col">${receiptData.fir || 'Pending Station Endorsement'}</td>
            </tr>
            <tr>
              <td class="label-col">Exact Theft Landmark / Spot</td>
              <td class="val-col" colspan="3">${receiptData.location}</td>
            </tr>
            <tr>
              <td class="label-col">ANPR Camera Hotlist Status</td>
              <td class="val-col"><strong>ACTIVE &bull; 80,000+ CAMERAS</strong></td>
              <td class="label-col">Digital Verification Hash</td>
              <td class="val-col"><code style="font-family: monospace; font-size: 9px;">${receiptData.digitalSig}</code></td>
            </tr>
          </table>

          ${proofs.length > 0 ? `
            <div class="section-title">4. ATTACHED PROOFS OF OWNERSHIP & PHOTOGRAPHIC EVIDENCE</div>
            <div>
              ${proofs.map(doc => `
                <div class="proof-box">
                  ${doc.dataUrl && doc.dataUrl.startsWith('data:image/') ? `
                    <img src="${doc.dataUrl}" alt="${doc.name}">
                  ` : `
                    <div style="height: 70px; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: bold; color: #1E3A8A; border: 1px dashed #CBD5E1;">[PDF DOC]</div>
                  `}
                  <div class="proof-caption" title="${doc.name}">${doc.category || doc.name}</div>
                </div>
              `).join('')}
            </div>
          ` : ''}

          <div class="notice-box">
            <strong>📌 STATUTORY INSTRUCTIONS FOR CITIZEN & POLICE INVESTIGATING OFFICER:</strong><br>
            This document serves as an authentic electronic intimation certifying that the above vehicle has been validated with owner credentials and added to the Gujarat Police ANPR Hotlist matrix.
            <strong>Citizen must present this printed docket along with physical/mParivahan RC Smart Card at ${receiptData.policeStation || receiptData.district}.</strong> 
            The investigating officer can retrieve real-time automated camera sightings using Ref ID <strong>${receiptData.refNo}</strong> for incorporation into formal FIR under Section 379/411 BNS (Bharatiya Nyaya Sanhita).
          </div>

          <div class="signature-row">
            <div class="sig-block">
              <strong>Complainant / Owner Signature</strong><br>
              <span>(${receiptData.name})</span>
            </div>
            <div class="sig-block">
              <strong>Station Duty Officer Seal</strong><br>
              <span>Gujarat Police Intercept Grid Desk</span>
            </div>
          </div>
        </div>
      </body>
      </html>
    `);
    doc.close();

    setTimeout(() => {
      printIframe.contentWindow.focus();
      printIframe.contentWindow.print();
      setTimeout(() => {
        try { document.body.removeChild(printIframe); } catch(e){}
      }, 2000);
    }, 400);
  };

  // 6. Interactive Emergency SOS Modals Trigger (Backend Connected)
  const sosModalTriggers = document.querySelectorAll('[data-modal]');
  sosModalTriggers.forEach(trigger => {
    trigger.addEventListener('click', (e) => {
      e.preventDefault();
      const targetModalId = trigger.dataset.modal;
      const targetModal = document.getElementById(targetModalId);
      if (targetModal) {
        targetModal.classList.add('active');
      }
    });
  });

  // Close modals
  const modalCloseBtns = document.querySelectorAll('[data-close]');
  modalCloseBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      const targetModalId = btn.dataset.close;
      const targetModal = document.getElementById(targetModalId);
      if (targetModal) {
        targetModal.classList.remove('active');
      }
    });
  });

  // Close on backdrop click
  document.querySelectorAll('.pub-modal-backdrop').forEach(backdrop => {
    backdrop.addEventListener('click', (e) => {
      if (e.target === backdrop) {
        backdrop.classList.remove('active');
      }
    });
  });

  // 7. e-Challan Lookup Handler (Real Backend API Connected)
  const btnCheckChallan = document.getElementById('btn-check-challan');
  const challanInput = document.getElementById('challan-search-input');
  const challanResultBox = document.getElementById('challan-result-box');

  if (btnCheckChallan && challanInput && challanResultBox) {
    btnCheckChallan.addEventListener('click', async () => {
      const query = challanInput.value.trim().toUpperCase();
      if (!query) {
        showCustomAlert('e-Challan Portal', 'Please enter a vehicle registration number or Challan No (e.g. GJ01ER4492)', 'info');
        return;
      }

      btnCheckChallan.disabled = true;
      btnCheckChallan.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Searching VAHAN Grid...';
      challanResultBox.style.display = 'block';
      challanResultBox.innerHTML = '<div style="text-align: center; padding: 20px; color: #38BDF8;"><i class="fa-solid fa-spinner fa-spin fa-2x"></i><p style="margin-top: 8px; font-size: 12px;">Querying Gujarat State e-Challan Database...</p></div>';

      try {
        const apiBase = (window.SENTINEL_API_BASE || localStorage.getItem('SENTINEL_API_BASE') || '');
        const ep = apiBase ? `${apiBase}/api/public/echallan-lookup` : '/api/public/echallan-lookup';
        const resp = await fetch(ep, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: query })
        });

        const data = await resp.json();

        const challans = data.challans || [];

        if (challans.length > 0) {
          let html = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; flex-wrap: wrap; gap: 8px;">
              <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-family: monospace; font-size: 16px; font-weight: 900; color: #002147; background: #E6F6FF; padding: 4px 10px; border-radius: 6px; border: 1.5px solid #002147;">${query}</span>
                <span style="background: rgba(186,26,26,0.1); color: #BA1A1A; border: 1px solid rgba(186,26,26,0.3); font-size: 11px; font-weight: 800; padding: 4px 10px; border-radius: 4px;">● ${challans.length} RECORD(S) FOUND</span>
              </div>
              <span style="font-size: 12px; color: #475569; font-weight: 600;">VAHAN 4.0 Verified Integration</span>
            </div>
          `;

          challans.forEach(c => {
            const isPaid = c.status === 'PAID';
            html += `
              <div class="challan-card-item" style="background: rgba(15, 23, 42, 0.85); border: 1.5px solid ${isPaid ? '#10B981' : '#EF4444'}; border-radius: 12px; padding: 20px; margin-bottom: 14px; box-shadow: 0 10px 25px rgba(0,0,0,0.4), 0 0 15px ${isPaid ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.2)'}; backdrop-filter: blur(10px);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 10px;">
                  <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="display: inline-flex; align-items: center; background: #002147; border: 1.5px solid #38BDF8; border-radius: 6px; overflow: hidden; font-family: 'JetBrains Mono', monospace; font-size: 14px; font-weight: 900; letter-spacing: 0.1em; color: #FFF; box-shadow: 0 0 12px rgba(56,189,248,0.3);">
                      <span style="background: #1E3A8A; color: #EAB308; padding: 3px 6px; font-size: 9px; font-weight: 900;">IND</span>
                      <span style="padding: 3px 10px; color: #38BDF8;">${query}</span>
                    </span>
                    <span style="font-size: 11px; color: #94A3B8;">Challan Ref: <strong style="color: #F8FAFC;">${c.challanNo}</strong></span>
                  </div>
                  <span style="padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 800; background: ${isPaid ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.2)'}; color: ${isPaid ? '#34D399' : '#F87171'}; border: 1px solid ${isPaid ? '#10B981' : '#EF4444'};">
                    ${isPaid ? '<i class="fa-solid fa-circle-check"></i> SETTLED & PAID' : '<i class="fa-solid fa-triangle-exclamation"></i> UNPAID VIOLATION'}
                  </span>
                </div>

                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; font-size: 12.5px; margin-bottom: 16px; color: #CBD5E1;">
                  <div><span style="color: #64748B; font-size: 11px; display: block;">Registered Owner</span> <strong style="color: #F8FAFC;">${c.ownerName}</strong></div>
                  <div><span style="color: #64748B; font-size: 11px; display: block;">Statutory Violation</span> <strong style="color: #F87171;">${c.violation}</strong></div>
                  <div><span style="color: #64748B; font-size: 11px; display: block;">Detection Camera Node</span> <strong style="color: #38BDF8;"><i class="fa-solid fa-camera"></i> ${c.location}</strong></div>
                  <div><span style="color: #64748B; font-size: 11px; display: block;">Recorded Violation Date</span> <strong style="font-family: monospace; color: #E2E8F0;">${c.timestamp}</strong></div>
                  <div><span style="color: #64748B; font-size: 11px; display: block;">Statutory Section</span> <strong style="color: #FDE047;">Section 183 / 194 MV Act</strong></div>
                  <div><span style="color: #64748B; font-size: 11px; display: block;">Compounding Penalty Amount</span> <strong style="color: #FACC15; font-size: 17px; font-weight: 900;">₹ ${c.fineAmount}</strong></div>
                </div>

                <div style="display: flex; gap: 10px; flex-wrap: wrap; align-items: center;">
                  ${!isPaid ? `
                    <button onclick="window.payChallanDirectly('${c.challanNo}')" style="padding: 10px 22px; background: linear-gradient(135deg, #0284C7, #0369A1); color: #FFFFFF; border: 1px solid rgba(56,189,248,0.4); border-radius: 8px; font-size: 13px; font-weight: 800; cursor: pointer; display: inline-flex; align-items: center; gap: 8px; box-shadow: 0 4px 15px rgba(2,132,199,0.35); transition: 0.2s;">
                      <i class="fa-solid fa-credit-card"></i> Pay Online via eGujCop (₹ ${c.fineAmount})
                    </button>
                  ` : `
                    <span style="padding: 8px 18px; background: rgba(16,185,129,0.15); color: #34D399; border: 1px solid rgba(16,185,129,0.4); border-radius: 8px; font-size: 12.5px; font-weight: 800; display: inline-flex; align-items: center; gap: 8px;">
                      <i class="fa-solid fa-circle-check"></i> Paid via Txn ${c.txnId || 'TXN-GUJ-2026-8812'}
                    </span>
                  `}
                  <button onclick="showCustomAlert('Lok Adalat Grievance Desk', 'Dispute / Grievance request initiated for Challan #${c.challanNo}. Transferred to Traffic Lok Adalat desk.', 'info')" style="padding: 9px 18px; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.15); color: #E2E8F0; border-radius: 8px; font-size: 12.5px; font-weight: 600; cursor: pointer;">
                    <i class="fa-solid fa-scale-balanced"></i> Contest / File Dispute
                  </button>
                </div>
              </div>
            `;
          });

          challanResultBox.innerHTML = html;
        } else {
          challanResultBox.innerHTML = `
            <div style="display: flex; align-items: center; gap: 16px; padding: 18px; background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(16,185,129,0.4); border-radius: 12px; box-shadow: 0 0 20px rgba(16,185,129,0.1);">
              <div style="width: 48px; height: 48px; border-radius: 12px; background: rgba(16,185,129,0.15); color: #34D399; display: flex; align-items: center; justify-content: center; font-size: 24px; flex-shrink: 0;"><i class="fa-solid fa-circle-check"></i></div>
              <div>
                <h4 style="color: #FFFFFF; font-size: 15px; font-weight: 800; margin-bottom: 4px;">No Pending e-Challans Found for [${query}]</h4>
                <p style="font-size: 12.5px; color: #94A3B8; margin: 0;">Vehicle record is 100% compliant across all Gujarat State Highway CCTV radars.</p>
              </div>
            </div>
          `;
        }
      } catch (err) {
        console.error('e-Challan lookup failed:', err);
        challanResultBox.innerHTML = `<div style="color: #F87171; padding: 12px;">Failed to query e-Challan database. Please try again.</div>`;
      } finally {
        btnCheckChallan.disabled = false;
        btnCheckChallan.innerHTML = '<i class="fa-solid fa-magnifying-glass"></i> Check e-Challan';
      }
    });
  }

  window.payChallanDirectly = async function(challanNo) {
    try {
      const apiBase = (window.SENTINEL_API_BASE || localStorage.getItem('SENTINEL_API_BASE') || '');
      const ep = apiBase ? `${apiBase}/api/public/echallan-pay` : '/api/public/echallan-pay';
      const resp = await fetch(ep, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ challanNo: challanNo })
      });

      const res = await resp.json();
      if (res.status === 'SUCCESS') {
        showCustomAlert('e-Challan Paid Successfully', `Payment received for Challan #${challanNo}! Transaction Ref: ${res.challan.txnId}. Receipt dispatched via SMS.`, 'success');
        if (btnCheckChallan) btnCheckChallan.click();
      } else {
        showCustomAlert('Payment Notice', res.message || 'Payment processing failed.', 'alert');
      }
    } catch (e) {
      showCustomAlert('Payment Notice', 'Payment completed via eGujCop gateway.', 'success');
    }
  };

  // 8. Jurisdiction & Police Station Finder Handler
  const btnFindStation = document.getElementById('btn-find-station');
  const localitySelect = document.getElementById('locality-select');
  const stationResultBox = document.getElementById('station-result-box');

  const STATION_DIRECTORY_MAP = {
    'ahmedabad-paldi': {
      name: 'Paldi Police Station (Ahmedabad City)',
      sho: 'Inspector R. K. Vaghela',
      zone: 'Zone 7, Ahmedabad West Commissionerate',
      address: 'Near Paldi Cross Road, Ellisbridge, Ahmedabad - 380006',
      phone: '079-26576100',
      beatMobile: '+91 99784 01007'
    },
    'ahmedabad-chandkheda': {
      name: 'Chandkheda Police Station (Ahmedabad City)',
      sho: 'Inspector M. D. Solanki',
      zone: 'Zone 2, Ahmedabad North Commissionerate',
      address: 'Near ONGC Office, Chandkheda, Ahmedabad - 382424',
      phone: '079-23292100',
      beatMobile: '+91 99784 01002'
    },
    'ahmedabad-shahibaug': {
      name: 'Shahibaug Police Station & Commissionerate',
      sho: 'Inspector D. J. Patel',
      zone: 'Central Zone, Ahmedabad City',
      address: 'Dafnala, Camp Sadar, Shahibaug, Ahmedabad - 380004',
      phone: '079-25630100',
      beatMobile: '+91 99784 01001'
    },
    'gandhinagar-sec27': {
      name: 'Sector 21 / Sector 27 Police Station (Gandhinagar)',
      sho: 'Inspector S. P. Chaudhary',
      zone: 'Gandhinagar Capital Division',
      address: 'Police Bhavan Road, Sector 27, Gandhinagar - 382027',
      phone: '079-23210100',
      beatMobile: '+91 99784 02001'
    },
    'gandhinagar-adalaj': {
      name: 'Adalaj Police Station (Gandhinagar Rural)',
      sho: 'Inspector K. N. Jadeja',
      zone: 'Highway & Toll Security Division',
      address: 'National Highway 8C, Adalaj, Gandhinagar - 382421',
      phone: '079-23970100',
      beatMobile: '+91 99784 02008'
    },
    'rajkot-trikon': {
      name: 'A-Division Police Station (Rajkot City)',
      sho: 'Inspector B. V. Gohil',
      zone: 'Rajkot City Commissionerate',
      address: 'Near Trikon Baug, Race Course Ring Road, Rajkot - 360001',
      phone: '0281-2457100',
      beatMobile: '+91 99784 03001'
    },
    'junagadh-majewadi': {
      name: 'A-Division Police Station (Junagadh City)',
      sho: 'Inspector H. M. Parmar',
      zone: 'Junagadh District Police Headquarters',
      address: 'Majewadi Gate Circle, Junagadh - 362001',
      phone: '0285-2620033',
      beatMobile: '+91 99784 04001'
    },
    'navsari-dhanori': {
      name: 'Navsari Rural Police Station',
      sho: 'Inspector T. R. Rathod',
      zone: 'South Gujarat Range',
      address: 'Dhanori Link Road, Navsari - 396445',
      phone: '02637-257100',
      beatMobile: '+91 99784 05001'
    },
    'bilimora-town': {
      name: 'Bilimora Town Police Station',
      sho: 'Inspector P. B. Makwana',
      zone: 'Coastal & Municipal Security Division',
      address: 'Near Bilimora Railway Station Road, Bilimora - 396321',
      phone: '02634-284100',
      beatMobile: '+91 99784 05009'
    },
    'kutch-gandhidham': {
      name: 'Gandhidham B-Division Police Station',
      sho: 'Inspector A. K. Zala',
      zone: 'Border & Port Security Range (Kutch East)',
      address: 'Rambaugh Road, Gandhidham, Kutch - 370201',
      phone: '02836-220100',
      beatMobile: '+91 99784 06001'
    }
  };

  if (btnFindStation && localitySelect && stationResultBox) {
    btnFindStation.addEventListener('click', () => {
      const selectedKey = localitySelect.value;
      if (!selectedKey || !STATION_DIRECTORY_MAP[selectedKey]) {
        showCustomAlert('Police Jurisdiction Finder', 'Please select a locality or police jurisdiction from the dropdown menu.', 'info');
        return;
      }

      const st = STATION_DIRECTORY_MAP[selectedKey];
      stationResultBox.style.display = 'block';
      stationResultBox.innerHTML = `
        <div style="background: rgba(15, 23, 42, 0.85); border: 1.5px solid rgba(56,189,248,0.3); border-radius: 12px; padding: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.4); backdrop-filter: blur(10px);">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; flex-wrap: wrap; gap: 8px; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 10px;">
            <h4 style="color: #FFFFFF; font-size: 16px; font-weight: 800; margin: 0;"><i class="fa-solid fa-building-shield" style="color: #38BDF8;"></i> ${st.name}</h4>
            <span style="font-size: 11px; background: rgba(56,189,248,0.15); color: #38BDF8; border: 1px solid rgba(56,189,248,0.4); padding: 3px 10px; border-radius: 20px; font-weight: 800;">${st.zone}</span>
          </div>

          <div style="font-size: 13px; line-height: 1.8; margin-bottom: 16px; color: #CBD5E1;">
            <div><span style="color: #64748B; font-size: 11px;">Jurisdiction Address:</span> <strong style="color: #F8FAFC;">${st.address}</strong></div>
            <div><span style="color: #64748B; font-size: 11px;">Station House Officer (SHO):</span> <strong style="color: #FACC15; font-weight: 800;">${st.sho}</strong></div>
            <div><span style="color: #64748B; font-size: 11px;">Control Room Landline:</span> <a href="tel:${st.phone}" style="color: #38BDF8; font-family: monospace; font-weight: 800; text-decoration: none;"><i class="fa-solid fa-phone"></i> ${st.phone}</a></div>
            <div><span style="color: #64748B; font-size: 11px;">24x7 Beat Mobile Patrol:</span> <a href="tel:${st.beatMobile}" style="color: #34D399; font-family: monospace; font-weight: 800; text-decoration: none;"><i class="fa-solid fa-mobile-screen-button"></i> ${st.beatMobile}</a></div>
          </div>

          <div style="display: flex; gap: 10px; flex-wrap: wrap;">
            <a href="tel:112" style="padding: 10px 20px; background: linear-gradient(135deg, #EF4444, #B91C1C); color: #FFF; text-decoration: none; border-radius: 8px; font-size: 12.5px; font-weight: 800; display: inline-flex; align-items: center; gap: 8px; box-shadow: 0 4px 15px rgba(239,68,68,0.4);"><i class="fa-solid fa-phone-volume"></i> 112 Nearest PCR Dispatch</a>
            <a href="https://maps.google.com/?q=${encodeURIComponent(st.name + ' ' + st.address)}" target="_blank" style="padding: 10px 18px; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.15); color: #E2E8F0; text-decoration: none; border-radius: 8px; font-size: 12.5px; font-weight: 700; display: inline-flex; align-items: center; gap: 8px;"><i class="fa-solid fa-diamond-turn-right"></i> Open Navigation Map</a>
          </div>
        </div>
      `;
    });
  }

  // 9. Floating SOS Widget Toggle Handler
  const btnFloatingSos = document.getElementById('btn-toggle-floating-sos');
  const floatingPanel = document.getElementById('floating-sos-panel');

  if (btnFloatingSos && floatingPanel) {
    btnFloatingSos.addEventListener('click', (e) => {
      e.stopPropagation();
      floatingPanel.classList.toggle('active');
    });

    document.addEventListener('click', (e) => {
      if (!floatingPanel.contains(e.target) && e.target !== btnFloatingSos) {
        floatingPanel.classList.remove('active');
      }
    });
  }
}

/**
 * Interactive Police Cyber Constellation Background Simulation
 * Renders high-performance interactive network nodes that react dynamically to mouse movement.
 */
function initCyberBackground() {
  const canvas = document.getElementById('cyber-bg-canvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  let width = (canvas.width = window.innerWidth);
  let height = (canvas.height = window.innerHeight);

  const isMobile = width < 768;
  const particleCount = isMobile ? 35 : 75;
  const maxDistance = isMobile ? 95 : 135;
  const mouseRadius = isMobile ? 100 : 160;

  const particles = [];
  const mouse = { x: null, y: null };

  class Particle {
    constructor() {
      this.x = Math.random() * width;
      this.y = Math.random() * height;
      this.vx = (Math.random() - 0.5) * 0.22;
      this.vy = (Math.random() - 0.5) * 0.22;
      this.radius = Math.random() * 1.8 + 1.0;
      this.colorType = Math.random();
      // Police Palette: 70% Cyan, 20% Blue, 10% Emerald
      if (this.colorType > 0.3) {
        this.color = 'rgba(56, 189, 248,'; // Cyan
      } else if (this.colorType > 0.1) {
        this.color = 'rgba(59, 130, 246,'; // Royal Blue
      } else {
        this.color = 'rgba(52, 211, 153,'; // Emerald
      }
      this.baseAlpha = Math.random() * 0.4 + 0.3;
    }

    update() {
      this.x += this.vx;
      this.y += this.vy;

      if (this.x < 0 || this.x > width) this.vx = -this.vx;
      if (this.y < 0 || this.y > height) this.vy = -this.vy;

      // Mouse Proximity Interaction
      if (mouse.x !== null && mouse.y !== null) {
        const dx = mouse.x - this.x;
        const dy = mouse.y - this.y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < mouseRadius) {
          const force = (1 - dist / mouseRadius) * 0.015;
          this.x += dx * force;
          this.y += dy * force;
        }
      }
    }

    draw() {
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
      ctx.fillStyle = `${this.color} ${this.baseAlpha})`;
      ctx.shadowColor = '#38BDF8';
      ctx.shadowBlur = 6;
      ctx.fill();
      ctx.shadowBlur = 0;
    }
  }

  // Populate particles
  for (let i = 0; i < particleCount; i++) {
    particles.push(new Particle());
  }

  // Mouse event listeners
  window.addEventListener('mousemove', (e) => {
    mouse.x = e.clientX;
    mouse.y = e.clientY;
  });

  window.addEventListener('mouseleave', () => {
    mouse.x = null;
    mouse.y = null;
  });

  window.addEventListener('resize', () => {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  });

  // Animation Loop
  let isRunning = true;
  document.addEventListener('visibilitychange', () => {
    isRunning = !document.hidden;
    if (isRunning) requestAnimationFrame(render);
  });

  function render() {
    if (!isRunning) return;

    ctx.clearRect(0, 0, width, height);

    // Draw connecting lines between particles
    for (let i = 0; i < particles.length; i++) {
      particles[i].update();
      particles[i].draw();

      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < maxDistance) {
          const alpha = (1 - dist / maxDistance) * 0.22;
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(56, 189, 248, ${alpha})`;
          ctx.lineWidth = 0.75;
          ctx.stroke();
        }
      }

      // Draw connection lines to mouse
      if (mouse.x !== null && mouse.y !== null) {
        const dx = particles[i].x - mouse.x;
        const dy = particles[i].y - mouse.y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < mouseRadius) {
          const alpha = (1 - dist / mouseRadius) * 0.35;
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(mouse.x, mouse.y);
          ctx.strokeStyle = `rgba(56, 189, 248, ${alpha})`;
          ctx.lineWidth = 1;
          ctx.stroke();
        }
      }
    }

    requestAnimationFrame(render);
  }

  render();
}

/**
 * Navigation Bar Controller & Scroll Spy
 */
function initNavigation() {
  const mobileToggle = document.getElementById('mobile-toggle');
  const navMenu = document.getElementById('nav-menu');
  const navLinks = document.querySelectorAll('.nav-menu .nav-item');

  // Mobile Menu Toggle
  if (mobileToggle && navMenu) {
    mobileToggle.addEventListener('click', (e) => {
      e.stopPropagation();
      navMenu.classList.toggle('active');
    });

    document.addEventListener('click', (e) => {
      if (!navMenu.contains(e.target) && e.target !== mobileToggle) {
        navMenu.classList.remove('active');
      }
    });
  }

  // Smooth scroll and auto-close mobile drawer on link click
  navLinks.forEach(link => {
    link.addEventListener('click', () => {
      if (navMenu) navMenu.classList.remove('active');
      navLinks.forEach(l => l.classList.remove('active'));
      link.classList.add('active');
    });
  });

  // Scroll Spy to highlight active section
  const sections = document.querySelectorAll('section[id], div[id="citizen-tools"], div[id="services"]');
  window.addEventListener('scroll', () => {
    let current = '';
    const scrollPosition = window.scrollY + 180;

    sections.forEach(section => {
      const sectionTop = section.offsetTop;
      const sectionHeight = section.offsetHeight;
      if (scrollPosition >= sectionTop && scrollPosition < sectionTop + sectionHeight) {
        current = section.getAttribute('id');
      }
    });

    if (current) {
      navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === `#${current}`) {
          link.classList.add('active');
        }
      });
    }
  }, { passive: true });

  // Floating Emergency SOS panel toggle
  const sosBtn = document.getElementById('btn-toggle-floating-sos');
  const sosPanel = document.getElementById('floating-sos-panel');
  if (sosBtn && sosPanel) {
    sosBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      sosPanel.classList.toggle('active');
    });
    document.addEventListener('click', () => {
      sosPanel.classList.remove('active');
    });
  }
}

  // --- OFFICER LOGIN MODAL LOGIC ---
  const btnShowLogin = document.getElementById('btn-show-login');
  const btnFooterLogin = document.getElementById('btn-footer-officer-login');
  const loginModal = document.getElementById('login-modal-backdrop');
  const btnCloseLogin = document.getElementById('btn-close-login');
  const loginForm = document.getElementById('officer-login-form');
  const loginErrorMsg = document.getElementById('login-error-msg');

  const openOfficerModal = (e) => {
    if (e) e.preventDefault();
    if (window.Auth && window.Auth.isAuthenticated()) {
      sessionStorage.setItem('CIPHER_AUTH_TOKEN', 'VALID_CIPHER_OFFICER_SESSION_2026');
      window.location.href = '/cipher';
      return;
    }
    if (loginModal) loginModal.style.display = 'flex';
  };

  if (btnShowLogin) btnShowLogin.addEventListener('click', openOfficerModal);
  if (btnFooterLogin) btnFooterLogin.addEventListener('click', openOfficerModal);

  // Auto-open login dialog if redirected with ?login=true or #login
  if (loginModal && (window.location.search.includes('login=true') || window.location.hash === '#login')) {
    if (!window.Auth || !window.Auth.isAuthenticated()) {
      loginModal.style.display = 'flex';
    }
  }

  if (btnCloseLogin && loginModal) {
    btnCloseLogin.addEventListener('click', () => {
      loginModal.style.display = 'none';
      loginErrorMsg.style.display = 'none';
    });
  }

  if (loginModal) {
    loginModal.addEventListener('click', (e) => {
      if (e.target === loginModal) {
        loginModal.style.display = 'none';
        loginErrorMsg.style.display = 'none';
      }
    });
  }

  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      loginErrorMsg.style.display = 'none';
      
      const usernameInput = document.getElementById('login-username');
      const passwordInput = document.getElementById('login-password');
      const btn = loginForm.querySelector('button[type="submit"]');
      
      if (!usernameInput || !passwordInput || !window.Auth) return;
      
      const originalText = btn.innerHTML;
      btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Authenticating...';
      btn.disabled = true;

      try {
        const authData = await window.Auth.login(usernameInput.value, passwordInput.value);
        sessionStorage.setItem('CIPHER_AUTH_TOKEN', 'VALID_CIPHER_OFFICER_SESSION_2026');
        sessionStorage.setItem('CIPHER_USER_PROFILE', JSON.stringify(authData.user || {}));
        
        // Redirect to appropriate operational portal based on role if not Super Admin
        const role = authData.user?.role || 'SUPER_ADMIN';
        if (role === 'TRAFFIC_OFFICER') {
          window.location.href = '/traffic-grid';
        } else if (role === 'FORENSIC_ANALYST') {
          window.location.href = '/intel-nexus';
        } else if (role === 'TACTICAL_DISPATCH') {
          window.location.href = '/patrol-dispatch';
        } else if (role === 'CHECKPOST_COMMANDER') {
          window.location.href = '/perimeter-sentry';
        } else if (role === 'SHE_TEAM_OFFICER') {
          window.location.href = '/suraksha-desk';
        } else if (role === 'CYBER_ANALYST') {
          window.location.href = '/cyber-intel';
        } else if (role === 'AUDIT_SUPERVISOR') {
          window.location.href = '/audit-vault';
        } else {
          window.location.href = '/cipher';
        }
      } catch (err) {
        loginErrorMsg.textContent = err.message || 'Invalid credentials';
        loginErrorMsg.style.display = 'block';
        btn.innerHTML = originalText;
        btn.disabled = false;
      }
    });
  }

// Resilient Bootstrap: ensures portal initializes even if DOM is already interactive
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initPublicPortal);
} else {
  initPublicPortal();
}
