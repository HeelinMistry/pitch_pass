import { apiRequest } from './api.js';
import { initPageTransition } from './ui.js';

export async function initDashboard() {
    initPageTransition();
    // 2. Initialize UI Components
    setupModalLogic();
    setupSteppers();

    // 3. Initial Data Load
    loadDashboardData();

    // 4. Attach Form Submission
    const generateBtn = document.getElementById('generateBtn');
    if (generateBtn) {
        // Remove the arrow function that doesn't execute anything
        // and point it directly to handleCreateMatch
        generateBtn.onclick = handleCreateMatch;
    }
}

/**
 * UI: Modal Toggle Logic
 */
function setupModalLogic() {
    const modal = document.getElementById('createMatchModal');

    window.openModal = () => {
        modal.classList.remove('hidden');
        setTimeout(() => modal.classList.remove('opacity-0'), 10);
    };

    window.closeModal = () => {
        modal.classList.add('opacity-0');
        setTimeout(() => modal.classList.add('hidden'), 300);
    };
}

/**
 * UI: Stepper Logic for Roster and Duration
 */
function setupSteppers() {
    let rosterCount = 14;
    const rosterDisplay = document.getElementById('rosterDisplay');

    document.getElementById('rosMinus').onclick = () => {
        if (rosterCount > 2) {
            rosterCount--;
            rosterDisplay.innerText = rosterCount;
        }
    };
    document.getElementById('rosPlus').onclick = () => {
        rosterCount++;
        rosterDisplay.innerText = rosterCount;
    };

    let duration = 1.0;
    const durationLabel = document.getElementById('durationLabel');

    document.getElementById('durMinus').onclick = () => {
        if (duration > 0.5) {
            duration -= 0.5;
            durationLabel.innerText = `${duration.toFixed(1)} Hr`;
        }
    };

    document.getElementById('durPlus').onclick = () => {
        if (duration < 5.0) {
            duration += 0.5;
            durationLabel.innerText = `${duration.toFixed(1)} Hr`;
        }
    };
}

/**
 * Render Dashboard
 */

function renderMatches(matches) {
    const container = document.getElementById('match-container');
    // Keep the header, clear the cards
    const header = container.querySelector('div');
    container.innerHTML = '';
    container.appendChild(header);

    if (!matches || matches.length === 0) {
        container.innerHTML = `<p class="text-pitch-outline">No matches found.</p>`;
        return;
    }

    matches.forEach(match => {
        const dateObj = new Date(match.date);
        const day = dateObj.getDate() || "??";
        const month = dateObj.toLocaleString('default', { month: 'short' }).toUpperCase() || "TBD";

        const isCancelled = match.is_cancelled === true;
        const isJoined = match.is_joined === true;

        let dateBoxClasses = "";
        if (isCancelled) {
            // Priority 1: Cancelled Style
            dateBoxClasses = "cancelled-date-box opacity-50 grayscale-[0.2]";
        } else if (isJoined) {
            // Priority 2: Joined Style (Muted/Settled)
            dateBoxClasses = "joined-date-box opacity-70";
        } else {
            // Priority 3: Neutral Style (Neon/Active - "Grab Spot")
            dateBoxClasses = "date-box opacity-60 grayscale-[0.5]";
        }

        const card = `
            <div class="match-card group relative rounded-2xl overflow-hidden flex flex-col md:flex-row transition-all border">

                <div class="p-6 md:w-24 ${dateBoxClasses}">
                    <span class="text-3xl font-black leading-none">${day}</span>
                    <span class="text-[10px] font-bold tracking-widest">${month}</span>
                </div>

                <div class="flex-1 p-6 flex flex-col md:flex-row justify-between items-center gap-6">
                    <div class="space-y-1">
                        <div class="flex items-center gap-2">
                            <p class="text-[10px] text-pitch-outline font-bold uppercase tracking-[0.2em]">${match.time || 'TBD'}</p>
                            ${isCancelled ? '<span class="bg-red-500/20 text-red-500 text-[9px] px-2 py-0.5 rounded-full font-black uppercase tracking-widest">Cancelled</span>' : ''}
                        </div>

                        <h4 class="font-headline text-2xl font-black uppercase italic ${isCancelled ? 'line-through text-pitch-outline' : ''}">
                            ${match.title}
                        </h4>

                        <p class="text-xs text-pitch-outline flex items-center gap-1">
                            <span class="material-symbols-outlined text-sm">location_on</span> ${match.location}
                        </p>
                    </div>

                    <button class="px-8 py-3 rounded-xl text-xs font-black uppercase tracking-widest transition-all"
                        onclick="window.location.href='match_details.html?id=${match.id}'">
                        Details
                    </button>
                </div>
            </div>
        `;
        container.insertAdjacentHTML('beforeend', card);
    });
}

function renderActivity(matches) {
    const activityFeed = document.getElementById('activity-feed');
    activityFeed.innerHTML = '';

    matches.slice(0, 3).forEach(match => {
        const item = `
            <div class="flex gap-4 items-start">
                <div class="w-8 h-8 rounded-full bg-pitch-green/10 flex items-center justify-center text-pitch-green">
                    <span class="material-symbols-outlined text-sm">stadium</span>
                </div>
                <div>
                    <p class="text-xs font-bold uppercase tracking-tight">Match Drafted</p>
                    <p class="text-[10px] text-pitch-outline">${match.title}</p>
                </div>
            </div>
        `;
        activityFeed.insertAdjacentHTML('beforeend', item);
    });
}

/**
 * Data: Backend
 */
async function handleCreateMatch() {
    const btn = document.getElementById('generateBtn');
    const originalText = btn.innerHTML;

    // Gather data from your dashboard.html IDs
    const payload = {
        title: document.getElementById('matchTitle')?.value || "Untitled Match",
        sport: document.getElementById('sportType').value,
        duration: parseFloat(document.getElementById('durationLabel').innerText),
        date_event: document.getElementById('matchDate')?.value || "TBD",
        time: document.getElementById('matchTime')?.value || "TBD",
        location: document.getElementById('matchLocation')?.value || "TBD",
        roster_size: parseInt(document.getElementById('rosterDisplay').innerText),
        cost: parseFloat(document.getElementById('matchCost')?.value) || 0
    };

    try {
        btn.innerHTML = "Deploying...";
        btn.disabled = true;

        // Use the full endpoint defined in matches.py
        const resp = await apiRequest('/matches/create', 'POST', payload);

        if (resp && resp.status === 'success') {
            window.closeModal();
            // Refresh the list so the new match appears
            await loadDashboardData();
        }
    } catch (err) {
        console.error("Match creation failed:", err);
        alert("Failed to create match. Check console.");
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}


async function loadDashboardData() {
    try {
        // apiRequest already returns the parsed JSON array
        const matches = await apiRequest('/matches');

        // Ensure we actually got data before trying to render
        if (matches && Array.isArray(matches)) {
            renderMatches(matches);
            renderActivity(matches);
        } else {
            console.warn("No matches found or invalid format received");
            renderMatches([]); // Render empty state
        }
    } catch (err) {
        console.error("Dashboard failed to load matches:", err);
    }
}