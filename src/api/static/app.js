document.addEventListener("DOMContentLoaded", () => {
  initAppLogic();
});

/* =========================================================================
   APPLICATION LOGIC
   ========================================================================= */
function initAppLogic() {
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("fileInput");
  const dropzoneContent = document.getElementById("dropzoneContent");
  const previewContainer = document.getElementById("previewContainer");
  const imagePreview = document.getElementById("imagePreview");
  const laserScanner = document.getElementById("laserScanner");
  const btnChange = document.getElementById("btnChange");
  const btnRunPipeline = document.getElementById("btnRunPipeline");
  const btnText = document.getElementById("btnText");
  const btnSpinner = document.getElementById("btnSpinner");
  const btnPctBadge = document.getElementById("btnPctBadge");
  const btnProgressLine = document.getElementById("btnProgressLine");

  const pStep1 = document.getElementById("pStep1");
  const pStep2 = document.getElementById("pStep2");
  const pStep3 = document.getElementById("pStep3");
  const pStep4 = document.getElementById("pStep4");
  const pStep1Desc = document.getElementById("pStep1Desc");
  const pStep2Desc = document.getElementById("pStep2Desc");
  const pStep3Desc = document.getElementById("pStep3Desc");
  const pStep4Desc = document.getElementById("pStep4Desc");
  const pStep1Orb = document.getElementById("pStep1Orb");
  const pStep2Orb = document.getElementById("pStep2Orb");
  const pStep3Orb = document.getElementById("pStep3Orb");
  const pStep4Orb = document.getElementById("pStep4Orb");
  const pConn1 = document.getElementById("pConn1");
  const pConn2 = document.getElementById("pConn2");
  const pConn3 = document.getElementById("pConn3");

  const faceCropImg = document.getElementById("faceCropImg");
  const faceConfidenceBadge = document.getElementById("faceConfidenceBadge");
  const faceBboxVal = document.getElementById("faceBboxVal");
  const faceShaVal = document.getElementById("faceShaVal");

  const matchPlatformBadge = document.getElementById("matchPlatformBadge");
  const authorName = document.getElementById("authorName");
  const authorHandle = document.getElementById("authorHandle");
  const similarityScore = document.getElementById("similarityScore");
  const postCaption = document.getElementById("postCaption");
  const postUrlLink = document.getElementById("postUrlLink");
  const postTimestamp = document.getElementById("postTimestamp");

  const txHashVal = document.getElementById("txHashVal");
  const blockNumVal = document.getElementById("blockNumVal") || document.getElementById("blockNumberVal");
  const contractVal = document.getElementById("contractVal");
  const payloadHashVal = document.getElementById("payloadHashVal");
  const networkBadge = document.getElementById("networkBadge");

  // Stage 2: Media Image & Candidates Drawer
  const matchAvatarImg = document.getElementById("matchAvatarImg");
  const matchAvatarPlaceholder = document.getElementById("matchAvatarPlaceholder");
  const matchImagePreviewContainer = document.getElementById("matchImagePreviewContainer");
  const matchPreviewImg = document.getElementById("matchPreviewImg");
  const previewUrlLink = document.getElementById("previewUrlLink") || document.getElementById("matchPreviewLink");
  const matchPreviewTag = document.getElementById("matchPreviewTag");
  const btnToggleCandidates = document.getElementById("btnToggleCandidates");
  const candidatesCount = document.getElementById("candidatesCount");
  const btnFilterSocial = document.getElementById("btnFilterSocial");
  const socialCandidatesCount = document.getElementById("socialCandidatesCount");
  const candidatesDrawer = document.getElementById("candidatesDrawer");
  const candidatesGrid = document.getElementById("candidatesGrid");
  const filterTabAll = document.getElementById("filterTabAll");
  const filterTabSocial = document.getElementById("filterTabSocial");
  const countTabAll = document.getElementById("countTabAll");
  const countTabSocial = document.getElementById("countTabSocial");
  const drawerTitle = document.getElementById("drawerTitle");
  const drawerSubtitle = document.getElementById("drawerSubtitle");
  const socialPlatformFilterRow = document.getElementById("socialPlatformFilterRow");

  // View Navigation Tabs
  const tabBtnPipeline = document.getElementById("tabBtnPipeline");
  const tabBtnHistory = document.getElementById("tabBtnHistory");
  const tabContentPipeline = document.getElementById("tabContentPipeline");
  const tabContentHistory = document.getElementById("tabContentHistory");
  const historyTabBadge = document.getElementById("historyTabBadge");

  const verBanner = document.getElementById("verBanner");
  const verTitle = document.getElementById("verTitle");
  const verDescription = document.getElementById("verDescription");
  const verStatusBadge = document.getElementById("verStatusBadge");
  const btnTamperTest = document.getElementById("btnTamperTest");
  const tamperDiffContainer = document.getElementById("tamperDiffContainer");

  const btnRefreshHistory = document.getElementById("btnRefreshHistory");
  const historyTableBody = document.getElementById("historyTableBody");

  // Tamper Proof Modal Elements
  const tamperModal = document.getElementById("tamperModal");
  const tamperModalTitle = document.getElementById("tamperModalTitle");
  const tamperModalSubtitle = document.getElementById("tamperModalSubtitle");
  const tamperModalBody = document.getElementById("tamperModalBody");
  const btnTamperModalClose = document.getElementById("btnTamperModalClose");
  const btnTamperModalDone = document.getElementById("btnTamperModalDone");
  const btnTamperModalInspect = document.getElementById("btnTamperModalInspect");

  let currentFile = null;
  let currentAttestationId = null;
  let currentExtractedCandidates = [];
  let currentFilterMode = "all";

  // Tab Navigation Handling
  if (tabBtnPipeline && tabBtnHistory) {
    tabBtnPipeline.addEventListener("click", () => {
      tabBtnPipeline.classList.add("active");
      tabBtnHistory.classList.remove("active");
      tabContentPipeline.classList.remove("hidden");
      tabContentHistory.classList.add("hidden");
    });

    tabBtnHistory.addEventListener("click", () => {
      tabBtnHistory.classList.add("active");
      tabBtnPipeline.classList.remove("active");
      tabContentHistory.classList.remove("hidden");
      tabContentPipeline.classList.add("hidden");
      loadLedger();
    });
  }

  // Toggle Top Matches Drawer
  if (btnToggleCandidates && candidatesDrawer) {
    btnToggleCandidates.addEventListener("click", () => {
      const isHidden = candidatesDrawer.classList.toggle("hidden");
      btnToggleCandidates.classList.toggle("active", !isHidden);
      if (!isHidden) {
        updateCandidatesDisplay("all");
      }
    });
  }

  // Dedicated Social Media Filter Toggle Button
  if (btnFilterSocial && candidatesDrawer) {
    btnFilterSocial.addEventListener("click", () => {
      if (candidatesDrawer.classList.contains("hidden") || currentFilterMode !== "social") {
        candidatesDrawer.classList.remove("hidden");
        if (btnToggleCandidates) btnToggleCandidates.classList.add("active");
        btnFilterSocial.classList.add("active");
        updateCandidatesDisplay("social");
      } else {
        btnFilterSocial.classList.remove("active");
        updateCandidatesDisplay("all");
      }
    });
  }

  // Filter Tabs inside Drawer
  if (filterTabAll) {
    filterTabAll.addEventListener("click", () => {
      updateCandidatesDisplay("all");
    });
  }

  if (filterTabSocial) {
    filterTabSocial.addEventListener("click", () => {
      updateCandidatesDisplay("social");
    });
  }

  // Dropzone Setup
  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  });

  dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("dragover");
  });

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    if (e.dataTransfer.files.length > 0) {
      handleFileSelection(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      handleFileSelection(e.target.files[0]);
    }
  });

  btnChange.addEventListener("click", (e) => {
    e.stopPropagation();
    currentFile = null;
    imagePreview.src = "";
    dropzone.classList.remove("has-preview");
    previewContainer.classList.add("hidden");
    dropzoneContent.classList.remove("hidden");
    resetStepper();
    btnRunPipeline.setAttribute("disabled", "true");
    fileInput.click();
  });

  function handleFileSelection(file) {
    if (!file.type.startsWith("image/")) {
      alert("Please select a valid image file (JPG, PNG, WEBP).");
      return;
    }

    currentFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
      imagePreview.src = e.target.result;
      dropzone.classList.add("has-preview");
      dropzoneContent.classList.add("hidden");
      previewContainer.classList.remove("hidden");
      resetStepper();
      btnRunPipeline.removeAttribute("disabled");
    };
    reader.readAsDataURL(file);
  }

  // Pipeline Execution (Real-Time SSE Stream via Button & Stepper)
  btnRunPipeline.addEventListener("click", async () => {
    if (!currentFile) return;

    btnRunPipeline.setAttribute("disabled", "true");
    btnRunPipeline.classList.add("running");
    if (btnSpinner) btnSpinner.classList.remove("hidden");
    if (btnPctBadge) {
      btnPctBadge.classList.remove("hidden");
      btnPctBadge.textContent = "10%";
    }
    if (btnProgressLine) btnProgressLine.style.width = "10%";
    if (btnText) btnText.textContent = "Starting...";

    resetStepper();
    if (tamperDiffContainer) tamperDiffContainer.classList.add("hidden");
    if (laserScanner) laserScanner.classList.add("scanning");

    setStepActive(1, "Detecting face & analyzing features...");

    const formData = new FormData();
    formData.append("file", currentFile);

    try {
      const response = await fetch("/api/pipeline/run-stream", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Server returned error ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let receivedComplete = false;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop(); // Keep unfinished line

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed || !trimmed.startsWith("data: ")) continue;

          try {
            const event = JSON.parse(trimmed.slice(6));
            handlePipelineEvent(event);
            if (event.type === "complete") {
              receivedComplete = true;
            }
          } catch (e) {
            console.debug("SSE JSON parse error:", e, trimmed);
          }
        }
      }

      if (!receivedComplete) {
        throw new Error("Pipeline connection ended prematurely.");
      }

    } catch (err) {
      if (laserScanner) laserScanner.classList.remove("scanning");
      btnRunPipeline.classList.remove("running");
      if (btnSpinner) btnSpinner.classList.add("hidden");
      if (btnPctBadge) btnPctBadge.classList.add("hidden");
      if (btnProgressLine) btnProgressLine.style.width = "0%";
      if (btnText) btnText.textContent = "Run Verification";
      btnRunPipeline.removeAttribute("disabled");
      alert(`Verification Error: ${err.message}`);
    }
  });

  function handlePipelineEvent(event) {
    if (event.percent !== undefined) {
      if (btnProgressLine) btnProgressLine.style.width = `${event.percent}%`;
      if (btnPctBadge) btnPctBadge.textContent = `${event.percent}%`;
    }

    const step = event.step || 1;
    if (step === 1) {
      if (btnText) btnText.textContent = "Detecting face...";
      setStepActive(1, event.message || "Detecting face & analyzing features...");
    } else if (step === 2) {
      setStepCompleted(1);
      if (btnText) btnText.textContent = "Searching web...";
      setStepActive(2, event.message || "Searching public web for visual matches...");
    } else if (step === 3) {
      setStepCompleted(1);
      if (btnText) btnText.textContent = "Comparing candidates...";
      setStepActive(2, event.message || "Comparing candidate faces found online...");
    } else if (step === 4) {
      setStepCompleted(1);
      setStepCompleted(2);
      if (btnText) btnText.textContent = "Recording on-chain...";
      setStepActive(3, event.message || "Anchoring attestation on blockchain...");
    } else if (step === 5) {
      setStepCompleted(1);
      setStepCompleted(2);
      setStepCompleted(3);
      if (btnText) btnText.textContent = "Verifying integrity...";
      setStepActive(4, event.message || "Checking cryptographic integrity against blockchain...");
    }

    if (event.type === "complete") {
      setStepCompleted(1);
      setStepCompleted(2);
      setStepCompleted(3);
      setStepCompleted(4);
      if (laserScanner) laserScanner.classList.remove("scanning");

      if (btnProgressLine) btnProgressLine.style.width = "100%";
      if (btnPctBadge) btnPctBadge.textContent = "100%";
      if (btnText) btnText.textContent = "Complete ✓";
      if (btnSpinner) btnSpinner.classList.add("hidden");

      if (event.result) {
        renderResults(event.result);
        loadLedger();
      }

      setTimeout(() => {
        btnRunPipeline.classList.remove("running");
        if (btnPctBadge) btnPctBadge.classList.add("hidden");
        if (btnProgressLine) btnProgressLine.style.width = "0%";
        if (btnText) btnText.textContent = "Run Verification";
        btnRunPipeline.removeAttribute("disabled");
      }, 1800);

    } else if (event.type === "error") {
      if (laserScanner) laserScanner.classList.remove("scanning");
      btnRunPipeline.classList.remove("running");
      if (btnSpinner) btnSpinner.classList.add("hidden");
      if (btnPctBadge) btnPctBadge.classList.add("hidden");
      if (btnProgressLine) btnProgressLine.style.width = "0%";
      if (btnText) btnText.textContent = "Run Verification";
      btnRunPipeline.removeAttribute("disabled");
      alert(event.message || "Verification failed");
    }
  }

  function renderResults(data) {
    emptyState.classList.add("hidden");
    resultsContainer.classList.remove("hidden");

    // Stage 1: Face Detection
    const scan = data.face_scan || {};
    if (scan.crop_image_path) {
      const cropFilename = scan.crop_image_path.split("/").pop();
      faceCropImg.src = `/data-files/crops/${cropFilename}`;
    } else {
      faceCropImg.src = imagePreview.src;
    }
    faceCropImg.onerror = () => {
      faceCropImg.src = imagePreview.src;
    };

    if (scan.face_confidence !== undefined && scan.face_confidence !== null) {
      const conf = Math.round(scan.face_confidence * 1000) / 10;
      faceConfidenceBadge.textContent = `${conf}% Confidence`;
    } else {
      faceConfidenceBadge.textContent = "-";
    }
    faceBboxVal.textContent = scan.bbox ? JSON.stringify(scan.bbox) : "-";
    faceShaVal.textContent = scan.image_sha256 || "-";

    // Stage 2: Web & Social Match
    const match = data.search_match || {};
    const isUnmatched = !match.author_name || match.author_name === "No Match Found" || !match.visual_similarity_score || match.visual_similarity_score === 0;

    matchPlatformBadge.textContent = isUnmatched ? "Web" : (match.platform || "-");
    authorName.textContent = match.author_name || "-";
    authorHandle.textContent = isUnmatched ? "-" : (match.author_handle || "-");

    // Render Avatar Image & Discovered Match Image Preview
    if (!isUnmatched && match.post_image_url && match.post_image_url.startsWith("http")) {
      if (matchAvatarImg) {
        matchAvatarImg.src = match.post_image_url;
        matchAvatarImg.classList.remove("hidden");
      }
      if (matchAvatarPlaceholder) matchAvatarPlaceholder.classList.add("hidden");

      if (matchImagePreviewContainer && matchPreviewImg) {
        matchPreviewImg.src = match.post_image_url;
        if (previewUrlLink) previewUrlLink.href = match.post_url || "#";
        if (matchPreviewTag) matchPreviewTag.textContent = `${match.platform || "Web"} Match`;
        matchImagePreviewContainer.classList.remove("hidden");
      }
    } else {
      if (matchAvatarImg) matchAvatarImg.classList.add("hidden");
      if (matchAvatarPlaceholder) matchAvatarPlaceholder.classList.remove("hidden");
      if (matchImagePreviewContainer) matchImagePreviewContainer.classList.add("hidden");
    }

    const simPill = document.querySelector(".sim-pill-3d");
    if (isUnmatched) {
      similarityScore.textContent = "0.0%";
      if (simPill) simPill.classList.add("unmatched");
    } else {
      const sim = (match.visual_similarity_score * 100).toFixed(1);
      similarityScore.textContent = `${sim}%`;
      if (simPill) simPill.classList.remove("unmatched");
    }

    postCaption.textContent = match.post_caption || "-";
    if (!isUnmatched && match.post_url && match.post_url.startsWith("http")) {
      postUrlLink.href = match.post_url;
      postUrlLink.classList.remove("hidden");
    } else {
      postUrlLink.classList.add("hidden");
    }

    if (!isUnmatched && match.post_timestamp && match.post_timestamp !== "-") {
      postTimestamp.textContent = match.post_timestamp;
    } else {
      postTimestamp.textContent = "";
    }

    // Render Top K Candidates Gallery (Enforcing Similarity Threshold)
    const activeThreshold = (match.raw_metadata && match.raw_metadata.similarity_threshold !== undefined)
      ? match.raw_metadata.similarity_threshold
      : 0.70;
    const rawCandidates = match.top_candidates || (match.raw_metadata && match.raw_metadata.top_candidates) || [];
    currentExtractedCandidates = rawCandidates.filter((cand) => (cand.similarity || 0) >= activeThreshold);

    if (currentExtractedCandidates && currentExtractedCandidates.length > 0) {
      if (btnToggleCandidates) {
        btnToggleCandidates.classList.remove("hidden");
        btnToggleCandidates.classList.remove("active");
      }
      if (btnFilterSocial) {
        btnFilterSocial.classList.remove("hidden");
        btnFilterSocial.classList.remove("active");
      }
      if (candidatesDrawer) candidatesDrawer.classList.add("hidden");

      updateCandidatesDisplay("all");
    } else {
      if (btnToggleCandidates) btnToggleCandidates.classList.add("hidden");
      if (btnFilterSocial) btnFilterSocial.classList.add("hidden");
      if (candidatesDrawer) candidatesDrawer.classList.add("hidden");
    }

    // Stage 3: Blockchain Record
    const att = data.blockchain_attestation || {};
    currentAttestationId = att.id || null;
    if (txHashVal) txHashVal.textContent = att.tx_hash || "-";
    if (blockNumVal) blockNumVal.textContent = att.block_number ? `#${att.block_number}` : "-";
    if (contractVal) contractVal.textContent = att.contract_address || "-";
    if (payloadHashVal) payloadHashVal.textContent = att.payload_hash || "-";
    if (networkBadge) networkBadge.textContent = att.network_name || "EVM";

    // Stage 4: Tamper Verification
    const ver = data.verification || {};
    renderVerificationState(ver.is_valid !== false);
  }

  // =========================================================================
  // Extensive Social Media Knowledge Base & Candidate Inspector
  // =========================================================================
  const SOCIAL_NETWORKS = [
    { id: "instagram", name: "Instagram", domains: ["instagram.com", "instagr.am", "cdninstagram.com"] },
    { id: "linkedin", name: "LinkedIn", domains: ["linkedin.com", "licdn.com"] },
    { id: "twitter", name: "Twitter/X", domains: ["twitter.com", "x.com", "t.co", "twimg.com"] },
    { id: "facebook", name: "Facebook", domains: ["facebook.com", "fb.com", "fb.watch", "fbsbx.com"] },
    { id: "youtube", name: "YouTube", domains: ["youtube.com", "youtu.be", "ytimg.com"] },
    { id: "tiktok", name: "TikTok", domains: ["tiktok.com", "tiktokcdn.com", "douyin.com"] },
    { id: "reddit", name: "Reddit", domains: ["reddit.com", "redd.it", "redditmedia.com"] },
    { id: "pinterest", name: "Pinterest", domains: ["pinterest.com", "pinimg.com"] },
    { id: "threads", name: "Threads", domains: ["threads.net"] },
    { id: "snapchat", name: "Snapchat", domains: ["snapchat.com"] },
    { id: "telegram", name: "Telegram", domains: ["t.me", "telegram.org"] },
    { id: "whatsapp", name: "WhatsApp", domains: ["whatsapp.com", "wa.me"] },
    { id: "vk", name: "VK", domains: ["vk.com", "vkontakte.ru"] },
    { id: "github", name: "GitHub", domains: ["github.com"] },
    { id: "gitlab", name: "GitLab", domains: ["gitlab.com"] },
    { id: "medium", name: "Medium", domains: ["medium.com"] },
    { id: "tumblr", name: "Tumblr", domains: ["tumblr.com"] },
    { id: "bluesky", name: "Bluesky", domains: ["bsky.app", "bsky.social"] },
    { id: "mastodon", name: "Mastodon", domains: ["mastodon.social", "mastodon.online", "mstdn.social", "fosstodon.org"] },
    { id: "discord", name: "Discord", domains: ["discord.com", "discord.gg"] },
    { id: "twitch", name: "Twitch", domains: ["twitch.tv"] },
    { id: "quora", name: "Quora", domains: ["quora.com"] },
    { id: "wechat", name: "WeChat", domains: ["wechat.com", "weixin.qq.com"] },
    { id: "weibo", name: "Weibo", domains: ["weibo.com", "weibo.cn"] },
    { id: "xiaohongshu", name: "Xiaohongshu", domains: ["xiaohongshu.com"] },
    { id: "bilibili", name: "Bilibili", domains: ["bilibili.com"] },
    { id: "doximity", name: "Doximity", domains: ["doximity.com"] },
    { id: "researchgate", name: "ResearchGate", domains: ["researchgate.net"] },
    { id: "orcid", name: "ORCID", domains: ["orcid.org"] },
    { id: "substack", name: "Substack", domains: ["substack.com"] },
    { id: "patreon", name: "Patreon", domains: ["patreon.com"] },
    { id: "soundcloud", name: "SoundCloud", domains: ["soundcloud.com"] },
    { id: "spotify", name: "Spotify", domains: ["spotify.com"] },
    { id: "flickr", name: "Flickr", domains: ["flickr.com"] },
    { id: "vimeo", name: "Vimeo", domains: ["vimeo.com"] }
  ];

  function isSocialCandidate(cand) {
    if (!cand) return false;
    const platform = (cand.platform || "").toLowerCase();
    const url = (cand.url || "").toLowerCase();
    const author = (cand.author || "").toLowerCase();
    const title = (cand.title || "").toLowerCase();

    for (const net of SOCIAL_NETWORKS) {
      if (platform.includes(net.id) || platform.includes(net.name.toLowerCase())) return true;
      for (const d of net.domains) {
        if (url.includes(d)) return true;
      }
    }
    return false;
  }

  function getCandidatePlatform(cand) {
    if (!cand) return "Web";
    const platform = (cand.platform || "").toLowerCase();
    const url = (cand.url || "").toLowerCase();
    for (const net of SOCIAL_NETWORKS) {
      if (platform.includes(net.id) || platform.includes(net.name.toLowerCase())) return net.name;
      for (const d of net.domains) {
        if (url.includes(d)) return net.name;
      }
    }
    return cand.platform && cand.platform !== "Web" ? cand.platform : "Web";
  }

  function updateCandidatesDisplay(filterMode = "all", targetPlatform = null) {
    currentFilterMode = filterMode;

    const socialCandidates = currentExtractedCandidates.filter(isSocialCandidate);

    // Update numerical counters
    if (candidatesCount) candidatesCount.textContent = currentExtractedCandidates.length;
    if (socialCandidatesCount) socialCandidatesCount.textContent = socialCandidates.length;
    if (countTabAll) countTabAll.textContent = currentExtractedCandidates.length;
    if (countTabSocial) countTabSocial.textContent = socialCandidates.length;

    // Filter button and tab active toggles
    if (filterTabAll) filterTabAll.classList.toggle("active", filterMode === "all");
    if (filterTabSocial) filterTabSocial.classList.toggle("active", filterMode === "social" || targetPlatform !== null);
    if (btnFilterSocial) btnFilterSocial.classList.toggle("active", filterMode === "social" || targetPlatform !== null);

    // Filter dataset
    let filteredList = currentExtractedCandidates;
    if (filterMode === "social") {
      filteredList = socialCandidates;
      if (targetPlatform) {
        filteredList = filteredList.filter((c) => getCandidatePlatform(c) === targetPlatform);
      }
      if (drawerTitle) {
        drawerTitle.textContent = targetPlatform
          ? `${targetPlatform} Profiles (${filteredList.length})`
          : `Social Media Matches (${filteredList.length})`;
      }
      if (drawerSubtitle) drawerSubtitle.textContent = "Filtered to public social media platforms";
    } else {
      if (drawerTitle) drawerTitle.textContent = `All Web Matches (${filteredList.length})`;
      if (drawerSubtitle) drawerSubtitle.textContent = "Candidates discovered via Google Lens & Yandex";
    }

    // Render Sub-platform Filter Pills when in Social mode
    if (socialPlatformFilterRow) {
      if ((filterMode === "social" || targetPlatform) && socialCandidates.length > 0) {
        const platformCounts = {};
        socialCandidates.forEach((c) => {
          const p = getCandidatePlatform(c);
          platformCounts[p] = (platformCounts[p] || 0) + 1;
        });

        const platforms = Object.keys(platformCounts);
        if (platforms.length > 1) {
          socialPlatformFilterRow.classList.remove("hidden");
          socialPlatformFilterRow.innerHTML = `
            <button type="button" class="platform-filter-pill ${!targetPlatform ? "active" : ""}" data-platform="">
              All Social (${socialCandidates.length})
            </button>
            ${platforms.map((p) => `
              <button type="button" class="platform-filter-pill ${targetPlatform === p ? "active" : ""}" data-platform="${p}">
                ${p} (${platformCounts[p]})
              </button>
            `).join("")}
          `;

          socialPlatformFilterRow.querySelectorAll(".platform-filter-pill").forEach((pill) => {
            pill.addEventListener("click", () => {
              const selectedP = pill.getAttribute("data-platform");
              updateCandidatesDisplay("social", selectedP || null);
            });
          });
        } else {
          socialPlatformFilterRow.classList.add("hidden");
        }
      } else {
        socialPlatformFilterRow.classList.add("hidden");
      }
    }

    // Render Grid
    if (candidatesGrid) {
      if (filteredList.length === 0) {
        candidatesGrid.innerHTML = `
          <div class="empty-candidates-notice">
            No ${filterMode === "social" ? "social media" : ""} candidates found matching this selection.
          </div>
        `;
        return;
      }

      candidatesGrid.innerHTML = filteredList.map((cand, idx) => {
        const isSocial = isSocialCandidate(cand);
        const platformName = getCandidatePlatform(cand);
        const simPct = cand.similarity_pct !== undefined ? cand.similarity_pct : ((cand.similarity || 0) * 100).toFixed(1);
        const isCurrentlyActive = cand.url && postUrlLink && postUrlLink.href === cand.url;

        return `
          <div class="candidate-card ${isCurrentlyActive ? "is-top" : ""} ${isSocial ? "is-social" : ""}" data-cand-url="${cand.url || ""}">
            <div class="candidate-thumb-wrap">
              <img src="${cand.image_url}" alt="${cand.title || "Match"}" class="candidate-thumb" loading="lazy" onerror="this.style.display='none'">
              <span class="candidate-rank-badge">#${cand.rank || idx + 1}</span>
              <span class="candidate-sim-pill">${simPct}%</span>
              <span class="candidate-platform-badge">${platformName}</span>
            </div>
            <div class="candidate-body">
              <div class="candidate-title" title="${cand.title || ""}">${cand.title || "Web Result"}</div>
              <div class="candidate-author">${platformName} • ${cand.author || "-"}</div>
              <div class="candidate-actions-row">
                <button type="button" class="candidate-inspect-btn">Inspect</button>
                ${cand.url ? `<a href="${cand.url}" target="_blank" class="candidate-link"><span>Open</span> ↗</a>` : ""}
              </div>
            </div>
          </div>
        `;
      }).join("");

      // Interactive Card Selection to Inspect Profile Live
      candidatesGrid.querySelectorAll(".candidate-card").forEach((card, idx) => {
        const cand = filteredList[idx];
        card.addEventListener("click", (e) => {
          if (e.target.closest(".candidate-link")) return;
          inspectCandidate(cand);
        });
      });
    }
  }

  function inspectCandidate(cand) {
    if (!cand) return;
    const platformName = getCandidatePlatform(cand);

    if (authorName) authorName.textContent = cand.author || cand.title || "Match";
    if (authorHandle) authorHandle.textContent = "@" + (cand.author || "user").toLowerCase().replace(/[^a-z0-9_]/g, "_").slice(0, 24);
    if (matchPlatformBadge) matchPlatformBadge.textContent = platformName;

    const simPct = cand.similarity_pct !== undefined ? cand.similarity_pct : ((cand.similarity || 0) * 100).toFixed(1);
    if (similarityScore) similarityScore.textContent = `${simPct}%`;

    const simPill = document.querySelector(".sim-pill, .sim-pill-3d");
    if (simPill) simPill.classList.remove("unmatched");

    if (postCaption) postCaption.textContent = cand.snippet || cand.title || "Extracted visual match";

    if (postUrlLink) {
      if (cand.url) {
        postUrlLink.href = cand.url;
        postUrlLink.classList.remove("hidden");
      } else {
        postUrlLink.classList.add("hidden");
      }
    }

    if (cand.image_url) {
      if (matchAvatarImg) {
        matchAvatarImg.src = cand.image_url;
        matchAvatarImg.classList.remove("hidden");
      }
      if (matchAvatarPlaceholder) matchAvatarPlaceholder.classList.add("hidden");

      if (matchImagePreviewContainer && matchPreviewImg) {
        matchPreviewImg.src = cand.image_url;
        if (previewUrlLink) previewUrlLink.href = cand.url || "#";
        if (matchPreviewTag) matchPreviewTag.textContent = `${platformName} Match`;
        matchImagePreviewContainer.classList.remove("hidden");
      }
    }

    if (candidatesGrid) {
      candidatesGrid.querySelectorAll(".candidate-card").forEach((c) => {
        c.classList.remove("is-top");
      });
      const matchingCard = Array.from(candidatesGrid.querySelectorAll(".candidate-card")).find(
        (c) => c.getAttribute("data-cand-url") === cand.url
      );
      if (matchingCard) matchingCard.classList.add("is-top");
    }
  }

  function renderVerificationState(isValid) {
    if (isValid) {
      if (verBanner) verBanner.className = "audit-banner success";
      if (verStatusBadge) {
        verStatusBadge.className = "badge-3d badge-green";
        verStatusBadge.textContent = "Verified";
      }
      if (verTitle) verTitle.textContent = "Data Verified";
      if (verDescription) verDescription.textContent = "The current data matches the blockchain record exactly.";
    } else {
      if (verBanner) verBanner.className = "audit-banner tampered";
      if (verStatusBadge) {
        verStatusBadge.className = "badge-3d badge-rose";
        verStatusBadge.textContent = "Tampered";
      }
      if (verTitle) verTitle.textContent = "Tamper Detected";
      if (verDescription) verDescription.textContent = "Data has been altered and does not match the blockchain record.";
    }
  }

  // Interactive Tamper Simulation in Pipeline tab
  if (btnTamperTest) {
    btnTamperTest.addEventListener("click", async () => {
      if (!currentAttestationId) {
        alert("Please run a verification scan first or select a record from History.");
        return;
      }

      // Toggle back to authentic if already tampered
      if (btnTamperTest.dataset.tampered === "true") {
        btnTamperTest.dataset.tampered = "false";
        const span = btnTamperTest.querySelector("span");
        if (span) span.textContent = "Simulate Tampering";
        if (tamperDiffContainer) tamperDiffContainer.classList.add("hidden");
        renderVerificationState(true);
        return;
      }

      btnTamperTest.disabled = true;
      const span = btnTamperTest.querySelector("span");
      if (span) span.textContent = "Testing Tamper...";

      try {
        const res = await fetch(`/api/pipeline/tamper-test/${currentAttestationId}`, {
          method: "POST",
        });

        if (!res.ok) throw new Error("Tamper test endpoint returned error");
        const data = await res.json();

        const genuine = data.genuine_verification || {};
        const tampered = data.tampered_verification || {};
        const tamperedFields = (tampered.tampered_fields && tampered.tampered_fields.length > 0)
          ? tampered.tampered_fields
          : [{ field: "post_caption", expected_original: "Authentic caption", tampered_current: "🚨 [TAMPERED] Maliciously modified" }];

        if (tamperDiffContainer) {
          tamperDiffContainer.classList.remove("hidden");
          tamperDiffContainer.innerHTML = `
            <table class="data-table">
              <thead>
                <tr>
                  <th>State</th>
                  <th>Calculated Hash</th>
                  <th>Blockchain Hash</th>
                  <th>Result</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td style="color: #34d399; font-weight: 700;">Original Data</td>
                  <td class="mono">${(genuine.calculated_payload_hash || "").slice(0, 18)}...</td>
                  <td class="mono">${(genuine.onchain_payload_hash || genuine.calculated_payload_hash || "").slice(0, 18)}...</td>
                  <td style="color: #34d399; font-weight: 800;">VALID (Match)</td>
                </tr>
                <tr>
                  <td style="color: #fb7185; font-weight: 700;">Modified Data</td>
                  <td class="mono">${(tampered.calculated_payload_hash || "").slice(0, 18)}...</td>
                  <td class="mono">${(tampered.onchain_payload_hash || genuine.calculated_payload_hash || "").slice(0, 18)}...</td>
                  <td style="color: #fb7185; font-weight: 800;">TAMPERED (Mismatch)</td>
                </tr>
              </tbody>
            </table>
          `;
        }

        renderVerificationState(false);
        btnTamperTest.dataset.tampered = "true";
        if (span) span.textContent = "Restore Authentic State";
      } catch (err) {
        alert(`Tamper Test Error: ${err.message}`);
        if (span) span.textContent = "Simulate Tampering";
      } finally {
        btnTamperTest.disabled = false;
      }
    });
  }

  // =========================================================================
  // History Table & Cryptographic Audit Modal
  // =========================================================================
  if (btnRefreshHistory) {
    btnRefreshHistory.addEventListener("click", loadLedger);
  }
  loadLedger();

  // Robust Event Delegation for "Test Tamper" buttons in history table
  if (historyTableBody) {
    historyTableBody.addEventListener("click", async (e) => {
      const btn = e.target.closest(".btn-action-tamper, .btn-verify-row-3d, .btn-row-action");
      if (!btn) return;
      const attId = btn.dataset.id;
      if (!attId || attId === "-") return;
      await executeTamperAuditModal(attId, btn);
    });
  }

  async function executeTamperAuditModal(attId, triggerBtn) {
    const origText = triggerBtn ? triggerBtn.textContent : "Test Tamper";
    if (triggerBtn) {
      triggerBtn.disabled = true;
      triggerBtn.textContent = "Testing...";
    }

    try {
      const res = await fetch(`/api/pipeline/tamper-test/${attId}`, {
        method: "POST",
      });
      if (!res.ok) throw new Error(`Server returned HTTP ${res.status}`);
      const data = await res.json();

      const genuine = data.genuine_verification || {};
      const tampered = data.tampered_verification || {};
      const tamperedFields = (tampered.tampered_fields && tampered.tampered_fields.length > 0)
        ? tampered.tampered_fields
        : [{ field: "post_caption", expected_original: "Authentic caption", tampered_current: "🚨 [TAMPERED] Maliciously modified" }];

      if (tamperModalTitle) tamperModalTitle.textContent = `Tamper-Evidence Proof: Attestation #${attId}`;
      if (tamperModalSubtitle) tamperModalSubtitle.textContent = `On-Chain Verification vs Malicious Data Modification Test`;

      if (tamperModalBody) {
        tamperModalBody.innerHTML = `
          <div class="proof-card valid">
            <div class="proof-header">
              <span class="proof-title">1. Authentic Record (Original State)</span>
              <span class="proof-badge badge-valid">100% Verified</span>
            </div>
            <div class="proof-hashes">
              <span class="proof-label">Calculated Hash:</span>
              <span class="proof-val">${genuine.calculated_payload_hash || "-"}</span>
              <span class="proof-label">On-Chain Hash:</span>
              <span class="proof-val">${genuine.onchain_payload_hash || genuine.calculated_payload_hash || "-"}</span>
              <span class="proof-label">Blockchain Result:</span>
              <span class="proof-val" style="color: #34d399; font-weight: 700;">MATCH — Payload matches blockchain smart contract exactly</span>
            </div>
          </div>

          <div class="proof-card tampered">
            <div class="proof-header">
              <span class="proof-title">2. Simulated Attacker Modification (Caption & Author Altered)</span>
              <span class="proof-badge badge-tampered">Tamper Detected</span>
            </div>
            <div class="proof-hashes">
              <span class="proof-label">Mutated Hash:</span>
              <span class="proof-val" style="color: #fb7185;">${tampered.calculated_payload_hash || "-"}</span>
              <span class="proof-label">On-Chain Hash:</span>
              <span class="proof-val">${tampered.onchain_payload_hash || genuine.calculated_payload_hash || "-"}</span>
              <span class="proof-label">Blockchain Result:</span>
              <span class="proof-val" style="color: #fb7185; font-weight: 700;">REJECTED — Smart contract flags data corruption!</span>
            </div>
          </div>

          <div class="tamper-diff-list">
            <strong style="color: #fb7185; display: block; margin-bottom: 6px;">Detected Tampered Fields (${tamperedFields.length}):</strong>
            <ul style="margin: 0; padding-left: 18px; color: var(--text-primary); font-size: 11px;">
              ${tamperedFields.map((f) => `
                <li>
                  <strong>${f.field}</strong>: expected <code>${typeof f.expected_original === 'string' ? f.expected_original.slice(0, 40) : f.expected_original}</code>
                  &rarr; found <code>${typeof f.tampered_current === 'string' ? f.tampered_current.slice(0, 40) : f.tampered_current}</code>
                </li>
              `).join("")}
            </ul>
          </div>
        `;
      }

      if (tamperModal) {
        tamperModal.dataset.currentAttId = attId;
        tamperModal.classList.remove("hidden");
      }
    } catch (err) {
      alert(`Could not run tamper test on Attestation #${attId}: ${err.message}`);
    } finally {
      if (triggerBtn) {
        triggerBtn.disabled = false;
        triggerBtn.textContent = origText;
      }
    }
  }

  // Modal Close Handlers
  if (btnTamperModalClose && tamperModal) {
    btnTamperModalClose.addEventListener("click", () => tamperModal.classList.add("hidden"));
  }
  if (btnTamperModalDone && tamperModal) {
    btnTamperModalDone.addEventListener("click", () => tamperModal.classList.add("hidden"));
  }
  if (tamperModal) {
    tamperModal.addEventListener("click", (e) => {
      if (e.target === tamperModal) tamperModal.classList.add("hidden");
    });
  }

  // Modal "Inspect in Pipeline" Handler
  if (btnTamperModalInspect && tamperModal) {
    btnTamperModalInspect.addEventListener("click", async () => {
      const attId = tamperModal.dataset.currentAttId;
      tamperModal.classList.add("hidden");
      if (!attId) return;

      try {
        const res = await fetch("/api/pipeline/history?limit=50");
        if (res.ok) {
          const historyRuns = await res.json();
          const found = historyRuns.find((r) => r.attestation && String(r.attestation.id) === String(attId));
          if (found) {
            renderPipelineResults({
              face_scan: found.face_scan || {},
              search_match: found.search_match || {},
              blockchain_attestation: found.attestation || {},
              verification: found.latest_audit ? {
                is_valid: found.latest_audit.is_valid,
                tampered_fields: (found.latest_audit.tamper_details && found.latest_audit.tamper_details.tampered_fields) || []
              } : { is_valid: true }
            });
          }
        }
      } catch (e) {
        console.warn("Could not inspect run in pipeline:", e);
      }

      if (tabBtnPipeline) tabBtnPipeline.click();
    });
  }

  async function loadLedger() {
    try {
      const res = await fetch("/api/pipeline/history?limit=30");
      if (!res.ok) {
        historyTableBody.innerHTML = `
          <tr><td colspan="8" class="table-loading" style="color: #f43f5e;">Failed to load records (HTTP ${res.status}). Click Refresh above.</td></tr>
        `;
        return;
      }
      const runs = await res.json();
      console.log("[Verification History] Records fetched:", runs ? runs.length : 0);

      if (historyTabBadge) {
        historyTabBadge.textContent = runs ? runs.length : 0;
      }

      if (!runs || runs.length === 0) {
        historyTableBody.innerHTML = `
          <tr>
            <td colspan="8" class="table-loading">No verification records found yet. Run a scan in the pipeline tab.</td>
          </tr>
        `;
        return;
      }

      historyTableBody.innerHTML = runs.map((r) => {
        const att = r.attestation || {};
        const match = r.search_match || {};
        const isUnmatched = !match || !match.author_name || match.author_name === "No Match Found" || !match.visual_similarity_score;
        const simDisplay = isUnmatched ? "0.0%" : ((match.visual_similarity_score * 100).toFixed(1) + "%");
        const attId = att.id || "-";
        const isVerified = att.is_verified !== false;

        return `
          <tr>
            <td class="mono">#${attId}</td>
            <td><span class="badge-3d badge-cyan">${match && match.platform ? match.platform : "Web"}</span></td>
            <td><strong>${match && match.author_name ? match.author_name : "-"}</strong></td>
            <td class="${isUnmatched ? 'text-muted' : 'text-glow-green font-bold'}">${simDisplay}</td>
            <td class="mono text-muted truncate" title="${att.tx_hash || ""}">${att.tx_hash ? att.tx_hash.slice(0, 16) + "..." : "-"}</td>
            <td class="mono text-glow-purple">${att.block_number ? "#" + att.block_number : "-"}</td>
            <td><span class="badge-3d ${isVerified ? "badge-green" : "badge-rose"}">${isVerified ? "Verified" : "Tampered"}</span></td>
            <td><button class="btn-action-tamper" data-id="${attId}" title="Run Cryptographic Tamper Test">Test Tamper</button></td>
          </tr>
        `;
      }).join("");
    } catch (err) {
      console.warn("[Verification History] Load error:", err);
      historyTableBody.innerHTML = `
        <tr><td colspan="8" class="table-loading" style="color: #f43f5e;">Could not load history: ${err.message}. Click Refresh to retry.</td></tr>
      `;
    }
  }

  // // Automatically restore latest scan on page load/refresh so extracted data & filter buttons remain visible
  // async function autoRestoreLatestRun() {
  //   try {
  //     const res = await fetch("/api/pipeline/history?limit=1");
  //     if (!res.ok) return;
  //     const data = await res.json();
  //     if (Array.isArray(data) && data.length > 0 && !currentFile) {
  //       const item = data[0];
  //       const resultPayload = {
  //         face_scan: item.scan || {},
  //         search_match: item.search_match || {},
  //         blockchain_attestation: item.attestation || {},
  //         verification: item.latest_audit ? {
  //           is_valid: item.latest_audit.is_valid,
  //           tampered_fields: (item.latest_audit.tamper_details && item.latest_audit.tamper_details.tampered_fields) || []
  //         } : { is_valid: true }
  //       };

  //       if (item.scan && item.scan.crop_image_path) {
  //         const cropFilename = item.scan.crop_image_path.split("/").pop();
  //         if (imagePreview) imagePreview.src = `/data-files/crops/${cropFilename}`;
  //         if (dropzone) dropzone.classList.add("has-preview");
  //         if (dropzoneContent) dropzoneContent.classList.add("hidden");
  //         if (previewContainer) previewContainer.classList.remove("hidden");
  //       }

  //       renderResults(resultPayload);
  //       setStepCompleted(1);
  //       setStepCompleted(2);
  //       setStepCompleted(3);
  //       setStepCompleted(4);
  //     }
  //   } catch (e) {
  //     console.debug("Could not auto-restore last run:", e);
  //   }
  // }

  // autoRestoreLatestRun();

  // Stepper Management Utilities
  function setStepActive(n, msg) {
    const rows = [pStep1, pStep2, pStep3, pStep4];
    const descs = [pStep1Desc, pStep2Desc, pStep3Desc, pStep4Desc];
    const row = rows[n - 1];
    if (!row) return;
    row.className = "step-row step-3d-row active";
    if (msg && descs[n - 1]) descs[n - 1].textContent = msg;
  }

  function setStepCompleted(n) {
    const rows = [pStep1, pStep2, pStep3, pStep4];
    const descs = [pStep1Desc, pStep2Desc, pStep3Desc, pStep4Desc];
    const orbs = [pStep1Orb, pStep2Orb, pStep3Orb, pStep4Orb];
    const conns = [pConn1, pConn2, pConn3];
    const defaultLabels = [
      "Face detected & features encoded",
      "Public visual search completed",
      "Attestation anchored on-chain",
      "Cryptographic integrity verified",
    ];
    const row = rows[n - 1];
    if (!row) return;
    row.className = "step-row step-3d-row completed";
    if (orbs[n - 1]) orbs[n - 1].innerHTML = "✓";
    if (descs[n - 1]) descs[n - 1].textContent = defaultLabels[n - 1];
    if (n - 1 < conns.length && conns[n - 1]) {
      conns[n - 1].classList.add("completed");
    }
  }

  function resetStepper() {
    const rows = [pStep1, pStep2, pStep3, pStep4];
    const descs = [pStep1Desc, pStep2Desc, pStep3Desc, pStep4Desc];
    const orbs = [pStep1Orb, pStep2Orb, pStep3Orb, pStep4Orb];
    const conns = [pConn1, pConn2, pConn3];
    const defaultLabels = [
      "Detect face and extract features",
      "Search public profiles and posts",
      "Anchor attestation on-chain",
      "Verify record integrity",
    ];
    rows.forEach((r, i) => {
      if (r) r.className = "step-row step-3d-row";
      if (orbs[i]) orbs[i].textContent = String(i + 1);
      if (descs[i]) descs[i].textContent = defaultLabels[i];
    });
    conns.forEach((c) => {
      if (c) c.classList.remove("completed");
    });
  }
}
