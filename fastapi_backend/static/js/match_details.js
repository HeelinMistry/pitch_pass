import { apiRequest } from './api.js';
import { initPageTransition } from './ui.js';

const urlParams = new URLSearchParams(window.location.search);
const matchId = urlParams.get('id');

export async function initMatchDetails() {
    initPageTransition();
    if (!matchId) return window.location.href = 'dashboard.html';

    fetchMatchDetails();
}

async function fetchMatchDetails() {
    try {
        const match = await apiRequest(`/matches/${matchId}`);

        if (match) {
            renderDetails(match);
        } else {
            console.error("Match data is empty");
        }
    } catch (err) {
        console.error("Failed to load match:", err);
    }
}

function renderDetails(match) {
    const container = document.getElementById('match-content');
    const isCancelled = match.is_cancelled;
    const isJoined = match.is_joined;

    // Logic for Buttons
    let actionBtn = "";
    if (isCancelled) {
        actionBtn = match.is_host
            ? `<button onclick="window.promptCancel()" class="w-full py-5 border border-pitch-green text-pitch-green font-black rounded-xl hover:bg-pitch-green/5 transition-all uppercase tracking-widest">Restore Match</button>`
            : `<button onclick="window.promptCancel()" class="w-full py-5 bg-white/5 text-pitch-outline font-black rounded-xl uppercase tracking-widest cursor-not-allowed">Match Cancelled</button>`;
    } else {
        if (isJoined) {
            actionBtn = `<button onclick="window.toggleJoin()" class="w-full py-5 border border-white/10 text-pitch-outline font-black rounded-xl hover:border-red-500 hover:text-red-500 transition-all uppercase tracking-widest flex items-center justify-center gap-2">
                <span class="material-symbols-outlined text-sm">logout</span> Leave Squad
            </button>`;
        } else {
            actionBtn = `<button onclick="window.toggleJoin()" class="w-full py-5 bg-pitch-green text-black font-black rounded-xl hover:shadow-[0_0_20px_rgba(202,253,0,0.3)] transition-all uppercase tracking-widest flex items-center justify-center gap-2">
                <span class="material-symbols-outlined text-sm">sports_soccer</span> Join Squad
            </button>`;
        }
    }

    container.innerHTML = `
        <header class="${isCancelled ? 'opacity-50' : ''}">
            <div class="flex items-center gap-4 mb-4">
                <span class="text-pitch-green font-headline font-black uppercase tracking-[0.3em] text-xs">
                    ${match.sport_type || 'Indoor Soccer'} • ${match.duration || '1.0'}HR
                </span>
                <span class="h-px w-8 bg-white/10"></span>
                <span class="text-pitch-outline text-[10px] font-bold uppercase tracking-widest">Host: ${match.host_username}</span>
            </div>
            <h1 class="text-5xl md:text-8xl font-black font-headline uppercase leading-none italic tracking-tighter mb-10 ${isCancelled ? 'line-through' : ''}">
                ${match.title}
            </h1>

            <div class="flex flex-wrap gap-6">
                <div class="bg-white/5 px-6 py-4 rounded-2xl border border-white/5 flex items-center gap-3">
                    <span class="material-symbols-outlined text-pitch-green">calendar_today</span>
                    <span class="text-xs font-black uppercase tracking-widest">${match.date_event || match.date}</span>
                </div>
                <div class="bg-white/5 px-6 py-4 rounded-2xl border border-white/5 flex items-center gap-3">
                    <span class="material-symbols-outlined text-pitch-green">schedule</span>
                    <span class="text-xs font-black uppercase tracking-widest">${match.time}</span>
                </div>
                <div class="bg-white/5 px-6 py-4 rounded-2xl border border-white/5 flex items-center gap-3">
                    <span class="material-symbols-outlined text-pitch-green">location_on</span>
                    <span class="text-xs font-black uppercase tracking-widest">${match.location}</span>
                </div>
            </div>
        </header>

        <div class="grid grid-cols-1 lg:grid-cols-12 gap-12">
            <div class="lg:col-span-8 ${isCancelled ? 'opacity-40' : ''}">
                <div class="glass-card p-8 border-white/5">
                    <h3 class="font-headline font-bold uppercase tracking-widest text-pitch-outline text-[10px] mb-8">Confirmed Squad (${match.current_roster}/${match.roster_size})</h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        ${match.player_list.map(player => `
                            <div class="flex items-center gap-4 p-4 bg-white/[0.03] rounded-xl border border-white/5 hover:border-pitch-green/20 transition-colors">
                                <div class="w-10 h-10 rounded-full bg-pitch-green text-black flex items-center justify-center font-black text-xs italic">
                                    ${player[0].toUpperCase()}
                                </div>
                                <span class="text-sm font-bold tracking-tight">${player}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>

            <div class="lg:col-span-4 space-y-6">
                <div class="glass-card p-8 border-pitch-green/20 bg-pitch-green/[0.02]">
                    <p class="text-[10px] font-black text-pitch-green uppercase tracking-widest mb-1">Match Fee</p>
                    <h2 class="text-5xl font-headline font-black mb-8 italic">R${match.cost}</h2>
                    ${actionBtn}
                    ${match.is_host && !isCancelled ? `<button onclick="window.promptCancel()" class="w-full mt-4 text-[10px] font-bold text-red-500/60 uppercase tracking-widest hover:text-red-500 transition-colors">Cancel Match</button>` : ''}
                </div>

                <div class="glass-card p-6 border-white/5">
                    <p class="text-[10px] font-black text-pitch-outline uppercase tracking-widest mb-4">Invite Squad</p>
                    <div class="flex items-center gap-2 bg-black/40 p-2 rounded-xl border border-white/5">
                        <input type="text" readonly value="${window.location.href}" class="bg-transparent border-none text-[10px] text-pitch-green font-mono w-full focus:ring-0">
                        <button onclick="window.copyShareLink()" class="p-2 hover:bg-white/10 rounded-lg transition-colors text-pitch-green">
                            <span class="material-symbols-outlined text-sm" id="copyIcon">content_copy</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Global Window Functions for HTML Onclicks
window.copyShareLink = () => {
    navigator.clipboard.writeText(window.location.href);
    const icon = document.getElementById('copyIcon');
    icon.innerText = "check";
    setTimeout(() => icon.innerText = "content_copy", 2000);
};

window.toggleJoin = async () => {
    const resp = await apiRequest(`/matches/${matchId}/toggle-join`, 'POST');
    if (resp) fetchMatchDetails();
};

window.promptCancel = () => {
    openConfirmModal("Cancel Match", "This will call off the game for everyone. Proceed?", async () => {
        await apiRequest(`/matches/${matchId}/toggle-cancel`, 'POST');
        fetchMatchDetails();
    });
};

// MODAL LOGIC
function openConfirmModal(title, msg, action) {
    const modal = document.getElementById('confirmModal');
    document.getElementById('confirmTitle').innerText = title;
    document.getElementById('confirmMessage').innerText = msg;
    const btn = document.getElementById('confirmActionBtn');

    btn.onclick = () => {
        action();
        closeConfirmModal();
    };

    modal.classList.remove('hidden');
    setTimeout(() => modal.classList.remove('opacity-0'), 10);
}

window.closeConfirmModal = () => {
    const modal = document.getElementById('confirmModal');
    modal.classList.add('opacity-0');
    setTimeout(() => modal.classList.add('hidden'), 300);
};