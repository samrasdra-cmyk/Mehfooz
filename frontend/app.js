/**
 * Mehfooz - Frontend Dashboard Application
 * Connects to FastAPI backend, Leaflet maps, Chart.js telemetry & Speech Synthesis
 */

document.addEventListener("DOMContentLoaded", () => {
    // State
    const state = {
        currentRegion: "shishper_lake",
        regions: {},
        currentAnalysis: null,
        history: [],
        currentLang: "en",
        translations: {
            en: "All parameters within safe threshold. Regular satellite observation continues.",
            ur: "[اردو] شیشپر جھیل کے تمام اشارے محفوظ حد کے اندر ہیں۔ مصنوعی سیارے کے ذریعے باقاعدہ مشاہدہ جاری ہے۔",
            sd: "[سنڌي] ششپر ڍنڍ جا سڀ اشارا محفوظ حد اندر آھن. باقاعده سيٽلائيٽ مشاهدو جاري آهي.",
            ps: "[پښتو] د ششپر جهيل ټول شاخصونه په خوندي حد کې دي. منظم سپوږمکۍ څارنه دوام لري."
        }
    };

    // DOM Elements
    const regionSelect = document.getElementById("regionSelect");
    const regionCoords = document.getElementById("regionCoords");
    const regionBasin = document.getElementById("regionBasin");
    const regionRecipients = document.getElementById("regionRecipients");
    const regionThreat = document.getElementById("regionThreat");
    const analysisDate = document.getElementById("analysisDate");
    const triggerBtn = document.getElementById("triggerBtn");

    const riskScoreVal = document.getElementById("riskScoreVal");
    const riskLevelBadge = document.getElementById("riskLevelBadge");
    const gaugeFill = document.getElementById("gaugeFill");
    const lakeAreaVal = document.getElementById("lakeAreaVal");
    const channelsVal = document.getElementById("channelsVal");
    const snowmeltVal = document.getElementById("snowmeltVal");
    const expansionVal = document.getElementById("expansionVal");
    const aiDescriptionText = document.getElementById("aiDescriptionText");

    const alertText = document.getElementById("alertText");
    const alertStateBadge = document.getElementById("alertStateBadge");
    const langTabs = document.querySelectorAll(".lang-tab");
    const playVoiceBtn = document.getElementById("playVoiceBtn");
    const voiceStatusText = document.getElementById("voiceStatusText");
    const smsFeed = document.getElementById("smsFeed");
    const toast = document.getElementById("toastNotification");
    const toastTitle = document.getElementById("toastTitle");
    const toastMessage = document.getElementById("toastMessage");

    // Initialize Default Date to Today
    const today = new Date().toISOString().split("T")[0];
    analysisDate.value = today;

    // Live UTC Clock
    function updateClock() {
        const now = new Date();
        document.getElementById("liveClock").textContent = now.toUTCString().replace("GMT", "UTC");
    }
    setInterval(updateClock, 1000);
    updateClock();

    // Leaflet Map Initialization
    const map = L.map("pakistanMap", {
        zoomControl: true,
        attributionControl: false
    }).setView([36.25, 74.65], 11);

    const satelliteLayer = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", {
        maxZoom: 18,
    }).addTo(map);

    const topoLayer = L.tileLayer("https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png", {
        maxZoom: 17,
    });

    document.getElementById("btnLayerSat").addEventListener("click", function() {
        this.classList.add("active");
        document.getElementById("btnLayerTopo").classList.remove("active");
        map.removeLayer(topoLayer);
        map.addLayer(satelliteLayer);
    });

    document.getElementById("btnLayerTopo").addEventListener("click", function() {
        this.classList.add("active");
        document.getElementById("btnLayerSat").classList.remove("active");
        map.removeLayer(satelliteLayer);
        map.addLayer(topoLayer);
    });

    let mapMarker = null;
    let mapPolygon = null;

    // Chart.js Telemetry Chart
    const ctx = document.getElementById("trendChart").getContext("2d");
    const trendChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: [],
            datasets: [
                {
                    label: "Lake Area (km²)",
                    data: [],
                    borderColor: "#06b6d4",
                    backgroundColor: "rgba(6, 182, 212, 0.1)",
                    fill: true,
                    tension: 0.35,
                    yAxisID: "y"
                },
                {
                    label: "Risk Score (0-1)",
                    data: [],
                    borderColor: "#ef4444",
                    backgroundColor: "transparent",
                    borderDash: [5, 5],
                    tension: 0.35,
                    yAxisID: "y1"
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: "index", intersect: false },
            plugins: {
                legend: {
                    labels: { color: "#9ca3af", font: { family: "Inter", size: 11 } }
                }
            },
            scales: {
                x: {
                    grid: { color: "rgba(255, 255, 255, 0.05)" },
                    ticks: { color: "#6b7280", font: { size: 10 } }
                },
                y: {
                    type: "linear",
                    display: true,
                    position: "left",
                    grid: { color: "rgba(255, 255, 255, 0.05)" },
                    ticks: { color: "#06b6d4" },
                    title: { display: true, text: "Area (km²)", color: "#06b6d4", font: { size: 10 } }
                },
                y1: {
                    type: "linear",
                    display: true,
                    position: "right",
                    min: 0,
                    max: 1.0,
                    grid: { drawOnChartArea: false },
                    ticks: { color: "#ef4444" },
                    title: { display: true, text: "Risk Index", color: "#ef4444", font: { size: 10 } }
                }
            }
        }
    });

    // Fetch Regions Registry
    async function loadRegions() {
        try {
            const res = await fetch("/regions");
            if (!res.ok) throw new Error("Failed to fetch regions");
            state.regions = await res.json();

            // Populate selector
            regionSelect.innerHTML = "";
            Object.entries(state.regions).forEach(([id, data]) => {
                const opt = document.createElement("option");
                opt.value = id;
                opt.textContent = `${data.name}`;
                regionSelect.appendChild(opt);
            });

            if (state.regions[state.currentRegion]) {
                regionSelect.value = state.currentRegion;
                updateRegionMeta(state.currentRegion);
            }
        } catch (err) {
            console.warn("Using offline fallback region configuration:", err);
            state.regions = {
                "shishper_lake": {
                    "name": "Shishper Glacial Lake",
                    "bbox": [74.55, 36.15, 74.65, 36.25],
                    "lat": 36.2,
                    "lon": 74.6,
                    "recipients": ["+920000000001"]
                },
                "passu_lake": {
                    "name": "Passu Glacial Lake",
                    "bbox": [74.85, 36.35, 74.95, 36.45],
                    "lat": 36.4,
                    "lon": 74.9,
                    "recipients": ["+920000000002"]
                }
            };
            updateRegionMeta(state.currentRegion);
        }
    }

    function updateRegionMeta(regionId) {
        const region = state.regions[regionId];
        if (!region) return;

        regionCoords.textContent = `${region.lat.toFixed(2)}° N, ${region.lon.toFixed(2)}° E`;
        regionBasin.textContent = regionId.includes("shishper") ? "Hunza Valley / Hassanabad" : "Gojal / Passu Glacier";
        regionRecipients.textContent = `${region.recipients.length} Emergency Cell(s)`;
        regionThreat.textContent = "High Surge Threat";

        // Update Map
        map.setView([region.lat, region.lon], 12);

        if (mapMarker) map.removeLayer(mapMarker);
        if (mapPolygon) map.removeLayer(mapPolygon);

        const customIcon = L.divIcon({
            className: 'custom-map-icon',
            html: `<div style="background:#06b6d4; width:18px; height:18px; border-radius:50%; border:3px solid #fff; box-shadow:0 0 12px #06b6d4;"></div>`,
            iconSize: [18, 18],
            iconAnchor: [9, 9]
        });

        mapMarker = L.marker([region.lat, region.lon], { icon: customIcon }).addTo(map)
            .bindPopup(`<strong>${region.name}</strong><br>Coordinates: ${region.lat}, ${region.lon}`)
            .openPopup();

        if (region.bbox) {
            const [minLon, minLat, maxLon, maxLat] = region.bbox;
            const bounds = [[minLat, minLon], [maxLat, maxLon]];
            mapPolygon = L.rectangle(bounds, {
                color: "#06b6d4",
                weight: 2,
                fillColor: "#06b6d4",
                fillOpacity: 0.15,
                dashArray: "4, 6"
            }).addTo(map);
        }

        loadHistory(regionId);
    }

    // Fetch History & Update Chart
    async function loadHistory(regionId) {
        try {
            const res = await fetch(`/history/${regionId}?limit=15`);
            if (!res.ok) return;
            const records = await res.json();
            state.history = records.reverse(); // chronological

            const labels = state.history.map(r => r.date || new Date(r.created_at).toLocaleDateString());
            const areas = state.history.map(r => r.lake_area_km2);
            const risks = state.history.map(r => r.risk_score);

            trendChart.data.labels = labels;
            trendChart.data.datasets[0].data = areas;
            trendChart.data.datasets[1].data = risks;
            trendChart.update();

            document.getElementById("historyCount").textContent = `${state.history.length} Telemetry Records`;
        } catch (err) {
            console.error("Failed to load history:", err);
        }
    }

    // Trigger Analysis Pipeline
    async function triggerAnalysis() {
        const regionId = regionSelect.value;
        const dateVal = analysisDate.value;
        
        triggerBtn.disabled = true;
        triggerBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> <span>Processing Pipeline...</span>`;

        try {
            const url = `/trigger-analysis/${regionId}${dateVal ? `?run_date=${dateVal}` : ''}`;
            const res = await fetch(url, { method: "POST" });
            if (!res.ok) throw new Error(await res.text());
            const data = await res.json();
            
            state.currentAnalysis = data;
            renderAnalysisResult(data);
            showToast("Analysis Completed", `Processed ${data.region_name} for ${data.date}`);
            
            // Reload history to show updated chart
            await loadHistory(regionId);
        } catch (err) {
            showToast("Pipeline Error", err.message, true);
        } finally {
            triggerBtn.disabled = false;
            triggerBtn.innerHTML = `<i class="fa-solid fa-satellite-dish"></i> <span>Run AI Pipeline Analysis</span>`;
        }
    }

    // Render Pipeline Results on UI
    function renderAnalysisResult(data) {
        const risk = data.risk;
        const analysis = data.analysis;

        // Risk Score & Dial
        const score = risk.risk_score;
        riskScoreVal.textContent = score.toFixed(2);
        
        // Gauge Math: total stroke length = 126
        const strokeOffset = Math.max(0, 126 - (score * 126));
        gaugeFill.style.strokeDashoffset = strokeOffset;

        if (score < 0.35) {
            gaugeFill.style.stroke = "#10b981";
            riskLevelBadge.className = "status-pill safe";
            riskLevelBadge.textContent = "Low Risk";
            alertStateBadge.textContent = "Safe Status";
            alertStateBadge.className = "badge-pulse";
        } else if (score < 0.65) {
            gaugeFill.style.stroke = "#f59e0b";
            riskLevelBadge.className = "status-pill warning";
            riskLevelBadge.textContent = "Moderate Warning";
            alertStateBadge.textContent = "Advisory Alert";
            alertStateBadge.className = "badge-pulse highlight-amber";
        } else {
            gaugeFill.style.stroke = "#ef4444";
            riskLevelBadge.className = "status-pill critical";
            riskLevelBadge.textContent = "CRITICAL HAZARD";
            alertStateBadge.textContent = "EMERGENCY BROADCAST";
            alertStateBadge.className = "badge-pulse status-pill critical";
        }

        // Metrics
        lakeAreaVal.textContent = `${analysis.lake_area_km2.toFixed(2)} km²`;
        channelsVal.textContent = analysis.new_channels ? "Breach Channels Active" : "None Detected";
        snowmeltVal.textContent = analysis.snowmelt_acceleration ? analysis.snowmelt_acceleration.toUpperCase() : "NORMAL";
        expansionVal.textContent = `${(risk.components.expansion_factor || 1.0).toFixed(2)}x`;
        aiDescriptionText.textContent = analysis.description || "Scene analysis completed.";

        // Alerts & Translations
        if (data.alerts && data.alerts.length > 0) {
            const primaryAlert = data.alerts[0];
            state.translations.en = primaryAlert.message || "GLOF Alert dispatched.";
            state.translations.ur = `[اردو] ہوشیار: ${data.region_name} کے خطرے کا اسکور ${score.toFixed(2)} تک پہنچ گیا ہے۔ براہ کرم محفوظ بلندی پر منتقل ہوں۔`;
            state.translations.sd = `[سنڌي] خبردار: ${data.region_name} لاءِ خطري جو اسڪور ${score.toFixed(2)} آهي. فوري طور تي محفوظ هنڌن ڏانهن وڃو.`;
            state.translations.ps = `[پښتو] خبرداری: د ${data.region_name} لپاره د خطر کچه ${score.toFixed(2)} ده. مهرباني وکړئ لوړو سیمو ته کډه شئ.`;
            
            // Populate SMS dispatch
            smsFeed.innerHTML = "";
            data.alerts.forEach(alert => {
                const item = document.createElement("div");
                item.className = "sms-item";
                item.innerHTML = `
                    <div class="sms-head">
                        <span class="sms-to"><i class="fa-solid fa-tower-broadcast"></i> ${alert.recipient}</span>
                        <span class="sms-time">${data.date}</span>
                    </div>
                    <div class="sms-body">${alert.message}</div>
                `;
                smsFeed.appendChild(item);
            });
        } else {
            state.translations.en = `Normal baseline for ${data.region_name}. Surface area: ${analysis.lake_area_km2.toFixed(2)} km².`;
            state.translations.ur = `[اردو] ${data.region_name} میں حالات معمول کے مطابق ہیں، رقبہ ${analysis.lake_area_km2.toFixed(2)} مربع کلومیٹر ہے۔`;
            state.translations.sd = `[سنڌي] ${data.region_name} ۾ صورتحال نارمل آهي، ڪو ايمرجنسي خطرو ناهي.`;
            state.translations.ps = `[پښتو] په ${data.region_name} کې وضعیت عادي دی، کوم بېړنی خطر نشته.`;
        }

        updateAlertDisplay();
    }

    function updateAlertDisplay() {
        const lang = state.currentLang;
        alertText.textContent = state.translations[lang] || state.translations.en;
        if (lang === "ur" || lang === "sd" || lang === "ps") {
            alertText.classList.add("urdu-font");
        } else {
            alertText.classList.remove("urdu-font");
        }
    }

    // Language Tab Switching
    langTabs.forEach(tab => {
        tab.addEventListener("click", () => {
            langTabs.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");
            state.currentLang = tab.dataset.lang;
            updateAlertDisplay();
        });
    });

    // Voice Synthesis Playback (Web Speech API)
    playVoiceBtn.addEventListener("click", () => {
        if (!('speechSynthesis' in window)) {
            voiceStatusText.textContent = "Audio speech unavailable";
            return;
        }

        window.speechSynthesis.cancel();
        const textToSpeak = alertText.textContent;
        const utterance = new SpeechSynthesisUtterance(textToSpeak);

        const langMap = {
            en: 'en-US',
            ur: 'ur-PK',
            sd: 'sd-PK',
            ps: 'ps-AF'
        };
        utterance.lang = langMap[state.currentLang] || 'en-US';
        utterance.rate = 0.95;

        utterance.onstart = () => {
            voiceStatusText.textContent = "Broadcasting alert audio...";
            playVoiceBtn.classList.add("pulse");
        };

        utterance.onend = () => {
            voiceStatusText.textContent = "Broadcast finished";
            playVoiceBtn.classList.remove("pulse");
        };

        utterance.onerror = () => {
            voiceStatusText.textContent = "Playback error";
            playVoiceBtn.classList.remove("pulse");
        };

        window.speechSynthesis.speak(utterance);
    });

    // Toast Function
    function showToast(title, message, isError = false) {
        toastTitle.textContent = title;
        toastMessage.textContent = message;
        toast.querySelector(".toast-icon").className = isError 
            ? "fa-solid fa-circle-exclamation toast-icon text-warning" 
            : "fa-solid fa-circle-check toast-icon text-emerald";
        
        toast.classList.remove("hidden");
        setTimeout(() => {
            toast.classList.add("hidden");
        }, 4000);
    }

    // Event Listeners
    regionSelect.addEventListener("change", (e) => {
        state.currentRegion = e.target.value;
        updateRegionMeta(state.currentRegion);
    });

    triggerBtn.addEventListener("click", triggerAnalysis);

    // Initial Load
    loadRegions();
});
