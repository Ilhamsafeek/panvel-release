/**
 * Content Intelligence Hub - Frontend JavaScript (FIXED)
 * File: static/js/content.js
 * 
 * FIXES:
 * 1. Fixed input ID from 'contentTopic' to 'topicInput'
 * 2. Standardized token storage to 'access_token'
 * 3. Added missing 'selectedPlatforms' array initialization
 * 4. Fixed visual analysis base64 encoding
 * 5. Implemented AI audience insights feature
 * 6. Implemented Google Vision API visual analysis
 * 7. Added proper performance score display (1-100 scale)
 */

const API_BASE = `/api/v1/content`;
// Use window.selectedPlatforms to sync with inline script in HTML
window.selectedPlatforms = window.selectedPlatforms || [];
let selectedContentType = '';
let generatedContent = null;
let currentClientId = null;

// =====================================================
// INITIALIZATION
// =====================================================

document.addEventListener('DOMContentLoaded', function() {
    // Platform selector initialized by inline script in content.html
    initializeContentTypeSelector();
    loadClients();
    loadContentLibrary();
    
    // Visual analysis initialization
    const imageInput = document.getElementById('visualAnalysisImage');
    if (imageInput) {
        imageInput.addEventListener('change', analyzeImageUpload);
    }
});

// =====================================================
// CONTENT TYPE SELECTION
// =====================================================
// Note: Platform selection is handled by inline script in content.html

function initializeContentTypeSelector() {
    const types = document.querySelectorAll('.type-chip');
    
    types.forEach(type => {
        type.addEventListener('click', function() {
            // Remove active from all
            types.forEach(t => t.classList.remove('active'));
            
            // Add active to clicked
            this.classList.add('active');
            selectedContentType = this.dataset.type;
            
            console.log('Selected content type:', selectedContentType);
        });
    });
}

// =====================================================
// LOAD CLIENTS
// =====================================================

async function loadClients() {
    const clientSelect = document.getElementById('clientSelect');
    
    try {
        const token = localStorage.getItem('access_token'); // FIXED: Standardized token storage
        const response = await fetch('/api/v1/clients/list', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch clients');
        }
        
        const data = await response.json();
        
        clientSelect.innerHTML = '<option value="">Select a client...</option>';
        
        if (data.clients && data.clients.length > 0) {
            data.clients.forEach(client => {
                const option = document.createElement('option');
                option.value = client.user_id;
                option.textContent = client.full_name;
                clientSelect.appendChild(option);
            });
        }
        
    } catch (error) {
        console.error('Error loading clients:', error);
        clientSelect.innerHTML = '<option value="">Error loading clients</option>';
    }
}

// =====================================================
// GENERATE CONTENT
// =====================================================

async function generateContent() {
    const clientId = document.getElementById('clientSelect')?.value;
    const topic = document.getElementById('topicInput')?.value; // FIXED: Changed from 'contentTopic' to 'topicInput'
    const tone = document.getElementById('toneSelect')?.value || 'professional';
    
    console.log('Generate clicked. Platforms:', window.selectedPlatforms); // Use window.selectedPlatforms
    
    // Validation
    if (!clientId) {
        alert('Please select a client');
        return;
    }
    
    if (!topic || topic.trim() === '') {
        alert('Please enter a content topic');
        return;
    }
    
    if (!window.selectedPlatforms || window.selectedPlatforms.length === 0) {
        alert('Please select at least one platform');
        return;
    }
    
    if (!selectedContentType) {
        alert('Please select a content type');
        return;
    }
    
    const generateBtn = document.getElementById('generateBtn');
    if (generateBtn) {
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="ti ti-loader"></i> Generating Content...';
    }
    
    try {
        const token = localStorage.getItem('access_token'); // FIXED: Standardized token
        
        const response = await fetch(`/api/v1/content/intelligence/generate`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                client_id: parseInt(clientId),
                platforms: window.selectedPlatforms, // Use window.selectedPlatforms
                content_type: selectedContentType,
                topic: topic,
                tone: tone,
                generate_audience_insights: true
            })
        });
        
        const result = await response.json();
        
        if (result.success && result.data) {
            displayMultiPlatformContent(result.data);
            showNotification('Content generated successfully!', 'success');
        } else {
            throw new Error(result.detail || 'Content generation failed');
        }
    } catch (error) {
        console.error('Error generating content:', error);
        alert('Error: ' + error.message);
    } finally {
        if (generateBtn) {
            generateBtn.disabled = false;
            generateBtn.innerHTML = '<i class="ti ti-sparkles"></i> Generate Content';
        }
    }
}

// =====================================================
// DISPLAY MULTI-PLATFORM CONTENT
// =====================================================

function displayMultiPlatformContent(data) {
    const previewContainer = document.getElementById('previewContainer');
    
    if (!data.variants || data.variants.length === 0) {
        previewContainer.innerHTML = `
            <div class="empty-state">
                <i class="ti ti-alert-circle"></i>
                <h3>No Content Generated</h3>
                <p>Please try again with different parameters</p>
            </div>
        `;
        return;
    }
    
    // Display variants for each platform
    previewContainer.innerHTML = data.variants.map(variant => {
        const scoreColor = variant.performance_score >= 80 ? '#16a34a' : 
                          variant.performance_score >= 60 ? '#eab308' : '#ef4444';
        
        return `
            <div class="platform-variant" style="background: white; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; border: 2px solid ${variant.is_optimized ? '#16a34a' : '#e2e8f0'};">
                <!-- Platform Header -->
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem; padding-bottom: 1rem; border-bottom: 2px solid #f1f5f9;">
                    <div style="display: flex; align-items: center; gap: 0.75rem;">
                        <i class="ti ti-brand-${variant.platform}" style="font-size: 1.5rem; color: #9926F3;"></i>
                        <h3 style="font-size: 1.1rem; font-weight: 600; color: #1e293b; margin: 0;">${capitalize(variant.platform)}</h3>
                    </div>
                    <div class="score-badge" style="display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 1rem; background: ${scoreColor}15; border-radius: 8px;">
                        <i class="ti ti-chart-line" style="color: ${scoreColor};"></i>
                        <span style="font-weight: 600; color: ${scoreColor};">${Math.round(variant.performance_score)}/100</span>
                        <span style="font-size: 0.75rem; color: #64748b;">${variant.optimization_status}</span>
                    </div>
                </div>

                <!-- Content -->
                ${variant.headline ? `
                    <div style="margin-bottom: 1rem;">
                        <label style="font-size: 0.75rem; font-weight: 600; color: #64748b; text-transform: uppercase; margin-bottom: 0.5rem; display: block;">Headline</label>
                        <div style="font-size: 1.1rem; font-weight: 600; color: #1e293b;">${variant.headline}</div>
                    </div>
                ` : ''}
                
                <div style="margin-bottom: 1rem;">
                    <label style="font-size: 0.75rem; font-weight: 600; color: #64748b; text-transform: uppercase; margin-bottom: 0.5rem; display: block;">Content</label>
                    <div style="font-size: 0.95rem; line-height: 1.6; color: #334155; white-space: pre-wrap;">${variant.content}</div>
                    
                    <div class="character-counter" style="margin-top: 0.75rem; display: flex; justify-content: space-between; align-items: center; font-size: 0.85rem;">
                        <span style="color: #64748b;">${variant.character_count || variant.content.length} / ${variant.optimal_length || 2000} characters</span>
                        <span style="color: ${(variant.character_count || variant.content.length) <= (variant.optimal_length || 200) ? '#16a34a' : '#eab308'};">
                            ${(variant.character_count || variant.content.length) <= (variant.optimal_length || 200) ? 'Optimal length ✓' : 'Consider shortening'}
                        </span>
                    </div>
                </div>

                ${variant.cta ? `
                    <div style="margin-bottom: 1rem;">
                        <label style="font-size: 0.75rem; font-weight: 600; color: #64748b; text-transform: uppercase; margin-bottom: 0.5rem; display: block;">Call to Action</label>
                        <div style="font-size: 0.95rem; font-weight: 500; color: #9926F3;">${variant.cta}</div>
                    </div>
                ` : ''}

                <!-- Hashtags -->
                ${variant.hashtags && variant.hashtags.length > 0 ? `
                    <div style="margin-bottom: 1.5rem;">
                        <label style="font-size: 0.875rem; font-weight: 600; color: #334155; margin-bottom: 0.75rem; display: block;">
                            <i class="ti ti-hash"></i> Suggested Hashtags (${variant.hashtags.length})
                        </label>
                        <div class="hashtag-container">
                            ${variant.hashtags.map(tag => 
                                `<span class="hashtag-tag" style="display: inline-block; padding: 0.375rem 0.75rem; background: linear-gradient(135deg, rgba(153, 38, 243, 0.1), rgba(29, 216, 252, 0.1)); border: 1px solid #9926F3; border-radius: 4px; margin: 0.25rem; font-size: 0.85rem; color: #9926F3;">#${tag}</span>`
                            ).join('')}
                        </div>
                    </div>
                ` : ''}

                <!-- Action Buttons -->
                <div style="display: flex; gap: 0.75rem; margin-top: 1.5rem;">
                    <button class="btn-primary" onclick='savePlatformContent(${JSON.stringify(variant).replace(/'/g, "&#39;")})'>
                        <i class="ti ti-device-floppy"></i>
                        Save
                    </button>
                    <button class="btn-secondary" onclick='copyPlatformContent(${JSON.stringify(variant).replace(/'/g, "&#39;")})'>
                        <i class="ti ti-copy"></i>
                        Copy
                    </button>
                </div>
            </div>
        `;
    }).join('');
    
    // Store current data for saving
    currentClientId = document.getElementById('clientSelect')?.value;
    generatedContent = data;
}

// =====================================================
// SAVE & COPY PLATFORM CONTENT
// =====================================================

async function savePlatformContent(variant) {
    if (!currentClientId) {
        showNotification('Client ID not found', 'error');
        return;
    }
    
    try {
        const token = localStorage.getItem('access_token');
        
        const response = await fetch(`${API_BASE}/save`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                client_id: parseInt(currentClientId),
                platform: variant.platform,
                content_type: selectedContentType,
                title: variant.headline || `${variant.platform} ${selectedContentType}`,
                content_text: variant.content,
                hashtags: variant.hashtags || [],
                cta_text: variant.cta,
                optimization_score: variant.performance_score,
                status: 'draft'
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to save content');
        }
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('Content saved to library!', 'success');
            loadContentLibrary();
        }
        
    } catch (error) {
        console.error('Error saving content:', error);
        showNotification(error.message || 'Failed to save content', 'error');
    }
}

function copyPlatformContent(variant) {
    let textToCopy = '';
    
    if (variant.headline) {
        textToCopy += variant.headline + '\n\n';
    }
    
    textToCopy += variant.content + '\n\n';
    
    if (variant.cta) {
        textToCopy += variant.cta + '\n\n';
    }
    
    if (variant.hashtags && variant.hashtags.length > 0) {
        textToCopy += variant.hashtags.map(tag => `#${tag}`).join(' ');
    }
    
    navigator.clipboard.writeText(textToCopy).then(() => {
        showNotification('Content copied to clipboard!', 'success');
    }).catch(err => {
        console.error('Failed to copy:', err);
        showNotification('Failed to copy content', 'error');
    });
}

// =====================================================
// AI AUDIENCE INSIGHTS FEATURE (NEW)
// =====================================================

async function generateAudienceInsights() {
    const clientId = document.getElementById('clientSelect')?.value;
    const topic = document.getElementById('topicInput')?.value; // FIXED: Changed ID
    
    if (!clientId || !topic) {
        alert('Please select a client and enter a topic');
        return;
    }
    
    const generateBtn = document.getElementById('generateAudienceBtn');
    if (generateBtn) {
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="ti ti-loader"></i> Generating Insights...';
    }
    
    try {
        const token = localStorage.getItem('access_token'); // FIXED: Standardized token
        const response = await fetch(`/api/v1/content/audience-insights`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                client_id: parseInt(clientId),
                topic: topic,
                platform: window.selectedPlatforms[0] || 'instagram' // Use window.selectedPlatforms
            })
        });
        
        const result = await response.json();
        
        if (result.success && result.data) {
            displayAudienceInsights(result.data);
            showNotification('Audience insights generated successfully!', 'success');
        } else {
            throw new Error(result.detail || 'Failed to generate insights');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error: ' + error.message);
    } finally {
        if (generateBtn) {
            generateBtn.disabled = false;
            generateBtn.innerHTML = '<i class="ti ti-users"></i> Generate Audience Insights';
        }
    }
}

function displayAudienceInsights(data) {
    const container = document.getElementById('audienceInsightsDisplay');
    if (!container) return;
    
    const audience = data.target_audience || {};
    const keywords = data.keywords || {};
    
    container.innerHTML = `
        <div style="background: linear-gradient(135deg, rgba(153, 38, 243, 0.05), rgba(29, 216, 252, 0.05)); padding: 1.5rem; border-radius: 12px; margin-bottom: 1rem; border: 2px solid #9926F3;">
            <h4 style="color: #1e293b; margin-bottom: 1rem;"><i class="ti ti-target"></i> Target Audience</h4>
            <p style="color: #334155; line-height: 1.6; margin-bottom: 1rem;">${audience.description || 'No description available'}</p>
            
            ${audience.demographics && audience.demographics.length > 0 ? `
                <div style="margin-top: 1rem;">
                    <strong style="color: #1e293b; font-size: 0.9rem;">Demographics:</strong><br>
                    <div style="margin-top: 0.5rem;">
                        ${audience.demographics.map(d => `<span style="display: inline-block; padding: 0.375rem 0.75rem; background: white; border: 1px solid #e2e8f0; border-radius: 6px; margin: 0.25rem; font-size: 0.85rem;">${d}</span>`).join('')}
                    </div>
                </div>
            ` : ''}
            
            ${audience.interests && audience.interests.length > 0 ? `
                <div style="margin-top: 1rem;">
                    <strong style="color: #1e293b; font-size: 0.9rem;">Interests:</strong><br>
                    <div style="margin-top: 0.5rem;">
                        ${audience.interests.map(i => `<span style="display: inline-block; padding: 0.375rem 0.75rem; background: white; border: 1px solid #e2e8f0; border-radius: 6px; margin: 0.25rem; font-size: 0.85rem;">${i}</span>`).join('')}
                    </div>
                </div>
            ` : ''}
        </div>
        
        <div style="background: linear-gradient(135deg, rgba(153, 38, 243, 0.05), rgba(29, 216, 252, 0.05)); padding: 1.5rem; border-radius: 12px; border: 2px solid #1DD8FC;">
            <h4 style="color: #1e293b; margin-bottom: 1rem;"><i class="ti ti-key"></i> Recommended Keywords</h4>
            
            ${keywords.primary && keywords.primary.length > 0 ? `
                <div style="margin-bottom: 1rem;">
                    <strong style="color: #1e293b; font-size: 0.9rem;">Primary Keywords:</strong><br>
                    <div style="margin-top: 0.5rem;">
                        ${keywords.primary.map(k => `<span style="display: inline-block; padding: 0.5rem 0.875rem; background: linear-gradient(135deg, rgba(153, 38, 243, 0.15), rgba(29, 216, 252, 0.15)); border: 2px solid #9926F3; border-radius: 6px; margin: 0.25rem; font-size: 0.875rem; color: #9926F3; font-weight: 600;">#${k}</span>`).join('')}
                    </div>
                </div>
            ` : ''}
            
            ${keywords.secondary && keywords.secondary.length > 0 ? `
                <div>
                    <strong style="color: #1e293b; font-size: 0.9rem;">Secondary Keywords:</strong><br>
                    <div style="margin-top: 0.5rem;">
                        ${keywords.secondary.map(k => `<span style="display: inline-block; padding: 0.5rem 0.875rem; background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 6px; margin: 0.25rem; font-size: 0.875rem; color: #64748b;">#${k}</span>`).join('')}
                    </div>
                </div>
            ` : ''}
        </div>
    `;
    
    container.style.display = 'block';
}

// =====================================================
// VISUAL ANALYSIS FEATURE (GOOGLE VISION API)
// =====================================================

async function analyzeImageUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    if (!file.type.startsWith('image/')) {
        alert('Please upload an image file');
        return;
    }
    
    if (file.size > 10 * 1024 * 1024) {
        alert('Image size must be less than 10MB');
        return;
    }
    
    // Show preview
    const reader = new FileReader();
    reader.onload = function(e) {
        const preview = document.getElementById('imagePreview');
        if (preview) {
            preview.innerHTML = `<img src="${e.target.result}" style="max-width: 100%; max-height: 400px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">`;
            preview.style.display = 'block';
        }
    };
    reader.readAsDataURL(file);
    
    // Convert to base64 for analysis
    const base64Reader = new FileReader();
    base64Reader.onload = async function(e) {
        // FIXED: Properly extract base64 without data URL prefix
        const base64String = e.target.result;
        const base64Data = base64String.split(',')[1]; // Remove "data:image/jpeg;base64," prefix
        await analyzeVisualContent(base64Data);
    };
    base64Reader.readAsDataURL(file);
}

async function analyzeVisualContent(base64Image) {
    const analyzeBtn = document.getElementById('analyzeVisualBtn');
    if (analyzeBtn) {
        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML = '<i class="ti ti-loader"></i> Analyzing...';
    }
    
    try {
        const token = localStorage.getItem('access_token'); // FIXED: Standardized token
        const response = await fetch(`/api/v1/content/analyze-visual`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                image_base64: base64Image,
                platform: window.selectedPlatforms[0] || 'instagram' // Use window.selectedPlatforms
            })
        });
        
        const result = await response.json();
        
        if (result.success && result.data) {
            displayVisualAnalysis(result.data);
            showNotification('Visual analysis complete!', 'success');
        } else {
            throw new Error(result.detail || 'Visual analysis failed');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error: ' + error.message);
    } finally {
        if (analyzeBtn) {
            analyzeBtn.disabled = false;
            analyzeBtn.innerHTML = '<i class="ti ti-scan"></i> Analyze Image';
        }
    }
}

function displayVisualAnalysis(analysis) {
    const container = document.getElementById('visualAnalysisResults');
    if (!container) return;
    
    const score = analysis.composition_score || 0;
    const scoreColor = score >= 70 ? '#10b981' : score >= 50 ? '#f59e0b' : '#ef4444';
    const scoreText = score >= 70 ? 'Optimized' : score >= 50 ? 'Good' : 'Needs Improvement';
    
    container.innerHTML = `
        <div style="background: white; border-radius: 12px; padding: 2rem; border: 2px solid ${scoreColor};">
            <!-- Score Header -->
            <div style="display: flex; align-items: center; gap: 2rem; margin-bottom: 2rem; padding-bottom: 1.5rem; border-bottom: 2px solid #f1f5f9;">
                <div style="text-align: center;">
                    <div style="width: 120px; height: 120px; border-radius: 50%; background: linear-gradient(135deg, ${scoreColor}20, ${scoreColor}40); display: flex; align-items: center; justify-content: center; border: 4px solid ${scoreColor};">
                        <div>
                            <div style="font-size: 2.5rem; font-weight: bold; color: ${scoreColor};">${Math.round(score)}</div>
                            <div style="font-size: 0.75rem; color: #64748b; margin-top: 0.25rem;">/ 100</div>
                        </div>
                    </div>
                    <div style="margin-top: 0.75rem; padding: 0.375rem 0.875rem; background: ${scoreColor}; color: white; border-radius: 6px; font-size: 0.875rem; font-weight: 600;">
                        ${scoreText}
                    </div>
                </div>
                
                <div style="flex: 1;">
                    <h3 style="color: #1e293b; margin-bottom: 1rem; font-size: 1.25rem;">Visual Analysis Results</h3>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem;">
                        <!-- Face Detection -->
                        <div style="padding: 0.875rem; background: ${analysis.face_detected ? '#d1fae5' : '#fee2e2'}; border-radius: 8px; border-left: 3px solid ${analysis.face_detected ? '#10b981' : '#ef4444'};">
                            <div style="display: flex; align-items: center; gap: 0.5rem;">
                                <i class="ti ti-${analysis.face_detected ? 'user-check' : 'user-x'}" style="font-size: 1.25rem; color: ${analysis.face_detected ? '#10b981' : '#ef4444'};"></i>
                                <span style="font-size: 0.9rem; font-weight: 500; color: #1e293b;">${analysis.face_detected ? `${analysis.faces_count} face(s) detected` : 'No faces detected'}</span>
                            </div>
                        </div>
                        
                        <!-- Object Detection -->
                        <div style="padding: 0.875rem; background: #f8fafc; border-radius: 8px; border-left: 3px solid #9926F3;">
                            <div style="display: flex; align-items: center; gap: 0.5rem;">
                                <i class="ti ti-tags" style="font-size: 1.25rem; color: #9926F3;"></i>
                                <span style="font-size: 0.9rem; font-weight: 500; color: #1e293b;">${analysis.labels ? analysis.labels.length : 0} objects detected</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Detailed Analysis -->
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-bottom: 1.5rem;">
                ${analysis.labels && analysis.labels.length > 0 ? `
                    <div>
                        <h4 style="color: #1e293b; margin-bottom: 0.75rem; font-size: 1rem;"><i class="ti ti-eye"></i> Detected Objects</h4>
                        <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                            ${analysis.labels.slice(0, 8).map(label => `
                                <span style="display: inline-block; padding: 0.375rem 0.75rem; background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 0.85rem; color: #475569;">${label}</span>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
                
                ${analysis.dominant_colors && analysis.dominant_colors.length > 0 ? `
                    <div>
                        <h4 style="color: #1e293b; margin-bottom: 0.75rem; font-size: 1rem;"><i class="ti ti-palette"></i> Color Palette</h4>
                        <div style="display: flex; gap: 0.75rem;">
                            ${analysis.dominant_colors.map(c => `
                                <div style="text-align: center;">
                                    <div style="width: 60px; height: 60px; background: ${c.rgb}; border-radius: 8px; border: 2px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.15);"></div>
                                    <div style="font-size: 0.7rem; color: #64748b; margin-top: 0.375rem;">${c.hex}</div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
            </div>
            
            ${analysis.text_detected ? `
                <div style="background: #f0f9ff; padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem; border-left: 3px solid #0284c7;">
                    <h4 style="color: #1e293b; margin-bottom: 0.5rem; font-size: 1rem;"><i class="ti ti-text"></i> Text Detected</h4>
                    <p style="font-size: 0.9rem; color: #334155; font-style: italic;">"${analysis.text_detected}"</p>
                </div>
            ` : ''}
            
            ${analysis.recommendations && analysis.recommendations.length > 0 ? `
                <div>
                    <h4 style="color: #1e293b; margin-bottom: 1rem; font-size: 1.1rem;"><i class="ti ti-bulb"></i> Improvement Recommendations</h4>
                    ${analysis.recommendations.map(rec => `
                        <div style="background: linear-gradient(135deg, rgba(153, 38, 243, 0.05), rgba(29, 216, 252, 0.05)); padding: 1.25rem; border-radius: 8px; margin-bottom: 0.75rem; border-left: 4px solid #9926F3;">
                            <p style="color: #334155; margin-bottom: 0.75rem; line-height: 1.6;">${rec.tip}</p>
                            <span style="display: inline-block; padding: 0.375rem 0.75rem; background: #10b981; color: white; border-radius: 6px; font-size: 0.8rem; font-weight: 600;">
                                <i class="ti ti-trending-up"></i> Potential Impact: ${rec.impact}
                            </span>
                        </div>
                    `).join('')}
                </div>
            ` : ''}
        </div>
    `;
    
    container.style.display = 'block';
}

// =====================================================
// LOAD CONTENT LIBRARY
// =====================================================

async function loadContentLibrary() {
    const libraryContainer = document.getElementById('contentLibrary');
    
    try {
        const token = localStorage.getItem('access_token'); // FIXED: Standardized token
        const response = await fetch(`${API_BASE}/list?limit=10`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch content library');
        }
        
        const result = await response.json();
        
        if (result.success && result.data.length > 0) {
            libraryContainer.innerHTML = result.data.map(content => `
                <div class="content-card" style="background: white; border-radius: 12px; padding: 1.5rem; border: 1px solid #e2e8f0; transition: all 0.2s;">
                    <div class="content-card-header">
                        <div>
                            <h3 style="font-size: 1rem; font-weight: 600; color: #1e293b; margin-bottom: 0.5rem;">
                                ${content.title || 'Untitled Content'}
                            </h3>
                            <div class="content-meta" style="display: flex; flex-wrap: wrap; gap: 0.75rem; font-size: 0.85rem; color: #64748b;">
                                <span><i class="ti ti-brand-${content.platform}"></i> ${capitalize(content.platform)}</span>
                                <span><i class="ti ti-file"></i> ${capitalize(content.content_type)}</span>
                                <span><i class="ti ti-user"></i> ${content.client_name}</span>
                                <span class="status-badge" style="padding: 0.25rem 0.625rem; background: ${content.status === 'published' ? '#dcfce7' : '#fef3c7'}; color: ${content.status === 'published' ? '#16a34a' : '#eab308'}; border-radius: 4px; font-weight: 500;">${capitalize(content.status)}</span>
                            </div>
                        </div>
                        <div class="content-actions" style="display: flex; gap: 0.5rem;">
                            <button class="btn-icon" onclick="viewContent(${content.content_id})" title="View" style="padding: 0.5rem; border: 1px solid #e2e8f0; border-radius: 6px; background: white; cursor: pointer;">
                                <i class="ti ti-eye"></i>
                            </button>
                            <button class="btn-icon" onclick="deleteContent(${content.content_id})" title="Delete" style="padding: 0.5rem; border: 1px solid #fee2e2; border-radius: 6px; background: white; color: #dc2626; cursor: pointer;">
                                <i class="ti ti-trash"></i>
                            </button>
                        </div>
                    </div>
                    
                    <p style="font-size: 0.9rem; color: #64748b; line-height: 1.6; margin: 1rem 0;">
                        ${truncateText(content.content_text, 150)}
                    </p>
                    
                    ${content.hashtags && content.hashtags.length > 0 ? `
                        <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 1rem;">
                            ${content.hashtags.slice(0, 5).map(tag => 
                                `<span style="display: inline-block; padding: 0.25rem 0.625rem; background: linear-gradient(135deg, rgba(153, 38, 243, 0.1), rgba(29, 216, 252, 0.1)); border: 1px solid #9926F3; border-radius: 4px; font-size: 0.8rem; color: #9926F3;">#${tag}</span>`
                            ).join('')}
                            ${content.hashtags.length > 5 ? 
                                `<span style="padding: 0.25rem 0.625rem; background: #f1f5f9; border-radius: 4px; font-size: 0.8rem; color: #64748b;">+${content.hashtags.length - 5} more</span>` : ''}
                        </div>
                    ` : ''}
                    
                    ${content.optimization_score ? `
                        <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #e2e8f0; display: flex; align-items: center; justify-content: space-between;">
                            <span style="font-size: 0.875rem; color: #64748b;">
                                <i class="ti ti-chart-line"></i> Performance Score
                            </span>
                            <div style="display: flex; align-items: center; gap: 0.5rem;">
                                <div style="width: 60px; height: 8px; background: #e2e8f0; border-radius: 4px; overflow: hidden;">
                                    <div style="width: ${content.optimization_score}%; height: 100%; background: ${content.optimization_score >= 70 ? '#10b981' : '#f59e0b'}; transition: width 0.3s;"></div>
                                </div>
                                <strong style="color: ${content.optimization_score >= 70 ? '#10b981' : '#f59e0b'};">${Math.round(content.optimization_score)}%</strong>
                            </div>
                        </div>
                    ` : ''}
                </div>
            `).join('');
        } else {
            libraryContainer.innerHTML = `
                <div class="empty-state" style="text-align: center; padding: 3rem; color: #94a3b8;">
                    <i class="ti ti-folder-off" style="font-size: 3rem; margin-bottom: 1rem; display: block;"></i>
                    <h3 style="color: #64748b; margin-bottom: 0.5rem;">No Content Yet</h3>
                    <p>Start generating content to build your library</p>
                </div>
            `;
        }
        
    } catch (error) {
        console.error('Error loading content library:', error);
        libraryContainer.innerHTML = `
            <div class="empty-state" style="text-align: center; padding: 3rem; color: #dc2626;">
                <i class="ti ti-alert-circle" style="font-size: 3rem; margin-bottom: 1rem; display: block;"></i>
                <h3>Failed to Load Content</h3>
                <p>${error.message}</p>
            </div>
        `;
    }
}

// =====================================================
// CONTENT ACTIONS
// =====================================================

async function viewContent(contentId) {
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_BASE}/${contentId}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch content');
        }
        
        const result = await response.json();
        
        if (result.success) {
            // Display in modal or preview panel
            alert('Content details:\n\n' + result.data.content_text);
        }
        
    } catch (error) {
        console.error('Error viewing content:', error);
        showNotification('Failed to load content', 'error');
    }
}

async function deleteContent(contentId) {
    if (!confirm('Are you sure you want to delete this content?')) {
        return;
    }
    
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_BASE}/${contentId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to delete content');
        }
        
        showNotification('Content deleted successfully', 'success');
        loadContentLibrary();
        
    } catch (error) {
        console.error('Error deleting content:', error);
        showNotification('Failed to delete content', 'error');
    }
}

// =====================================================
// UTILITY FUNCTIONS
// =====================================================

function capitalize(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function truncateText(text, maxLength) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: ${type === 'success' ? '#dcfce7' : type === 'error' ? '#fee2e2' : '#dbeafe'};
        color: ${type === 'success' ? '#16a34a' : type === 'error' ? '#dc2626' : '#2563eb'};
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        z-index: 9999;
        animation: slideIn 0.3s ease;
        font-weight: 500;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}