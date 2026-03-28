/**
 * Standard page entry transition
 */
export function initPageTransition() {
    document.body.style.opacity = "1";
}

/**
 * Universal Modal Controller
 * Expects #confirmModal, #confirmTitle, #confirmMessage, and #confirmActionBtn in HTML
 */
let pendingAction = null;

export function openConfirmModal(title, msg, action, isError = false) {
    const modal = document.getElementById('confirmModal');
    if (!modal) return;

    document.getElementById('confirmTitle').innerText = title;
    document.getElementById('confirmMessage').innerText = msg;

    const actionBtn = document.getElementById('confirmActionBtn');
    actionBtn.className = isError
        ? "flex-1 py-3 rounded-xl font-bold text-xs bg-error text-white"
        : "flex-1 py-3 rounded-xl font-bold text-xs bg-primary-container text-black";

    pendingAction = action;
    modal.classList.remove('hidden');
    setTimeout(() => modal.classList.remove('opacity-0'), 10);
}

export function closeConfirmModal() {
    const modal = document.getElementById('confirmModal');
    modal.classList.add('opacity-0');
    setTimeout(() => modal.classList.add('hidden'), 300);
}

// Hook up the close button globally if it exists
document.getElementById('closeModalBtn')?.addEventListener('click', closeConfirmModal);
document.getElementById('confirmActionBtn')?.addEventListener('click', () => {
    if (pendingAction) pendingAction();
    closeConfirmModal();
});