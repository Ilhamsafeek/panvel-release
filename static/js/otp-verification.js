/**
 * OTP Verification UI Component
 */

const OTP_CONFIG = {
    apiBase: window.APP_CONFIG?.apiBaseUrl || '/api',
    otpLength: 6,
    resendCooldown: 90 // seconds
};

class OTPVerifier {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.identifier = options.identifier;
        this.identifierType = options.identifierType; // 'phone' or 'email'
        this.purpose = options.purpose || 'registration';
        this.onSuccess = options.onSuccess || (() => {});
        this.onError = options.onError || ((err) => alert(err));
        
        this.resendTimer = null;
        this.resendCountdown = 0;
        
        this.render();
        this.attachEventListeners();
    }
    
    render() {
        this.container.innerHTML = `
            <div class="otp-verification-container">
                <div class="otp-header">
                    <i class="ti ti-shield-check"></i>
                    <h3>Verification Required</h3>
                    <p>Enter the 6-digit code sent to ${this.maskIdentifier(this.identifier)}</p>
                </div>
                
                <div class="otp-input-group">
                    ${Array.from({length: OTP_CONFIG.otpLength}, (_, i) => `
                        <input 
                            type="text" 
                            class="otp-input" 
                            id="otp-${i}" 
                            maxlength="1" 
                            pattern="[0-9]"
                            inputmode="numeric"
                            autocomplete="off"
                        />
                    `).join('')}
                </div>
                
                <div class="otp-actions">
                    <button id="verifyOtpBtn" class="btn btn-primary" disabled>
                        <i class="ti ti-check"></i>
                        Verify Code
                    </button>
                    
                    <button id="resendOtpBtn" class="btn btn-secondary">
                        <i class="ti ti-refresh"></i>
                        <span id="resendText">Resend Code</span>
                    </button>
                </div>
                
                <div id="otpError" class="otp-error" style="display: none;"></div>
            </div>
        `;
        
        this.addStyles();
    }
    
    addStyles() {
        if (document.getElementById('otp-styles')) return;
        
        const style = document.createElement('style');
        style.id = 'otp-styles';
        style.textContent = `
            .otp-verification-container {
                max-width: 500px;
                margin: 0 auto;
                padding: 2rem;
                background: white;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }
            .otp-header {
                text-align: center;
                margin-bottom: 2rem;
            }
            .otp-header i {
                font-size: 3rem;
                background: linear-gradient(135deg, #9926F3, #1DD8FC);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            .otp-input-group {
                display: flex;
                gap: 0.5rem;
                justify-content: center;
                margin-bottom: 1.5rem;
            }
            .otp-input {
                width: 50px;
                height: 60px;
                text-align: center;
                font-size: 24px;
                font-weight: 600;
                border: 2px solid #cbd5e1;
                border-radius: 8px;
                transition: all 0.2s;
            }
            .otp-input:focus {
                outline: none;
                border-color: #9926F3;
                box-shadow: 0 0 0 3px rgba(153, 38, 243, 0.1);
            }
            .otp-input.filled {
                border-color: #9926F3;
                background: #faf5ff;
            }
            .otp-actions {
                display: flex;
                flex-direction: column;
                gap: 1rem;
            }
            .otp-error {
                margin-top: 1rem;
                padding: 0.75rem;
                background: #fee2e2;
                border: 1px solid #fca5a5;
                border-radius: 8px;
                color: #dc2626;
                text-align: center;
            }
        `;
        document.head.appendChild(style);
    }
    
    attachEventListeners() {
        // OTP input handling
        const inputs = this.container.querySelectorAll('.otp-input');
        inputs.forEach((input, index) => {
            input.addEventListener('input', (e) => this.handleOtpInput(e, index));
            input.addEventListener('keydown', (e) => this.handleKeyDown(e, index));
            input.addEventListener('paste', (e) => this.handlePaste(e));
        });
        
        // Verify button
        document.getElementById('verifyOtpBtn').addEventListener('click', () => this.verifyOtp());
        
        // Resend button
        document.getElementById('resendOtpBtn').addEventListener('click', () => this.resendOtp());
        
        // Auto-focus first input
        inputs[0].focus();
    }
    
    handleOtpInput(e, index) {
        const input = e.target;
        const value = input.value;
        
        // Only allow digits
        if (!/^\d$/.test(value)) {
            input.value = '';
            return;
        }
        
        input.classList.add('filled');
        
        // Move to next input
        const inputs = this.container.querySelectorAll('.otp-input');
        if (index < inputs.length - 1) {
            inputs[index + 1].focus();
        }
        
        // Check if all filled
        this.checkCompletion();
    }
    
    handleKeyDown(e, index) {
        const inputs = this.container.querySelectorAll('.otp-input');
        
        if (e.key === 'Backspace' && !e.target.value && index > 0) {
            inputs[index - 1].focus();
            inputs[index - 1].value = '';
            inputs[index - 1].classList.remove('filled');
        }
        
        if (e.key === 'ArrowLeft' && index > 0) {
            inputs[index - 1].focus();
        }
        
        if (e.key === 'ArrowRight' && index < inputs.length - 1) {
            inputs[index + 1].focus();
        }
    }
    
    handlePaste(e) {
        e.preventDefault();
        const paste = e.clipboardData.getData('text');
        const digits = paste.replace(/\D/g, '').slice(0, OTP_CONFIG.otpLength);
        
        const inputs = this.container.querySelectorAll('.otp-input');
        digits.split('').forEach((digit, index) => {
            if (inputs[index]) {
                inputs[index].value = digit;
                inputs[index].classList.add('filled');
            }
        });
        
        this.checkCompletion();
    }
    
    checkCompletion() {
        const inputs = this.container.querySelectorAll('.otp-input');
        const otp = Array.from(inputs).map(input => input.value).join('');
        
        const verifyBtn = document.getElementById('verifyOtpBtn');
        verifyBtn.disabled = otp.length !== OTP_CONFIG.otpLength;
    }
    
    async verifyOtp() {
        const inputs = this.container.querySelectorAll('.otp-input');
        const otp = Array.from(inputs).map(input => input.value).join('');
        
        const verifyBtn = document.getElementById('verifyOtpBtn');
        const originalText = verifyBtn.innerHTML;
        verifyBtn.disabled = true;
        verifyBtn.innerHTML = '<i class="ti ti-loader rotating"></i> Verifying...';
        
        try {
            const response = await fetch(`${OTP_CONFIG.apiBase}/otp/verify`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    identifier: this.identifier,
                    otp_code: otp,
                    purpose: this.purpose
                })
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                this.showSuccess('Verification successful!');
                setTimeout(() => this.onSuccess(data), 1000);
            } else {
                throw new Error(data.detail || data.error || 'Verification failed');
            }
        } catch (error) {
            this.showError(error.message);
            this.clearInputs();
        } finally {
            verifyBtn.disabled = false;
            verifyBtn.innerHTML = originalText;
        }
    }
    
    async resendOtp() {
        if (this.resendCountdown > 0) return;
        
        const resendBtn = document.getElementById('resendOtpBtn');
        resendBtn.disabled = true;
        
        try {
            const response = await fetch(`${OTP_CONFIG.apiBase}/otp/send`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    identifier: this.identifier,
                    identifier_type: this.identifierType,
                    purpose: this.purpose
                })
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                this.showSuccess('New code sent!');
                this.startResendCooldown();
            } else {
                throw new Error(data.detail || 'Failed to resend code');
            }
        } catch (error) {
            this.showError(error.message);
            resendBtn.disabled = false;
        }
    }
    
    startResendCooldown() {
        this.resendCountdown = OTP_CONFIG.resendCooldown;
        const resendBtn = document.getElementById('resendOtpBtn');
        const resendText = document.getElementById('resendText');
        
        this.resendTimer = setInterval(() => {
            this.resendCountdown--;
            resendText.textContent = `Resend in ${this.resendCountdown}s`;
            
            if (this.resendCountdown <= 0) {
                clearInterval(this.resendTimer);
                resendBtn.disabled = false;
                resendText.textContent = 'Resend Code';
            }
        }, 1000);
    }
    
    maskIdentifier(identifier) {
        if (this.identifierType === 'phone') {
            return identifier.replace(/(\d{2})\d+(\d{4})/, '$1****$2');
        } else {
            return identifier.replace(/(.{2})(.*)(@.*)/, '$1****$3');
        }
    }
    
    clearInputs() {
        const inputs = this.container.querySelectorAll('.otp-input');
        inputs.forEach(input => {
            input.value = '';
            input.classList.remove('filled');
        });
        inputs[0].focus();
    }
    
    showError(message) {
        const errorDiv = document.getElementById('otpError');
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        setTimeout(() => errorDiv.style.display = 'none', 5000);
    }
    
    showSuccess(message) {
        const errorDiv = document.getElementById('otpError');
        errorDiv.style.background = '#d1fae5';
        errorDiv.style.borderColor = '#6ee7b7';
        errorDiv.style.color = '#065f46';
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    }
}

// Usage example:
// const otpVerifier = new OTPVerifier('otp-container', {
//     identifier: '+15551234567',
//     identifierType: 'phone',
//     purpose: 'registration',
//     onSuccess: (data) => { /* redirect or continue */ },
//     onError: (error) => { /* handle error */ }
// });