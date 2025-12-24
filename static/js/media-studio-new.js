/**
 * Creative Media Studio - Frontend JavaScript
 * File: static/js/media-studio.js
 */

const API_BASE = '/api/v1/media-studio';
let selectedImageSize = '1024x1024';
let currentClientId = null;
let currentBrandKit = null;

// =====================================================
// INITIALIZATION
// =====================================================

document.addEventListener('DOMContentLoaded', function() {
    initializeSizeSelector();
    initializeColorPickers();
    loadClients();
    loadMediaAssets();
    getCurrentUserClientId();
});

// =====================================================
// BRAND KIT - COLOR PICKER INITIALIZATION
// =====================================================

function initializeColorPickers() {
    const colorInputs = [
        { picker: 'brandPrimaryColor', text: 'brandPrimaryColorText' },
        { picker: 'brandSecondaryColor', text: 'brandSecondaryColorText' },
        { picker: 'brandAccentColor', text: 'brandAccentColorText' }
    ];
    
    colorInputs.forEach(({ picker, text }) => {
        const pickerEl = document.getElementById(picker);
        const textEl = document.getElementById(text);
        
        if (pickerEl && textEl) {
            pickerEl.addEventListener('input', function() {
                textEl.value = this.value.toUpperCase();
            });
        }
    });
}

// =====================================================
// BRAND KIT - GET CURRENT USER CLIENT ID
// =====================================================

async function getCurrentUserClientId() {
    try {
        const response = await fetch('/api/v1/auth/me', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        const data = await response.json();
        
        if (data.user) {
            // If user is a client, use their user_id
            if (data.user.role === 'client') {
                currentClientId = data.user.user_id;
                loadBrandKit(currentClientId);
            } else {
                // For admin/employee, check if there's a client filter
                const clientSelect = document.getElementById('filterClient');
                if (clientSelect && clientSelect.value) {
                    currentClientId = parseInt(clientSelect.value);
                    loadBrandKit(currentClientId);
                }
            }
        }
    } catch (error) {
        console.error('Error getting current user:', error);
    }
}

// =====================================================
// BRAND KIT - MODAL FUNCTIONS
// =====================================================

function openBrandKitManager() {
    const modal = document.getElementById('brandKitModal');
    if (!modal) {
        console.error('Brand Kit modal not found');
        return;
    }
    
    // Load existing brand kit data if available
    if (currentClientId) {
        loadBrandKitForEdit(currentClientId);
    }
    
    modal.classList.add('show');
}

function closeBrandKitManager() {
    const modal = document.getElementById('brandKitModal');
    if (modal) {
        modal.classList.remove('show');
    }
}

// =====================================================
// BRAND KIT - LOAD FOR EDITING
// =====================================================

async function loadBrandKitForEdit(clientId) {
    try {
        const response = await fetch(`/api/v1/brand-kit/client/${clientId}`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        const data = await response.json();
        
        if (data.success && data.brand_kit) {
            const kit = data.brand_kit;
            
            // Pre-fill form
            document.getElementById('brandPrimaryColor').value = kit.primary_color || '#9926F3';
            document.getElementById('brandPrimaryColorText').value = kit.primary_color || '#9926F3';
            
            document.getElementById('brandSecondaryColor').value = kit.secondary_color || '#1DD8FC';
            document.getElementById('brandSecondaryColorText').value = kit.secondary_color || '#1DD8FC';
            
            document.getElementById('brandAccentColor').value = kit.accent_color || '#FF6B6B';
            document.getElementById('brandAccentColorText').value = kit.accent_color || '#FF6B6B';
            
            document.getElementById('brandPrimaryFont').value = kit.primary_font || 'Gilroy';
            document.getElementById('brandSecondaryFont').value = kit.secondary_font || 'Arial';
            document.getElementById('brandVoice').value = kit.brand_voice || 'professional';
        }
    } catch (error) {
        console.error('Error loading brand kit for edit:', error);
    }
}

// =====================================================
// BRAND KIT - SAVE
// =====================================================

async function saveBrandKit() {
    // Try multiple ways to get client ID
    let clientId = currentClientId;
    
    if (!clientId) {
        // Try to get from any client dropdown
        const clientSelects = ['imageClient', 'videoClient', 'filterClient'];
        for (const selectId of clientSelects) {
            const select = document.getElementById(selectId);
            if (select && select.value) {
                clientId = parseInt(select.value);
                break;
            }
        }
    }
    
    if (!clientId) {
        showNotification('Unable to determine client. Please select a client and try again.', 'error');
        console.error('No client ID available');
        return;
    }
    
    const brandData = {
        client_id: clientId,
        primary_color: document.getElementById('brandPrimaryColor').value,
        secondary_color: document.getElementById('brandSecondaryColor').value,
        accent_color: document.getElementById('brandAccentColor').value,
        primary_font: document.getElementById('brandPrimaryFont').value,
        secondary_font: document.getElementById('brandSecondaryFont').value,
        brand_voice: document.getElementById('brandVoice').value
    };
    
    console.log('Saving brand kit for client:', clientId, brandData);
    
    try {
        const response = await fetch('/api/v1/brand-kit/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            },
            body: JSON.stringify(brandData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('✓ Brand kit saved successfully! It will be applied to all AI generations.', 'success');
            closeBrandKitManager();
            currentClientId = clientId;
            loadBrandKit(clientId);
        } else {
            showNotification('Failed to save brand kit: ' + (data.message || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Error saving brand kit:', error);
        showNotification('Error saving brand kit. Please try again.', 'error');
    }
}

// =====================================================
// BRAND KIT - LOAD AND DISPLAY
// =====================================================

async function loadBrandKit(clientId) {
    try {
        const response = await fetch(`/api/v1/brand-kit/client/${clientId}`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        const data = await response.json();
        
        if (data.success && data.brand_kit) {
            currentClientId = clientId;
            currentBrandKit = data.brand_kit;
            displayBrandKitIndicator(data.brand_kit);
            console.log('[BRAND KIT] Loaded:', data.brand_kit);
        } else {
            // No brand kit found - clear indicator
            currentBrandKit = null;
            const indicator = document.getElementById('brandKitIndicator');
            if (indicator) {
                indicator.innerHTML = '';
            }
            console.log('[BRAND KIT] No brand kit found for client:', clientId);
        }
    } catch (error) {
        console.error('Error loading brand kit:', error);
    }
}

// =====================================================
// BRAND KIT - DISPLAY INDICATOR
// =====================================================

function displayBrandKitIndicator(brandKit) {
    const indicator = document.getElementById('brandKitIndicator');
    if (!indicator) return;
    
    indicator.innerHTML = `
        <div style="display: flex; align-items: center; gap: 0.5rem; padding: 0.75rem 1rem; background: linear-gradient(135deg, rgba(153, 38, 243, 0.1), rgba(29, 216, 252, 0.1)); border-radius: 8px; border: 1px solid rgba(153, 38, 243, 0.2);">
            <i class="ti ti-palette" style="font-size: 1.25rem; background: linear-gradient(135deg, #9926F3, #1DD8FC); -webkit-background-clip: text; -webkit-text-fill-color: transparent;"></i>
            <div style="flex: 1;">
                <div style="font-weight: 600; font-size: 0.9rem; color: #1e293b;">Brand Kit Active</div>
                <div style="font-size: 0.75rem; color: #64748b;">Colors & fonts will be applied automatically to AI generations</div>
            </div>
            <div style="display: flex; gap: 0.25rem;">
                ${brandKit.primary_color ? `<div style="width: 24px; height: 24px; border-radius: 4px; background: ${brandKit.primary_color}; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.1);"></div>` : ''}
                ${brandKit.secondary_color ? `<div style="width: 24px; height: 24px; border-radius: 4px; background: ${brandKit.secondary_color}; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.1);"></div>` : ''}
                ${brandKit.accent_color ? `<div style="width: 24px; height: 24px; border-radius: 4px; background: ${brandKit.accent_color}; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.1);"></div>` : ''}
            </div>
            <button onclick="openBrandKitManager()" class="btn-icon" style="background: white;">
                <i class="ti ti-settings"></i>
            </button>
        </div>
    `;
}

// =====================================================
// SIZE SELECTOR
// =====================================================

function initializeSizeSelector() {
    const sizeChips = document.querySelectorAll('.size-chip');
    
    sizeChips.forEach(chip => {
        chip.addEventListener('click', function() {
            sizeChips.forEach(c => c.classList.remove('active'));
            this.classList.add('active');
            selectedImageSize = this.dataset.size;
        });
    });
}

// =====================================================
// MODAL FUNCTIONS
// =====================================================

function openImageGenerator() {
    document.getElementById('imageModal').classList.add('show');
    
    // Load brand kit for selected client
    const clientSelect = document.getElementById('imageClient');
    if (clientSelect && clientSelect.value) {
        loadBrandKit(parseInt(clientSelect.value));
    }
}

function openVideoGenerator() {
    document.getElementById('videoModal').classList.add('show');
    
    // Load brand kit for selected client
    const clientSelect = document.getElementById('videoClient');
    if (clientSelect && clientSelect.value) {
        loadBrandKit(parseInt(clientSelect.value));
    }
}

function openDesignStudio() {
    document.getElementById('designModal').classList.add('show');
}

function openAnimationGenerator() {
    document.getElementById('animationModal').classList.add('show');
    
    // Load brand kit for selected client
    const clientSelect = document.getElementById('animationClient');
    if (clientSelect && clientSelect.value) {
        loadBrandKit(parseInt(clientSelect.value));
    }
}

function openImageToVideo() {
    document.getElementById('imageToVideoModal').classList.add('show');
}

function openImageToAnimation() {
    document.getElementById('imageToAnimationModal').classList.add('show');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('show');
}

// =====================================================
// LOAD CLIENTS
// =====================================================

async function loadClients() {
    const clientSelects = [
        'imageClient', 
        'videoClient', 
        'designClient', 
        'filterClient',
        'animationClient',
        'imageToVideoClient',
        'imageToAnimationClient'
    ];
    
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch('/api/v1/clients/list', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch clients');
        }
        
        const data = await response.json();
        
        clientSelects.forEach(selectId => {
            const select = document.getElementById(selectId);
            if (select && data.clients) {
                data.clients.forEach(client => {
                    const option = document.createElement('option');
                    option.value = client.user_id;
                    option.textContent = client.company_name || client.email;
                    select.appendChild(option);
                });
                
                // Add change listener to load brand kit
                select.addEventListener('change', function() {
                    const clientId = parseInt(this.value);
                    if (clientId) {
                        currentClientId = clientId;
                        loadBrandKit(clientId);
                    } else {
                        currentClientId = null;
                        currentBrandKit = null;
                        const indicator = document.getElementById('brandKitIndicator');
                        if (indicator) indicator.innerHTML = '';
                    }
                });
            }
        });
        
    } catch (error) {
        console.error('Error loading clients:', error);
    }
}

// =====================================================
// NOTIFICATION HELPER
// =====================================================

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// =====================================================
// GENERATE IMAGE (DALL-E)
// =====================================================

async function generateImage(event) {
    event.preventDefault();
    
    const generateBtn = document.getElementById('generateImageBtn');
    const originalBtnText = generateBtn.innerHTML;
    
    try {
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="ti ti-loader"></i> Generating...';
        
        const token = localStorage.getItem('access_token');
        const clientId = document.getElementById('imageClient').value;
        const prompt = document.getElementById('imagePrompt').value;
        const quality = document.getElementById('imageQuality').value;
        const style = document.getElementById('imageStyle').value;
        
        const response = await fetch(`${API_BASE}/generate/image`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                client_id: parseInt(clientId),
                prompt: prompt,
                size: selectedImageSize,
                quality: quality,
                style: style,
                n: 1
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to generate image');
        }
        
        const result = await response.json();
        
        if (result.success) {
            let message = 'Image generated successfully!';
            if (result.brand_applied) {
                message += ' (Brand kit applied ✓)';
            }
            showNotification(message, 'success');
            closeModal('imageModal');
            document.getElementById('imageForm').reset();
            loadMediaAssets();
        }
        
    } catch (error) {
        console.error('Error generating image:', error);
        showNotification(error.message || 'Failed to generate image', 'error');
    } finally {
        generateBtn.disabled = false;
        generateBtn.innerHTML = originalBtnText;
    }
}

// =====================================================
// GENERATE VIDEO (SYNTHESIA)
// =====================================================

async function generateVideo(event) {
    event.preventDefault();
    
    const generateBtn = document.getElementById('generateVideoBtn');
    const originalBtnText = generateBtn.innerHTML;
    
    try {
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="ti ti-loader"></i> Generating...';
        
        const token = localStorage.getItem('access_token');
        const clientId = document.getElementById('videoClient').value;
        const title = document.getElementById('videoTitle').value;
        const script = document.getElementById('videoScript').value;
        const background = document.getElementById('videoBackground').value;
        
        const response = await fetch(`${API_BASE}/generate/video`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                client_id: parseInt(clientId),
                script: script,
                title: title,
                background: background
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to generate video');
        }
        
        const result = await response.json();
        
        if (result.success) {
            let message = 'Video generation started! This may take a few minutes.';
            if (result.brand_applied) {
                message += ' (Brand kit applied ✓)';
            }
            showNotification(message, 'success');
            closeModal('videoModal');
            document.getElementById('videoForm').reset();
            
            // Start checking video status
            if (result.video_id) {
                checkVideoStatus(result.video_id);
            }
        }
        
    } catch (error) {
        console.error('Error generating video:', error);
        showNotification(error.message || 'Failed to generate video', 'error');
    } finally {
        generateBtn.disabled = false;
        generateBtn.innerHTML = originalBtnText;
    }
}

// =====================================================
// CHECK VIDEO STATUS
// =====================================================

async function checkVideoStatus(videoId) {
    let attempts = 0;
    const maxAttempts = 30; // 5 minutes
    
    const checkStatus = async () => {
        try {
            const token = localStorage.getItem('access_token');
            const response = await fetch(`${API_BASE}/video/status/${videoId}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.ok) {
                const result = await response.json();
                
                if (result.status === 'complete') {
                    showNotification('Video is ready!', 'success');
                    loadMediaAssets();
                    return true;
                } else if (result.status === 'failed') {
                    showNotification('Video generation failed', 'error');
                    return true;
                } else if (attempts >= maxAttempts) {
                    showNotification('Video is still processing. Please check back later.', 'info');
                    return true;
                }
            }
            
            attempts++;
            setTimeout(checkStatus, 10000); // Check again in 10 seconds
            
        } catch (error) {
            console.error('Error checking video status:', error);
        }
    };
    
    setTimeout(checkStatus, 10000); // Start checking after 10 seconds
}

// =====================================================
// GENERATE ANIMATION (TEXT-TO-ANIMATION)
// =====================================================

async function generateAnimation(event) {
    event.preventDefault();
    
    const generateBtn = document.getElementById('generateAnimationBtn');
    const originalBtnText = generateBtn.innerHTML;
    
    try {
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="ti ti-loader"></i> Generating...';
        
        const token = localStorage.getItem('access_token');
        const clientId = document.getElementById('animationClient').value;
        const title = document.getElementById('animationTitle').value;
        const prompt = document.getElementById('animationPrompt').value;
        const style = document.getElementById('animationStyle').value;
        const duration = document.getElementById('animationDuration').value;
        
        const response = await fetch(`${API_BASE}/generate/animation`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                client_id: parseInt(clientId),
                title: title,
                prompt: prompt,
                style: style,
                duration: parseInt(duration)
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to generate animation');
        }
        
        const result = await response.json();
        
        if (result.success) {
            let message = 'Animation generated successfully!';
            if (result.brand_applied) {
                message += ' (Brand kit applied ✓)';
            }
            showNotification(message, 'success');
            closeModal('animationModal');
            document.getElementById('animationForm').reset();
            loadMediaAssets();
        }
        
    } catch (error) {
        console.error('Error generating animation:', error);
        showNotification(error.message || 'Failed to generate animation', 'error');
    } finally {
        generateBtn.disabled = false;
        generateBtn.innerHTML = originalBtnText;
    }
}

// =====================================================
// CONVERT IMAGE TO VIDEO
// =====================================================

async function convertImageToVideo(event) {
    event.preventDefault();
    
    const convertBtn = document.getElementById('convertImageToVideoBtn');
    const originalBtnText = convertBtn.innerHTML;
    
    try {
        convertBtn.disabled = true;
        convertBtn.innerHTML = '<i class="ti ti-loader"></i> Converting...';
        
        const token = localStorage.getItem('access_token');
        const clientId = document.getElementById('imageToVideoClient').value;
        const imageFile = document.getElementById('sourceImage').files[0];
        const motionPrompt = document.getElementById('motionPrompt').value;
        const duration = document.getElementById('videoLength').value;
        
        if (!imageFile) {
            throw new Error('Please select an image');
        }
        
        // Convert image to base64
        const base64Image = await fileToBase64(imageFile);
        
        const response = await fetch(`${API_BASE}/convert/image-to-video`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                client_id: parseInt(clientId),
                image_data: base64Image,
                motion_prompt: motionPrompt,
                duration: parseInt(duration)
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to convert image to video');
        }
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('Image converted to video successfully!', 'success');
            closeModal('imageToVideoModal');
            document.getElementById('imageToVideoForm').reset();
            loadMediaAssets();
        }
        
    } catch (error) {
        console.error('Error converting image to video:', error);
        showNotification(error.message || 'Failed to convert image to video', 'error');
    } finally {
        convertBtn.disabled = false;
        convertBtn.innerHTML = originalBtnText;
    }
}

// =====================================================
// CONVERT IMAGE TO ANIMATION
// =====================================================

async function convertImageToAnimation(event) {
    event.preventDefault();
    
    const convertBtn = document.getElementById('convertImageToAnimationBtn');
    const originalBtnText = convertBtn.innerHTML;
    
    try {
        convertBtn.disabled = true;
        convertBtn.innerHTML = '<i class="ti ti-loader"></i> Creating...';
        
        const token = localStorage.getItem('access_token');
        const clientId = document.getElementById('imageToAnimationClient').value;
        const imageFile = document.getElementById('animSourceImage').files[0];
        const animationEffect = document.getElementById('animationEffect').value;
        const animationType = document.getElementById('animationType').value;
        
        if (!imageFile) {
            throw new Error('Please select an image');
        }
        
        // Convert image to base64
        const base64Image = await fileToBase64(imageFile);
        
        const response = await fetch(`${API_BASE}/convert/image-to-animation`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                client_id: parseInt(clientId),
                image_data: base64Image,
                animation_effect: animationEffect,
                animation_type: animationType
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create animation');
        }
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('Animation created successfully!', 'success');
            closeModal('imageToAnimationModal');
            document.getElementById('imageToAnimationForm').reset();
            loadMediaAssets();
        }
        
    } catch (error) {
        console.error('Error creating animation:', error);
        showNotification(error.message || 'Failed to create animation', 'error');
    } finally {
        convertBtn.disabled = false;
        convertBtn.innerHTML = originalBtnText;
    }
}

// =====================================================
// FILE TO BASE64 HELPER
// =====================================================

function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
            const base64 = reader.result.split(',')[1];
            resolve(base64);
        };
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

// =====================================================
// CREATE DESIGN (CANVA)
// =====================================================

async function createDesign(event) {
    event.preventDefault();
    
    const createBtn = document.getElementById('createDesignBtn');
    const originalBtnText = createBtn.innerHTML;
    
    try {
        createBtn.disabled = true;
        createBtn.innerHTML = '<i class="ti ti-loader"></i> Creating...';
        
        const token = localStorage.getItem('access_token');
        const clientId = document.getElementById('designClient').value;
        const title = document.getElementById('designTitle').value;
        const designType = document.getElementById('designType').value;
        
        const response = await fetch(`${API_BASE}/create-design`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                client_id: parseInt(clientId),
                title: title,
                design_type: designType,
                content_elements: {}
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create design');
        }
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('✓ Design created successfully!', 'success');
            closeModal('designModal');
            loadMediaAssets();
            
            // Open Canva editor in new tab
            if (result.edit_url) {
                window.open(result.edit_url, '_blank');
            }
        }
        
    } catch (error) {
        console.error('Error creating design:', error);
        showNotification(error.message || 'Failed to create design', 'error');
    } finally {
        createBtn.disabled = false;
        createBtn.innerHTML = originalBtnText;
    }
}

// =====================================================
// LOAD MEDIA ASSETS
// =====================================================

async function loadMediaAssets() {
    const libraryContainer = document.getElementById('mediaLibrary');
    
    try {
        libraryContainer.innerHTML = `
            <div class="loading-state">
                <div class="loader-spinner"></div>
                <p>Loading media library...</p>
            </div>
        `;
        
        const token = localStorage.getItem('access_token');
        const filterType = document.getElementById('filterType').value;
        const filterClient = document.getElementById('filterClient').value;
        
        let url = `${API_BASE}/assets?limit=50`;
        if (filterType) url += `&asset_type=${filterType}`;
        if (filterClient) url += `&client_id=${filterClient}`;
        
        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch assets');
        }
        
        const result = await response.json();
        
        if (result.success && result.data.length > 0) {
            libraryContainer.innerHTML = `
                <div class="asset-grid">
                    ${result.data.map(asset => createAssetCard(asset)).join('')}
                </div>
            `;
        } else {
            libraryContainer.innerHTML = `
                <div class="empty-state">
                    <i class="ti ti-folder-off"></i>
                    <h3>No Media Assets Yet</h3>
                    <p>Start creating images, videos, or designs to build your library</p>
                </div>
            `;
        }
        
    } catch (error) {
        console.error('Error loading assets:', error);
        libraryContainer.innerHTML = `
            <div class="empty-state">
                <i class="ti ti-alert-circle"></i>
                <h3>Failed to Load Assets</h3>
                <p>${error.message}</p>
            </div>
        `;
    }
}

// =====================================================
// CREATE ASSET CARD
// =====================================================

function createAssetCard(asset) {
    const typeIcons = {
        'image': 'ti-photo',
        'video': 'ti-video',
        'animation': 'ti-gif',
        'presentation': 'ti-presentation'
    };
    
    const generationLabels = {
        'dall-e-3': 'DALL-E',
        'synthesia': 'Synthesia',
        'canva': 'Canva',
        'ideogram': 'Ideogram',
        'openai': 'OpenAI'
    };
    
    const icon = typeIcons[asset.asset_type] || 'ti-file';
    const genLabel = generationLabels[asset.generation_type] || asset.generation_type;
    
    const isImage = asset.asset_type === 'image' && asset.file_url;
    const previewContent = isImage 
        ? `<img src="${asset.file_url}" alt="${asset.asset_name}" onerror="this.style.display='none'; this.parentElement.innerHTML='<i class=\\'ti ${icon}\\'></i>';">`
        : `<i class="ti ${icon}"></i>`;
    
    const escapedUrl = (asset.file_url || '').replace(/'/g, "\\'");
    
    return `
        <div class="asset-card">
            <div class="asset-preview">
                ${previewContent}
                ${asset.ai_generated ? `<span class="asset-badge">${genLabel}</span>` : ''}
            </div>
            <div class="asset-info">
                <h3>${asset.asset_name || 'Untitled Asset'}</h3>
                <div class="asset-meta">
                    ${new Date(asset.created_at).toLocaleDateString()}
                </div>
                <div class="asset-actions">
                    <button class="btn-icon" onclick="downloadAsset(${asset.asset_id})" title="Download">
                        <i class="ti ti-download"></i>
                    </button>
                    <button class="btn-icon" onclick="viewAsset('${escapedUrl}')" title="View">
                        <i class="ti ti-eye"></i>
                    </button>
                    <button class="btn-icon" onclick="deleteAsset(${asset.asset_id})" title="Delete">
                        <i class="ti ti-trash"></i>
                    </button>
                </div>
            </div>
        </div>
    `;
}

// =====================================================
// ASSET ACTIONS
// =====================================================

async function downloadAsset(assetId) {
    try {
        showNotification('Starting download...', 'info');
        
        const token = localStorage.getItem('access_token');
        
        const response = await fetch(`${API_BASE}/assets/${assetId}/download`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Download failed');
        }
        
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            const data = await response.json();
            if (data.redirect_url) {
                window.open(data.redirect_url, '_blank');
                return;
            }
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `asset_${assetId}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        showNotification('Download completed', 'success');
        
    } catch (error) {
        console.error('Download error:', error);
        showNotification('Failed to download asset', 'error');
    }
}

function viewAsset(url) {
    if (url && (url.startsWith('http') || url.startsWith('/static'))) {
        window.open(url, '_blank');
    } else {
        showNotification('View URL not available', 'error');
    }
}

async function deleteAsset(assetId) {
    if (!confirm('Are you sure you want to delete this asset?')) {
        return;
    }
    
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_BASE}/assets/${assetId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to delete asset');
        }
        
        showNotification('Asset deleted successfully', 'success');
        loadMediaAssets();
        
    } catch (error) {
        console.error('Error deleting asset:', error);
        showNotification(error.message || 'Failed to delete asset', 'error');
    }
}