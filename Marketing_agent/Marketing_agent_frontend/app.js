(() => {
  'use strict';

  const CONFIG = { apiBase: 'https://ridgeline-8ylq.onrender.com' };

  const $ = (sel, ctx = document) => ctx.querySelector(sel);
  const $$ = (sel, ctx = document) => Array.from(ctx.querySelectorAll(sel));

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- helpers ---------- */
  function escapeHtml(str) {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function formatText(raw) {
    if (!raw) return '';
    const lines = raw.replace(/\r\n/g, '\n').split('\n');
    let html = '';
    let inList = false;
    const closeList = () => { if (inList) { html += '</ul>'; inList = false; } };

    for (let line of lines) {
      const trimmed = line.trim();
      if (!trimmed) { closeList(); continue; }
      const bulletMatch = trimmed.match(/^[-*•]\s+(.*)/);
      const numberMatch = trimmed.match(/^\d+[.)]\s+(.*)/);
      if (bulletMatch || numberMatch) {
        if (!inList) { html += '<ul class="fmt-list">'; inList = true; }
        html += `<li>${escapeHtml(bulletMatch ? bulletMatch[1] : numberMatch[1])}</li>`;
        continue;
      }
      closeList();
      if (/^(Subject|Variant \d+):/i.test(trimmed)) {
        html += `<p class="fmt-label">${escapeHtml(trimmed)}</p>`;
        continue;
      }
      html += `<p>${escapeHtml(trimmed)}</p>`;
    }
    closeList();
    return html;
  }

  const CHANNEL_META = {
    poster_image: { title: 'Generated Poster', tag: 'Poster Asset' },
    tagline_whatsapp: { title: 'WhatsApp Tagline', tag: 'Hook' },
    tagline_instagram: { title: 'Instagram Tagline', tag: 'Hook' },
    tagline_email: { title: 'Email Subject', tag: 'Hook' },
    tagline_linkedin: { title: 'LinkedIn Tagline', tag: 'Hook' },
    instagram_poster: { title: 'Instagram Caption', tag: 'Social Copy' },
    whatsapp_message: { title: 'WhatsApp Message', tag: 'Broadcast Copy' },
    email: { title: 'Email Invitation', tag: 'Email Copy' },
    linkedin_post: { title: 'LinkedIn Post', tag: 'Professional Copy' },
    unstop_copy: { title: 'Unstop Hackathon Listing', tag: 'Platform Form Copy' },
    devpost_copy: { title: 'Devpost Hackathon Listing', tag: 'Platform Form Copy' },
    hackerearth_copy: { title: 'HackerEarth Hackathon Listing', tag: 'Platform Form Copy' },
  };
  const CHANNEL_ORDER = [
    'poster_image',
    'tagline_whatsapp',
    'tagline_instagram',
    'tagline_email',
    'tagline_linkedin',
    'instagram_poster',
    'whatsapp_message',
    'email',
    'linkedin_post',
    'unstop_copy',
    'devpost_copy',
    'hackerearth_copy'
  ];

  function copyBtnHtml() {
    return `<button type="button" class="copy-btn" data-copy>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
      <span>Copy</span>
    </button>`;
  }

  function wireCopyButtons(container) {
    $$('[data-copy]', container).forEach(btn => {
      btn.addEventListener('click', () => {
        const text = btn.closest('.content-card, .result-card').dataset.rawText || '';
        navigator.clipboard.writeText(text).then(() => {
          const label = $('span', btn);
          const original = label.textContent;
          label.textContent = 'Copied';
          setTimeout(() => { label.textContent = original; }, 1400);
        });
      });
    });
  }

  /* ---------- status / health ---------- */
  const statusPill = $('#statusPill');
  const statusText = $('#statusText');
  const apiInput = $('#apiBaseInput');

  async function checkHealth() {
    statusPill.dataset.state = 'checking';
    statusText.textContent = 'Checking';
    try {
      const res = await fetch(CONFIG.apiBase + '/', { method: 'GET' });
      if (!res.ok) throw new Error('bad status');
      statusPill.dataset.state = 'online';
      statusText.textContent = 'Connected';
    } catch (err) {
      statusPill.dataset.state = 'offline';
      statusText.textContent = 'Offline';
    }
  }

  $('#settingsToggle').addEventListener('click', () => {
    $('#settingsPanel').classList.toggle('is-open');
  });

  const smtpServerInput = $('#smtpServerInput');
  const smtpPortInput = $('#smtpPortInput');
  const smtpSenderInput = $('#smtpSenderInput');
  const smtpPasswordInput = $('#smtpPasswordInput');
  const smtpConductorInput = $('#smtpConductorInput');

  function saveSmtpSettings() {
    const settings = {
      server: smtpServerInput ? smtpServerInput.value.trim() : '',
      port: smtpPortInput ? smtpPortInput.value.trim() : '',
      sender: smtpSenderInput ? smtpSenderInput.value.trim() : '',
      password: smtpPasswordInput ? smtpPasswordInput.value.trim() : '',
      conductor_email: smtpConductorInput ? smtpConductorInput.value.trim() : ''
    };
    localStorage.setItem('ridgeline_smtp_settings', JSON.stringify(settings));
  }

  function loadSmtpSettings() {
    try {
      const raw = localStorage.getItem('ridgeline_smtp_settings');
      if (raw) {
        const settings = JSON.parse(raw);
        if (smtpServerInput) smtpServerInput.value = settings.server || '';
        if (smtpPortInput) smtpPortInput.value = settings.port || '';
        if (smtpSenderInput) smtpSenderInput.value = settings.sender || '';
        if (smtpPasswordInput) smtpPasswordInput.value = settings.password || '';
        if (smtpConductorInput) smtpConductorInput.value = settings.conductor_email || '';
      }
    } catch (e) {
      console.error("Error loading SMTP settings:", e);
    }
  }

  function getSmtpSettings() {
    return {
      server: smtpServerInput ? smtpServerInput.value.trim() : '',
      port: smtpPortInput ? smtpPortInput.value.trim() : '',
      sender: smtpSenderInput ? smtpSenderInput.value.trim() : '',
      password: smtpPasswordInput ? smtpPasswordInput.value.trim() : '',
      conductor_email: smtpConductorInput ? smtpConductorInput.value.trim() : ''
    };
  }

  [smtpServerInput, smtpPortInput, smtpSenderInput, smtpPasswordInput, smtpConductorInput].forEach(el => {
    if (el) el.addEventListener('change', saveSmtpSettings);
  });

  loadSmtpSettings();

  /* ---------- social sharing ---------- */
  const socialShareCard = $('#socialShareCard');
  const shareTabInsta = $('#shareTabInsta');
  const shareTabLinkedin = $('#shareTabLinkedin');
  const shareCaptionInput = $('#shareCaptionInput');
  const shareUserInput = $('#shareUserInput');
  const sharePassInput = $('#sharePassInput');
  const shareUserLabel = $('#shareUserLabel');
  const sharePassLabel = $('#sharePassLabel');
  const shareDemoModeInput = $('#shareDemoModeInput');
  const shareSubmitBtn = $('#shareSubmitBtn');
  const shareStatusMessage = $('#shareStatusMessage');

  let activePlatform = 'instagram';
  let generatedData = null;

  function selectSharePlatform(platform) {
    activePlatform = platform;
    if (shareStatusMessage) shareStatusMessage.hidden = true;
    
    if (platform === 'instagram') {
      if (shareTabInsta) { shareTabInsta.className = 'btn btn-primary'; shareTabInsta.style.justifyContent = 'center'; }
      if (shareTabLinkedin) { shareTabLinkedin.className = 'btn btn-ghost'; shareTabLinkedin.style.justifyContent = 'center'; }
      
      if (shareUserLabel) shareUserLabel.textContent = 'Instagram Username';
      if (shareUserInput) { shareUserInput.placeholder = 'e.g. hackathon_organizer'; shareUserInput.value = ''; }
      if (sharePassLabel) sharePassLabel.textContent = 'Instagram Password';
      if (sharePassInput) { sharePassInput.placeholder = '••••••••'; sharePassInput.value = ''; sharePassInput.type = 'password'; }
      
      if (shareSubmitBtn) shareSubmitBtn.querySelector('.btn-label').textContent = 'Post to Instagram';
      
      if (generatedData && shareCaptionInput) {
        shareCaptionInput.value = generatedData.instagram_poster || generatedData.tagline_instagram || '';
      }
    } else {
      if (shareTabInsta) { shareTabInsta.className = 'btn btn-ghost'; shareTabInsta.style.justifyContent = 'center'; }
      if (shareTabLinkedin) { shareTabLinkedin.className = 'btn btn-primary'; shareTabLinkedin.style.justifyContent = 'center'; }
      
      if (shareUserLabel) shareUserLabel.textContent = 'LinkedIn Access Token';
      if (shareUserInput) { shareUserInput.placeholder = 'e.g. AQW... (Bearer Token)'; shareUserInput.value = ''; }
      if (sharePassLabel) sharePassLabel.textContent = 'LinkedIn Person URN';
      if (sharePassInput) { sharePassInput.placeholder = 'e.g. 12345678 (URN)'; sharePassInput.value = ''; sharePassInput.type = 'text'; }
      
      if (shareSubmitBtn) shareSubmitBtn.querySelector('.btn-label').textContent = 'Post to LinkedIn';
      
      if (generatedData && shareCaptionInput) {
        shareCaptionInput.value = generatedData.linkedin_post || generatedData.tagline_linkedin || '';
      }
    }
  }

  function runSimulatedPublish(platformName, logContainer) {
    if (!logContainer) return;
    logContainer.style.display = 'block';
    logContainer.innerHTML = '';
    logContainer.style.color = 'var(--lavender)';
    
    const logs = [
      `[1/5] Opening browser instance for ${platformName}...`,
      `[2/5] Navigating to ${platformName} creation form...`,
      `[3/5] Automating form fields: copying Title, Theme, and Guidelines...`,
      `[4/5] Attaching composed poster asset from cache...`,
      `[5/5] Submitting listing draft for approval...`,
      `✨ [SUCCESS] Hackathon listed successfully on ${platformName}! (Demo simulated)`
    ];
    
    let index = 0;
    function printNext() {
      if (index < logs.length) {
        const p = document.createElement('p');
        p.style.margin = '4px 0';
        p.style.fontFamily = 'var(--font-mono)';
        p.style.fontSize = '0.78rem';
        p.style.lineHeight = '1.3';
        if (index === logs.length - 1) {
          p.style.color = '#8FD4A8';
          p.style.fontWeight = 'bold';
        }
        p.textContent = logs[index];
        logContainer.appendChild(p);
        index++;
        setTimeout(printNext, 800);
      }
    }
    printNext();
  }
  window.runSimulatedPublish = runSimulatedPublish;

  if (shareTabInsta && shareTabLinkedin) {
    shareTabInsta.addEventListener('click', () => selectSharePlatform('instagram'));
    shareTabLinkedin.addEventListener('click', () => selectSharePlatform('linkedin'));
  }

  if (shareSubmitBtn) {
    shareSubmitBtn.addEventListener('click', async () => {
      const username = shareUserInput.value.trim();
      const password = sharePassInput.value.trim();
      const caption = shareCaptionInput.value.trim();
      const demoMode = shareDemoModeInput ? shareDemoModeInput.checked : false;

      if (!username || !password || !caption) {
        if (shareStatusMessage) {
          shareStatusMessage.style.color = 'var(--coral)';
          shareStatusMessage.textContent = 'Please fill in all the details, boss!';
          shareStatusMessage.hidden = false;
        }
        return;
      }

      shareSubmitBtn.disabled = true;
      shareSubmitBtn.dataset.loading = 'true';
      if (shareStatusMessage) {
        shareStatusMessage.style.color = 'var(--lavender)';
        shareStatusMessage.textContent = demoMode ? 'Simulating post upload...' : 'Connecting to API...';
        shareStatusMessage.hidden = false;
      }

      try {
        const res = await fetch(CONFIG.apiBase + '/api/share-social-media', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            platform: activePlatform,
            username: username,
            password: password,
            caption: caption,
            confirm_post: true,
            demo_mode: demoMode
          })
        });

        const resData = await res.json();
        if (!res.ok) throw new Error(resData.detail || 'Posting failed.');

        if (shareStatusMessage) {
          shareStatusMessage.style.color = '#8FD4A8';
          shareStatusMessage.textContent = resData.message || 'Successfully posted!';
        }
      } catch (err) {
        if (shareStatusMessage) {
          shareStatusMessage.style.color = 'var(--coral)';
          shareStatusMessage.textContent = err.message || 'Error occurred while sharing.';
        }
      } finally {
        shareSubmitBtn.disabled = false;
        shareSubmitBtn.dataset.loading = 'false';
      }
    });
  }

  apiInput.value = CONFIG.apiBase;
  apiInput.addEventListener('change', () => {
    const val = apiInput.value.trim().replace(/\/+$/, '');
    if (val) { CONFIG.apiBase = val; updateFooter(); checkHealth(); }
  });

  /* ---------- relay pulse ---------- */
  function animateRelay(pathEl, dotEl, duration = 1400) {
    if (!pathEl || !dotEl) return () => {};
    const len = pathEl.getTotalLength();
    let cancelled = false;
    let raf;
    let loopStart = null;

    function loop(ts) {
      if (cancelled) return;
      if (loopStart === null) loopStart = ts;
      const t = ((ts - loopStart) % duration) / duration;
      const point = pathEl.getPointAtLength(t * len);
      dotEl.setAttribute('cx', point.x);
      dotEl.setAttribute('cy', point.y);
      dotEl.setAttribute('opacity', '1');
      raf = requestAnimationFrame(loop);
    }
    raf = requestAnimationFrame(loop);
    return () => { cancelled = true; cancelAnimationFrame(raf); dotEl.setAttribute('opacity', '0'); };
  }

  /* ---------- 1. Launch kit generator ---------- */
  const kitForm = $('#kitForm');
  const kitButton = $('#kitBtn');
  const kitEmpty = $('#kitEmpty');
  const kitResults = $('#kitResults');
  const kitGrid = $('#kitGrid');
  const kitError = $('#kitError');
  const kitRelayPath = $('#kitRelayPath');
  const kitRelayDot = $('#kitRelayDot');

  let stopKitRelay = null;

  kitForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const payload = {
      name: $('#kitNameInput').value.trim(),
      theme: $('#kitThemeInput').value.trim(),
      audience: $('#kitAudienceInput').value,
      rounds: parseInt($('#kitRoundsInput').value, 10) || 1,
      venue: $('#kitVenueInput') ? $('#kitVenueInput').value.trim() : "",
      insta_id: $('#kitInstaInput') ? $('#kitInstaInput').value.trim() : "",
      linkedin_id: $('#kitLinkedinInput') ? $('#kitLinkedinInput').value.trim() : "",
    };

    kitButton.disabled = true;
    kitButton.dataset.loading = 'true';
    kitEmpty.hidden = true;
    kitResults.hidden = false;
    kitResults.dataset.state = 'loading';
    kitGrid.innerHTML = Array.from({ length: 4 }).map(() =>
      `<div class="content-card"><div class="skeleton"></div><div class="skeleton"></div><div class="skeleton short"></div></div>`
    ).join('');

    if (socialShareCard) {
      socialShareCard.style.display = 'none';
    }

    if (!reduceMotion) stopKitRelay = animateRelay(kitRelayPath, kitRelayDot);

    try {
      const res = await fetch(CONFIG.apiBase + '/api/generate-launch-kit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'The relay failed.');

      kitGrid.innerHTML = CHANNEL_ORDER.map(k => {
        const meta = CHANNEL_META[k];
        const title = meta ? meta.title : k.replace(/_/g, ' ').toUpperCase();
        const text = data[k];
        if (!text) return '';

        // Special rendering for poster
        if (k === 'poster_image') {
          return `
            <div class="content-card" style="grid-column: 1 / -1; display: flex; flex-direction: column; align-items: center; gap: 16px;">
              <div class="content-card-head" style="width: 100%;">
                <h3 class="content-card-title">${escapeHtml(title)}</h3>
                <a href="${text}" download="hackathon_poster.jpg" class="copy-btn" style="text-decoration: none;">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" style="width:13px;height:13px;"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>
                  <span>Download Poster</span>
                </a>
              </div>
              <div class="poster-preview" style="position: relative; border-radius: var(--radius-md); overflow: hidden; border: 1px solid rgba(251,241,236,0.18); max-width: 100%; width: 400px; box-shadow: 0 12px 28px rgba(0,0,0,0.5); background: rgba(0,0,0,0.2);">
                <img src="${text}" alt="Generated Poster" style="display: block; width: 100%; height: auto;" />
                <span class="corner tl"></span><span class="corner tr"></span>
                <span class="corner bl"></span><span class="corner br"></span>
              </div>
            </div>`;
        }

        // Special rendering for platform listing copy
        if (k === 'unstop_copy' || k === 'devpost_copy' || k === 'hackerearth_copy') {
          return `
            <div class="content-card" data-raw-text="${escapeHtml(text)}">
              <div class="content-card-head">
                <h3 class="content-card-title">${escapeHtml(title)}</h3>
                ${copyBtnHtml()}
              </div>
              <div class="agent-body">${formatText(text)}</div>
              <button type="button" class="btn btn-ghost" onclick="window.runSimulatedPublish('${title}', this.nextElementSibling)" style="margin-top: 14px; font-size: 0.8rem; padding: 6px 12px; width: 100%; justify-content: center;">
                Publish Listing (Simulated Automation)
              </button>
              <div class="publish-log" style="display: none; background: rgba(0,0,0,0.4); border-radius: 8px; padding: 10px; margin-top: 10px; border: 1px solid rgba(251,241,236,0.1); text-align: left;"></div>
            </div>`;
        }

        return `
          <div class="content-card" data-raw-text="${escapeHtml(text)}">
            <div class="content-card-head">
              <h3 class="content-card-title">${escapeHtml(title)}</h3>
              ${copyBtnHtml()}
            </div>
            <div class="agent-body">${formatText(text)}</div>
          </div>`;
      }).join('');

      wireCopyButtons(kitGrid);
      kitResults.dataset.state = 'ready';
      
      generatedData = data;
      selectSharePlatform(activePlatform);
      if (socialShareCard) {
        socialShareCard.style.display = 'block';
      }

    } catch (err) {
      kitResults.hidden = true;
      kitEmpty.hidden = true;
      kitError.hidden = false;
      $('#kitErrorMsg').textContent = `Couldn't reach the agents at ${CONFIG.apiBase}. Confirm the FastAPI server is running.`;
    } finally {
      kitButton.disabled = false;
      kitButton.dataset.loading = 'false';
      if (stopKitRelay) stopKitRelay();
    }
  });

  /* ---------- 2. Round reminders ---------- */
  const reminderForm = $('#reminderForm');
  const reminderButton = $('#reminderBtn');
  const reminderEmpty = $('#reminderEmpty');
  const reminderResult = $('#reminderResult');
  const reminderError = $('#reminderError');
  const reminderText = $('#reminderText');

  reminderForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    reminderError.hidden = true;
    reminderButton.disabled = true;
    reminderButton.dataset.loading = 'true';
    reminderEmpty.hidden = true;
    reminderResult.hidden = true;

    const payload = {
      round_number: parseInt($('#reminderRoundInput').value, 10) || 1,
      days_left: parseInt($('#reminderDaysInput').value, 10),
      candidate_emails: $('#reminderEmailsInput') ? $('#reminderEmailsInput').value.trim() : "",
      smtp_settings: getSmtpSettings(),
    };

    try {
      const res = await fetch(CONFIG.apiBase + '/api/round-reminder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Reminder generation failed.');
      reminderResult.dataset.rawText = data.message || '';
      reminderText.innerHTML = formatText(data.message || '');
      reminderResult.hidden = false;
      wireCopyButtons(reminderResult);
    } catch (err) {
      reminderError.hidden = false;
      $('#reminderErrorMsg').textContent = `Couldn't reach the agent at ${CONFIG.apiBase}.`;
    } finally {
      reminderButton.disabled = false;
      reminderButton.dataset.loading = 'false';
    }
  });

  /* ---------- 3. Registration pulse ---------- */
  const regForm = $('#regForm');
  const regButton = $('#regBtn');
  const regEmpty = $('#regEmpty');
  const regResults = $('#regResults');
  const regError = $('#regError');
  const orgAlertCard = $('#orgAlertCard');
  const candMsgCard = $('#candMsgCard');

  regForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    regError.hidden = true;
    regButton.disabled = true;
    regButton.dataset.loading = 'true';
    regEmpty.hidden = true;
    regResults.hidden = true;

    const payload = {
      candidate_name: $('#regCandidateInput').value.trim(),
      candidate_email: $('#regEmailInput') ? $('#regEmailInput').value.trim() : "",
      hackathon_name: $('#regHackathonInput').value.trim(),
      total_registrations_today: parseInt($('#regCountInput').value, 10) || 0,
      problem_statement: $('#regProblemInput').value.trim(),
      smtp_settings: getSmtpSettings(),
    };

    try {
      const res = await fetch(CONFIG.apiBase + '/api/registration-event', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Registration update failed.');

      orgAlertCard.dataset.rawText = data.organizer_alert || '';
      $('#orgAlertBody', orgAlertCard).innerHTML = formatText(data.organizer_alert || '');
      candMsgCard.dataset.rawText = data.candidate_message || '';
      $('#candMsgBody', candMsgCard).innerHTML = formatText(data.candidate_message || '');

      regResults.hidden = false;
      wireCopyButtons(regResults);
    } catch (err) {
      regError.hidden = false;
      $('#regErrorMsg').textContent = `Couldn't reach the agent at ${CONFIG.apiBase}.`;
    } finally {
      regButton.disabled = false;
      regButton.dataset.loading = 'false';
    }
  });

  /* ---------- Final Round Scheduler ---------- */
  const schedulerForm = $('#schedulerForm');
  const schedulerButton = $('#schedBtn');
  const schedulerEmpty = $('#schedEmpty');
  const schedulerResults = $('#schedResults');
  const schedulerError = $('#schedError');
  const schedTableBody = $('#schedTableBody');
  const copySchedBtn = $('#copySchedBtn');

  if (schedulerForm) {
    schedulerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (schedulerError) schedulerError.hidden = true;
      if (schedulerButton) {
        schedulerButton.disabled = true;
        schedulerButton.dataset.loading = 'true';
      }
      if (schedulerEmpty) schedulerEmpty.hidden = true;
      if (schedulerResults) schedulerResults.hidden = true;

      const payload = {
        candidates_raw: $('#schedCandidatesInput').value.trim(),
        start_time: $('#schedStartTimeInput').value,
        slot_duration_minutes: parseInt($('#schedDurationInput').value, 10) || 30,
        platform: $('#schedPlatformInput').value,
        confirm_scheduling: true,
        smtp_settings: getSmtpSettings(),
        demo_mode: $('#schedDemoModeInput') ? $('#schedDemoModeInput').checked : true
      };

      try {
        const res = await fetch(CONFIG.apiBase + '/api/schedule-final-round', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Scheduling failed.');

        // Build schedule table rows
        if (schedTableBody) {
          schedTableBody.innerHTML = data.schedule.map(slot => `
            <tr style="border-bottom: 1px solid rgba(251,241,236,0.15);">
              <td style="padding: 10px 4px;"><strong>${escapeHtml(slot.name)}</strong><br><span style="font-size:0.76rem;color:rgba(251,241,236,0.55);">${escapeHtml(slot.email)}</span></td>
              <td style="padding: 10px 4px; font-family:var(--font-mono); font-size:0.8rem; color:var(--lavender);">${escapeHtml(slot.start)}</td>
              <td style="padding: 10px 4px;"><a href="${slot.link}" target="_blank" style="color:var(--coral); text-decoration:underline; font-size:0.8rem;">Join Meeting</a></td>
            </tr>
          `).join('');
        }

        // Enable copy schedule as plain text table
        if (copySchedBtn) {
          const tableText = data.schedule.map(s => `${s.name} (${s.email}) | Slot: ${s.start} | Link: ${s.link}`).join('\n');
          copySchedBtn.onclick = () => {
            navigator.clipboard.writeText(tableText).then(() => {
              const label = copySchedBtn.querySelector('span');
              const original = label.textContent;
              label.textContent = 'Copied!';
              setTimeout(() => { label.textContent = original; }, 1400);
            });
          };
        }

        if (schedulerResults) schedulerResults.hidden = false;
      } catch (err) {
        if (schedulerError) {
          schedulerError.hidden = false;
          $('#schedErrorMsg').textContent = err.message || `Couldn't reach the server.`;
        }
      } finally {
        if (schedulerButton) {
          schedulerButton.disabled = false;
          schedulerButton.dataset.loading = 'false';
        }
      }
    });
  }

  /* ---------- 4. Vision check ---------- */
  const visionForm = $('#visionForm');
  const visionButton = $('#visionBtn');
  const dropzone = $('#dropzone');
  const fileInput = $('#fileInput');
  const previewImg = $('#previewImg');
  const previewWrap = $('#previewWrap');
  const visionResults = $('#visionResults');
  const visionEmpty = $('#visionEmpty');
  const visionError = $('#visionError');
  const visionBody = $('#visionBody');

  let selectedFile = null;

  function setFile(file) {
    if (!file || !file.type.startsWith('image/')) return;
    selectedFile = file;
    previewImg.src = URL.createObjectURL(file);
    previewWrap.hidden = false;
    dropzone.dataset.hasFile = 'true';
  }

  dropzone.addEventListener('click', () => fileInput.click());
  fileInput.addEventListener('change', () => setFile(fileInput.files[0]));
  ['dragenter', 'dragover'].forEach(evt => dropzone.addEventListener(evt, (e) => { e.preventDefault(); dropzone.dataset.drag = 'true'; }));
  ['dragleave', 'drop'].forEach(evt => dropzone.addEventListener(evt, (e) => { e.preventDefault(); dropzone.dataset.drag = 'false'; }));
  dropzone.addEventListener('drop', (e) => setFile(e.dataTransfer.files[0]));

  visionForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    visionError.hidden = true;
    if (!selectedFile) {
      visionError.hidden = false;
      $('#visionErrorMsg').textContent = 'Add an image before sending it up for a read.';
      return;
    }
    const fd = new FormData();
    fd.append('campaign_name', $('#visionCampaignInput').value.trim());
    fd.append('image', selectedFile);

    visionButton.disabled = true;
    visionButton.dataset.loading = 'true';
    visionEmpty.hidden = true;
    visionResults.hidden = false;
    visionBody.innerHTML = '<div class="skeleton"></div><div class="skeleton"></div><div class="skeleton short"></div>';

    try {
      const res = await fetch(CONFIG.apiBase + '/api/analyze-vision-assets', { method: 'POST', body: fd });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'The asset could not be read.');
      visionBody.innerHTML = formatText(data.vision_analysis || '') || '<p>No analysis returned.</p>';
    } catch (err) {
      visionResults.hidden = true;
      visionError.hidden = false;
      $('#visionErrorMsg').textContent = `Couldn't reach the vision agent at ${CONFIG.apiBase}.`;
    } finally {
      visionButton.disabled = false;
      visionButton.dataset.loading = 'false';
    }
  });

  /* ---------- smooth scroll + reveal ---------- */
  $$('[data-scroll-to]').forEach(btn => {
    btn.addEventListener('click', () => {
      const target = $(btn.dataset.scrollTo);
      if (target) target.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'start' });
    });
  });

  const revealEls = $$('[data-reveal]');
  if ('IntersectionObserver' in window && !reduceMotion) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) { entry.target.classList.add('is-visible'); io.unobserve(entry.target); }
      });
    }, { threshold: 0.12 });
    revealEls.forEach(el => io.observe(el));
  } else {
    revealEls.forEach(el => el.classList.add('is-visible'));
  }

  /* ---------- hero parallax ---------- */
  const heroLayers = $$('.ridge-layer');
  const hero = $('#hero');
  if (hero && !reduceMotion) {
    hero.addEventListener('pointermove', (e) => {
      const rect = hero.getBoundingClientRect();
      const px = (e.clientX - rect.left) / rect.width - 0.5;
      const py = (e.clientY - rect.top) / rect.height - 0.5;
      heroLayers.forEach(layer => {
        const depth = parseFloat(layer.dataset.depth || '0');
        layer.style.transform = `translate3d(${px * depth}px, ${py * depth * 0.4}px, 0)`;
      });
    });
  }

  /* ---------- footer / init ---------- */
  const footerApiBase = $('#footerApiBase');
  function updateFooter() { if (footerApiBase) footerApiBase.textContent = CONFIG.apiBase; }

  updateFooter();
  checkHealth();
})();
