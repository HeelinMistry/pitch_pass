const API_URL = 'http://localhost:8000/api';

export async function initDashboard() {
    // 1. Check for Token (Secure the Route)
    const token = localStorage.getItem('pitchpass_token');
    if (!token) {
        window.location.href = 'login.html';
        return;
    }

    // 2. Initialize UI Components
    setupModalLogic();
    setupSteppers();

    // 3. Initial Data Load
    await loadDashboardData(token);

    // 4. Attach Form Submission
    const generateBtn = document.getElementById('generateBtn');
    if (generateBtn) {
        generateBtn.onclick = () => handleCreateMatch(token);
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
 * Data: Create Match on Backend
 */
async function handleCreateMatch(token) {
    const btn = document.getElementById('generateBtn');
    const originalText = btn.innerHTML;

    const payload = {
        title: document.getElementById('matchTitle')?.value || "Untitled Match",
        sport: document.getElementById('sportType').value,
        duration: parseInt(document.getElementById('durationLabel').innerText),
        date_event: document.getElementById('matchDate')?.value || "TBD",
        time: document.getElementById('matchTime')?.value || "TBD",
        location: document.getElementById('matchLocation')?.value || "TBD",
        roster_size: parseInt(document.getElementById('rosterDisplay').innerText),
        cost: parseFloat(document.getElementById('matchCost')?.value) || 0
    };

    try {
        btn.innerHTML = "Deploying...";
        const resp = await fetch(`${API_URL}/matches`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(payload)
        });

        if (resp.ok) {
            window.closeModal();
            await loadDashboardData(token); // Refresh the list
        } else {
            console.error("Match creation failed");
        }
    } catch (err) {
        console.error("Network Error:", err);
    } finally {
        btn.innerHTML = originalText;
    }
}

/**
 * Data: Fetch and Render Dashboard
 */
async function loadDashboardData(token) {
    try {
        const response = await fetch(`${API_URL}/dashboard/matches`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.status === 401) {
            localStorage.removeItem('pitchpass_token');
            window.location.href = 'login.html';
            return;
        }

        const matches = await response.json();
        renderMatches(matches);
        renderActivity(matches);
    } catch (err) {
        console.error("API Sync Failed", err);
    }
}

function renderMatches(matches) {
    const container = document.getElementById('match-container');
    // Keep the header, clear the cards
    const header = container.querySelector('div');
    container.innerHTML = '';
    container.appendChild(header);

    matches.forEach(match => {
        const dateObj = new Date(match.date);
        const day = dateObj.getDate() || "??";
        const month = dateObj.toLocaleString('default', { month: 'short' }).toUpperCase() || "TBD";

        const isCancelled = match.is_cancelled === true;
        const isJoined = match.is_joined === true;

        const card = `
            <div class="match-card group relative rounded-2xl overflow-hidden flex flex-col md:flex-row transition-all border
                ${isCancelled ? 'border-red-500/30 opacity-60 grayscale-[0.5]' : 'border-white/5 bg-white/5'}
                ${isJoined ? 'border-white/5 bg-white/5' : 'border-pitch-green/20 bg-pitch-green/[0.02] shadow-[0_0_20px_rgba(202,253,0,0.05)]'}">

                <div class="date-box p-6 md:w-24
                ${isCancelled ? 'bg-red-500 text-white' : 'bg-white-500 text-black'}
                ${isJoined ? 'bg-white-500 text-white' : 'bg-pitch-green text-black'}">
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