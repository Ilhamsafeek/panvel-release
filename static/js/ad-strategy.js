/**
 * Ad Strategy & Suggestion Engine - Frontend JavaScript (FIXED)
 * File: static/js/ad-strategy.js
 * 
 * FIXES:
 * - Real modals instead of alerts
 * - Proper JSON parsing and display
 * - No dummy data
 */

const API_BASE = `/api/v1/ad-strategy`;
let selectedPlatform = '';
let selectedContentType = '';
let generatedContent = null;
let currentClientId = null;
let selectedAdCopy = null;



// Platform-specific data
const PLATFORM_DATA = {
    meta: {
        name: 'Meta (Facebook & Instagram)',
        formats: [
            { value: 'feed', label: 'Feed' },
            { value: 'stories', label: 'Stories' },
            { value: 'reels', label: 'Reels' },
            { value: 'carousel', label: 'Carousel' }
        ],
        placements: ['Feed', 'Stories', 'Reels', 'Messenger', 'Audience Network']
    },
    google: {
        name: 'Google Ads',
        formats: [
            { value: 'search', label: 'Search Text Ad' },
            { value: 'display', label: 'Display Image Ad' },
            { value: 'video', label: 'Video Ad (YouTube)' },
            { value: 'responsive', label: 'Responsive Search Ad' }
        ],
        placements: ['Search Network', 'Display Network', 'YouTube', 'Gmail', 'Discover']
    },
    linkedin: {
        name: 'LinkedIn',
        formats: [
            { value: 'sponsored_content', label: 'Sponsored Content' },
            { value: 'message_ad', label: 'Message Ad' },
            { value: 'text_ad', label: 'Text Ad' },
            { value: 'dynamic_ad', label: 'Dynamic Ad' }
        ],
        placements: ['Feed', 'Messaging', 'Right Rail']
    }
};

// Global state
let currentObjectiveGuidance = null;
let uploadedMediaAssets = [];
let currentCampaignData = null;



// =====================================================
// INITIALIZATION
// =====================================================

document.addEventListener('DOMContentLoaded', function () {
    loadClients();
    loadDashboard();
    setupEventListeners();
    loadCampaigns();
});


function setupEventListeners() {
    // Platform change handler
    const platformSelect = document.getElementById('campaignPlatform');
    if (platformSelect) {
        platformSelect.addEventListener('change', handlePlatformChange);
    }
    
    // Objective change handler
    const objectiveSelect = document.getElementById('campaignObjective');
    if (objectiveSelect) {
        objectiveSelect.addEventListener('change', handleObjectiveChange);
    }
}



async function handlePlatformChange(event) {
    const platform = event.target.value;
    
    if (!platform) {
        document.getElementById('campaignObjective').innerHTML = '<option value="">Select objective...</option>';
        hideObjectiveGuidance();
        return;
    }
    
    // Load platform-specific objectives
    await loadPlatformObjectives(platform);
    
    // Show platform info
    showPlatformInfo(platform);
}


async function loadPlatformObjectives(platform) {
    try {
        const response = await fetch(`${API_BASE}/platforms/${platform}/objectives`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) throw new Error('Failed to load objectives');
        
        const data = await response.json();
        const objectiveSelect = document.getElementById('campaignObjective');
        
        objectiveSelect.innerHTML = '<option value="">Select objective...</option>';
        
        data.objectives.forEach(obj => {
            const option = document.createElement('option');
            option.value = obj.value;
            option.textContent = obj.label;
            option.title = obj.description;
            objectiveSelect.appendChild(option);
        });
        
    } catch (error) {
        console.error('Error loading objectives:', error);
        showNotification('Failed to load platform objectives', 'error');
    }
}

function showPlatformInfo(platform) {
    const platformInfo = PLATFORM_DATA[platform];
    if (!platformInfo) return;
    
    // Show format options
    const formatContainer = document.getElementById('platformFormatsContainer');
    if (formatContainer) {
        formatContainer.innerHTML = `
            <div class="form-group">
                <label>Ad Format</label>
                <select class="form-control" id="adFormat">
                    <option value="">Select format...</option>
                    ${platformInfo.formats.map(f => 
                        `<option value="${f.value}">${f.label}</option>`
                    ).join('')}
                </select>
            </div>
        `;
    }
    
    // Show placement info
    const placementContainer = document.getElementById('platformPlacementsInfo');
    if (placementContainer) {
        placementContainer.innerHTML = `
            <div style="margin-top: 1rem; padding: 1rem; background: #f8fafc; border-radius: 8px;">
                <div style="font-weight: 600; margin-bottom: 0.5rem;">Available Placements:</div>
                <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                    ${platformInfo.placements.map(p => 
                        `<span style="padding: 0.25rem 0.75rem; background: white; border-radius: 20px; font-size: 0.875rem;">${p}</span>`
                    ).join('')}
                </div>
            </div>
        `;
    }
}



// ========== OBJECTIVE-BASED GUIDANCE ==========

async function handleObjectiveChange(event) {
    const objective = event.target.value;
    const platform = document.getElementById('campaignPlatform').value;
    const budget = parseFloat(document.getElementById('campaignBudget').value) || 0;
    
    if (!objective || !platform || budget < 100) {
        hideObjectiveGuidance();
        return;
    }
    
    // Show loading
    showGuidanceLoading();
    
    // Get AI guidance
    await getObjectiveGuidance(platform, objective, budget);
}

async function getObjectiveGuidance(platform, objective, budget) {
    try {
        const response = await fetch(`${API_BASE}/guidance/objective`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                platform,
                objective,
                budget,
                target_audience: {
                    age_range: [18, 65],
                    genders: ['all'],
                    countries: ['US']
                },
                industry: document.getElementById('clientIndustry')?.value || null
            })
        });
        
        if (!response.ok) throw new Error('Failed to get guidance');
        
        const data = await response.json();
        currentObjectiveGuidance = data.guidance;
        
        displayObjectiveGuidance(data.guidance);
        
    } catch (error) {
        console.error('Error getting objective guidance:', error);
        hideObjectiveGuidance();
        showNotification('Failed to get AI guidance', 'error');
    }
}

function showGuidanceLoading() {
    const container = document.getElementById('objectiveGuidanceContainer');
    if (!container) return;
    
    container.style.display = 'block';
    container.innerHTML = `
        <div style="padding: 2rem; text-align: center;">
            <i class="ti ti-loader" style="font-size: 2rem; color: #6366f1; animation: spin 1s linear infinite;"></i>
            <div style="margin-top: 1rem; color: #64748b;">Getting AI recommendations...</div>
        </div>
    `;
}

function displayObjectiveGuidance(guidance) {
    const container = document.getElementById('objectiveGuidanceContainer');
    if (!container) return;
    
    const settings = guidance.platform_specific_settings;
    const targeting = guidance.targeting_refinements;
    const creative = guidance.creative_guidelines;
    const performance = guidance.performance_expectations;
    
    container.innerHTML = `
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.5rem; border-radius: 8px 8px 0 0;">
            <h3 style="margin: 0; display: flex; align-items: center; gap: 0.5rem;">
                <i class="ti ti-sparkles"></i>
                AI-Powered Campaign Guidance
            </h3>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Personalized recommendations for ${guidance.platform.toUpperCase()} - ${guidance.objective}</p>
        </div>
        
        <div style="background: white; padding: 1.5rem; border-radius: 0 0 8px 8px; border: 1px solid #e2e8f0;">
            <!-- Ad Formats -->
            <div style="margin-bottom: 1.5rem;">
                <div style="font-weight: 600; margin-bottom: 0.75rem; display: flex; align-items: center; gap: 0.5rem;">
                    <i class="ti ti-layout"></i>
                    Recommended Ad Formats
                </div>
                <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                    ${settings.recommended_ad_formats.map(format => `
                        <span style="padding: 0.5rem 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 20px; font-size: 0.875rem;">
                            ${format}
                        </span>
                    `).join('')}
                </div>
            </div>
            
            <!-- Bidding Strategy -->
            <div style="margin-bottom: 1.5rem;">
                <div style="font-weight: 600; margin-bottom: 0.75rem; display: flex; align-items: center; gap: 0.5rem;">
                    <i class="ti ti-currency-dollar"></i>
                    Bidding Strategy
                </div>
                <div style="padding: 1rem; background: #f8fafc; border-radius: 8px;">
                    <div style="font-weight: 600; color: #6366f1; margin-bottom: 0.5rem;">
                        ${settings.bidding_strategy}
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 0.75rem;">
                        <div>
                            <div style="font-size: 0.75rem; color: #64748b;">Daily Budget</div>
                            <div style="font-weight: 600; font-size: 1.25rem;">$${settings.budget_allocation.daily_budget.toFixed(2)}</div>
                        </div>
                        <div>
                            <div style="font-size: 0.75rem; color: #64748b;">Lifetime Budget</div>
                            <div style="font-weight: 600; font-size: 1.25rem;">$${settings.budget_allocation.lifetime_budget.toFixed(2)}</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Performance Expectations -->
            <div style="margin-bottom: 1.5rem;">
                <div style="font-weight: 600; margin-bottom: 0.75rem; display: flex; align-items: center; gap: 0.5rem;">
                    <i class="ti ti-chart-line"></i>
                    Expected Performance
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem;">
                    <div style="padding: 1rem; background: #f8fafc; border-radius: 8px; text-align: center;">
                        <div style="font-size: 0.75rem; color: #64748b; margin-bottom: 0.5rem;">Estimated Reach</div>
                        <div style="font-weight: 700; font-size: 1.5rem; color: #6366f1;">${performance.estimated_reach.toLocaleString()}</div>
                    </div>
                    <div style="padding: 1rem; background: #f8fafc; border-radius: 8px; text-align: center;">
                        <div style="font-size: 0.75rem; color: #64748b; margin-bottom: 0.5rem;">Expected CTR</div>
                        <div style="font-weight: 700; font-size: 1.5rem; color: #10b981;">${performance.estimated_ctr}%</div>
                    </div>
                    <div style="padding: 1rem; background: #f8fafc; border-radius: 8px; text-align: center;">
                        <div style="font-size: 0.75rem; color: #64748b; margin-bottom: 0.5rem;">Estimated CPC</div>
                        <div style="font-weight: 700; font-size: 1.5rem; color: #f59e0b;">$${performance.estimated_cpc.toFixed(2)}</div>
                    </div>
                    <div style="padding: 1rem; background: #f8fafc; border-radius: 8px; text-align: center;">
                        <div style="font-size: 0.75rem; color: #64748b; margin-bottom: 0.5rem;">Estimated Conversions</div>
                        <div style="font-weight: 700; font-size: 1.5rem; color: #8b5cf6;">${performance.estimated_conversions}</div>
                    </div>
                </div>
            </div>
            
            <!-- Optimization Tips -->
            <div>
                <div style="font-weight: 600; margin-bottom: 0.75rem; display: flex; align-items: center; gap: 0.5rem;">
                    <i class="ti ti-bulb"></i>
                    Optimization Tips
                </div>
                <ul style="margin: 0; padding-left: 1.5rem; color: #475569;">
                    ${guidance.optimization_tips.map(tip => `<li style="margin-bottom: 0.5rem;">${tip}</li>`).join('')}
                </ul>
            </div>
        </div>
    `;
    
    container.style.display = 'block';
}

function hideObjectiveGuidance() {
    const container = document.getElementById('objectiveGuidanceContainer');
    if (container) {
        container.style.display = 'none';
        container.innerHTML = '';
    }
    currentObjectiveGuidance = null;
}



function initializeMediaUpload(campaignId) {
    const dropZone = document.getElementById('mediaDropZone');
    const fileInput = document.getElementById('mediaFileInput');
    
    if (!dropZone || !fileInput) return;
    
    // Click to upload
    dropZone.addEventListener('click', () => fileInput.click());
    
    // File input change
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleMediaFiles(e.target.files, campaignId);
        }
    });
    
    // Drag and drop
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = '#6366f1';
        dropZone.style.background = '#f8fafc';
    });
    
    dropZone.addEventListener('dragleave', () => {
        dropZone.style.borderColor = '#e2e8f0';
        dropZone.style.background = 'white';
    });
    
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = '#e2e8f0';
        dropZone.style.background = 'white';
        
        if (e.dataTransfer.files.length > 0) {
            handleMediaFiles(e.dataTransfer.files, campaignId);
        }
    });
}

async function handleMediaFiles(files, campaignId) {
    const platform = document.getElementById('campaignPlatform').value;
    
    if (!platform) {
        showNotification('Please select a platform first', 'error');
        return;
    }
    
    for (let file of files) {
        await uploadMediaFile(file, platform, campaignId);
    }
}


function removeMedia(assetId) {
    uploadedMediaAssets = uploadedMediaAssets.filter(a => a.asset_id !== assetId);
    updateMediaGallery();
}



// =====================================================
// TAB SWITCHING
// =====================================================
function switchTab(tabName) {
    // Remove active class from all tabs
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    event.target.closest('.tab').classList.add('active');
    
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    // Show selected tab
    document.getElementById(`${tabName}-tab`).classList.add('active');
    
    // Load data based on tab
    if (tabName === 'campaigns') {
        loadCampaigns();
    } else if (tabName === 'audience') {
        loadAudienceSegments();
    } else if (tabName === 'monitoring') {
        // NEW: Load monitoring data
        loadCampaignMonitoring();
    }
}

// =====================================================
// LOAD CLIENTS
// =====================================================

const token = localStorage.getItem('access_token');

async function loadClients() {
    try {
        const response = await fetch('/api/v1/clients/list', {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) throw new Error('Failed to fetch clients');

        const data = await response.json();

        const selectors = ['filterClientCampaign', 'filterClientAudience'];
        selectors.forEach(id => {
            const select = document.getElementById(id);
            if (select) {
                select.innerHTML = '<option value="">All Clients</option>';
                if (data.clients && data.clients.length > 0) {
                    data.clients.forEach(client => {
                        select.innerHTML += `<option value="${client.user_id}">${client.full_name}</option>`;
                    });
                }
            }
        });

        if (data.clients && data.clients.length === 1) {
            currentClientId = data.clients[0].user_id;
        }

    } catch (error) {
        console.error('Error loading clients:', error);
        showNotification('Failed to load clients', 'error');
    }
}

// =====================================================
// DASHBOARD
// =====================================================

async function loadDashboard() {
    const clientId = currentClientId || (await getFirstClientId());
    if (!clientId) {
        showEmptyDashboard();
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/dashboard/${clientId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) throw new Error('Failed to load dashboard');

        const data = await response.json();

        displayDashboardStats(data.campaign_stats);
        displayPlatformPerformance(data.platform_performance);
        displayRecentCampaigns(data.recent_campaigns);

    } catch (error) {
        console.error('Error loading dashboard:', error);
        showNotification('Failed to load dashboard data', 'error');
    }
}

async function getFirstClientId() {
    try {
        const response = await fetch('/api/v1/clients/list', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await response.json();
        return data.clients && data.clients.length > 0 ? data.clients[0].user_id : null;
    } catch {
        return null;
    }
}

function displayDashboardStats(stats) {
    const container = document.getElementById('dashboardStats');
    if (!stats) {
        container.innerHTML = '<div class="empty-state"><p>No campaign data available</p></div>';
        return;
    }

    container.innerHTML = `
        <div class="stat-card">
            <div class="stat-icon"><i class="ti ti-badge-ad"></i></div>
            <div class="stat-value">${stats.total_campaigns || 0}</div>
            <div class="stat-label">Total Campaigns</div>
        </div>
        <div class="stat-card">
            <div class="stat-icon"><i class="ti ti-bolt"></i></div>
            <div class="stat-value">${stats.active_campaigns || 0}</div>
            <div class="stat-label">Active Campaigns</div>
        </div>
        <div class="stat-card">
            <div class="stat-icon"><i class="ti ti-player-pause"></i></div>
            <div class="stat-value">${stats.paused_campaigns || 0}</div>
            <div class="stat-label">Paused</div>
        </div>
        <div class="stat-card">
            <div class="stat-icon"><i class="ti ti-currency-dollar"></i></div>
            <div class="stat-value">₹${Number(stats.total_budget || 0).toLocaleString()}</div>
            <div class="stat-label">Total Budget</div>
        </div>
    `;
}

function displayPlatformPerformance(platforms) {
    const container = document.getElementById('platformPerformance');

    if (!platforms || platforms.length === 0) {
        container.innerHTML = '<div class="empty-state"><i class="ti ti-chart-bar"></i><p>No performance data yet</p></div>';
        return;
    }

    container.innerHTML = platforms.map(platform => `
        <div class="campaign-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <h3 style="margin: 0; text-transform: capitalize;">${platform.platform}</h3>
                <span class="platform-badge">${platform.campaigns} Campaigns</span>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem;">
                <div>
                    <div style="font-size: 0.875rem; color: #64748b;">Impressions</div>
                    <div style="font-size: 1.25rem; font-weight: 600;">${Number(platform.impressions || 0).toLocaleString()}</div>
                </div>
                <div>
                    <div style="font-size: 0.875rem; color: #64748b;">Clicks</div>
                    <div style="font-size: 1.25rem; font-weight: 600;">${Number(platform.clicks || 0).toLocaleString()}</div>
                </div>
                <div>
                    <div style="font-size: 0.875rem; color: #64748b;">Spend</div>
                    <div style="font-size: 1.25rem; font-weight: 600;">₹${Number(platform.spend || 0).toLocaleString()}</div>
                </div>
                <div>
                    <div style="font-size: 0.875rem; color: #64748b;">Conversions</div>
                    <div style="font-size: 1.25rem; font-weight: 600;">${platform.conversions || 0}</div>
                </div>
            </div>
        </div>
    `).join('');
}

function displayRecentCampaigns(campaigns) {
    const container = document.getElementById('recentCampaigns');

    if (!campaigns || campaigns.length === 0) {
        container.innerHTML = '<div class="empty-state"><i class="ti ti-badge-ad"></i><p>No campaigns yet</p></div>';
        return;
    }

    container.innerHTML = campaigns.map(campaign => `
        <div class="campaign-card" onclick="viewCampaign(${campaign.campaign_id})">
            <div class="campaign-header">
                <div>
                    <div class="campaign-title">${campaign.campaign_name}</div>
                    <div class="campaign-meta">
                        <span><i class="ti ti-calendar"></i> ${new Date(campaign.created_at).toLocaleDateString()}</span>
                        <span><i class="ti ti-user"></i> ${campaign.creator_name}</span>
                    </div>
                </div>
                <div style="display: flex; gap: 0.5rem; align-items: start;">
                    <span class="status-badge ${campaign.status}">${campaign.status}</span>
                    <span class="platform-badge">${campaign.platform}</span>
                </div>
            </div>
            <div style="font-size: 0.875rem; color: #64748b;">
                Budget: ₹${Number(campaign.budget).toLocaleString()}
            </div>
        </div>
    `).join('');
}

function showEmptyDashboard() {
    document.getElementById('dashboardStats').innerHTML = '<div class="empty-state"><i class="ti ti-chart-bar"></i><p>No data available. Create your first campaign to get started.</p></div>';
}

// =====================================================
// CAMPAIGNS
// =====================================================
async function loadCampaigns() {
    const clientId = document.getElementById('filterClientCampaign').value;
    const platform = document.getElementById('filterPlatformCampaign').value;

    const container = document.getElementById('campaignsList');
    container.innerHTML = '<div style="text-align: center; padding: 2rem;"><div class="loading-spinner"></div><p>Loading campaigns...</p></div>';

    try {
        let url;

        // If "All Clients" is selected (empty value), use list-all endpoint
        if (!clientId || clientId === '') {
            url = `${API_BASE}/campaigns/list-all`;
            if (platform) url += `?platform=${platform}`;
        } else {
            // Specific client selected
            url = `${API_BASE}/campaigns/list/${clientId}`;
            if (platform) url += `?platform=${platform}`;
        }

        const response = await fetch(url, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) throw new Error('Failed to load campaigns');

        const data = await response.json();

        if (!data.campaigns || data.campaigns.length === 0) {
            container.innerHTML = '<div class="empty-state"><i class="ti ti-badge-ad"></i><h3>No campaigns yet</h3><p>Create your first campaign to get started</p></div>';
            return;
        }

        container.innerHTML = data.campaigns.map(campaign => `
            <div class="campaign-card" onclick="viewCampaign(${campaign.campaign_id})">
                <div class="campaign-header">
                    <div>
                        <div class="campaign-title">${campaign.campaign_name}</div>
                        <div class="campaign-meta">
                            <span><i class="ti ti-calendar"></i> ${new Date(campaign.created_at).toLocaleDateString()}</span>
                            <span><i class="ti ti-building"></i> ${campaign.client_name || 'Unknown Client'}</span>
                            <span><i class="ti ti-user"></i> ${campaign.creator_name}</span>
                        </div>
                    </div>
                    <div style="display: flex; gap: 0.5rem; align-items: start;">
                        <span class="status-badge ${campaign.status}">${campaign.status}</span>
                        <span class="platform-badge">${campaign.platform}</span>
                    </div>
                </div>
                <div class="campaign-footer">
                    <div>Budget: ₹${Number(campaign.budget || 0).toLocaleString()}</div>
                    <div>${campaign.total_ads || 0} ads</div>
                </div>
            </div>
        `).join('');

    } catch (error) {
        console.error('Error loading campaigns:', error);
        container.innerHTML = '<div class="empty-state"><i class="ti ti-alert-circle"></i><p>Failed to load campaigns</p></div>';
        showNotification('Failed to load campaigns', 'error');
    }
}


function openCreateCampaignModal() {
    // Load clients into modal dropdown
    loadClientsForModal('campaignClient');

    // Set default start date to today
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('campaignStartDate').value = today;

    // Show modal
    document.getElementById('campaignModal').style.display = 'flex';
}

function closeCampaignModal() {
    document.getElementById('campaignModal').style.display = 'none';
    document.getElementById('campaignForm').reset();
}

async function submitCampaign() {
    const btn = document.getElementById('submitCampaignBtn');
    btn.disabled = true;
    btn.innerHTML = '<i class="ti ti-loader"></i> Creating...';

    try {
        const platform = document.getElementById('campaignPlatform').value;
        const objective = document.getElementById('campaignObjective').value;
        
        if (!platform || !objective) {
            throw new Error('Please select platform and objective');
        }
        
        const formData = {
            client_id: parseInt(document.getElementById('campaignClient').value),
            campaign_name: document.getElementById('campaignName').value,
            platform,
            objective,
            budget: parseFloat(document.getElementById('campaignBudget').value),
            start_date: document.getElementById('campaignStartDate').value,
            end_date: document.getElementById('campaignEndDate').value || null,
            bidding_strategy: currentObjectiveGuidance?.platform_specific_settings?.bidding_strategy || null,
            target_audience: currentObjectiveGuidance?.targeting_refinements || {},
            placement_settings: currentObjectiveGuidance?.platform_specific_settings || {},
            ab_test_config: document.getElementById('enableABTest')?.checked ? {} : null
        };

        const response = await fetch(`${API_BASE}/campaigns/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create campaign');
        }

        const data = await response.json();
        currentCampaignData = { campaign_id: data.campaign_id, ...formData };
        
        showNotification('Campaign created successfully!', 'success');
        
        // Show next step: Create Ads
        showCreateAdsStep(data.campaign_id, platform, objective);

    } catch (error) {
        console.error('Error creating campaign:', error);
        showNotification(error.message, 'error');
        btn.disabled = false;
        btn.innerHTML = '<i class="ti ti-check"></i> Create Campaign';
    }
}


// ========== CREATE ADS STEP ==========

function showCreateAdsStep(campaignId, platform, objective) {
    const modal = document.getElementById('campaignModal');
    const modalBody = modal.querySelector('.modal-body');
    
    modalBody.innerHTML = `
        <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 1.5rem; border-radius: 8px; margin-bottom: 2rem;">
            <h3 style="margin: 0; display: flex; align-items: center; gap: 0.5rem;">
                <i class="ti ti-check"></i>
                Campaign Created Successfully!
            </h3>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Now let's create your first ad for this campaign</p>
        </div>
        
        <form id="createAdForm" onsubmit="event.preventDefault(); submitPlatformSpecificAd(${campaignId}, '${platform}', '${objective}');">
            <!-- Platform-Specific Fields -->
            <div id="platformSpecificFields"></div>
            
            <!-- Media Upload -->
            <div class="form-group">
                <label>Media Assets</label>
                <div id="mediaDropZone" style="border: 2px dashed #e2e8f0; border-radius: 8px; padding: 2rem; text-align: center; cursor: pointer; transition: all 0.3s;">
                    <i class="ti ti-upload" style="font-size: 2rem; color: #94a3b8;"></i>
                    <div style="margin-top: 0.5rem; color: #64748b;">Click or drag files to upload</div>
                    <div style="font-size: 0.875rem; color: #94a3b8; margin-top: 0.25rem;">Images (JPG, PNG) or Videos (MP4)</div>
                </div>
                <input type="file" id="mediaFileInput" accept="image/*,video/*" multiple style="display: none;">
                <div id="uploadProgressContainer" style="margin-top: 1rem;"></div>
                <div id="mediaGallery" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 1rem; margin-top: 1rem;"></div>
            </div>
            
            <div style="display: flex; gap: 1rem; justify-content: flex-end; margin-top: 2rem;">
                <button type="button" class="btn btn-secondary" onclick="skipToPublish(${campaignId})">
                    Skip & Publish Campaign
                </button>
                <button type="submit" class="btn btn-primary" id="submitAdBtn">
                    <i class="ti ti-check"></i> Create Ad
                </button>
            </div>
        </form>
    `;
    
    // Render platform-specific fields
    renderPlatformSpecificAdFields(platform, objective);
    
    // Initialize media upload
    initializeMediaUpload(campaignId);
}


async function renderPlatformSpecificAdFields(platform, objective) {
    const container = document.getElementById('platformSpecificFields');
    const platformData = PLATFORM_DATA[platform];
    
    // Get AI-powered objective guidance
    await fetchObjectiveGuidance(platform, objective);
    
    let fieldsHTML = `
        <div class="form-group">
            <label>Ad Name *</label>
            <input type="text" class="form-control" id="adName" required placeholder="e.g., Summer Sale Ad 1">
        </div>
    `;
    
    // ========== META (FACEBOOK & INSTAGRAM) ==========
    if (platform === 'meta') {
        fieldsHTML += `
            <!-- Meta-Specific Fields -->
            <div class="alert" style="background: linear-gradient(135deg, #9926F3 0%, #1DD8FC 100%); color: white; padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem;">
                <i class="ti ti-brand-facebook"></i> Meta Ad Requirements
                <p style="font-size: 0.875rem; margin: 0.5rem 0 0 0;">Feed ads: 125 chars | Stories: 60 chars | Reels: 100 chars</p>
            </div>
            
            <div class="form-group">
                <label>Ad Format * <i class="ti ti-info-circle" title="Choose where your ad appears"></i></label>
                <select class="form-control" id="metaAdFormat" required onchange="updateMetaCharLimits(this.value)">
                    <option value="">Select format...</option>
                    <option value="FEED">Feed Post (Facebook & Instagram)</option>
                    <option value="STORY">Stories (Full Screen, Vertical)</option>
                    <option value="REEL">Reels (Short-form Video)</option>
                    <option value="CAROUSEL">Carousel (Multiple Images)</option>
                    <option value="COLLECTION">Collection (Product Catalog)</option>
                </select>
                <small id="metaFormatHelp" class="form-text"></small>
            </div>
            
            <div class="form-grid" style="grid-template-columns: 2fr 1fr;">
                <div class="form-group">
                    <label>Primary Text *</label>
                    <textarea class="form-control" id="adPrimaryText" required rows="3" maxlength="125"
                        placeholder="Main ad copy - appears above your creative"></textarea>
                </div>
                <div style="padding-top: 2rem;">
                    <div style="background: #f8fafc; padding: 0.75rem; border-radius: 8px;">
                        <div style="font-size: 0.75rem; color: #64748b;">Character Count</div>
                        <div style="font-size: 1.5rem; font-weight: 600; color: var(--primary-color);">
                            <span id="primaryTextCount">0</span>/125
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="form-group">
                <label>Headline *</label>
                <input type="text" class="form-control" id="adHeadline" required maxlength="40"
                    placeholder="Catchy headline (max 40 characters)">
                <small><span id="headlineCount">0</span>/40 characters</small>
            </div>
            
            <div class="form-group">
                <label>Description (Optional)</label>
                <input type="text" class="form-control" id="adDescription" maxlength="30"
                    placeholder="Short description (max 30 characters)">
                <small><span id="descriptionCount">0</span>/30 characters</small>
            </div>
            
            <div class="form-group">
                <label>Destination URL *</label>
                <input type="url" class="form-control" id="adDestinationUrl" required
                    placeholder="https://yourwebsite.com/landing-page">
            </div>
            
            <div class="form-group">
                <label>Call to Action</label>
                <select class="form-control" id="adCTA">
                    <option value="LEARN_MORE">Learn More</option>
                    <option value="SHOP_NOW">Shop Now</option>
                    <option value="SIGN_UP">Sign Up</option>
                    <option value="DOWNLOAD">Download</option>
                    <option value="GET_QUOTE">Get Quote</option>
                    <option value="CONTACT_US">Contact Us</option>
                    <option value="BOOK_NOW">Book Now</option>
                    <option value="APPLY_NOW">Apply Now</option>
                </select>
            </div>
            
            <div class="form-group">
                <label>Placements (Auto-optimized by default)</label>
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.5rem;">
                    <label style="display: flex; align-items: center; padding: 0.5rem; background: #f8fafc; border-radius: 6px;">
                        <input type="checkbox" checked value="facebook_feed" style="margin-right: 0.5rem;"> Facebook Feed
                    </label>
                    <label style="display: flex; align-items: center; padding: 0.5rem; background: #f8fafc; border-radius: 6px;">
                        <input type="checkbox" checked value="instagram_feed" style="margin-right: 0.5rem;"> Instagram Feed
                    </label>
                    <label style="display: flex; align-items: center; padding: 0.5rem; background: #f8fafc; border-radius: 6px;">
                        <input type="checkbox" checked value="facebook_stories" style="margin-right: 0.5rem;"> Facebook Stories
                    </label>
                    <label style="display: flex; align-items: center; padding: 0.5rem; background: #f8fafc; border-radius: 6px;">
                        <input type="checkbox" checked value="instagram_stories" style="margin-right: 0.5rem;"> Instagram Stories
                    </label>
                </div>
                <small class="form-text">Uncheck placements you want to exclude</small>
            </div>
        `;
    }
    
    // ========== GOOGLE ADS ==========
    else if (platform === 'google') {
        fieldsHTML += `
            <!-- Google Ads-Specific Fields -->
            <div class="alert" style="background: linear-gradient(135deg, #4285F4 0%, #34A853 100%); color: white; padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem;">
                <i class="ti ti-brand-google"></i> Google Ads Requirements
                <p style="font-size: 0.875rem; margin: 0.5rem 0 0 0;">Provide 3-15 headlines and 2-4 descriptions for responsive ads</p>
            </div>
            
            <div class="form-group">
                <label>Campaign Type *</label>
                <select class="form-control" id="googleCampaignType" required onchange="updateGoogleFields(this.value)">
                    <option value="">Select type...</option>
                    <option value="SEARCH">Search (Text Ads on Google Search)</option>
                    <option value="DISPLAY">Display (Banner Ads on Websites)</option>
                    <option value="VIDEO">Video (YouTube Ads)</option>
                    <option value="SHOPPING">Shopping (Product Listings)</option>
                    <option value="PERFORMANCE_MAX">Performance Max (All Channels)</option>
                </select>
            </div>
            
            <div id="googleSearchFields" style="display: none;">
                <div class="form-group">
                    <label>Headlines (3-15 required) * <i class="ti ti-info-circle" title="Google rotates these automatically"></i></label>
                    <div id="googleHeadlinesContainer">
                        <input type="text" class="form-control google-headline" style="margin-bottom: 0.5rem;" maxlength="30" 
                            placeholder="Headline 1 (max 30 characters)" required>
                        <input type="text" class="form-control google-headline" style="margin-bottom: 0.5rem;" maxlength="30" 
                            placeholder="Headline 2 (max 30 characters)" required>
                        <input type="text" class="form-control google-headline" style="margin-bottom: 0.5rem;" maxlength="30" 
                            placeholder="Headline 3 (max 30 characters)" required>
                    </div>
                    <button type="button" class="btn btn-sm btn-secondary" onclick="addGoogleHeadline()">
                        <i class="ti ti-plus"></i> Add Headline (Max 15)
                    </button>
                </div>
                
                <div class="form-group">
                    <label>Descriptions (2-4 required) *</label>
                    <div id="googleDescriptionsContainer">
                        <textarea class="form-control google-description" style="margin-bottom: 0.5rem;" maxlength="90" rows="2"
                            placeholder="Description 1 (max 90 characters)" required></textarea>
                        <textarea class="form-control google-description" style="margin-bottom: 0.5rem;" maxlength="90" rows="2"
                            placeholder="Description 2 (max 90 characters)" required></textarea>
                    </div>
                    <button type="button" class="btn btn-sm btn-secondary" onclick="addGoogleDescription()">
                        <i class="ti ti-plus"></i> Add Description (Max 4)
                    </button>
                </div>
                
                <div class="form-group">
                    <label>Final URL *</label>
                    <input type="url" class="form-control" id="googleFinalUrl" required
                        placeholder="https://yourwebsite.com/landing-page">
                </div>
                
                <div class="form-group">
                    <label>Display Path (Optional)</label>
                    <div class="form-grid" style="grid-template-columns: 1fr 1fr;">
                        <input type="text" class="form-control" id="googlePath1" maxlength="15"
                            placeholder="Path 1 (e.g., 'shoes')">
                        <input type="text" class="form-control" id="googlePath2" maxlength="15"
                            placeholder="Path 2 (e.g., 'sale')">
                    </div>
                    <small class="form-text">Appears as: yourwebsite.com/path1/path2</small>
                </div>
                
                <div class="form-group">
                    <label>Keywords (Comma-separated)</label>
                    <textarea class="form-control" id="googleKeywords" rows="2"
                        placeholder="running shoes, athletic footwear, sports shoes"></textarea>
                    <small class="form-text">Keywords help trigger your search ads</small>
                </div>
            </div>
        `;
    }
    
    // ========== LINKEDIN ==========
    else if (platform === 'linkedin') {
        fieldsHTML += `
            <!-- LinkedIn-Specific Fields -->
            <div class="alert" style="background: linear-gradient(135deg, #0077B5 0%, #00A0DC 100%); color: white; padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem;">
                <i class="ti ti-brand-linkedin"></i> LinkedIn Ad Requirements
                <p style="font-size: 0.875rem; margin: 0.5rem 0 0 0;">Professional B2B advertising with job title & company targeting</p>
            </div>
            
            <div class="form-group">
                <label>Ad Format *</label>
                <select class="form-control" id="linkedinAdFormat" required onchange="updateLinkedInFields(this.value)">
                    <option value="">Select format...</option>
                    <option value="SPONSORED_CONTENT">Sponsored Content (Native Feed Posts)</option>
                    <option value="MESSAGE_AD">Message Ads (Direct InMail)</option>
                    <option value="TEXT_AD">Text Ads (Sidebar Ads)</option>
                    <option value="VIDEO_AD">Video Ads (Feed Video)</option>
                    <option value="CAROUSEL">Carousel (Multiple Images)</option>
                </select>
            </div>
            
            <div id="linkedinSponsoredFields">
                <div class="form-group">
                    <label>Introductory Text * <i class="ti ti-info-circle" title="Main message, max 600 chars"></i></label>
                    <textarea class="form-control" id="linkedinIntroText" required rows="4" maxlength="600"
                        placeholder="Introduce your content (appears above the image/video)"></textarea>
                    <small><span id="linkedinIntroCount">0</span>/600 characters</small>
                </div>
                
                <div class="form-group">
                    <label>Headline *</label>
                    <input type="text" class="form-control" id="linkedinHeadline" required maxlength="200"
                        placeholder="Headline (max 200 characters)">
                    <small><span id="linkedinHeadlineCount">0</span>/200 characters</small>
                </div>
                
                <div class="form-group">
                    <label>Destination URL *</label>
                    <input type="url" class="form-control" id="linkedinDestinationUrl" required
                        placeholder="https://yourwebsite.com/landing-page">
                </div>
                
                <div class="form-group">
                    <label>Call to Action</label>
                    <select class="form-control" id="linkedinCTA">
                        <option value="LEARN_MORE">Learn More</option>
                        <option value="APPLY">Apply</option>
                        <option value="DOWNLOAD">Download</option>
                        <option value="SIGN_UP">Sign Up</option>
                        <option value="REGISTER">Register</option>
                        <option value="JOIN">Join</option>
                        <option value="ATTEND">Attend</option>
                        <option value="REQUEST_DEMO">Request Demo</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>Target Audience (Optional but Recommended)</label>
                    <div style="background: #f8fafc; padding: 1rem; border-radius: 8px;">
                        <div class="form-group" style="margin-bottom: 0.75rem;">
                            <label style="font-size: 0.875rem;">Job Titles</label>
                            <input type="text" class="form-control" id="linkedinJobTitles" 
                                placeholder="e.g., CEO, Marketing Director, VP Sales">
                        </div>
                        <div class="form-group" style="margin-bottom: 0.75rem;">
                            <label style="font-size: 0.875rem;">Company Size</label>
                            <select class="form-control" id="linkedinCompanySize">
                                <option value="">All Sizes</option>
                                <option value="1-10">1-10 employees</option>
                                <option value="11-50">11-50 employees</option>
                                <option value="51-200">51-200 employees</option>
                                <option value="201-500">201-500 employees</option>
                                <option value="501-1000">501-1000 employees</option>
                                <option value="1001+">1001+ employees</option>
                            </select>
                        </div>
                        <div class="form-group" style="margin-bottom: 0;">
                            <label style="font-size: 0.875rem;">Industries</label>
                            <input type="text" class="form-control" id="linkedinIndustries" 
                                placeholder="e.g., Technology, Healthcare, Finance">
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
  
    // ========== UNIVERSAL MEDIA UPLOAD SECTION (Single Unified Section) ==========
fieldsHTML += `
    <hr style="margin: 2rem 0; border: none; border-top: 1px solid #e2e8f0;">
    
    <div class="form-group">
        <label style="font-size: 1rem; font-weight: 600; margin-bottom: 0.5rem; display: block;">
            <i class="ti ti-photo"></i> Media Assets *
        </label>
        <p style="font-size: 0.875rem; color: #64748b; margin-bottom: 1.5rem;">
            Upload images/videos OR provide URLs (at least one required)
        </p>
        
        <!-- Combined Upload Area -->
        <div style="background: #f8fafc; border: 2px dashed #cbd5e1; border-radius: 12px; padding: 2rem; margin-bottom: 1.5rem;" 
             id="dropZone"
             ondragover="handleDragOver(event)"
             ondragleave="handleDragLeave(event)"
             ondrop="handleDrop(event)">
            
            <input type="file" 
                   id="mediaFileInput" 
                   accept="image/jpeg,image/jpg,image/png,video/mp4,video/quicktime" 
                   multiple 
                   style="display: none;" 
                   onchange="handleFileSelection(event)">
            
            <div style="text-align: center;">
                <i class="ti ti-upload" style="font-size: 3rem; color: var(--primary-color); margin-bottom: 1rem; display: block;"></i>
                
                <button type="button" class="btn btn-primary" style="margin-bottom: 1rem;" onclick="document.getElementById('mediaFileInput').click()">
                    <i class="ti ti-upload"></i> Upload Files
                </button>
                
                <p style="font-size: 0.875rem; color: #64748b; margin: 0;">
                    or drag and drop files here
                </p>
                
                <p style="font-size: 0.75rem; color: #94a3b8; margin-top: 0.5rem;">
                    Images: JPG, PNG (max 30MB) | Videos: MP4, MOV (max 4GB)
                </p>
            </div>
            
            <!-- Upload Progress -->
            <div id="uploadProgressContainer" style="margin-top: 1.5rem;"></div>
        </div>
        
        <!-- Uploaded Files Gallery -->
        <div id="uploadedMediaGallery" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 1rem; margin-bottom: 1.5rem;"></div>
        
        <!-- OR Divider -->
        <div style="display: flex; align-items: center; gap: 1rem; margin: 1.5rem 0;">
            <div style="flex: 1; height: 1px; background: #e2e8f0;"></div>
            <span style="color: #64748b; font-size: 0.875rem; font-weight: 500;">OR provide URLs</span>
            <div style="flex: 1; height: 1px; background: #e2e8f0;"></div>
        </div>
        
        <!-- URL Inputs -->
        <div id="mediaUrlsContainer" style="display: flex; flex-direction: column; gap: 0.5rem;">
            <input type="url" class="form-control" placeholder="https://example.com/image1.jpg" style="font-size: 0.875rem;">
            <input type="url" class="form-control" placeholder="https://example.com/image2.jpg" style="font-size: 0.875rem;">
        </div>
        
        <button type="button" class="btn btn-sm btn-secondary" style="margin-top: 0.5rem;" onclick="addMoreMediaUrl()">
            <i class="ti ti-plus"></i> Add More URLs
        </button>
    </div>
    
    <!-- Objective-Based Guidance Display -->
    <div id="objectiveGuidanceDisplay" style="margin-top: 2rem;"></div>
`;


    container.innerHTML = fieldsHTML;
    
    // Initialize character counters
    initializeCharacterCounters();
    
    // Show platform-specific fields based on selection
    if (platform === 'google') {
        updateGoogleFields('SEARCH'); // Default to search
    }
    if (platform === 'linkedin') {
        updateLinkedInFields('SPONSORED_CONTENT'); // Default to sponsored
    }
}




// ========== HELPER FUNCTIONS ==========

function updateMetaCharLimits(format) {
    const help = document.getElementById('metaFormatHelp');
    const primaryText = document.getElementById('adPrimaryText');
    
    switch(format) {
        case 'FEED':
            primaryText.maxLength = 125;
            help.textContent = '📱 Feed ads: Perfect for detailed storytelling (125 chars)';
            break;
        case 'STORY':
            primaryText.maxLength = 60;
            help.textContent = '📱 Stories: Short & punchy for full-screen impact (60 chars)';
            break;
        case 'REEL':
            primaryText.maxLength = 100;
            help.textContent = '🎬 Reels: Engaging short-form video content (100 chars)';
            break;
        case 'CAROUSEL':
            primaryText.maxLength = 125;
            help.textContent = '🎠 Carousel: Showcase multiple products/features (125 chars)';
            break;
        case 'COLLECTION':
            primaryText.maxLength = 125;
            help.textContent = '🛍️ Collection: Drive product discovery with catalog (125 chars)';
            break;
    }
}

function updateGoogleFields(campaignType) {
    const searchFields = document.getElementById('googleSearchFields');
    searchFields.style.display = campaignType === 'SEARCH' || campaignType === 'PERFORMANCE_MAX' ? 'block' : 'none';
}

function updateLinkedInFields(format) {
    const sponsoredFields = document.getElementById('linkedinSponsoredFields');
    sponsoredFields.style.display = format === 'SPONSORED_CONTENT' || format === 'VIDEO_AD' || format === 'CAROUSEL' ? 'block' : 'none';
}

function addGoogleHeadline() {
    const container = document.getElementById('googleHeadlinesContainer');
    const currentCount = container.querySelectorAll('.google-headline').length;
    
    if (currentCount >= 15) {
        showNotification('Maximum 15 headlines allowed', 'warning');
        return;
    }
    
    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'form-control google-headline';
    input.style.marginBottom = '0.5rem';
    input.maxLength = 30;
    input.placeholder = `Headline ${currentCount + 1} (max 30 characters)`;
    
    container.appendChild(input);
}

function addGoogleDescription() {
    const container = document.getElementById('googleDescriptionsContainer');
    const currentCount = container.querySelectorAll('.google-description').length;
    
    if (currentCount >= 4) {
        showNotification('Maximum 4 descriptions allowed', 'warning');
        return;
    }
    
    const textarea = document.createElement('textarea');
    textarea.className = 'form-control google-description';
    textarea.style.marginBottom = '0.5rem';
    textarea.maxLength = 90;
    textarea.rows = 2;
    textarea.placeholder = `Description ${currentCount + 1} (max 90 characters)`;
    
    container.appendChild(textarea);
}

function initializeCharacterCounters() {
    // Meta counters
    const primaryText = document.getElementById('adPrimaryText');
    const headline = document.getElementById('adHeadline');
    const description = document.getElementById('adDescription');
    
    if (primaryText) {
        primaryText.addEventListener('input', (e) => {
            document.getElementById('primaryTextCount').textContent = e.target.value.length;
        });
    }
    
    if (headline) {
        headline.addEventListener('input', (e) => {
            document.getElementById('headlineCount').textContent = e.target.value.length;
        });
    }
    
    if (description) {
        description.addEventListener('input', (e) => {
            document.getElementById('descriptionCount').textContent = e.target.value.length;
        });
    }
    
    // LinkedIn counters
    const linkedinIntro = document.getElementById('linkedinIntroText');
    const linkedinHeadline = document.getElementById('linkedinHeadline');
    
    if (linkedinIntro) {
        linkedinIntro.addEventListener('input', (e) => {
            document.getElementById('linkedinIntroCount').textContent = e.target.value.length;
        });
    }
    
    if (linkedinHeadline) {
        linkedinHeadline.addEventListener('input', (e) => {
            document.getElementById('linkedinHeadlineCount').textContent = e.target.value.length;
        });
    }
}



// ========== DRAG AND DROP HANDLERS ==========

function handleDragOver(event) {
    event.preventDefault();
    event.stopPropagation();
    
    const dropZone = document.getElementById('dropZone');
    dropZone.style.borderColor = 'var(--primary-color)';
    dropZone.style.background = 'linear-gradient(135deg, rgba(153, 38, 243, 0.05) 0%, rgba(29, 216, 252, 0.05) 100%)';
}

function handleDragLeave(event) {
    event.preventDefault();
    event.stopPropagation();
    
    const dropZone = document.getElementById('dropZone');
    dropZone.style.borderColor = '#cbd5e1';
    dropZone.style.background = '#f8fafc';
}

function handleDrop(event) {
    event.preventDefault();
    event.stopPropagation();
    
    const dropZone = document.getElementById('dropZone');
    dropZone.style.borderColor = '#cbd5e1';
    dropZone.style.background = '#f8fafc';
    
    const files = event.dataTransfer.files;
    if (files.length > 0) {
        processFiles(files);
    }
}

// ========== FILE SELECTION AND UPLOAD ==========

async function handleFileSelection(event) {
    const files = event.target.files;
    if (files.length > 0) {
        await processFiles(files);
    }
}



async function processFiles(files) {
    const campaignId = document.getElementById('adCampaignId').value;
    const platform = currentSelectedPlatform;
    
    if (!campaignId || !platform) {
        showNotification('Campaign information missing. Please close and reopen the modal.', 'error');
        return;
    }
    
    for (let file of files) {
        await uploadMediaFile(file, platform, campaignId);
    }
}

async function uploadMediaFile(file, platform, campaignId) {
    const token = localStorage.getItem('token');
    
    // Validate file type
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'video/mp4', 'video/quicktime'];
    if (!validTypes.includes(file.type)) {
        showNotification(`Invalid file type: ${file.type}. Please use JPG, PNG, MP4, or MOV.`, 'error');
        return;
    }
    
    // Validate file size
    const maxSize = file.type.startsWith('video') ? 4 * 1024 * 1024 * 1024 : 30 * 1024 * 1024;
    if (file.size > maxSize) {
        const maxSizeMB = maxSize / (1024 * 1024);
        showNotification(`File too large. Max size: ${maxSizeMB}MB`, 'error');
        return;
    }
    
    // Show upload progress
    const uploadId = showUploadProgress(file.name);
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('platform', platform);
        formData.append('campaign_id', campaignId);
        
        const response = await fetch(`${API_BASE}/ads/media/upload`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload failed');
        }
        
        const data = await response.json();
        
        // Add to uploaded assets
        uploadedMediaAssets.push({
            asset_id: data.asset_id,
            media_id: data.media_id,
            url: data.url,
            file_name: file.name,
            file_type: file.type,
            platform: platform
        });
        
        updateUploadProgress(uploadId, 'success', file.name);
        updateMediaGallery();
        
        showNotification(`✅ ${file.name} uploaded successfully`, 'success');
        
    } catch (error) {
        console.error('Upload error:', error);
        updateUploadProgress(uploadId, 'error', file.name);
        showNotification(`Failed to upload ${file.name}: ${error.message}`, 'error');
    }
}


function showUploadProgress(fileName) {
    const container = document.getElementById('uploadProgressContainer');
    if (!container) return null;
    
    const uploadId = `upload_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const progressHTML = `
        <div id="${uploadId}" style="padding: 0.75rem; background: white; border-radius: 8px; margin-bottom: 0.5rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 0.875rem; display: flex; align-items: center; gap: 0.5rem;">
                    <i class="ti ti-file"></i> ${fileName}
                </span>
                <i class="ti ti-loader" style="animation: spin 1s linear infinite; color: var(--primary-color);"></i>
            </div>
            <div style="margin-top: 0.5rem; height: 4px; background: #e2e8f0; border-radius: 2px; overflow: hidden;">
                <div style="height: 100%; background: var(--primary-color); width: 0%; animation: progressBar 2s ease-in-out;"></div>
            </div>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', progressHTML);
    return uploadId;
}

function updateUploadProgress(uploadId, status, fileName) {
    const element = document.getElementById(uploadId);
    if (!element) return;
    
    const icon = status === 'success' ? 
        '<i class="ti ti-circle-check" style="color: #22c55e; font-size: 1.25rem;"></i>' : 
        '<i class="ti ti-circle-x" style="color: #ef4444; font-size: 1.25rem;"></i>';
    
    const bgColor = status === 'success' ? '#f0fdf4' : '#fef2f2';
    
    element.style.background = bgColor;
    element.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-size: 0.875rem; display: flex; align-items: center; gap: 0.5rem;">
                <i class="ti ti-file"></i> ${fileName}
            </span>
            ${icon}
        </div>
    `;
    
    // Remove after 3 seconds if success
    if (status === 'success') {
        setTimeout(() => {
            element.style.animation = 'fadeOut 0.3s ease-out';
            setTimeout(() => element.remove(), 300);
        }, 3000);
    }
}




function updateMediaGallery() {
    const gallery = document.getElementById('uploadedMediaGallery');
    if (!gallery) return;
    
    if (uploadedMediaAssets.length === 0) {
        gallery.innerHTML = '';
        return;
    }
    
    gallery.innerHTML = uploadedMediaAssets.map((asset, index) => {
        const isVideo = asset.file_type && asset.file_type.startsWith('video');
        
        return `
            <div style="position: relative; aspect-ratio: 1; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border: 2px solid var(--primary-color);">
                ${isVideo ? `
                    <video src="${asset.url}" style="width: 100%; height: 100%; object-fit: cover;"></video>
                    <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: rgba(0,0,0,0.6); border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;">
                        <i class="ti ti-player-play" style="color: white; font-size: 1.5rem;"></i>
                    </div>
                ` : `
                    <img src="${asset.url}" alt="${asset.file_name}" style="width: 100%; height: 100%; object-fit: cover;">
                `}
                
                <button onclick="removeUploadedAsset(${index})" type="button"
                    style="position: absolute; top: 4px; right: 4px; background: rgba(239, 68, 68, 0.9); color: white; border: none; border-radius: 50%; width: 28px; height: 28px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s;">
                    <i class="ti ti-x" style="font-size: 16px;"></i>
                </button>
                
                <div style="position: absolute; bottom: 0; left: 0; right: 0; background: linear-gradient(to top, rgba(0,0,0,0.7), transparent); padding: 0.5rem; color: white; font-size: 0.75rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                    ${asset.file_name}
                </div>
            </div>
        `;
    }).join('');
}

function removeUploadedAsset(index) {
    if (confirm('Remove this media asset?')) {
        uploadedMediaAssets.splice(index, 1);
        updateMediaGallery();
        showNotification('Media asset removed', 'info');
    }
}

function addMoreMediaUrl() {
    const container = document.getElementById('mediaUrlsContainer');
    const input = document.createElement('input');
    input.type = 'url';
    input.className = 'form-control';
    input.style.fontSize = '0.875rem';
    input.placeholder = 'https://example.com/image.jpg';
    
    container.appendChild(input);
}


// ========== OBJECTIVE-BASED AI GUIDANCE ==========

async function fetchObjectiveGuidance(platform, objective) {
    const token = localStorage.getItem('token');
    const guidanceDisplay = document.getElementById('objectiveGuidanceDisplay');
    
    if (!guidanceDisplay) return;
    
    // Show loading
    guidanceDisplay.innerHTML = `
        <div style="background: #f8fafc; padding: 1.5rem; border-radius: 12px; text-align: center;">
            <i class="ti ti-loader" style="font-size: 2rem; animation: spin 1s linear infinite; color: var(--primary-color);"></i>
            <p style="margin-top: 1rem; color: #64748b;">Generating AI recommendations...</p>
        </div>
    `;
    
    try {
        const response = await fetch(`${API_BASE}/ads/objective-guidance`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                platform,
                objective,
                budget: parseFloat(document.getElementById('campaignBudget')?.value || 1000),
                target_audience: {},
                industry: null
            })
        });
        
        if (!response.ok) throw new Error('Failed to fetch guidance');
        
        const data = await response.json();
        
        // Display guidance
        displayObjectiveGuidance(data.guidance);
        
    } catch (error) {
        console.error('Guidance error:', error);
        guidanceDisplay.innerHTML = '';
    }
}

function displayObjectiveGuidance(guidance) {
    const guidanceDisplay = document.getElementById('objectiveGuidanceDisplay');
    if (!guidanceDisplay) return;
    
    const settings = guidance.platform_specific_settings || {};
    const creative = guidance.creative_guidelines || {};
    const performance = guidance.performance_expectations || {};
    const tips = guidance.optimization_tips || [];
    
    guidanceDisplay.innerHTML = `
        <div style="background: linear-gradient(135deg, rgba(153, 38, 243, 0.1) 0%, rgba(29, 216, 252, 0.1) 100%); padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(153, 38, 243, 0.2);">
            <h3 style="margin: 0 0 1rem 0; display: flex; align-items: center; gap: 0.5rem;">
                <i class="ti ti-bulb"></i> AI Recommendations for ${guidance.objective}
            </h3>
            
            ${settings.recommended_ad_formats && settings.recommended_ad_formats.length > 0 ? `
                <div style="margin-bottom: 1rem;">
                    <strong style="color: var(--primary-color);">Recommended Ad Formats:</strong>
                    <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 0.5rem;">
                        ${settings.recommended_ad_formats.map(format => `
                            <span style="padding: 0.25rem 0.75rem; background: white; border-radius: 16px; font-size: 0.875rem; border: 1px solid var(--primary-color); color: var(--primary-color);">
                                ${format}
                            </span>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
            
            ${settings.bidding_strategy ? `
                <div style="margin-bottom: 1rem;">
                    <strong style="color: var(--primary-color);">Bidding Strategy:</strong>
                    <p style="margin: 0.5rem 0 0 0; color: #64748b;">${settings.bidding_strategy}</p>
                </div>
            ` : ''}
            
            ${performance.estimated_ctr ? `
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin-bottom: 1rem;">
                    <div style="background: white; padding: 1rem; border-radius: 8px;">
                        <div style="font-size: 0.75rem; color: #64748b;">Est. CTR</div>
                        <div style="font-size: 1.5rem; font-weight: 600; color: var(--primary-color);">${performance.estimated_ctr}%</div>
                    </div>
                    ${performance.estimated_cpc ? `
                        <div style="background: white; padding: 1rem; border-radius: 8px;">
                            <div style="font-size: 0.75rem; color: #64748b;">Est. CPC</div>
                            <div style="font-size: 1.5rem; font-weight: 600; color: var(--primary-color);">$${performance.estimated_cpc}</div>
                        </div>
                    ` : ''}
                    ${performance.estimated_reach ? `
                        <div style="background: white; padding: 1rem; border-radius: 8px;">
                            <div style="font-size: 0.75rem; color: #64748b;">Est. Reach</div>
                            <div style="font-size: 1.5rem; font-weight: 600; color: var(--primary-color);">${performance.estimated_reach.toLocaleString()}</div>
                        </div>
                    ` : ''}
                </div>
            ` : ''}
            
            ${tips.length > 0 ? `
                <div>
                    <strong style="color: var(--primary-color);">Optimization Tips:</strong>
                    <ul style="margin: 0.5rem 0 0 0; padding-left: 1.5rem; color: #64748b;">
                        ${tips.map(tip => `<li>${tip}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
        </div>
    `;
}



// ========== SUBMIT PLATFORM-SPECIFIC AD ==========

async function submitPlatformSpecificAd(campaignId, platform, objective) {
    const btn = document.getElementById('submitAdBtn');
    btn.disabled = true;
    btn.innerHTML = '<i class="ti ti-loader"></i> Creating Ad...';
    
    try {
        // Collect media IDs
        const mediaIds = uploadedMediaAssets.map(a => a.media_id);
        const mediaUrls = uploadedMediaAssets.map(a => a.url);
        
        if (mediaIds.length === 0 && platform !== 'google') {
            throw new Error('Please upload at least one media file');
        }
        
        // Collect platform-specific data
        let adData = {
            campaign_id: campaignId,
            platform,
            objective,
            ad_name: document.getElementById('adName').value,
            media_ids: mediaIds,
            media_urls: mediaUrls
        };
        
        // Platform-specific fields
        if (platform === 'meta') {
            adData = {
                ...adData,
                primary_text: document.getElementById('adPrimaryText').value,
                headline: document.getElementById('adHeadline').value,
                description: document.getElementById('adDescription').value || '',
                destination_url: document.getElementById('adDestinationUrl').value,
                call_to_action: document.getElementById('adCTA').value,
                platform_specific_data: {
                    format: document.getElementById('metaAdFormat').value
                }
            };
        } else if (platform === 'google') {
            const headlines = Array.from(document.querySelectorAll('[data-headline]'))
                .map(el => el.value)
                .filter(v => v.trim());
            
            const descriptions = Array.from(document.querySelectorAll('[data-description]'))
                .map(el => el.value)
                .filter(v => v.trim());
            
            const keywords = document.getElementById('googleKeywords').value
                .split('\n')
                .filter(k => k.trim());
            
            if (headlines.length < 3) {
                throw new Error('At least 3 headlines required for Google Ads');
            }
            if (descriptions.length < 2) {
                throw new Error('At least 2 descriptions required for Google Ads');
            }
            
            adData = {
                ...adData,
                primary_text: headlines[0],
                headline: headlines.join(' | '),
                description: descriptions.join(' | '),
                destination_url: document.getElementById('googleFinalUrl').value,
                platform_specific_data: {
                    campaign_type: document.getElementById('googleCampaignType').value,
                    headlines,
                    descriptions,
                    keywords
                }
            };
        } else if (platform === 'linkedin') {
            adData = {
                ...adData,
                primary_text: document.getElementById('linkedinIntroText').value,
                headline: document.getElementById('linkedinHeadline').value,
                destination_url: document.getElementById('linkedinDestinationUrl').value,
                call_to_action: document.getElementById('linkedinCTA').value,
                platform_specific_data: {
                    format: document.getElementById('linkedinAdFormat').value
                }
            };
        }
        
        // Create ad via API
        const response = await fetch(`${API_BASE}/ads/create-platform-specific`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(adData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create ad');
        }
        
        const data = await response.json();
        
        showNotification('Ad created successfully!', 'success');
        
        // Show publish option
        showPublishOption(campaignId, platform);
        
    } catch (error) {
        console.error('Error creating ad:', error);
        showNotification(error.message, 'error');
        btn.disabled = false;
        btn.innerHTML = '<i class="ti ti-check"></i> Create Ad';
    }
}




// ========== PUBLISH CAMPAIGN ==========

function showPublishOption(campaignId, platform) {
    const modal = document.getElementById('campaignModal');
    const modalBody = modal.querySelector('.modal-body');
    
    modalBody.innerHTML = `
        <div style="background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); color: white; padding: 2rem; border-radius: 8px; text-align: center; margin-bottom: 2rem;">
            <i class="ti ti-confetti" style="font-size: 3rem;"></i>
            <h3 style="margin: 1rem 0 0.5rem 0;">Campaign Ready!</h3>
            <p style="margin: 0; opacity: 0.9;">Your campaign is ready to go live on ${PLATFORM_DATA[platform].name}</p>
        </div>
        
        <div style="background: #f8fafc; padding: 1.5rem; border-radius: 8px; margin-bottom: 2rem;">
            <h4 style="margin: 0 0 1rem 0;">What happens when you publish?</h4>
            <ul style="margin: 0; padding-left: 1.5rem; color: #475569;">
                <li style="margin-bottom: 0.5rem;">Campaign will be sent to ${PLATFORM_DATA[platform].name} ad platform</li>
                <li style="margin-bottom: 0.5rem;">Ad status will be set to PAUSED (you can activate it later)</li>
                <li style="margin-bottom: 0.5rem;">You'll receive a confirmation with external campaign ID</li>
                <li style="margin-bottom: 0.5rem;">You can monitor performance in real-time</li>
            </ul>
        </div>
        
        <div style="display: flex; gap: 1rem; justify-content: center;">
            <button class="btn btn-secondary" onclick="closeCampaignModal(); loadCampaigns();">
                Publish Later
            </button>
            <button class="btn btn-primary" onclick="publishCampaignNow(${campaignId})">
                <i class="ti ti-rocket"></i> Publish to ${PLATFORM_DATA[platform].name}
            </button>
        </div>
    `;
}



async function publishCampaignNow(campaignId) {
    const btn = event.target;
    btn.disabled = true;
    btn.innerHTML = '<i class="ti ti-loader"></i> Publishing...';
    
    try {
        const response = await fetch(`${API_BASE}/campaigns/${campaignId}/publish`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to publish campaign');
        }
        
        const data = await response.json();
        
        showNotification(data.message, 'success');
        
        // Show success message
        showPublishSuccess(data);
        
    } catch (error) {
        console.error('Error publishing campaign:', error);
        showNotification(error.message, 'error');
        btn.disabled = false;
        btn.innerHTML = '<i class="ti ti-rocket"></i> Publish Campaign';
    }
}



function showPublishSuccess(data) {
    const modal = document.getElementById('campaignModal');
    const modalBody = modal.querySelector('.modal-body');
    
    modalBody.innerHTML = `
        <div style="text-align: center; padding: 2rem;">
            <div style="width: 80px; height: 80px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 1.5rem;">
                <i class="ti ti-check" style="font-size: 3rem; color: white;"></i>
            </div>
            <h3 style="margin: 0 0 0.5rem 0;">Campaign Published Successfully!</h3>
            <p style="color: #64748b; margin: 0 0 2rem 0;">Your campaign is now live on the ad platform</p>
            
            ${data.external_campaign_id ? `
                <div style="background: #f8fafc; padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem;">
                    <div style="font-size: 0.875rem; color: #64748b; margin-bottom: 0.5rem;">External Campaign ID</div>
                    <div style="font-family: monospace; color: #475569;">${data.external_campaign_id}</div>
                </div>
            ` : ''}
            
            <button class="btn btn-primary" onclick="closeCampaignModal(); loadCampaigns();">
                <i class="ti ti-check"></i> Done
            </button>
        </div>
    `;
}

function skipToPublish(campaignId) {
    if (!confirm('Skip creating ads and publish the campaign? You can add ads later.')) {
        return;
    }
    
    publishCampaignNow(campaignId);
}



async function publishCampaign(campaignId) {
    if (!confirm('Publish this campaign to the ad platform?')) return;

    try {
        const response = await fetch(`${API_BASE}/campaigns/${campaignId}/publish`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to publish campaign');
        }

        const data = await response.json();
        showNotification(data.message, 'success');
        loadCampaigns();

    } catch (error) {
        console.error('Error publishing campaign:', error);
        showNotification(error.message, 'error');
    }
}


async function viewCampaign(campaignId) {
    try {
        // Fetch campaign details using new endpoint
        const campaignResponse = await fetch(`${API_BASE}/campaigns/details/${campaignId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!campaignResponse.ok) throw new Error('Failed to fetch campaign');

        const campaignData = await campaignResponse.json();
        const campaign = campaignData.campaign;

        if (!campaign) {
            showNotification('Campaign not found', 'error');
            return;
        }

        // Fetch campaign ads
        const adsResponse = await fetch(`${API_BASE}/campaigns/${campaignId}/ads`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        let ads = [];
        if (adsResponse.ok) {
            const adsData = await adsResponse.json();
            ads = adsData.ads || [];
        }

        // Fetch performance data
        const perfResponse = await fetch(`${API_BASE}/performance/${campaignId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        let performance = null;
        if (perfResponse.ok) {
            const perfData = await perfResponse.json();
            performance = perfData.performance || null;
        }

        // Display campaign details modal
        displayCampaignDetailsModal(campaign, ads, performance);

    } catch (error) {
        console.error('Error loading campaign details:', error);
        showNotification('Failed to load campaign details', 'error');
    }
}


function displayCampaignDetailsModal(campaign, ads, performance) {
    const modal = document.getElementById('campaignDetailsModal');
    if (!modal) {
        createCampaignDetailsModal();
    }

    const detailsContainer = document.getElementById('campaignDetailsContent');

    // Campaign header
    let html = `
        <div style="margin-bottom: 2rem;">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;">
                <div>
                    <h2 style="margin: 0 0 0.5rem 0; font-size: 1.5rem;">${campaign.campaign_name}</h2>
                    <div style="display: flex; gap: 0.75rem; align-items: center;">
                        <span class="status-badge ${campaign.status}">${campaign.status}</span>
                        <span class="platform-badge">${campaign.platform}</span>
                        <span style="color: #64748b; font-size: 0.875rem;">
                            <i class="ti ti-target"></i> ${campaign.objective}
                        </span>
                    </div>
                </div>
                <div style="display: flex; gap: 0.75rem;">
                    ${campaign.status === 'draft' ? `
                        <button class="btn btn-primary" onclick="publishCampaign(${campaign.campaign_id})">
                            <i class="ti ti-send"></i> Publish
                        </button>
                    ` : ''}
                    ${campaign.status === 'active' ? `
                        <button class="btn btn-secondary" onclick="pauseCampaign(${campaign.campaign_id})">
                            <i class="ti ti-player-pause"></i> Pause
                        </button>
                    ` : ''}
                    ${campaign.status === 'paused' ? `
                        <button class="btn btn-primary" onclick="resumeCampaign(${campaign.campaign_id})">
                            <i class="ti ti-player-play"></i> Resume
                        </button>
                    ` : ''}
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; background: #f8fafc; padding: 1.5rem; border-radius: 8px;">
                <div>
                    <div style="font-size: 0.875rem; color: #64748b; margin-bottom: 0.25rem;">Budget</div>
                    <div style="font-size: 1.25rem; font-weight: 600;">₹${Number(campaign.budget).toLocaleString()}</div>
                </div>
                <div>
                    <div style="font-size: 0.875rem; color: #64748b; margin-bottom: 0.25rem;">Start Date</div>
                    <div style="font-size: 1rem; font-weight: 500;">${new Date(campaign.start_date).toLocaleDateString()}</div>
                </div>
                ${campaign.end_date ? `
                <div>
                    <div style="font-size: 0.875rem; color: #64748b; margin-bottom: 0.25rem;">End Date</div>
                    <div style="font-size: 1rem; font-weight: 500;">${new Date(campaign.end_date).toLocaleDateString()}</div>
                </div>
                ` : ''}
                <div>
                    <div style="font-size: 0.875rem; color: #64748b; margin-bottom: 0.25rem;">Bidding Strategy</div>
                    <div style="font-size: 0.875rem; font-weight: 500;">${campaign.bidding_strategy || 'Automatic'}</div>
                </div>
                <div>
                    <div style="font-size: 0.875rem; color: #64748b; margin-bottom: 0.25rem;">Total Ads</div>
                    <div style="font-size: 1.25rem; font-weight: 600;">${ads.length}</div>
                </div>
            </div>
        </div>
    `;

    // Performance metrics
    if (performance) {
        html += `
            <div style="margin-bottom: 2rem;">
                <h3 style="margin: 0 0 1rem 0; font-size: 1.125rem;">
                    <i class="ti ti-chart-line"></i> Performance Metrics
                </h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem;">
                    <div class="stat-card">
                        <div class="stat-label">Impressions</div>
                        <div class="stat-value">${Number(performance.impressions || 0).toLocaleString()}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Clicks</div>
                        <div class="stat-value">${Number(performance.clicks || 0).toLocaleString()}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">CTR</div>
                        <div class="stat-value">${(performance.ctr || 0).toFixed(2)}%</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">CPC</div>
                        <div class="stat-value">₹${(performance.cpc || 0).toFixed(2)}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Conversions</div>
                        <div class="stat-value">${Number(performance.conversions || 0).toLocaleString()}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Spent</div>
                        <div class="stat-value">₹${Number(performance.amount_spent || 0).toLocaleString()}</div>
                    </div>
                </div>
            </div>
        `;
    }

    // Campaign ads
    html += `
        <div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <h3 style="margin: 0; font-size: 1.125rem;">
                    <i class="ti ti-ad"></i> Campaign Ads (${ads.length})
                </h3>
                <button class="btn btn-primary" onclick="openCreateAdModal(${campaign.campaign_id})">
                    <i class="ti ti-plus"></i> Create Ad
                </button>
            </div>
            
            ${ads.length === 0 ? `
                <div class="empty-state" style="padding: 2rem;">
                    <i class="ti ti-ad"></i>
                    <p>No ads created yet</p>
                </div>
            ` : `
                <div style="display: grid; gap: 1rem;">
                    ${ads.map(ad => `
                        <div style="border: 1px solid #e2e8f0; border-radius: 8px; padding: 1rem;">
                            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.75rem;">
                                <div>
                                    <div style="font-weight: 600; margin-bottom: 0.25rem;">${ad.ad_name}</div>
                                    <div style="font-size: 0.875rem; color: #64748b;">${ad.ad_format}</div>
                                </div>
                                <span class="status-badge ${ad.status}">${ad.status}</span>
                            </div>
                            
                            <div style="margin-bottom: 0.75rem;">
                                <div style="font-size: 0.875rem; font-weight: 500; margin-bottom: 0.25rem;">Headline:</div>
                                <div style="font-size: 0.875rem;">${ad.headline}</div>
                            </div>
                            
                            <div style="margin-bottom: 0.75rem;">
                                <div style="font-size: 0.875rem; font-weight: 500; margin-bottom: 0.25rem;">Primary Text:</div>
                                <div style="font-size: 0.875rem; color: #64748b;">${ad.primary_text}</div>
                            </div>
                            
                            ${ad.total_impressions ? `
                                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(100px, 1fr)); gap: 1rem; padding-top: 0.75rem; border-top: 1px solid #e2e8f0;">
                                    <div>
                                        <div style="font-size: 0.75rem; color: #64748b;">Impressions</div>
                                        <div style="font-size: 0.875rem; font-weight: 600;">${Number(ad.total_impressions).toLocaleString()}</div>
                                    </div>
                                    <div>
                                        <div style="font-size: 0.75rem; color: #64748b;">Clicks</div>
                                        <div style="font-size: 0.875rem; font-weight: 600;">${Number(ad.total_clicks).toLocaleString()}</div>
                                    </div>
                                    <div>
                                        <div style="font-size: 0.75rem; color: #64748b;">CTR</div>
                                        <div style="font-size: 0.875rem; font-weight: 600;">${(ad.avg_ctr || 0).toFixed(2)}%</div>
                                    </div>
                                    <div>
                                        <div style="font-size: 0.75rem; color: #64748b;">CPC</div>
                                        <div style="font-size: 0.875rem; font-weight: 600;">₹${(ad.avg_cpc || 0).toFixed(2)}</div>
                                    </div>
                                </div>
                            ` : ''}
                        </div>
                    `).join('')}
                </div>
            `}
        </div>
    `;

    detailsContainer.innerHTML = html;
    document.getElementById('campaignDetailsModal').style.display = 'flex';
}

function createCampaignDetailsModal() {
    const modal = document.createElement('div');
    modal.id = 'campaignDetailsModal';
    modal.className = 'modal';
    modal.style.display = 'none';

    modal.innerHTML = `
        <div class="modal-overlay" onclick="closeCampaignDetailsModal()"></div>
        <div class="modal-container" style="max-width: 1200px; max-height: 90vh; overflow-y: auto;">
            <div class="modal-header">
                <h2><i class="ti ti-badge-ad"></i> Campaign Details</h2>
                <button class="modal-close" onclick="closeCampaignDetailsModal()">
                    <i class="ti ti-x"></i>
                </button>
            </div>
            <div class="modal-body" id="campaignDetailsContent">
                <div style="text-align: center; padding: 2rem;">
                    <div class="loading-spinner"></div>
                    <p>Loading campaign details...</p>
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(modal);
}

function closeCampaignDetailsModal() {
    const modal = document.getElementById('campaignDetailsModal');
    if (modal) {
        modal.style.display = 'none';
    }
}
async function pauseCampaign(campaignId) {
    await controlCampaign(campaignId, 'pause');
}

async function resumeCampaign(campaignId) {
    await controlCampaign(campaignId, 'resume');
}

async function controlCampaign(campaignId, action) {
    if (!confirm(`Are you sure you want to ${action} this campaign?`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/campaigns/${campaignId}/control`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ action })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `Failed to ${action} campaign`);
        }
        
        const data = await response.json();
        showNotification(data.message, 'success');
        loadCampaigns();
        
    } catch (error) {
        console.error(`Error ${action}ing campaign:`, error);
        showNotification(error.message, 'error');
    }
}


let currentSelectedPlatform = ''; // Global variable to store platform
let currentSelectedObjective = ''; // Global variable to store objective

async function openCreateAdModal(campaignId) {
    const token = localStorage.getItem('token');
    
    try {
        // Fetch campaign details to get platform and objective
        const response = await fetch(`${API_BASE}/ads/campaigns/${campaignId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch campaign details');
        }
        
        const campaign = await response.json();
        
        // Store platform and objective globally
        currentSelectedPlatform = campaign.platform.toLowerCase();
        currentSelectedObjective = campaign.objective || 'AWARENESS';
        
        // Check if modal exists, if not create it
        let modal = document.getElementById('createAdModal');
        if (!modal) {
            createAdModal();
            modal = document.getElementById('createAdModal');
        }
        
        // Reset form and uploaded assets
        uploadedMediaAssets = [];
        document.getElementById('createAdForm').reset();
        document.getElementById('adCampaignId').value = campaignId;
        
        // Clear any previous uploads
        const uploadProgressContainer = document.getElementById('uploadProgressContainer');
        if (uploadProgressContainer) uploadProgressContainer.innerHTML = '';
        
        const uploadedGallery = document.getElementById('uploadedMediaGallery');
        if (uploadedGallery) uploadedGallery.innerHTML = '';
        
        // Display campaign info in modal header
        const modalHeader = modal.querySelector('.modal-header h2');
        if (modalHeader) {
            modalHeader.innerHTML = `
                <i class="ti ti-ad"></i> Create Ad for ${campaign.campaign_name}
                <span style="font-size: 0.875rem; font-weight: 400; color: #64748b; margin-left: 0.5rem;">
                    (${campaign.platform.toUpperCase()})
                </span>
            `;
        }
        
        // Render platform-specific fields
        await renderPlatformSpecificAdFields(currentSelectedPlatform, currentSelectedObjective);
        
        // Show modal
        modal.style.display = 'flex';
        
        // Focus on first input
        setTimeout(() => {
            const firstInput = modal.querySelector('input:not([type="hidden"]), textarea, select');
            if (firstInput) firstInput.focus();
        }, 100);
        
    } catch (error) {
        console.error('Error opening ad creation modal:', error);
        showNotification('Failed to open ad creation form: ' + error.message, 'error');
    }
}

function createAdModal() {
    const modal = document.createElement('div');
    modal.id = 'createAdModal';
    modal.className = 'modal';
    modal.style.display = 'none';

    modal.innerHTML = `
        <div class="modal-overlay" onclick="closeCreateAdModal()"></div>
        <div class="modal-container" style="max-width: 900px; max-height: 90vh; overflow-y: auto;">
            <div class="modal-header">
                <h2><i class="ti ti-ad"></i> Create New Ad</h2>
                <button class="modal-close" onclick="closeCreateAdModal()">
                    <i class="ti ti-x"></i>
                </button>
            </div>
            <div class="modal-body">
                <form id="createAdForm" onsubmit="event.preventDefault(); submitCreateAd();">
                    <input type="hidden" id="adCampaignId">
                    
                    <!-- Platform-specific fields will be injected here -->
                    <div id="platformSpecificFields"></div>
                    
                    <div style="display: flex; gap: 1rem; justify-content: flex-end; margin-top: 2rem; padding-top: 1.5rem; border-top: 1px solid #e2e8f0;">
                        <button type="button" class="btn btn-secondary" onclick="closeCreateAdModal()">
                            <i class="ti ti-x"></i> Cancel
                        </button>
                        <button type="submit" class="btn btn-primary" id="submitAdBtn">
                            <i class="ti ti-check"></i> Create Ad
                        </button>
                    </div>
                </form>
            </div>
        </div>
    `;

    document.body.appendChild(modal);
}

function closeCreateAdModal() {
    const modal = document.getElementById('createAdModal');
    if (modal) {
        modal.style.display = 'none';
    }
    
    // Reset uploaded assets
    uploadedMediaAssets = [];
    
    // Clear form
    const form = document.getElementById('createAdForm');
    if (form) form.reset();
    
    // Clear upload progress and gallery
    const uploadProgressContainer = document.getElementById('uploadProgressContainer');
    if (uploadProgressContainer) uploadProgressContainer.innerHTML = '';
    
    const uploadedGallery = document.getElementById('uploadedMediaGallery');
    if (uploadedGallery) uploadedGallery.innerHTML = '';
}

// Helper function to show notification
function showNotification(message, type = 'info') {
    // Check if notification container exists
    let container = document.getElementById('notificationContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notificationContainer';
        container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 10000; display: flex; flex-direction: column; gap: 10px;';
        document.body.appendChild(container);
    }
    
    // Create notification element
    const notification = document.createElement('div');
    notification.style.cssText = `
        padding: 1rem 1.5rem;
        border-radius: 8px;
        background: ${type === 'success' ? '#22c55e' : type === 'error' ? '#ef4444' : type === 'warning' ? '#f59e0b' : '#3b82f6'};
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        display: flex;
        align-items: center;
        gap: 0.75rem;
        animation: slideInRight 0.3s ease-out;
        max-width: 350px;
    `;
    
    const icon = type === 'success' ? 'ti-circle-check' : 
                 type === 'error' ? 'ti-alert-circle' : 
                 type === 'warning' ? 'ti-alert-triangle' : 'ti-info-circle';
    
    notification.innerHTML = `
        <i class="ti ${icon}" style="font-size: 1.25rem;"></i>
        <span style="flex: 1;">${message}</span>
        <button onclick="this.parentElement.remove()" style="background: none; border: none; color: white; cursor: pointer; padding: 0; font-size: 1.25rem;">
            <i class="ti ti-x"></i>
        </button>
    `;
    
    container.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

// Add CSS animations for notifications
if (!document.getElementById('notificationStyles')) {
    const style = document.createElement('style');
    style.id = 'notificationStyles';
    style.textContent = `
        @keyframes slideInRight {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @keyframes slideOutRight {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(400px);
                opacity: 0;
            }
        }
        
        @keyframes spin {
            from {
                transform: rotate(0deg);
            }
            to {
                transform: rotate(360deg);
            }
        }
    `;
    document.head.appendChild(style);
}



async function submitCreateAd() {
    const token = localStorage.getItem('token');
    const campaignId = document.getElementById('adCampaignId').value;
    const platform = currentSelectedPlatform; // Store when modal opens
    
    const submitBtn = document.getElementById('submitAdBtn');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="ti ti-loader"></i> Creating...';
    
    try {
        let adData = {
            campaign_id: parseInt(campaignId),
            ad_name: document.getElementById('adName').value,
            platform: platform,
            media_ids: uploadedMediaAssets.map(a => a.media_id)
        };
        
        // Collect media URLs if any
        const mediaUrls = [];
        document.querySelectorAll('#mediaUrlsContainer input[type="url"]').forEach(input => {
            if (input.value.trim()) mediaUrls.push(input.value.trim());
        });
        
        // Platform-specific data collection
        if (platform === 'meta') {
            adData = {
                ...adData,
                primary_text: document.getElementById('adPrimaryText').value,
                headline: document.getElementById('adHeadline').value,
                description: document.getElementById('adDescription')?.value || '',
                destination_url: document.getElementById('adDestinationUrl').value,
                call_to_action: document.getElementById('adCTA').value,
                platform_specific_data: {
                    ad_format: document.getElementById('metaAdFormat').value,
                    placements: Array.from(document.querySelectorAll('input[type="checkbox"]:checked')).map(cb => cb.value)
                }
            };
        } 
        else if (platform === 'google') {
            const headlines = Array.from(document.querySelectorAll('.google-headline'))
                .map(input => input.value.trim())
                .filter(v => v);
            
            const descriptions = Array.from(document.querySelectorAll('.google-description'))
                .map(textarea => textarea.value.trim())
                .filter(v => v);
            
            if (headlines.length < 3) {
                throw new Error('At least 3 headlines required for Google Ads');
            }
            if (descriptions.length < 2) {
                throw new Error('At least 2 descriptions required for Google Ads');
            }
            
            adData = {
                ...adData,
                primary_text: headlines[0],
                headline: headlines.join(' | '),
                description: descriptions.join(' | '),
                destination_url: document.getElementById('googleFinalUrl').value,
                call_to_action: '',
                platform_specific_data: {
                    campaign_type: document.getElementById('googleCampaignType').value,
                    headlines,
                    descriptions,
                    keywords: document.getElementById('googleKeywords')?.value.split(',').map(k => k.trim()).filter(k => k) || [],
                    path1: document.getElementById('googlePath1')?.value || '',
                    path2: document.getElementById('googlePath2')?.value || ''
                }
            };
        } 
        else if (platform === 'linkedin') {
            adData = {
                ...adData,
                primary_text: document.getElementById('linkedinIntroText').value,
                headline: document.getElementById('linkedinHeadline').value,
                description: '',
                destination_url: document.getElementById('linkedinDestinationUrl').value,
                call_to_action: document.getElementById('linkedinCTA').value,
                platform_specific_data: {
                    ad_format: document.getElementById('linkedinAdFormat').value,
                    targeting: {
                        job_titles: document.getElementById('linkedinJobTitles')?.value.split(',').map(t => t.trim()).filter(t => t) || [],
                        company_size: document.getElementById('linkedinCompanySize')?.value || '',
                        industries: document.getElementById('linkedinIndustries')?.value.split(',').map(i => i.trim()).filter(i => i) || []
                    }
                }
            };
        }
        
        // Add media URLs if no files uploaded
        if (uploadedMediaAssets.length === 0 && mediaUrls.length > 0) {
            adData.media_urls = mediaUrls;
        }
        
        // Create ad via API
        const response = await fetch(`${API_BASE}/ads/create-platform-specific`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(adData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create ad');
        }
        
        const data = await response.json();
        
        showNotification('✅ Ad created successfully!', 'success');
        closeCreateAdModal();
        
        // Refresh campaign details
        if (typeof loadCampaignAds === 'function') {
            loadCampaignAds(campaignId);
        }
        
        // Reset uploaded assets
        uploadedMediaAssets = [];
        
    } catch (error) {
        console.error('Create ad error:', error);
        showNotification(error.message, 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="ti ti-check"></i> Create Ad';
    }
}




// =====================================================
// AUDIENCE SEGMENTS
// =====================================================
async function loadAudienceSegments() {
    const clientId = document.getElementById('filterClientAudience').value;

    const container = document.getElementById('audienceSegmentsList');
    container.innerHTML = '<div style="text-align: center; padding: 2rem;"><div class="loading-spinner"></div><p>Loading segments...</p></div>';

    try {
        let url;

        // If "All Clients" is selected (empty value), use list-all endpoint
        if (!clientId || clientId === '') {
            url = `${API_BASE}/audience/list-all`;
        } else {
            // Specific client selected
            url = `${API_BASE}/audience/list/${clientId}`;
        }

        const response = await fetch(url, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) throw new Error('Failed to load segments');

        const data = await response.json();

        if (!data.segments || data.segments.length === 0) {
            container.innerHTML = '<div class="empty-state"><i class="ti ti-users"></i><h3>No audience segments yet</h3><p>Create a segment to target specific audiences</p></div>';
            return;
        }

        container.innerHTML = data.segments.map(segment => `
            <div class="campaign-card">
                <div class="campaign-header">
                    <div>
                        <div class="campaign-title">${segment.segment_name}</div>
                        <div class="campaign-meta">
                            <span><i class="ti ti-calendar"></i> ${new Date(segment.created_at).toLocaleDateString()}</span>
                            <span><i class="ti ti-building"></i> ${segment.client_name || 'Unknown Client'}</span>
                            <span><i class="ti ti-user"></i> ${segment.creator_name}</span>
                        </div>
                    </div>
                    <span class="platform-badge">${segment.platform}</span>
                </div>
                <div style="margin-top: 1rem;">
                    <div style="font-size: 0.875rem; color: #64748b; margin-bottom: 0.5rem;">Estimated Reach</div>
                    <div style="font-size: 1.25rem; font-weight: 600;">${Number(segment.estimated_size || 0).toLocaleString()} people</div>
                </div>
            </div>
        `).join('');

    } catch (error) {
        console.error('Error loading segments:', error);
        container.innerHTML = '<div class="empty-state"><i class="ti ti-alert-circle"></i><p>Failed to load segments</p></div>';
        showNotification('Failed to load audience segments', 'error');
    }
}



function openCreateAudienceModal() {
    // Load clients into modal dropdown
    loadClientsForModal('audienceClient');

    // Show modal
    document.getElementById('audienceModal').style.display = 'flex';
}

function closeAudienceModal() {
    document.getElementById('audienceModal').style.display = 'none';
    document.getElementById('audienceForm').reset();
}


async function submitAudience() {
    const btn = document.getElementById('submitAudienceBtn');
    btn.disabled = true;
    btn.innerHTML = '<i class="ti ti-loader"></i> Creating & Analyzing...';

    try {
        // Get device targeting
        const deviceCheckboxes = document.querySelectorAll('#audienceModal input[type="checkbox"]:checked');
        const devices = Array.from(deviceCheckboxes).map(cb => cb.value).filter(v => v);

        const formData = {
            client_id: parseInt(document.getElementById('audienceClient').value),
            platform: document.getElementById('audiencePlatform').value,
            segment_name: document.getElementById('audienceName').value,
            demographics: {
                age: document.getElementById('audienceAge').value || null,
                gender: document.getElementById('audienceGender').value,
                location: document.getElementById('audienceLocation').value || null
            },
            interests: document.getElementById('audienceInterests').value
                .split(',')
                .map(i => i.trim())
                .filter(i => i),
            behaviors: document.getElementById('audienceBehaviors').value
                .split(',')
                .map(b => b.trim())
                .filter(b => b),
            device_targeting: devices.length > 0 ? { devices: devices } : null,
            lookalike_source: document.getElementById('audienceLookalike').value || null
        };

        const response = await fetch(`${API_BASE}/audience/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create audience segment');
        }

        const data = await response.json();

        // SHOW AI INSIGHTS MODAL
        showAudienceInsightsModal(data);

        closeAudienceModal();

        // Reload audience segments
        document.getElementById('filterClientAudience').value = formData.client_id;
        loadAudienceSegments();

    } catch (error) {
        console.error('Error creating audience:', error);
        showNotification(error.message, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="ti ti-check"></i> Create Audience';
    }
}



function showAudienceInsightsModal(data) {
    const insights = data.ai_suggestions;
    const segment = data.segment_criteria;

    // Create modal HTML
    const modalHTML = `
        <div class="modal" id="insightsModal" style="display: flex;">
            <div class="modal-overlay" onclick="closeInsightsModal()"></div>
            <div class="modal-container" style="max-width: 1200px; max-height: 90vh; overflow-y: auto;">
                <div class="modal-header">
                    <h2><i class="ti ti-sparkles"></i> AI-Powered Audience Insights</h2>
                    <button class="modal-close" onclick="closeInsightsModal()">
                        <i class="ti ti-x"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="success-banner" style="background: linear-gradient(135deg, #10b981, #059669); color: white; padding: 1.5rem; border-radius: 12px; margin-bottom: 2rem;">
                        <div style="display: flex; align-items: center; gap: 1rem;">
                            <i class="ti ti-check-circle" style="font-size: 2.5rem;"></i>
                            <div>
                                <h3 style="margin: 0; font-size: 1.25rem;">Audience Created Successfully!</h3>
                                <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Segment ID: ${data.segment_id} | Estimated Reach: ${insights.estimated_reach?.toLocaleString() || 'N/A'} people</p>
                            </div>
                        </div>
                    </div>

                    <!-- Platform-Specific Recommendations -->
                    <div class="content-panel" style="margin-bottom: 1.5rem;">
                        <h3 style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;">
                            <i class="ti ti-target"></i> Platform-Specific Targeting
                        </h3>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem;">
                            ${insights.interest_recommendations ? `
                                <div style="background: #f8fafc; padding: 1rem; border-radius: 8px; border-left: 4px solid #9926F3;">
                                    <div style="font-weight: 600; margin-bottom: 0.5rem; color: #9926F3;">Interest Recommendations</div>
                                    <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                                        ${insights.interest_recommendations.slice(0, 8).map(interest =>
        `<span style="background: white; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.875rem; border: 1px solid #e2e8f0;">${interest}</span>`
    ).join('')}
                                    </div>
                                </div>
                            ` : ''}
                            
                            ${insights.behavior_suggestions ? `
                                <div style="background: #f8fafc; padding: 1rem; border-radius: 8px; border-left: 4px solid #1DD8FC;">
                                    <div style="font-weight: 600; margin-bottom: 0.5rem; color: #1DD8FC;">Behavior Targeting</div>
                                    <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                                        ${insights.behavior_suggestions.slice(0, 6).map(behavior =>
        `<span style="background: white; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.875rem; border: 1px solid #e2e8f0;">${behavior}</span>`
    ).join('')}
                                    </div>
                                </div>
                            ` : ''}
                            
                            ${insights.in_market_audiences ? `
                                <div style="background: #f8fafc; padding: 1rem; border-radius: 8px; border-left: 4px solid #10b981;">
                                    <div style="font-weight: 600; margin-bottom: 0.5rem; color: #10b981;">In-Market Audiences (Google)</div>
                                    <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                                        ${insights.in_market_audiences.slice(0, 6).map(audience =>
        `<span style="background: white; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.875rem; border: 1px solid #e2e8f0;">${audience}</span>`
    ).join('')}
                                    </div>
                                </div>
                            ` : ''}
                        </div>
                    </div>

                    <!-- Lookalike Audiences -->
                    ${insights.lookalike_suggestions && insights.lookalike_suggestions.length > 0 ? `
                        <div class="content-panel" style="margin-bottom: 1.5rem;">
                            <h3 style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;">
                                <i class="ti ti-users-group"></i> Lookalike Audience Expansion
                            </h3>
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem;">
                                ${insights.lookalike_suggestions.map(lookalike => `
                                    <div style="background: linear-gradient(135deg, rgba(153, 38, 243, 0.05), rgba(29, 216, 252, 0.05)); padding: 1.25rem; border-radius: 10px; border: 1px solid #e2e8f0;">
                                        <div style="font-weight: 600; font-size: 1.1rem; margin-bottom: 0.5rem;">${lookalike.type}</div>
                                        <div style="display: flex; justify-content: space-between; margin-top: 0.75rem;">
                                            <div>
                                                <div style="font-size: 0.75rem; color: #64748b; text-transform: uppercase;">Estimated Size</div>
                                                <div style="font-weight: 600; color: #1e293b;">${lookalike.size?.toLocaleString() || 'N/A'}</div>
                                            </div>
                                            <div>
                                                <div style="font-size: 0.75rem; color: #64748b; text-transform: uppercase;">Similarity</div>
                                                <div style="font-weight: 600; color: #10b981;">${lookalike.similarity || 0}%</div>
                                            </div>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}

                    <!-- Device & Time Recommendations -->
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-bottom: 1.5rem;">
                        ${insights.device_breakdown ? `
                            <div class="content-panel">
                                <h3 style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;">
                                    <i class="ti ti-device-desktop"></i> Device Distribution
                                </h3>
                                <div style="display: flex; flex-direction: column; gap: 0.75rem;">
                                    ${Object.entries(insights.device_breakdown).map(([device, percentage]) => `
                                        <div>
                                            <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                                                <span style="text-transform: capitalize; font-weight: 500;">${device}</span>
                                                <span style="font-weight: 600; color: #9926F3;">${percentage}%</span>
                                            </div>
                                            <div style="background: #e2e8f0; height: 8px; border-radius: 4px; overflow: hidden;">
                                                <div style="background: linear-gradient(90deg, #9926F3, #1DD8FC); height: 100%; width: ${percentage}%; transition: width 0.3s;"></div>
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}

                        ${insights.best_times && insights.best_times.length > 0 ? `
                            <div class="content-panel">
                                <h3 style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;">
                                    <i class="ti ti-clock"></i> Best Posting Times
                                </h3>
                                <div style="display: flex; flex-direction: column; gap: 0.5rem;">
                                    ${insights.best_times.slice(0, 4).map(time => `
                                        <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.75rem; background: #f8fafc; border-radius: 6px;">
                                            <div>
                                                <div style="font-weight: 600;">${time.day}</div>
                                                <div style="font-size: 0.875rem; color: #64748b;">${time.hour}</div>
                                            </div>
                                            <div style="background: linear-gradient(135deg, #10b981, #059669); color: white; padding: 0.25rem 0.75rem; border-radius: 20px; font-weight: 600; font-size: 0.875rem;">
                                                ${time.engagement_score}% Engagement
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}
                    </div>

                    <!-- Budget Recommendation -->
                    ${insights.budget_recommendation ? `
                        <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.1)); border: 2px solid #10b981; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem;">
                            <div style="display: flex; align-items: start; gap: 1rem;">
                                <i class="ti ti-currency-dollar" style="font-size: 2rem; color: #10b981;"></i>
                                <div>
                                    <h3 style="margin: 0 0 0.5rem 0; color: #059669;">Budget Recommendation</h3>
                                    <p style="margin: 0; line-height: 1.6; color: #064e3b;">${insights.budget_recommendation}</p>
                                </div>
                            </div>
                        </div>
                    ` : ''}

                    <!-- Action Button -->
                    <div style="text-align: center; padding-top: 1rem;">
                        <button class="btn btn-primary" onclick="closeInsightsModal()" style="padding: 0.75rem 2rem;">
                            <i class="ti ti-check"></i> Got It
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Add modal to page
    const existingModal = document.getElementById('insightsModal');
    if (existingModal) {
        existingModal.remove();
    }

    document.body.insertAdjacentHTML('beforeend', modalHTML);

    showNotification('Audience created with AI insights!', 'success');
}

function closeInsightsModal() {
    const modal = document.getElementById('insightsModal');
    if (modal) {
        modal.style.display = 'none';
        setTimeout(() => modal.remove(), 300);
    }
}


// ========== FEATURE 2: GENERATE AI AUDIENCE SUGGESTIONS ==========

async function generateAIAudienceInsights() {
    const clientId = document.getElementById('audienceClient').value;

    if (!clientId) {
        showNotification('Please select a client first', 'error');
        return;
    }

    const btn = event.target;
    btn.disabled = true;
    btn.innerHTML = '<i class="ti ti-loader"></i> Generating AI Insights...';

    try {
        const response = await fetch(`${API_BASE}/audience/generate-insights`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ client_id: parseInt(clientId) })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to generate insights');
        }

        const data = await response.json();

        // Display AI-generated insights modal
        displayGeneratedInsights(data.insights, data.client_name);

    } catch (error) {
        console.error('Error generating insights:', error);
        showNotification(error.message, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="ti ti-sparkles"></i> Generate AI Insights';
    }
}

function displayGeneratedInsights(insights, clientName) {
    const modalHTML = `
        <div class="modal" id="generatedInsightsModal" style="display: flex;">
            <div class="modal-overlay" onclick="closeGeneratedInsightsModal()"></div>
            <div class="modal-container" style="max-width: 1400px; max-height: 90vh; overflow-y: auto;">
                <div class="modal-header">
                    <h2><i class="ti ti-brain"></i> AI-Generated Audience Insights for ${clientName}</h2>
                    <button class="modal-close" onclick="closeGeneratedInsightsModal()">
                        <i class="ti ti-x"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <!-- Audience Segments -->
                    <h3 style="margin-bottom: 1rem;"><i class="ti ti-users"></i> Recommended Audience Segments</h3>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 1.5rem; margin-bottom: 2rem;">
                        ${insights.audience_segments.map((segment, index) => `
                            <div class="campaign-card" style="cursor: default;">
                                <div style="display: flex; justify-content: between; align-items: start; margin-bottom: 1rem;">
                                    <div>
                                        <div style="font-weight: 700; font-size: 1.1rem; margin-bottom: 0.25rem;">${segment.segment_name}</div>
                                        <span class="status-badge" style="background: ${segment.priority === 'High' ? '#10b981' : segment.priority === 'Medium' ? '#f59e0b' : '#6b7280'};">
                                            ${segment.priority} Priority
                                        </span>
                                    </div>
                                    <button class="btn btn-secondary" onclick='createSegmentFromAI(${JSON.stringify(segment)})' style="padding: 0.5rem 1rem; font-size: 0.875rem;">
                                        <i class="ti ti-plus"></i> Create
                                    </button>
                                </div>
                                
                                <div style="margin-bottom: 1rem;">
                                    <div style="font-size: 0.75rem; color: #64748b; text-transform: uppercase; margin-bottom: 0.25rem;">Demographics</div>
                                    <div style="font-size: 0.875rem;">
                                        ${segment.demographics.age_range} • ${segment.demographics.gender} • ${segment.demographics.location}
                                    </div>
                                </div>
                                
                                <div style="margin-bottom: 1rem;">
                                    <div style="font-size: 0.75rem; color: #64748b; text-transform: uppercase; margin-bottom: 0.5rem;">Key Interests</div>
                                    <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                                        ${segment.interests.slice(0, 6).map(interest =>
        `<span style="background: #f1f5f9; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.8rem;">${interest}</span>`
    ).join('')}
                                    </div>
                                </div>
                                
                                <div style="margin-bottom: 1rem;">
                                    <div style="font-size: 0.75rem; color: #64748b; text-transform: uppercase; margin-bottom: 0.5rem;">Pain Points</div>
                                    <ul style="margin: 0; padding-left: 1.25rem; font-size: 0.875rem; line-height: 1.6;">
                                        ${segment.pain_points.slice(0, 3).map(pain => `<li>${pain}</li>`).join('')}
                                    </ul>
                                </div>
                                
                                <div style="display: flex; justify-content: space-between; padding-top: 1rem; border-top: 1px solid #e2e8f0;">
                                    <div>
                                        <div style="font-size: 0.75rem; color: #64748b;">Est. Reach</div>
                                        <div style="font-weight: 600;">${segment.estimated_size.toLocaleString()}</div>
                                    </div>
                                    <div>
                                        <div style="font-size: 0.75rem; color: #64748b;">Platforms</div>
                                        <div style="display: flex; gap: 0.25rem;">
                                            ${segment.platform_recommendations.map(p =>
        `<span style="font-size: 0.75rem; padding: 0.25rem 0.5rem; background: #e2e8f0; border-radius: 4px;">${p.toUpperCase()}</span>`
    ).join('')}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>

                    <!-- Platform-Specific Targeting -->
                    <h3 style="margin-bottom: 1rem;"><i class="ti ti-target"></i> Platform-Specific Targeting Recommendations</h3>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; margin-bottom: 2rem;">
                        ${insights.platform_specific_targeting.meta ? `
                            <div class="content-panel">
                                <div style="font-weight: 700; margin-bottom: 1rem; color: #1877f2;">Meta (Facebook & Instagram)</div>
                                <div style="margin-bottom: 0.75rem;">
                                    <div style="font-size: 0.75rem; color: #64748b; margin-bottom: 0.5rem;">INTERESTS</div>
                                    <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                                        ${insights.platform_specific_targeting.meta.interests.slice(0, 5).map(int =>
        `<span style="background: #f1f5f9; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.8rem;">${int}</span>`
    ).join('')}
                                    </div>
                                </div>
                                <div>
                                    <div style="font-size: 0.75rem; color: #64748b; margin-bottom: 0.5rem;">LOOKALIKE POTENTIAL</div>
                                    <span class="status-badge" style="background: ${insights.platform_specific_targeting.meta.lookalike_potential === 'High' ? '#10b981' : '#f59e0b'};">
                                        ${insights.platform_specific_targeting.meta.lookalike_potential}
                                    </span>
                                </div>
                            </div>
                        ` : ''}
                        
                        ${insights.platform_specific_targeting.google ? `
                            <div class="content-panel">
                                <div style="font-weight: 700; margin-bottom: 1rem; color: #4285f4;">Google Ads</div>
                                <div style="margin-bottom: 0.75rem;">
                                    <div style="font-size: 0.75rem; color: #64748b; margin-bottom: 0.5rem;">IN-MARKET AUDIENCES</div>
                                    <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                                        ${insights.platform_specific_targeting.google.in_market.slice(0, 4).map(aud =>
        `<span style="background: #f1f5f9; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.8rem;">${aud}</span>`
    ).join('')}
                                    </div>
                                </div>
                                <div>
                                    <div style="font-size: 0.75rem; color: #64748b; margin-bottom: 0.5rem;">AFFINITY AUDIENCES</div>
                                    <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                                        ${insights.platform_specific_targeting.google.affinity.slice(0, 3).map(aff =>
        `<span style="background: #f1f5f9; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.8rem;">${aff}</span>`
    ).join('')}
                                    </div>
                                </div>
                            </div>
                        ` : ''}
                        
                        ${insights.platform_specific_targeting.linkedin ? `
                            <div class="content-panel">
                                <div style="font-weight: 700; margin-bottom: 1rem; color: #0077b5;">LinkedIn</div>
                                <div style="margin-bottom: 0.75rem;">
                                    <div style="font-size: 0.75rem; color: #64748b; margin-bottom: 0.5rem;">JOB TITLES</div>
                                    <div style="font-size: 0.875rem;">
                                        ${insights.platform_specific_targeting.linkedin.job_titles.slice(0, 3).join(', ')}
                                    </div>
                                </div>
                                <div>
                                    <div style="font-size: 0.75rem; color: #64748b; margin-bottom: 0.5rem;">COMPANY SIZES</div>
                                    <div style="display: flex; gap: 0.5rem;">
                                        ${insights.platform_specific_targeting.linkedin.company_sizes.map(size =>
        `<span style="background: #f1f5f9; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.8rem;">${size}</span>`
    ).join('')}
                                    </div>
                                </div>
                            </div>
                        ` : ''}
                    </div>

                    <!-- Budget & Messaging -->
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;">
                        <div class="content-panel">
                            <h3 style="margin-bottom: 1rem;"><i class="ti ti-currency-dollar"></i> Budget Allocation</h3>
                            ${Object.entries(insights.recommended_budget_allocation).map(([platform, percentage]) => `
                                <div style="margin-bottom: 0.75rem;">
                                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                                        <span style="text-transform: capitalize; font-weight: 500;">${platform}</span>
                                        <span style="font-weight: 600; color: #9926F3;">${percentage}%</span>
                                    </div>
                                    <div style="background: #e2e8f0; height: 8px; border-radius: 4px; overflow: hidden;">
                                        <div style="background: linear-gradient(90deg, #9926F3, #1DD8FC); height: 100%; width: ${percentage}%;"></div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                        
                        <div class="content-panel">
                            <h3 style="margin-bottom: 1rem;"><i class="ti ti-message"></i> Key Messaging Themes</h3>
                            <ul style="margin: 0; padding-left: 1.25rem; line-height: 1.8;">
                                ${insights.key_messaging_themes.map(theme => `<li>${theme}</li>`).join('')}
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    const existingModal = document.getElementById('generatedInsightsModal');
    if (existingModal) {
        existingModal.remove();
    }

    document.body.insertAdjacentHTML('beforeend', modalHTML);
}

function closeGeneratedInsightsModal() {
    const modal = document.getElementById('generatedInsightsModal');
    if (modal) {
        modal.style.display = 'none';
        setTimeout(() => modal.remove(), 300);
    }
}

function createSegmentFromAI(segment) {
    // Pre-fill the audience creation form with AI data
    document.getElementById('audienceName').value = segment.segment_name;
    document.getElementById('audienceInterests').value = segment.interests.join(', ');
    document.getElementById('audienceBehaviors').value = segment.behaviors.join(', ');
    document.getElementById('audienceAge').value = segment.demographics.age_range;
    document.getElementById('audienceLocation').value = segment.demographics.location;

    // Close insights modal and show create modal
    closeGeneratedInsightsModal();
    openCreateAudienceModal();

    showNotification('Form pre-filled with AI suggestions. Review and submit!', 'success');
}


// ========== FEATURE 3: CAMPAIGN MONITORING DASHBOARD ==========

async function loadCampaignMonitoring() {
    const container = document.getElementById('campaignMonitoringList');
    container.innerHTML = '<div style="text-align: center; padding: 3rem;"><div class="loading-spinner"></div><p>Loading active campaigns...</p></div>';

    try {
        const response = await fetch(`${API_BASE}/campaigns/monitor/active`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) throw new Error('Failed to load monitoring data');

        const data = await response.json();

        if (!data.active_campaigns || data.active_campaigns.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="ti ti-chart-line"></i>
                    <h3>No Active Campaigns</h3>
                    <p>Create and activate campaigns to monitor their performance here</p>
                </div>
            `;
            return;
        }

        container.innerHTML = data.active_campaigns.map(campaign => {
            const rec = campaign.ai_recommendations;
            const statusColors = {
                'Excellent': 'green',
                'Good': 'blue',
                'Needs Attention': 'orange',
                'Critical': 'red'
            };

            return `
                <div class="campaign-card" style="border-left: 4px solid ${statusColors[rec?.status] || 'gray'};">
                    <div class="campaign-header" style="margin-bottom: 1.5rem;">
                        <div>
                            <div class="campaign-title">${campaign.campaign_name}</div>
                            <div class="campaign-meta">
                                <span><i class="ti ti-building"></i> ${campaign.client_name}</span>
                                <span><i class="ti ti-calendar"></i> Started ${new Date(campaign.created_at).toLocaleDateString()}</span>
                            </div>
                        </div>
                        <div style="display: flex; gap: 0.5rem; align-items: start;">
                            <span class="status-badge" style="background: ${statusColors[rec?.status] || '#6b7280'};">
                                ${rec?.status || 'Analyzing'}
                            </span>
                            <span class="platform-badge">${campaign.platform}</span>
                        </div>
                    </div>

                    <!-- Performance Metrics -->
                    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1.5rem; padding: 1rem; background: #f8fafc; border-radius: 8px;">
                        <div>
                            <div style="font-size: 0.75rem; color: #64748b; text-transform: uppercase;">Impressions</div>
                            <div style="font-weight: 700; font-size: 1.25rem;">${Number(campaign.total_impressions).toLocaleString()}</div>
                        </div>
                        <div>
                            <div style="font-size: 0.75rem; color: #64748b; text-transform: uppercase;">CTR</div>
                            <div style="font-weight: 700; font-size: 1.25rem;">${Number(campaign.avg_ctr).toFixed(2)}%</div>
                        </div>
                        <div>
                            <div style="font-size: 0.75rem; color: #64748b; text-transform: uppercase;">CPC</div>
                            <div style="font-weight: 700; font-size: 1.25rem;">$${Number(campaign.avg_cpc).toFixed(2)}</div>
                        </div>
                        <div>
                            <div style="font-size: 0.75rem; color: #64748b; text-transform: uppercase;">Conversions</div>
                            <div style="font-weight: 700; font-size: 1.25rem;">${Number(campaign.total_conversions)}</div>
                        </div>
                    </div>

                    <!-- AI Recommendations -->
                    ${rec && rec.priority_actions && rec.priority_actions.length > 0 ? `
                        <div style="margin-bottom: 1.5rem;">
                            <div style="font-weight: 600; margin-bottom: 0.75rem; display: flex; align-items: center; gap: 0.5rem;">
                                <i class="ti ti-alert-circle"></i> Priority Actions
                            </div>
                            ${rec.priority_actions.slice(0, 3).map(action => `
                                <div style="background: ${action.priority === 'High' ? 'rgba(239, 68, 68, 0.1)' : action.priority === 'Medium' ? 'rgba(245, 158, 11, 0.1)' : 'rgba(59, 130, 246, 0.1)'}; 
                                           border-left: 3px solid ${action.priority === 'High' ? '#ef4444' : action.priority === 'Medium' ? '#f59e0b' : '#3b82f6'}; 
                                           padding: 1rem; margin-bottom: 0.75rem; border-radius: 6px;">
                                    <div style="font-weight: 600; margin-bottom: 0.25rem; display: flex; justify-content: space-between; align-items: center;">
                                        <span>${action.action}</span>
                                        <span style="font-size: 0.75rem; padding: 0.25rem 0.5rem; background: white; border-radius: 12px;">${action.priority}</span>
                                    </div>
                                    <div style="font-size: 0.875rem; color: #475569; margin-bottom: 0.5rem;">${action.reason}</div>
                                    <div style="font-size: 0.875rem; color: #10b981;"><strong>Impact:</strong> ${action.impact}</div>
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}

                    <!-- Quick Wins -->
                    ${rec && rec.quick_wins && rec.quick_wins.length > 0 ? `
                        <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.05), rgba(5, 150, 105, 0.05)); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                            <div style="font-weight: 600; margin-bottom: 0.75rem; color: #059669;"><i class="ti ti-bolt"></i> Quick Wins</div>
                            <ul style="margin: 0; padding-left: 1.25rem; line-height: 1.8; color: #064e3b;">
                                ${rec.quick_wins.map(win => `<li>${win}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}

                    <!-- Budget & Performance -->
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                        ${rec?.budget_recommendation ? `
                            <div style="padding: 0.75rem; background: #fef3c7; border-radius: 6px;">
                                <div style="font-size: 0.75rem; color: #92400e; font-weight: 600;">BUDGET</div>
                                <div style="font-weight: 600; color: #78350f;">${rec.budget_recommendation}</div>
                            </div>
                        ` : ''}
                        ${rec?.estimated_improvement ? `
                            <div style="padding: 0.75rem; background: #d1fae5; border-radius: 6px;">
                                <div style="font-size: 0.75rem; color: #065f46; font-weight: 600;">EST. IMPROVEMENT</div>
                                <div style="font-weight: 600; color: #047857;">${rec.estimated_improvement}</div>
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;
        }).join('');

    } catch (error) {
        console.error('Error loading monitoring:', error);
        container.innerHTML = '<div class="empty-state"><i class="ti ti-alert-circle"></i><p>Failed to load monitoring data</p></div>';
        showNotification('Failed to load campaign monitoring', 'error');
    }
}


async function loadClientsForModal(selectId) {
    try {
        const response = await fetch('/api/v1/clients/list', {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) throw new Error('Failed to fetch clients');

        const data = await response.json();
        const select = document.getElementById(selectId);

        select.innerHTML = '<option value="">Select client...</option>';
        if (data.clients && data.clients.length > 0) {
            data.clients.forEach(client => {
                select.innerHTML += `<option value="${client.user_id}">${client.full_name}</option>`;
            });
        }

    } catch (error) {
        console.error('Error loading clients:', error);
    }
}

// =====================================================
// AI PLATFORM RECOMMENDATIONS
// =====================================================

async function getPlatformRecommendations() {
    const btn = document.getElementById('recommendBtn');
    const objective = document.getElementById('recObjective').value;
    const budget = parseFloat(document.getElementById('recBudget').value);
    const industry = document.getElementById('recIndustry').value;

    if (!objective || !budget) {
        showNotification('Please fill in all required fields', 'error');
        return;
    }

    btn.disabled = true;
    btn.innerHTML = '<i class="ti ti-wand"></i> Analyzing...<span class="loading-spinner"></span>';

    try {
        const response = await fetch(`${API_BASE}/platform/recommend`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                client_id: 1,
                campaign_objective: objective,
                budget: budget,
                target_audience: {},
                industry: industry || null
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to get recommendations');
        }

        const data = await response.json();
        displayPlatformRecommendations(data.recommendations);

    } catch (error) {
        console.error('Error getting recommendations:', error);
        showNotification(error.message, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="ti ti-wand"></i> Get Recommendations';
    }
}

function displayPlatformRecommendations(recommendations) {
    const container = document.getElementById('platformRecommendations');

    if (!recommendations || !recommendations.recommendations) {
        container.innerHTML = '<p>No recommendations available</p>';
        return;
    }

    container.innerHTML = recommendations.recommendations.map((rec, index) => {
        // Properly handle formats array
        const formatsHtml = rec.formats && Array.isArray(rec.formats)
            ? rec.formats.map(fmt => `
                <div style="margin-bottom: 0.75rem; padding: 0.75rem; background: white; border-radius: 6px;">
                    <strong>${fmt.format_name}</strong> (${fmt.budget_allocation}% of platform budget)<br>
                    <small style="color: #64748b;">${fmt.reason}</small><br>
                    <small style="color: #64748b;">Specs: ${fmt.creative_specs}</small>
                </div>
            `).join('')
            : '<p>No format details available</p>';

        return `
            <div class="recommendation-card">
                <h4>${index + 1}. ${rec.platform} - ${rec.budget_percent}% of budget</h4>
                <p style="margin-bottom: 1rem; color: #475569;">${rec.reasoning}</p>
                
                <h5 style="margin-top: 1rem; margin-bottom: 0.5rem;">Recommended Formats:</h5>
                ${formatsHtml}
                
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin-top: 1rem;">
                    <div>
                        <div style="font-size: 0.875rem; color: #64748b;">Expected CTR</div>
                        <div style="font-weight: 500;">${rec.expected_ctr}%</div>
                    </div>
                    <div>
                        <div style="font-size: 0.875rem; color: #64748b;">Expected CPC</div>
                        <div style="font-weight: 500;">₹${rec.expected_cpc}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.875rem; color: #64748b;">Placement</div>
                        <div style="font-weight: 500;">${rec.recommended_placement || 'Automatic'}</div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// =====================================================
// AI AD COPY GENERATOR
// =====================================================

async function generateAdCopy() {
    const btn = document.getElementById('generateCopyBtn');
    const product = document.getElementById('copyProduct').value;
    const audience = document.getElementById('copyAudience').value;
    const platform = document.getElementById('copyPlatform').value;
    const benefits = document.getElementById('copyBenefits').value.split(',').map(b => b.trim()).filter(b => b);

    if (!product || !audience) {
        showNotification('Please fill in all required fields', 'error');
        return;
    }

    btn.disabled = true;
    btn.innerHTML = '<i class="ti ti-sparkles"></i> Generating...<span class="loading-spinner"></span>';

    try {
        const response = await fetch(`${API_BASE}/adcopy/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                campaign_objective: 'conversions',
                product_service: product,
                target_audience: audience,
                platform: platform,
                key_benefits: benefits,
                tone: 'professional',
                cta_type: 'Learn More'
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to generate ad copy');
        }

        const data = await response.json();
        displayAdCopyResults(data.ad_copy);

    } catch (error) {
        console.error('Error generating ad copy:', error);
        showNotification(error.message, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="ti ti-sparkles"></i> Generate Ad Copy';
    }
}

function displayAdCopyResults(adCopy) {
    const container = document.getElementById('adCopyResults');

    if (!adCopy || !adCopy.variations) {
        container.innerHTML = '<p>No ad copy generated</p>';
        return;
    }

    container.innerHTML = `
        <h3 style="margin-bottom: 1rem;">Generated Ad Copy Variations</h3>
        ${adCopy.variations.map((variation, index) => `
            <div class="ad-copy-variation" onclick="selectAdCopy(${index}, this)">
                <h4 style="margin-bottom: 1rem; color: #9926F3;">Variation ${index + 1}</h4>
                <div style="margin-bottom: 0.75rem;">
                    <strong>Headline:</strong><br>
                    ${variation.headline}
                </div>
                <div style="margin-bottom: 0.75rem;">
                    <strong>Primary Text:</strong><br>
                    ${variation.primary_text}
                </div>
                ${variation.description ? `
                    <div style="margin-bottom: 0.75rem;">
                        <strong>Description:</strong><br>
                        ${variation.description}
                    </div>
                ` : ''}
                ${variation.hashtags && variation.hashtags.length > 0 ? `
                    <div>
                        <strong>Hashtags:</strong><br>
                        ${variation.hashtags.map(tag => `#${tag}`).join(' ')}
                    </div>
                ` : ''}
            </div>
        `).join('')}
    `;
}

function selectAdCopy(index, element) {
    document.querySelectorAll('.ad-copy-variation').forEach(v => v.classList.remove('selected'));
    element.classList.add('selected');
    selectedAdCopy = index;
    showNotification(`Variation ${index + 1} selected!`, 'success');
}

// =====================================================
// PERFORMANCE FORECASTER
// =====================================================

async function forecastPerformance() {
    const btn = document.getElementById('forecastBtn');
    const platform = document.getElementById('forecastPlatform').value;
    const budget = parseFloat(document.getElementById('forecastBudget').value);
    const duration = parseInt(document.getElementById('forecastDuration').value);
    const audience = parseInt(document.getElementById('forecastAudience').value);

    if (!budget || !duration || !audience) {
        showNotification('Please fill in all required fields', 'error');
        return;
    }

    btn.disabled = true;
    btn.innerHTML = '<i class="ti ti-calculator"></i> Calculating...<span class="loading-spinner"></span>';

    try {
        const response = await fetch(`${API_BASE}/forecast`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                platform: platform,
                objective: 'conversions',
                budget: budget,
                duration_days: duration,
                target_audience_size: audience,
                include_breakeven: true,
                average_order_value: 75,
                run_simulations: true
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to generate forecast');
        }

        const data = await response.json();
        displayForecastResults(data.forecast);

    } catch (error) {
        console.error('Error generating forecast:', error);
        showNotification(error.message, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="ti ti-calculator"></i> Calculate Forecast';
    }
}

function displayForecastResults(forecast) {
    const container = document.getElementById('forecastResults');

    if (!forecast || !forecast.total_metrics) {
        container.innerHTML = '<p>No forecast available</p>';
        return;
    }

    const metrics = forecast.total_metrics;

    let breakEvenHtml = '';
    if (forecast.breakeven_analysis) {
        const ba = forecast.breakeven_analysis;
        breakEvenHtml = `
            <div style="margin-top: 1.5rem; padding: 1rem; background: #f8fafc; border-radius: 8px;">
                <h4 style="margin-bottom: 0.75rem;">Break-Even Analysis</h4>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                    <div>
                        <div style="font-size: 0.875rem; color: #64748b;">Break-Even Conversions</div>
                        <div style="font-size: 1.25rem; font-weight: 600;">${ba.breakeven_conversions}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.875rem; color: #64748b;">Projected Conversions</div>
                        <div style="font-size: 1.25rem; font-weight: 600;">${ba.projected_conversions}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.875rem; color: #64748b;">Status</div>
                        <div style="font-size: 1.25rem; font-weight: 600; color: ${ba.profitability_status === 'Profitable' ? '#10b981' : '#ef4444'};">
                            ${ba.profitability_status}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    container.innerHTML = `
        <h3 style="margin-bottom: 1rem;">Performance Forecast</h3>
        <div class="forecast-grid">
            <div class="forecast-metric">
                <div class="forecast-metric-label">Total Impressions</div>
                <div class="forecast-metric-value">${Number(metrics.impressions).toLocaleString()}</div>
            </div>
            <div class="forecast-metric">
                <div class="forecast-metric-label">Total Clicks</div>
                <div class="forecast-metric-value">${Number(metrics.clicks).toLocaleString()}</div>
            </div>
            <div class="forecast-metric">
                <div class="forecast-metric-label">Est. Conversions</div>
                <div class="forecast-metric-value">${metrics.conversions}</div>
            </div>
            <div class="forecast-metric">
                <div class="forecast-metric-label">Engagements</div>
                <div class="forecast-metric-value">${Number(metrics.engagements).toLocaleString()}</div>
            </div>
            <div class="forecast-metric">
                <div class="forecast-metric-label">CTR</div>
                <div class="forecast-metric-value">${metrics.ctr}%</div>
            </div>
            <div class="forecast-metric">
                <div class="forecast-metric-label">CPC</div>
                <div class="forecast-metric-value">₹${metrics.cpc}</div>
            </div>
            <div class="forecast-metric">
                <div class="forecast-metric-label">Est. ROAS</div>
                <div class="forecast-metric-value">${metrics.roas}x</div>
            </div>
            <div class="forecast-metric">
                <div class="forecast-metric-label">Engagement Rate</div>
                <div class="forecast-metric-value">${metrics.engagement_rate}%</div>
            </div>
        </div>
        
        ${breakEvenHtml}
        
        ${forecast.optimization_tips && forecast.optimization_tips.length > 0 ? `
            <div style="margin-top: 1.5rem; padding: 1rem; background: #f8fafc; border-radius: 8px;">
                <h4 style="margin-bottom: 0.75rem;">Optimization Tips</h4>
                <ul style="margin: 0; padding-left: 1.5rem;">
                    ${forecast.optimization_tips.map(tip => `<li style="margin-bottom: 0.5rem;">${tip}</li>`).join('')}
                </ul>
            </div>
        ` : ''}
        
        <p style="margin-top: 1rem; font-size: 0.875rem; color: #64748b;">
            ${forecast.confidence_level}
        </p>
    `;
}