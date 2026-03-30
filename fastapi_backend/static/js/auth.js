import { apiRequest } from './api.js';

// If SimpleWebAuthnBrowser is loaded via script tag in HTML,
// we pull the methods from the global window object.
const { startRegistration, startAuthentication } = window.SimpleWebAuthnBrowser;

/**
 * Helper to determine where to send the user after a successful login
 */
export function getRedirectTarget() {
    const urlParams = new URLSearchParams(window.location.search);
    let target = urlParams.get('redirect');

    if (!target || target.includes('login.html' || target.trim() === "")) {
        return 'dashboard.html';
    }
    return decodeURIComponent(target);
}

/**
 * UI Status Updater
 */
function updateStatus(msg, isError = false) {
    const statusMsg = document.getElementById('statusMessage');
    if (!statusMsg) return;

    statusMsg.textContent = msg;
    statusMsg.style.color = isError ? 'var(--error)' : 'var(--primary-container)';
    statusMsg.classList.toggle('font-bold', true);
}

// --- REGISTRATION LOGIC ---
export async function handleRegister() {
    const username = document.getElementById('username').value;
    if (!username) return updateStatus('Please enter a username', true);

    updateStatus('Requesting biometric setup...');

    try {
        // 1. Get Registration Options from Backend
        const options = await apiRequest(`/auth/register/options/${username}`);
        if (!options) throw new Error("Failed to get registration options");

        // 2. Trigger Browser Biometrics (FaceID/TouchID/Passkey)
        const attestationResponse = await startRegistration({ optionsJSON: options });

        // 3. Verify Response with Backend
        const result = await apiRequest('/auth/register/verify', 'POST', {
            username,
            response: attestationResponse
        });

        if (result.status === 'success') {
            updateStatus('✅ Registered! You can now login.');
        } else {
            updateStatus('❌ Registration Failed', true);
        }
    } catch (err) {
        updateStatus('Error: ' + err.message, true);
    }
}

// --- LOGIN LOGIC ---
export async function handleLogin() {
    const usernameInput = document.getElementById('username');
    const username = usernameInput ? usernameInput.value : '';

    if (!username) return updateStatus('Please enter a username', true);

    updateStatus('Awaiting biometrics...');

    try {
        // 1. Get Login Options from Backend
        const options = await apiRequest(`/auth/login/options/${username}`);
        if (!options) throw new Error('User not found or error fetching options');

        console.log("Allow Credentials Check:", options.allowCredentials);
        // 2. Trigger Browser Authentication
        // CRITICAL: We use startAuthentication from the library.
        // If your library is imported via script tag, it might be SimpleWebAuthnBrowser.startAuthentication
        const assertionResponse = await startAuthentication({ optionsJSON: options });
        // 3. Verify with Backend and get JWT
        const result = await apiRequest('/auth/login/verify', 'POST', {
            username,
            response: assertionResponse
        });

        if (result.status === 'success' && result.access_token) {
            updateStatus('✅ Access Granted!');
            localStorage.setItem('pitchpass_token', result.access_token);

            setTimeout(() => {
                window.location.href = getRedirectTarget();
            }, 800);
        } else {
            updateStatus(result.detail || '❌ Login Failed', true);
        }
    } catch (err) {
        console.log("here");
        console.error("Login Error Details:", err);
        // This handles cases where user cancels biometrics or the challenge is expired
        if (err.name === 'NotAllowedError') {
            updateStatus('Fingerprint/FaceID cancelled', true);
        } else {
            updateStatus('Error: ' + err.message, true);
        }
    }
}