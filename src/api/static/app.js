document.addEventListener("DOMContentLoaded", () => {
  // Initialize 3D Engine & UI Controllers
  initThreeJSBackground();
  initTiltPhysics();
  initAppLogic();
});

/* =========================================================================
   1. THREE.JS 3D INTERACTIVE HOLOGRAPHIC CYBER GLOBE WITH PARALLAX
   ========================================================================= */
function initThreeJSBackground() {
  const canvas = document.getElementById("webglCanvas");
  if (!canvas || typeof THREE === "undefined") return;

  const scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(0x05070e, 0.0035);

  const camera = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 0.1, 1000);
  camera.position.set(0, 0, 115);

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

  // Globe Group for consolidated rotation & parallax tilt
  const globeGroup = new THREE.Group();
  globeGroup.position.set(0, -8, -15);
  scene.add(globeGroup);

  // Soft Dot Texture Generator
  const createSoftDotTexture = () => {
    const c = document.createElement("canvas");
    c.width = 64;
    c.height = 64;
    const ctx = c.getContext("2d");
    const g = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
    g.addColorStop(0, "rgba(255, 255, 255, 1)");
    g.addColorStop(0.3, "rgba(56, 189, 248, 0.7)");
    g.addColorStop(0.7, "rgba(14, 165, 233, 0.15)");
    g.addColorStop(1, "rgba(0, 0, 0, 0)");
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.arc(32, 32, 32, 0, Math.PI * 2);
    ctx.fill();
    return new THREE.CanvasTexture(c);
  };

  const dotTexture = createSoftDotTexture();

  // 1. Globe Base Sphere Wireframe (Latitude & Longitude Grid)
  const globeRadius = 46;
  const globeWireGeo = new THREE.SphereGeometry(globeRadius, 36, 36);
  const globeWireMat = new THREE.MeshBasicMaterial({
    color: 0x0284c7,
    wireframe: true,
    transparent: true,
    opacity: 0.08,
  });
  const globeWireMesh = new THREE.Mesh(globeWireGeo, globeWireMat);
  globeGroup.add(globeWireMesh);

  // 2. Outer Atmospheric Holographic Glow Shell
  const atmosphereGeo = new THREE.SphereGeometry(globeRadius * 1.04, 32, 32);
  const atmosphereMat = new THREE.MeshBasicMaterial({
    color: 0x38bdf8,
    wireframe: true,
    transparent: true,
    opacity: 0.03,
  });
  const atmosphereMesh = new THREE.Mesh(atmosphereGeo, atmosphereMat);
  globeGroup.add(atmosphereMesh);

  // 3. Globe Surface Biometric Nodes (Fibonacci Spiral Distribution)
  const nodeCount = 1100;
  const nodePositions = new Float32Array(nodeCount * 3);
  const nodeColors = new Float32Array(nodeCount * 3);

  const colorCyan = new THREE.Color(0x38bdf8);
  const colorIndigo = new THREE.Color(0x818cf8);
  const colorEmerald = new THREE.Color(0x34d399);

  for (let i = 0; i < nodeCount; i++) {
    const phi = Math.acos(-1 + (2 * i) / nodeCount);
    const theta = Math.sqrt(nodeCount * Math.PI) * phi;

    const x = globeRadius * Math.cos(theta) * Math.sin(phi);
    const y = globeRadius * Math.sin(theta) * Math.sin(phi);
    const z = globeRadius * Math.cos(phi);

    nodePositions[i * 3] = x;
    nodePositions[i * 3 + 1] = y;
    nodePositions[i * 3 + 2] = z;

    const chosenColor = Math.random() > 0.6 ? colorCyan : (Math.random() > 0.3 ? colorIndigo : colorEmerald);
    nodeColors[i * 3] = chosenColor.r;
    nodeColors[i * 3 + 1] = chosenColor.g;
    nodeColors[i * 3 + 2] = chosenColor.b;
  }

  const nodeGeo = new THREE.BufferGeometry();
  nodeGeo.setAttribute("position", new THREE.BufferAttribute(nodePositions, 3));
  nodeGeo.setAttribute("color", new THREE.BufferAttribute(nodeColors, 3));

  const nodeMat = new THREE.PointsMaterial({
    size: 2.4,
    map: dotTexture,
    vertexColors: true,
    transparent: true,
    opacity: 0.5,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });

  const nodePoints = new THREE.Points(nodeGeo, nodeMat);
  globeGroup.add(nodePoints);

  // 4. Glowing Inter-Continental Arcs (Decentralized Consensus Lines)
  const arcMaterial = new THREE.LineBasicMaterial({
    color: 0x38bdf8,
    transparent: true,
    opacity: 0.25,
  });

  for (let i = 0; i < 14; i++) {
    const idx1 = Math.floor(Math.random() * nodeCount);
    const idx2 = Math.floor(Math.random() * nodeCount);

    const v1 = new THREE.Vector3(
      nodePositions[idx1 * 3],
      nodePositions[idx1 * 3 + 1],
      nodePositions[idx1 * 3 + 2]
    );
    const v2 = new THREE.Vector3(
      nodePositions[idx2 * 3],
      nodePositions[idx2 * 3 + 1],
      nodePositions[idx2 * 3 + 2]
    );

    // Midpoint elevated away from center to create 3D arc
    const mid = new THREE.Vector3().addVectors(v1, v2).multiplyScalar(0.5);
    const distance = v1.distanceTo(v2);
    mid.normalize().multiplyScalar(globeRadius + distance * 0.25);

    const curve = new THREE.QuadraticBezierCurve3(v1, mid, v2);
    const curvePoints = curve.getPoints(24);
    const curveGeo = new THREE.BufferGeometry().setFromPoints(curvePoints);
    const arcLine = new THREE.Line(curveGeo, arcMaterial);
    globeGroup.add(arcLine);
  }

  // 5. Surrounding Deep Space Particle Stars (Distant Layer)
  const starCount = 350;
  const starPositions = new Float32Array(starCount * 3);
  for (let i = 0; i < starCount; i++) {
    const r = 90 + Math.random() * 80;
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos((Math.random() * 2) - 1);

    starPositions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
    starPositions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
    starPositions[i * 3 + 2] = -40 + r * Math.cos(phi);
  }

  const starGeo = new THREE.BufferGeometry();
  starGeo.setAttribute("position", new THREE.BufferAttribute(starPositions, 3));
  const starMat = new THREE.PointsMaterial({
    size: 1.6,
    color: 0x94a3b8,
    transparent: true,
    opacity: 0.25,
  });
  const starField = new THREE.Points(starGeo, starMat);
  scene.add(starField);

  // Mouse Parallax Physics
  let mouseX = 0;
  let mouseY = 0;
  let targetX = 0;
  let targetY = 0;

  window.addEventListener("mousemove", (e) => {
    mouseX = (e.clientX - window.innerWidth / 2) * 0.04;
    mouseY = (e.clientY - window.innerHeight / 2) * 0.04;
  });

  window.addEventListener("resize", () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });

  // Render Loop
  function animate() {
    requestAnimationFrame(animate);

    targetX += (mouseX - targetX) * 0.035;
    targetY += (mouseY - targetY) * 0.035;

    // Continuous globe rotation on Y axis
    globeGroup.rotation.y += 0.0012;
    globeGroup.rotation.x = 0.15 + targetY * 0.008;
    globeGroup.rotation.z = targetX * 0.005;

    starField.rotation.y += 0.0002;

    // Camera Parallax
    camera.position.x = targetX * 0.35;
    camera.position.y = -targetY * 0.35;
    camera.lookAt(scene.position);

    renderer.render(scene, camera);
  }

  animate();
}

/* =========================================================================
   2. CARD PHYSICS
   ========================================================================= */
function initTiltPhysics() {
  // Slanting and tilting on hover disabled
}

/* =========================================================================
   3. APPLICATION LOGIC
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
  const blockNumVal = document.getElementById("blockNumVal");
  const contractVal = document.getElementById("contractVal");
  const payloadHashVal = document.getElementById("payloadHashVal");
  const networkBadge = document.getElementById("networkBadge");

  // Stage 2: Media Image & Candidates Drawer
  const matchAvatarImg = document.getElementById("matchAvatarImg");
  const matchAvatarPlaceholder = document.getElementById("matchAvatarPlaceholder");
  const matchImagePreviewContainer = document.getElementById("matchImagePreviewContainer");
  const matchPreviewImg = document.getElementById("matchPreviewImg");
  const previewUrlLink = document.getElementById("previewUrlLink");
  const matchPreviewTag = document.getElementById("matchPreviewTag");
  const btnToggleCandidates = document.getElementById("btnToggleCandidates");
  const candidatesCount = document.getElementById("candidatesCount");
  const candidatesDrawer = document.getElementById("candidatesDrawer");
  const candidatesGrid = document.getElementById("candidatesGrid");

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

  let currentFile = null;
  let currentAttestationId = null;

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
    tamperDiffContainer.classList.add("hidden");
    laserScanner.classList.add("scanning");

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
      laserScanner.classList.remove("scanning");
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
      laserScanner.classList.remove("scanning");

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
      laserScanner.classList.remove("scanning");
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

    // Render Top K Candidates Gallery
    const candidates = match.top_candidates || (match.raw_metadata && match.raw_metadata.top_candidates) || [];
    if (candidates && candidates.length > 0) {
      if (btnToggleCandidates) {
        btnToggleCandidates.classList.remove("hidden");
        btnToggleCandidates.classList.remove("active");
        if (candidatesCount) candidatesCount.textContent = candidates.length;
      }
      if (candidatesDrawer) candidatesDrawer.classList.add("hidden");

      if (candidatesGrid) {
        candidatesGrid.innerHTML = candidates.map((cand) => {
          const isTopMatch = cand.similarity === match.visual_similarity_score;
          const simPct = cand.similarity_pct !== undefined ? cand.similarity_pct : ((cand.similarity || 0) * 100).toFixed(1);
          const isLow = (cand.similarity || 0) < 0.40;
          return `
            <div class="candidate-card ${isTopMatch ? "is-top" : ""}">
              <div class="candidate-thumb-wrap">
                <img src="${cand.image_url}" alt="${cand.title || "Match"}" class="candidate-thumb" loading="lazy" onerror="this.style.display='none'">
                <span class="candidate-rank-badge">#${cand.rank || 1}</span>
                <span class="candidate-sim-pill ${isLow ? "low" : ""}">${simPct}%</span>
              </div>
              <div class="candidate-body">
                <div class="candidate-title" title="${cand.title || ""}">${cand.title || "Web Result"}</div>
                <div class="candidate-author">${cand.platform || "Web"} • ${cand.author || "-"}</div>
                ${cand.url ? `<a href="${cand.url}" target="_blank" class="candidate-link"><span>View Source</span> ↗</a>` : ""}
              </div>
            </div>
          `;
        }).join("");
      }
    } else {
      if (btnToggleCandidates) btnToggleCandidates.classList.add("hidden");
      if (candidatesDrawer) candidatesDrawer.classList.add("hidden");
    }

    // Stage 3: Blockchain Record
    const att = data.blockchain_attestation || {};
    currentAttestationId = att.id || null;
    txHashVal.textContent = att.tx_hash || "-";
    blockNumVal.textContent = att.block_number ? `#${att.block_number}` : "-";
    contractVal.textContent = att.contract_address || "-";
    payloadHashVal.textContent = att.payload_hash || "-";
    networkBadge.textContent = att.network_name || "EVM";

    // Stage 4: Tamper Verification
    const ver = data.verification || {};
    renderVerificationState(ver.is_valid !== false);
  }

  function renderVerificationState(isValid) {
    if (isValid) {
      verBanner.className = "audit-banner-3d success";
      verStatusBadge.className = "badge-3d badge-green";
      verStatusBadge.textContent = "Verified";
      verTitle.textContent = "Data Verified";
      verDescription.textContent = "The current data matches the blockchain record exactly.";
    } else {
      verBanner.className = "audit-banner-3d danger";
      verStatusBadge.className = "badge-3d badge-rose";
      verStatusBadge.textContent = "Tampered";
      verTitle.textContent = "Tamper Detected";
      verDescription.textContent = "Data has been altered and does not match the blockchain record.";
    }
  }

  // Interactive Tamper Simulation
  btnTamperTest.addEventListener("click", async () => {
    if (!currentAttestationId) {
      alert("Please run a verification scan first.");
      return;
    }

    btnTamperTest.disabled = true;
    btnTamperTest.querySelector("span").textContent = "Testing Tamper...";

    try {
      const res = await fetch(`/api/pipeline/tamper-test/${currentAttestationId}`, {
        method: "POST",
      });

      if (!res.ok) throw new Error("Tamper test endpoint returned error");
      const data = await res.json();

      const genuine = data.genuine_verification;
      const tampered = data.tampered_verification;

      tamperDiffContainer.classList.remove("hidden");
      tamperDiffContainer.innerHTML = `
        <table class="audit-3d-table">
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
              <td class="mono">${genuine.calculated_payload_hash.slice(0, 18)}...</td>
              <td class="mono">${genuine.onchain_payload_hash.slice(0, 18)}...</td>
              <td style="color: #34d399; font-weight: 800;">VALID (Match)</td>
            </tr>
            <tr>
              <td style="color: #fb7185; font-weight: 700;">Modified Data</td>
              <td class="mono">${tampered.calculated_payload_hash.slice(0, 18)}...</td>
              <td class="mono">${tampered.onchain_payload_hash.slice(0, 18)}...</td>
              <td style="color: #fb7185; font-weight: 800;">TAMPERED (Mismatch)</td>
            </tr>
          </tbody>
        </table>
      `;

      renderVerificationState(false);
    } catch (err) {
      alert(`Tamper Test Error: ${err.message}`);
    } finally {
      btnTamperTest.querySelector("span").textContent = "Simulate Tampering";
      btnTamperTest.disabled = false;
    }
  });

  // History Table
  btnRefreshHistory.addEventListener("click", loadLedger);
  loadLedger();

  async function loadLedger() {
    try {
      const res = await fetch("/api/pipeline/history?limit=30");
      if (!res.ok) {
        historyTableBody.innerHTML = `
          <tr><td colspan="8" class="table-loading-3d" style="color: #f43f5e;">Failed to load records (HTTP ${res.status}). Click Refresh above.</td></tr>
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
            <td colspan="8" class="table-loading-3d">No verification records found yet. Run a scan in the pipeline tab.</td>
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
            <td><button class="btn-verify-row-3d btn-row-action" data-id="${attId}">Test Tamper</button></td>
          </tr>
        `;
      }).join("");

      document.querySelectorAll(".btn-row-action").forEach((btn) => {
        btn.addEventListener("click", () => {
          currentAttestationId = btn.dataset.id;
          if (tabBtnPipeline) tabBtnPipeline.click();
          btnTamperTest.click();
        });
      });
    } catch (err) {
      console.warn("[Verification History] Load error:", err);
      historyTableBody.innerHTML = `
        <tr><td colspan="8" class="table-loading-3d" style="color: #f43f5e;">Could not load history: ${err.message}. Click Refresh to retry.</td></tr>
      `;
    }
  }

  // Stepper Management Utilities
  function setStepActive(n, msg) {
    const rows = [pStep1, pStep2, pStep3, pStep4];
    const descs = [pStep1Desc, pStep2Desc, pStep3Desc, pStep4Desc];
    const row = rows[n - 1];
    if (!row) return;
    row.className = "step-3d-row active";
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
    row.className = "step-3d-row completed";
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
      if (r) r.className = "step-3d-row";
      if (orbs[i]) orbs[i].textContent = String(i + 1);
      if (descs[i]) descs[i].textContent = defaultLabels[i];
    });
    conns.forEach((c) => {
      if (c) c.classList.remove("completed");
    });
  }
}
