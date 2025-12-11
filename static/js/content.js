// File: /static/js/content.js
// Content Intelligence Hub - Multiple Platform Selection

// Global state
let selectedPlatforms = [];
let selectedContentType = null;
let currentClient = null;

// Platform character limits
const platformLimits = {
    instagram: {
        text: 2200,
        caption: 2200,
        hashtags: 30
    },
    facebook: {
        text: 63206,
        caption: 2200,
        hashtags: 30
    },
    linkedin: {
        text: 3000,
        caption: 3000,
        hashtags: 10
    },
    twitter: {
        text: 280,
        caption: 280,
        hashtags: 10
    },
    pinterest: {
        text: 500,
        caption: 500,
        hashtags: 20
    }
};

// Platform-specific guidelines
const platformGuidelines = {
    instagram: {
        name: "Instagram",
        icon: "ti-brand-instagram",
        tips: [
            "Use high-quality visuals and engaging captions",
            "First 125 characters are visible before 'more' button",
            "Use 3-5 relevant hashtags for optimal reach",
            "Post when your audience is most active (typically 11am-1pm)",
            "Stories disappear after 24 hours - use highlights for important content"
        ]
    },
    facebook: {
        name: "Facebook",
        icon: "ti-brand-facebook",
        tips: [
            "Keep posts concise - shorter posts (40-80 chars) get higher engagement",
            "Posts with images get 2.3x more engagement",
            "Ask questions to increase comments and engagement",
            "Best posting times: Wednesday 11am-1pm",
            "Use Facebook Live for real-time engagement"
        ]
    },
    linkedin: {
        name: "LinkedIn",
        icon: "ti-brand-linkedin",
        tips: [
            "Professional tone - focus on industry insights and thought leadership",
            "Articles perform better than short posts",
            "Use 3-5 relevant hashtags maximum",
            "Best posting times: Tuesday-Thursday 10am-12pm",
            "Include a clear call-to-action"
        ]
    },
    twitter: {
        name: "Twitter",
        icon: "ti-brand-twitter",
        tips: [
            "Keep it concise - 280 character limit",
            "Tweets with images get 150% more retweets",
            "Use 1-2 relevant hashtags",
            "Best posting times: Weekdays 12pm-3pm",
            "Engage with replies quickly for better visibility"
        ]
    },
    pinterest: {
        name: "Pinterest",
        icon: "ti-brand-pinterest",
        tips: [
            "Vertical images perform best (2:3 ratio)",
            "Use keyword-rich descriptions",
            "Include relevant hashtags (up to 20)",
            "Best posting times: Saturday 8pm-11pm",
            "Create multiple pins for the same content"
        ]
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializePlatformSelector();
    initializeContentTypeSelector();
    loadClients();
    loadContentLibrary();
});

// ============================================================================
// PLATFORM SELECTION (MULTIPLE)
// ============================================================================

function initializePlatformSelector() {
    const platformOptions = document.querySelectorAll('.platform-option');
    
    platformOptions.forEach(option => {
        option.addEventListener('click', function() {
            const platform = this.dataset.platform;
            
            // Toggle selection
            if (selectedPlatforms.includes(platform)) {
                // Remove from selection
                selectedPlatforms = selectedPlatforms.filter(p => p !== platform);
                this.classList.remove('active');
            } else {
                // Add to selection
                selectedPlatforms.push(platform);
                this.classList.add('active');
            }
            
            updateSelectedPlatformsDisplay();
            updatePlatformGuidelines();
        });
    });
}

function updateSelectedPlatformsDisplay() {
    const infoDiv = document.getElementById('selectedPlatformsInfo');
    const listSpan = document.getElementById('selectedPlatformsList');
    
    if (selectedPlatforms.length === 0) {
        infoDiv.classList.remove('show');
        listSpan.textContent = 'None';
    } else {
        infoDiv.classList.add('show');
        
        // Create platform badges
        const badges = selectedPlatforms.map(platform => {
            const guideline = platformGuidelines[platform];
            return `<span class="platform-badge">
                <i class="${guideline.icon}"></i>
                ${guideline.name}
            </span>`;
        }).join('');
        
        listSpan.innerHTML = badges;
    }
}

function updatePlatformGuidelines() {
    const guidelinesSection = document.getElementById('guidelinesSection');
    const guidelinesContent = document.getElementById('guidelinesContent');
    
    if (selectedPlatforms.length === 0) {
        guidelinesSection.style.display = 'none';
        return;
    }
    
    guidelinesSection.style.display = 'block';
    
    // Create guidelines HTML for each selected platform
    const guidelinesHTML = selectedPlatforms.map(platform => {
        const guideline = platformGuidelines[platform];
        const limits = platformLimits[platform];
        
        return `
            <div class="guideline-box">
                <h4><i class="${guideline.icon}"></i> ${guideline.name} Guidelines</h4>
                <ul class="guideline-list">
                    ${guideline.tips.map(tip => `<li>${tip}</li>`).join('')}
                    <li><strong>Character limit:</strong> ${limits.text} characters</li>
                    <li><strong>Max hashtags:</strong> ${limits.hashtags}</li>
                </ul>
            </div>
        `;
    }).join('');
    
    guidelinesContent.innerHTML = guidelinesHTML;
}

// ============================================================================
// CONTENT TYPE SELECTION
// ============================================================================

function initializeContentTypeSelector() {
    const typeChips = document.querySelectorAll('.type-chip');
    
    typeChips.forEach(chip => {
        chip.addEventListener('click', function() {
            // Remove active from all
            typeChips.forEach(c => c.classList.remove('active'));
            
            // Add active to clicked
            this.classList.add('active');
            selectedContentType = this.dataset.type;
        });
    });
}

// ============================================================================
// CLIENT LOADING
// ============================================================================

async function loadClients() {
    try {
        const response = await fetch('/api/v1/clients/dropdown-list');
        const data = await response.json();
        
        const select = document.getElementById('clientSelect');
        
        if (data.success && data.data.length > 0) {
            select.innerHTML = '<option value="">Select a client...</option>';
            data.data.forEach(client => {
                const option = document.createElement('option');
                option.value = client.client_id;
                option.textContent = client.name;
                select.appendChild(option);
            });
        } else {
            select.innerHTML = '<option value="">No clients available</option>';
        }
    } catch (error) {
        console.error('Error loading clients:', error);
        document.getElementById('clientSelect').innerHTML = 
            '<option value="">Error loading clients</option>';
    }
}

// ============================================================================
// CONTENT GENERATION
// ============================================================================

async function generateContent() {
    // Validation
    if (selectedPlatforms.length === 0) {
        showNotification('Please select at least one platform', 'error');
        return;
    }
    
    if (!selectedContentType) {
        showNotification('Please select a content type', 'error');
        return;
    }
    
    const clientId = document.getElementById('clientSelect').value;
    if (!clientId) {
        showNotification('Please select a client', 'error');
        return;
    }
    
    const topic = document.getElementById('topicInput').value.trim();
    if (!topic) {
        showNotification('Please enter a topic or content brief', 'error');
        return;
    }
    
    const tone = document.getElementById('toneSelect').value;
    const audience = document.getElementById('audienceInput').value.trim();
    const keywords = document.getElementById('keywordsInput').value.trim();
    
    // Disable button and show loading
    const generateBtn = document.getElementById('generateBtn');
    generateBtn.disabled = true;
    generateBtn.innerHTML = '<i class="ti ti-loader"></i> Generating...';
    
    // Show loading in preview
    const previewContainer = document.getElementById('previewContainer');
    previewContainer.innerHTML = `
        <div class="loading-state">
            <div class="loader-spinner"></div>
            <p>AI is generating content for ${selectedPlatforms.length} platform(s)...</p>
        </div>
    `;
    
    try {
        const response = await fetch('/api/v1/content-intelligence/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                client_id: clientId,
                platforms: selectedPlatforms,
                content_type: selectedContentType,
                topic: topic,
                tone: tone,
                target_audience: audience || null,
                keywords: keywords ? keywords.split(',').map(k => k.trim()) : []
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayGeneratedContent(data.data);
            showNotification('Content generated successfully!', 'success');
            
            // Refresh content library
            loadContentLibrary();
        } else {
            showNotification(data.message || 'Failed to generate content', 'error');
            previewContainer.innerHTML = `
                <div class="empty-state">
                    <i class="ti ti-alert-circle"></i>
                    <h3>Generation Failed</h3>
                    <p>${data.message || 'Please try again'}</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error generating content:', error);
        showNotification('Error generating content. Please try again.', 'error');
        previewContainer.innerHTML = `
            <div class="empty-state">
                <i class="ti ti-alert-circle"></i>
                <h3>Error Occurred</h3>
                <p>Unable to generate content. Please try again.</p>
            </div>
        `;
    } finally {
        // Re-enable button
        generateBtn.disabled = false;
        generateBtn.innerHTML = '<i class="ti ti-sparkles"></i> Generate Content';
    }
}

// ============================================================================
// DISPLAY GENERATED CONTENT
// ============================================================================

function displayGeneratedContent(contentData) {
    const previewContainer = document.getElementById('previewContainer');
    
    let html = '';
    
    // Display variants for each platform
    if (contentData.variants && Object.keys(contentData.variants).length > 0) {
        Object.entries(contentData.variants).forEach(([platform, variant]) => {
            const guideline = platformGuidelines[platform];
            const limits = platformLimits[platform];
            
            html += `
                <div class="generated-content">
                    <div class="content-preview">
                        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
                            <h3 style="margin: 0; display: flex; align-items: center; gap: 0.5rem;">
                                <i class="${guideline.icon}"></i>
                                ${guideline.name}
                            </h3>
                            <span class="status-badge status-draft">Draft</span>
                        </div>
                        
                        <div style="margin-bottom: 1rem;">
                            <strong>Content:</strong>
                            <p style="margin: 0.5rem 0; line-height: 1.6;">${variant.content || ''}</p>
                        </div>
                        
                        ${variant.hashtags && variant.hashtags.length > 0 ? `
                            <div class="hashtag-container">
                                ${variant.hashtags.map(tag => 
                                    `<span class="hashtag-tag">#${tag}</span>`
                                ).join('')}
                            </div>
                        ` : ''}
                        
                        <div class="character-counter">
                            <span>${variant.content ? variant.content.length : 0} / ${limits.text} characters</span>
                            <span>${variant.hashtags ? variant.hashtags.length : 0} / ${limits.hashtags} hashtags</span>
                        </div>
                        <div class="counter-bar">
                            <div class="counter-fill" style="width: ${variant.content ? (variant.content.length / limits.text * 100) : 0}%"></div>
                        </div>
                    </div>
                    
                    ${variant.optimization_score ? `
                        <div class="optimization-score">
                            <div class="score-circle">${variant.optimization_score}</div>
                            <div class="score-details">
                                <h4>Optimization Score</h4>
                                <p>Based on platform best practices and engagement predictions</p>
                            </div>
                        </div>
                    ` : ''}
                    
                    <div class="content-actions" style="margin-top: 1rem;">
                        <button class="btn-primary" onclick="saveContent('${contentData.content_id}', '${platform}')">
                            <i class="ti ti-device-floppy"></i> Save
                        </button>
                        <button class="btn-secondary" onclick="editContent('${contentData.content_id}', '${platform}')">
                            <i class="ti ti-edit"></i> Edit
                        </button>
                        <button class="btn-secondary" onclick="copyToClipboard('${variant.content}')">
                            <i class="ti ti-copy"></i> Copy
                        </button>
                    </div>
                </div>
            `;
        });
    } else {
        html = `
            <div class="empty-state">
                <i class="ti ti-alert-circle"></i>
                <h3>No Content Generated</h3>
                <p>Unable to generate content variants. Please try again.</p>
            </div>
        `;
    }
    
    previewContainer.innerHTML = html;
}

// ============================================================================
// CONTENT LIBRARY
// ============================================================================

async function loadContentLibrary() {
    const libraryContainer = document.getElementById('contentLibrary');
    
    try {
        const response = await fetch('/api/v1/content-intelligence/library');
        const data = await response.json();
        
        if (data.success && data.data.length > 0) {
            let html = '';
            
            data.data.forEach(content => {
                const platforms = content.platforms || [];
                const platformBadges = platforms.map(p => {
                    const guideline = platformGuidelines[p];
                    return `<span class="platform-badge">
                        <i class="${guideline.icon}"></i>
                        ${guideline.name}
                    </span>`;
                }).join('');
                
                html += `
                    <div class="content-card">
                        <div class="content-card-header">
                            <div>
                                <h4>${content.content_title || 'Untitled Content'}</h4>
                                <div class="content-meta">
                                    <span><i class="ti ti-calendar"></i> ${formatDate(content.created_at)}</span>
                                    <span>${platformBadges}</span>
                                </div>
                            </div>
                            <div class="content-actions">
                                <button class="btn-icon" onclick="viewContent('${content.content_id}')" title="View">
                                    <i class="ti ti-eye"></i>
                                </button>
                                <button class="btn-icon" onclick="editContent('${content.content_id}')" title="Edit">
                                    <i class="ti ti-edit"></i>
                                </button>
                                <button class="btn-icon" onclick="deleteContent('${content.content_id}')" title="Delete">
                                    <i class="ti ti-trash"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            libraryContainer.innerHTML = html;
        } else {
            libraryContainer.innerHTML = `
                <div class="empty-state">
                    <i class="ti ti-folder-off"></i>
                    <h3>No Content Yet</h3>
                    <p>Generated content will appear here</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading content library:', error);
        libraryContainer.innerHTML = `
            <div class="empty-state">
                <i class="ti ti-alert-circle"></i>
                <h3>Error Loading Library</h3>
                <p>Unable to load content library</p>
            </div>
        `;
    }
}

// ============================================================================
// CONTENT ACTIONS
// ============================================================================

async function saveContent(contentId, platform) {
    try {
        const response = await fetch(`/api/v1/content-intelligence/${contentId}/save`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ platform })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Content saved successfully!', 'success');
            loadContentLibrary();
        } else {
            showNotification(data.message || 'Failed to save content', 'error');
        }
    } catch (error) {
        console.error('Error saving content:', error);
        showNotification('Error saving content', 'error');
    }
}

function editContent(contentId, platform) {
    // Implement edit functionality
    showNotification('Edit functionality coming soon', 'info');
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Content copied to clipboard!', 'success');
    }).catch(err => {
        console.error('Error copying to clipboard:', err);
        showNotification('Failed to copy content', 'error');
    });
}

async function viewContent(contentId) {
    // Implement view functionality
    showNotification('View functionality coming soon', 'info');
}

async function deleteContent(contentId) {
    if (!confirm('Are you sure you want to delete this content?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/v1/content-intelligence/${contentId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Content deleted successfully!', 'success');
            loadContentLibrary();
        } else {
            showNotification(data.message || 'Failed to delete content', 'error');
        }
    } catch (error) {
        console.error('Error deleting content:', error);
        showNotification('Error deleting content', 'error');
    }
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
        return 'Today';
    } else if (diffDays === 1) {
        return 'Yesterday';
    } else if (diffDays < 7) {
        return `${diffDays} days ago`;
    } else {
        return date.toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric' 
        });
    }
}

function showNotification(message, type = 'info') {
    // Implement your notification system
    // For now, using console and alert
    console.log(`[${type.toUpperCase()}] ${message}`);
    
    // You can replace this with a proper toast/notification system
    if (type === 'error') {
        alert(message);
    }
}