/**
 * Social Media Command Center - Module 6
 * File: static/js/social-media.js
 * 
 * FULLY CORRECTED VERSION
 */

const API_BASE = '/api/v1/social-media';
let currentMonth = new Date().getMonth();
let currentYear = new Date().getFullYear();
let selectedContentId = null;
let selectedMediaUrls = [];
let selectedPlatforms = [];
let currentEditingPostId = null;

// =====================================================
// INITIALIZATION
// =====================================================

document.addEventListener('DOMContentLoaded', function () {
    loadClients();
    loadPosts();
    loadCalendar();
    loadTrendingTopics();
    loadPerformanceSummaries();
    initializePlatformSelector();
    loadStats();
    loadConnectedAccounts(); 

    const filterClient = document.getElementById('filterClient');
    if (filterClient) {
        filterClient.addEventListener('change', function () {
            loadStats();
            loadCalendar();
            loadPosts();
            loadConnectedAccounts();
        });
    }

    const captionInput = document.getElementById('postCaption');
    const charCount = document.getElementById('captionCharCount');

    if (captionInput && charCount) {
        captionInput.addEventListener('input', function () {
            charCount.textContent = this.value.length;
        });
    }
    loadConnectedAccounts();
});

// =====================================================
// PLATFORM SELECTOR - MULTI-SELECT SUPPORT
// =====================================================

function initializePlatformSelector() {
    const platforms = document.querySelectorAll('.platform-option');
    platforms.forEach(platform => {
        platform.addEventListener('click', function (e) {
            e.preventDefault();
            const platformName = this.dataset.platform;

            if (this.classList.contains('selected')) {
                this.classList.remove('selected');
                selectedPlatforms = selectedPlatforms.filter(p => p !== platformName);
            } else {
                this.classList.add('selected');
                selectedPlatforms.push(platformName);
            }

            document.getElementById('postPlatform').value = selectedPlatforms.join(',');
            updatePlatformCount();
        });
    });
}

function updatePlatformCount() {
    const countEl = document.getElementById('selectedPlatformCount');
    if (countEl) {
        if (selectedPlatforms.length > 0) {
            countEl.textContent = `${selectedPlatforms.length} platform${selectedPlatforms.length > 1 ? 's' : ''} selected`;
            countEl.style.display = 'block';
        } else {
            countEl.style.display = 'none';
        }
    }
}

// =====================================================
// LOAD CLIENTS
// =====================================================
async function loadClients() {
    const clientSelects = ['postClient', 'modalClientSelect', 'filterClient', 'connectClientId'];

    try {
        const token = localStorage.getItem('access_token');

        // CORRECT ENDPOINT - /clients/list
        const response = await fetch('/api/v1/clients/list', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            console.error('Failed to load clients:', response.status);
            return;
        }

        const data = await response.json();
        const clients = data.clients || [];

        clientSelects.forEach(selectId => {
            const select = document.getElementById(selectId);
            if (select) {
                select.innerHTML = '<option value="">Select Client</option>';
                clients.forEach(client => {
                    const option = document.createElement('option');
                    option.value = client.user_id || client.client_id;
                    option.textContent = client.full_name || client.business_name || client.email;
                    select.appendChild(option);
                });
            }
        });
    } catch (error) {
        console.error('Error loading clients:', error);
    }
}
// =====================================================
// LOAD STATS
// =====================================================

async function loadStats() {
    try {
        const token = localStorage.getItem('access_token');
        if (!token) return;

        const clientId = document.getElementById('filterClient')?.value || '';

        let url = `${API_BASE}/stats`;
        if (clientId) url += `?client_id=${clientId}`;

        let response = await fetch(url, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            const data = await response.json();
            const stats = data.stats || {};
            updateStatsDisplay(stats.total || 0, stats.scheduled || 0, stats.published || 0, stats.draft || 0);
            return;
        }

        url = `${API_BASE}/posts`;
        if (clientId) url += `?client_id=${clientId}`;

        response = await fetch(url, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) {
            updateStatsDisplay(0, 0, 0, 0);
            return;
        }

        const data = await response.json();
        const posts = data.posts || [];

        const total = posts.length;
        const scheduled = posts.filter(p => p.status === 'scheduled').length;
        const published = posts.filter(p => p.status === 'published').length;
        const draft = posts.filter(p => p.status === 'draft').length;

        updateStatsDisplay(total, scheduled, published, draft);

    } catch (error) {
        console.error('Error in loadStats:', error);
        updateStatsDisplay(0, 0, 0, 0);
    }
}

function updateStatsDisplay(total, scheduled, published, draft) {
    const totalEl = document.getElementById('totalPosts');
    const scheduledEl = document.getElementById('scheduledPosts');
    const publishedEl = document.getElementById('publishedPosts');
    const draftEl = document.getElementById('draftPosts');

    if (totalEl) totalEl.textContent = total;
    if (scheduledEl) scheduledEl.textContent = scheduled;
    if (publishedEl) publishedEl.textContent = published;
    if (draftEl) draftEl.textContent = draft;
}

function updateStats(posts) {
    if (!posts || !Array.isArray(posts)) posts = [];

    const total = posts.length;
    const scheduled = posts.filter(p => p.status === 'scheduled').length;
    const published = posts.filter(p => p.status === 'published').length;
    const draft = posts.filter(p => p.status === 'draft').length;

    updateStatsDisplay(total, scheduled, published, draft);
}



// =====================================================
// LOAD POSTS (LIST VIEW)
// =====================================================
// =====================================================
// LOAD POSTS (LIST VIEW) - WITH CONFLICT DETECTION
// =====================================================

async function loadPosts() {
    const postsList = document.getElementById('postsList');

    try {
        if (postsList) {
            postsList.innerHTML = `
                <div class="loading-state">
                    <div class="loader-spinner"></div>
                    <p>Loading posts...</p>
                </div>
            `;
        }

        const token = localStorage.getItem('access_token');
        const clientId = document.getElementById('filterClient')?.value || '';
        const platform = document.getElementById('filterPlatform')?.value || '';
        const status = document.getElementById('filterStatus')?.value || '';

        let url = `${API_BASE}/posts?`;
        if (clientId) url += `client_id=${clientId}&`;
        if (platform) url += `platform=${platform}&`;
        if (status) url += `status=${status}&`;

        const response = await fetch(url, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) throw new Error('Failed to load posts');

        const data = await response.json();
        const posts = data.posts || [];

        updateStats(posts);

        if (!posts || posts.length === 0) {
            if (postsList) {
                postsList.innerHTML = `
                    <div class="empty-state" style="padding: 3rem; text-align: center;">
                        <i class="ti ti-calendar-off" style="font-size: 3rem; color: #94a3b8;"></i>
                        <h3 style="margin-top: 1rem; color: #475569;">No Posts Found</h3>
                        <p style="color: #94a3b8;">Create your first social media post to get started</p>
                        <button class="btn btn-primary" onclick="openPostModal()" style="margin-top: 1rem;">
                            <i class="ti ti-plus"></i> Create Post
                        </button>
                    </div>
                `;
            }
            return;
        }

        // ✅ DETECT CONFLICTS BETWEEN POSTS
        const conflicts = detectPostConflicts(posts);

        // Platform colors
        const platformColors = {
            'instagram': '#E1306C',
            'facebook': '#1877F2',
            'linkedin': '#0A66C2',
            'twitter': '#1DA1F2',
            'pinterest': '#E60023'
        };

        // Status colors
        const statusColors = {
            'draft': '#f59e0b',
            'scheduled': '#3b82f6',
            'published': '#10b981'
        };

        let html = '';
        posts.forEach(post => {
            const platformClass = `platform-${post.platform}`;
            const statusClass = `status-${post.status}`;
            const scheduledDate = post.scheduled_at
                ? new Date(post.scheduled_at).toLocaleString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                })
                : 'Not scheduled';
            const publishedDate = post.published_at
                ? new Date(post.published_at).toLocaleString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                })
                : null;
            const hashtags = post.hashtags || [];
            const mediaCount = post.media_count || 0;
            const platformColor = platformColors[post.platform] || '#9926F3';
            const statusColor = statusColors[post.status] || '#64748b';

            // Determine which date to show
            let dateDisplay = '';
            if (post.status === 'published' && publishedDate) {
                dateDisplay = `<span style="color: #10b981;"><i class="ti ti-check"></i> Published ${publishedDate}</span>`;
            } else if (post.scheduled_at) {
                dateDisplay = `<span><i class="ti ti-calendar"></i> ${scheduledDate}</span>`;
            } else {
                dateDisplay = `<span style="color: #94a3b8;"><i class="ti ti-clock"></i> Draft</span>`;
            }

            // Publish button for draft/scheduled posts
            const publishButton = (post.status === 'draft' || post.status === 'scheduled')
                ? `<button onclick="publishPost(${post.post_id})" title="Publish Now"
                    style="background: linear-gradient(135deg, #10b981, #059669); color: white; 
                    border: none; padding: 0.5rem 0.75rem; border-radius: 8px; cursor: pointer;
                    transition: all 0.3s ease; display: flex; align-items: center; gap: 0.25rem;">
                    <i class="ti ti-send"></i>
                </button>`
                : '';

            // ✅ CHECK IF THIS POST HAS CONFLICTS
            const postConflicts = conflicts[post.post_id] || [];
            const hasConflicts = postConflicts.length > 0;

            html += `
                <div class="post-card" style="display: flex; gap: 1.5rem; padding: 1.5rem; 
                    background: white; border-radius: 16px; border: 2px solid ${hasConflicts ? '#f59e0b' : '#e2e8f0'}; 
                    margin-bottom: 1rem; transition: all 0.3s ease;
                    ${hasConflicts ? 'box-shadow: 0 4px 12px rgba(245, 158, 11, 0.2);' : ''}">
                    
                    <!-- Platform Icon -->
                    <div style="width: 56px; height: 56px; border-radius: 12px; 
                        background: ${platformColor}; display: flex; align-items: center; 
                        justify-content: center; flex-shrink: 0;">
                        <i class="ti ti-brand-${post.platform}" style="font-size: 1.75rem; color: white;"></i>
                    </div>
                    
                    <!-- Post Content -->
                    <div style="flex: 1; min-width: 0;">
                        <!-- Header -->
                        <div style="display: flex; justify-content: space-between; align-items: start; 
                            margin-bottom: 0.75rem;">
                            <div>
                                <div style="font-weight: 600; color: #1e293b; font-size: 15px; 
                                    margin-bottom: 0.25rem;">
                                    ${post.client_name || 'Unknown Client'}
                                </div>
                                <span style="display: inline-block; padding: 0.25rem 0.625rem; 
                                    border-radius: 6px; font-size: 12px; font-weight: 600; 
                                    background: ${statusColor}20; color: ${statusColor};">
                                    ${post.status.toUpperCase()}
                                </span>
                            </div>
                        </div>
                        
                        <!-- Caption -->
                        <div style="color: #475569; font-size: 14px; line-height: 1.6; 
                            margin-bottom: 0.75rem;">
                            ${truncateText(post.caption, 150) || 'No caption...'}
                        </div>
                        
                        <!-- ✅ CONFLICT WARNING -->
                        ${hasConflicts ? `
                            <div class="conflict-warning" style="display: inline-flex; align-items: center; gap: 0.375rem; 
                                padding: 0.375rem 0.75rem; background: #fef3c7; border: 1px solid #f59e0b; 
                                border-radius: 6px; font-size: 12px; font-weight: 600; color: #92400e; 
                                margin-top: 0.5rem;">
                                <i class="ti ti-alert-triangle" style="color: #f59e0b;"></i>
                                <span>Scheduling Conflict: ${postConflicts.length} post(s) within 2 hours</span>
                            </div>
                            <div style="font-size: 11px; color: #78350f; margin-top: 0.25rem;">
                                ${postConflicts.map(c => 
                                    `• "${truncateText(c.caption, 40)}" scheduled ${c.time_difference}`
                                ).join('<br>')}
                            </div>
                        ` : ''}
                        
                        <!-- Meta Info -->
                        <div style="display: flex; gap: 1rem; flex-wrap: wrap; 
                            font-size: 0.85rem; color: #64748b; margin-top: 0.75rem;">
                            ${dateDisplay}
                            <span><i class="ti ti-photo"></i> ${mediaCount} media</span>
                            <span><i class="ti ti-hash"></i> ${hashtags.length} hashtags</span>
                        </div>
                    </div>
                    
                    <!-- Post Actions -->
                    <div style="display: flex; gap: 0.5rem; flex-shrink: 0; align-items: start;">
                        ${publishButton}
                        <button onclick="editPost(${post.post_id})" title="Edit"
                            style="background: #f1f5f9; color: #475569; border: none; 
                            padding: 0.5rem 0.75rem; border-radius: 8px; cursor: pointer;
                            transition: all 0.3s ease;">
                            <i class="ti ti-pencil"></i>
                        </button>
                        <button onclick="deletePost(${post.post_id})" title="Delete"
                            style="background: #fef2f2; color: #ef4444; border: none; 
                            padding: 0.5rem 0.75rem; border-radius: 8px; cursor: pointer;
                            transition: all 0.3s ease;">
                            <i class="ti ti-trash"></i>
                        </button>
                    </div>
                </div>
            `;
        });

        if (postsList) postsList.innerHTML = html;

    } catch (error) {
        console.error('Error loading posts:', error);
        if (postsList) {
            postsList.innerHTML = `
                <div class="empty-state" style="padding: 3rem; text-align: center;">
                    <i class="ti ti-alert-circle" style="font-size: 3rem; color: #ef4444;"></i>
                    <h3 style="margin-top: 1rem; color: #475569;">Failed to Load Posts</h3>
                    <p style="color: #94a3b8;">${error.message}</p>
                    <button class="btn btn-primary" onclick="loadPosts()" style="margin-top: 1rem;">
                        <i class="ti ti-refresh"></i> Retry
                    </button>
                </div>
            `;
        }
        updateStats([]);
    }
}



// ✅ NEW: DETECT CONFLICTS BETWEEN POSTS
function detectPostConflicts(posts) {
    const conflicts = {};
    
    // Only check scheduled posts
    const scheduledPosts = posts.filter(p => 
        p.status === 'scheduled' && p.scheduled_at
    );
    
    scheduledPosts.forEach(post => {
        const postTime = new Date(post.scheduled_at);
        const twoHoursBefore = new Date(postTime.getTime() - (2 * 60 * 60 * 1000));
        const twoHoursAfter = new Date(postTime.getTime() + (2 * 60 * 60 * 1000));
        
        const conflictingPosts = scheduledPosts.filter(other => {
            if (other.post_id === post.post_id) return false;
            if (other.platform !== post.platform) return false;
            if (other.client_id !== post.client_id) return false;
            
            const otherTime = new Date(other.scheduled_at);
            return otherTime > twoHoursBefore && otherTime < twoHoursAfter;
        });
        
        if (conflictingPosts.length > 0) {
            conflicts[post.post_id] = conflictingPosts.map(c => {
                const diff = Math.abs(new Date(c.scheduled_at) - postTime);
                const hours = Math.floor(diff / (1000 * 60 * 60));
                const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
                
                return {
                    post_id: c.post_id,
                    caption: c.caption,
                    scheduled_at: c.scheduled_at,
                    time_difference: hours > 0 ? `${hours}h ${minutes}m away` : `${minutes}m away`
                };
            });
        }
    });
    
    return conflicts;
}
// Helper function for text truncation
function truncateText(text, maxLength) {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
}


function truncateText(text, maxLength) {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
}


// =====================================================
// ACCOUNT CONNECTION MANAGEMENT
// =====================================================

function openAccountConnectionModal() {
    document.getElementById('accountConnectionModal').style.display = 'flex';
    document.getElementById('platformSelectionStep').style.display = 'block';
    document.getElementById('platformInstructionsStep').style.display = 'none';

    // Load clients into the form
    loadClientsForConnection();
}

function closeAccountConnectionModal() {
    document.getElementById('accountConnectionModal').style.display = 'none';
    document.getElementById('accountConnectForm').reset();
}

function backToPlatformSelection() {
    document.getElementById('platformSelectionStep').style.display = 'block';
    document.getElementById('platformInstructionsStep').style.display = 'none';
    document.getElementById('accountConnectForm').reset();
}

async function loadClientsForConnection() {
    try {
        const response = await fetch('/api/v1/clients/list', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            const select = document.getElementById('connectClientId');
            select.innerHTML = '<option value="">Select Client</option>';

            data.clients.forEach(client => {
                const option = document.createElement('option');
                option.value = client.user_id;
                option.textContent = client.full_name || client.email;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading clients:', error);
    }
}

function showPlatformInstructions(platform) {
    document.getElementById('platformSelectionStep').style.display = 'none';
    document.getElementById('platformInstructionsStep').style.display = 'block';

    const platformInfo = {
        'instagram': {
            name: 'Instagram Business',
            icon: 'ti-brand-instagram',
            color: '#E1306C',
            description: 'Post photos, videos, and stories to your Instagram business account.',
            note: 'Requires Instagram Business Account connected to Facebook Page'
        },
        'facebook': {
            name: 'Facebook Page',
            icon: 'ti-brand-facebook',
            color: '#1877F2',
            description: 'Share posts, photos, and videos to your Facebook business page.',
            note: 'Requires Facebook Business Page'
        },
        'linkedin': {
            name: 'LinkedIn',
            icon: 'ti-brand-linkedin',
            color: '#0A66C2',
            description: 'Share professional content with your LinkedIn network.',
            note: 'Posts to your personal LinkedIn profile'
        },
        'twitter': {
            name: 'Twitter/X',
            icon: 'ti-brand-twitter',
            color: '#1DA1F2',
            description: 'Tweet and engage with your Twitter/X followers.',
            note: 'Posts to your Twitter account'
        },
        'pinterest': {
            name: 'Pinterest',
            icon: 'ti-brand-pinterest',
            color: '#E60023',
            description: 'Create pins and share inspiration on Pinterest boards.',
            note: 'Posts to your Pinterest account'
        }
    };

    const info = platformInfo[platform];

    document.getElementById('connectionModalTitle').innerHTML =
        `<i class="ti ${info.icon}" style="color: ${info.color};"></i> Connect ${info.name}`;

    const instructions = `
        <div style="text-align: center;">
            <div style="width: 100px; height: 100px; margin: 0 auto 2rem; border-radius: 50%; 
                background: linear-gradient(135deg, ${info.color}22, ${info.color}44);
                display: flex; align-items: center; justify-content: center;">
                <i class="ti ${info.icon}" style="font-size: 3rem; color: ${info.color};"></i>
            </div>
            
            <h2 style="margin-bottom: 1rem; color: #1e293b; font-size: 1.75rem;">Connect to ${info.name}</h2>
            <p style="color: #64748b; margin-bottom: 2rem; font-size: 1.05rem; max-width: 500px; margin-left: auto; margin-right: auto;">
                ${info.description}
            </p>
            
            <form onsubmit="connectAccountOAuth(event, '${platform}')" style="max-width: 450px; margin: 0 auto;">
                <div class="form-group" style="margin-bottom: 2rem; text-align: left;">
                    <label style="display: block; margin-bottom: 0.75rem; font-weight: 600; color: #475569; font-size: 1rem;">
                        <i class="ti ti-user"></i> Select Client <span style="color: #ef4444;">*</span>
                    </label>
                    <select class="form-control" id="oauthClientId" required 
                        style="width: 100%; padding: 0.875rem; font-size: 1rem; border: 2px solid #e2e8f0; border-radius: 10px;">
                        <option value="">Choose which client account to connect...</option>
                    </select>
                </div>
                
                <button type="submit" class="btn btn-primary" 
                    style="width: 100%; padding: 1.25rem; font-size: 1.125rem; font-weight: 600; 
                    background: linear-gradient(135deg, ${info.color}, ${info.color}dd); 
                    border: none; border-radius: 10px; display: flex; align-items: center; justify-content: center; gap: 0.75rem;">
                    <i class="ti ti-login"></i> 
                    Connect ${info.name}
                </button>
            </form>
            
            <div style="margin-top: 2.5rem; padding: 1.25rem; background: #f8fafc; border-radius: 12px; text-align: left; border-left: 4px solid ${info.color};">
                <div style="display: flex; align-items: start; gap: 0.75rem;">
                    <i class="ti ti-info-circle" style="color: ${info.color}; font-size: 1.25rem; flex-shrink: 0; margin-top: 0.125rem;"></i>
                    <div>
                        <p style="margin: 0 0 0.5rem 0; color: #1e293b; font-weight: 600; font-size: 0.95rem;">What happens next?</p>
                        <ol style="margin: 0; padding-left: 1.25rem; color: #64748b; font-size: 0.9rem; line-height: 1.7;">
                            <li>A secure popup window will open</li>
                            <li>Log in to your ${info.name} account</li>
                            <li>Authorize PanvelIQ to post on your behalf</li>
                            <li>Done! You can now publish posts directly</li>
                        </ol>
                        <p style="margin: 0.75rem 0 0 0; color: #94a3b8; font-size: 0.85rem;">
                            <i class="ti ti-lock"></i> ${info.note}
                        </p>
                    </div>
                </div>
            </div>
            
            <p style="color: #94a3b8; font-size: 0.875rem; margin-top: 1.5rem; display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
                <i class="ti ti-shield-check"></i> 
                Your login credentials are never stored. We only receive a secure access token.
            </p>
        </div>
    `;

    document.getElementById('instructionsContent').innerHTML = instructions;


    loadClientsForOAuth();
}



function getPlatformPermissions(platform) {
    const permissions = {
        'instagram': `
            <li>Post photos and videos to your Instagram feed</li>
            <li>Access your Instagram business account info</li>
            <li>View post insights and analytics</li>
        `,
        'facebook': `
            <li>Post content to your Facebook pages</li>
            <li>Manage your page posts</li>
            <li>Read engagement metrics</li>
        `,
        'linkedin': `
            <li>Post updates on your behalf</li>
            <li>Access your profile information</li>
            <li>Share content to your network</li>
        `,
        'twitter': `
            <li>Post and manage tweets</li>
            <li>Read your profile information</li>
            <li>Access your timeline</li>
        `,
        'pinterest': `
            <li>Create and manage pins</li>
            <li>Access your boards</li>
            <li>View your account information</li>
        `
    };

    return permissions[platform] || '<li>Basic account access</li>';
}

async function loadClientsForOAuth() {
    try {
        //  FIXED - Get token correctly
        const token = localStorage.getItem('access_token') || getCookie('access_token');

        if (!token) {
            console.error('No access token found');
            showNotification('Please login again', 'error');
            return;
        }

        const response = await fetch('/api/v1/clients/list', {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            if (response.status === 401) {
                console.error('Unauthorized - token may be expired');
                showNotification('Session expired. Please login again.', 'error');
                // Optionally redirect to login
                // window.location.href = '/auth/login';
                return;
            }
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        const select = document.getElementById('oauthClientId');

        if (select) {
            select.innerHTML = '<option value="">Choose client to connect...</option>';

            const clients = data.clients || [];
            clients.forEach(client => {
                const option = document.createElement('option');
                option.value = client.user_id || client.client_id;
                option.textContent = client.full_name || client.business_name || client.email;
                select.appendChild(option);
            });

            if (clients.length === 0) {
                select.innerHTML = '<option value="">No clients available</option>';
            }
        }
    } catch (error) {
        console.error('Error loading clients:', error);
        const select = document.getElementById('oauthClientId');
        if (select) {
            select.innerHTML = '<option value="">Error loading clients</option>';
        }
    }
}

// Helper function to get cookie
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}


async function connectAccountOAuth(event, platform) {
    event.preventDefault();
    
    console.log('=== OAuth Connection Started ===');
    console.log('Platform:', platform);
    
    const clientId = document.getElementById('oauthClientId').value;
    console.log('Client ID:', clientId);
    
    if (!clientId) {
        showNotification('Please select a client', 'error');
        return;
    }
    
    // Get token with detailed logging
    let token = localStorage.getItem('access_token');
    console.log('Token from localStorage:', token ? `Found (${token.length} chars)` : 'NOT FOUND');
    
    if (!token) {
        token = getCookie('access_token');
        console.log('Token from cookie:', token ? `Found (${token.length} chars)` : 'NOT FOUND');
    }
    
    if (!token) {
        console.error('❌ No token available!');
        showNotification('Please login to continue', 'error');
        setTimeout(() => {
            window.location.href = '/auth/login';
        }, 1500);
        return;
    }
    
    console.log(' Token acquired, first 30 chars:', token.substring(0, 30) + '...');
    
    // Build OAuth URL
    const oauthUrl = `/api/v1/social-media/oauth/connect/${platform}?client_id=${clientId}&token=${encodeURIComponent(token)}`;
    
    console.log('OAuth URL (first 150 chars):', oauthUrl.substring(0, 150) + '...');
    console.log('Full URL length:', oauthUrl.length);
    
    // Open popup
    const width = 600;
    const height = 700;
    const left = (screen.width / 2) - (width / 2);
    const top = (screen.height / 2) - (height / 2);
    
    console.log('Opening popup window...');
    
    const popup = window.open(
        oauthUrl,
        'OAuth Authorization',
        `width=${width},height=${height},left=${left},top=${top},toolbar=no,menubar=no,scrollbars=yes,resizable=yes`
    );
    
    if (!popup) {
        console.error('❌ Popup blocked!');
        showNotification('⚠️ Popup blocked! Please allow popups for this site.', 'error');
        return;
    }
    
    console.log(' Popup opened successfully');
    
    // Monitor popup
    let messageReceived = false;
    
    const checkInterval = setInterval(() => {
        if (popup.closed) {
            clearInterval(checkInterval);
            if (!messageReceived) {
                console.log('Popup closed without completing OAuth');
            }
        }
    }, 500);
    
    // Listen for success
    const messageHandler = function(event) {
        console.log('📨 Message received:', event.data);
        
        if (event.data && event.data.type === 'oauth_success') {
            messageReceived = true;
            clearInterval(checkInterval);
            
            const platformName = platform.charAt(0).toUpperCase() + platform.slice(1);
            showNotification(` ${platformName} connected successfully!`, 'success');
            
            closeAccountConnectionModal();
            loadConnectedAccounts();
            
            window.removeEventListener('message', messageHandler);
        }
    };
    
    window.addEventListener('message', messageHandler);
    
    // Cleanup
    setTimeout(() => {
        clearInterval(checkInterval);
        window.removeEventListener('message', messageHandler);
    }, 600000);
}

window.testOAuth = function() {
    const token = localStorage.getItem('access_token');
    console.log('Test - Token:', token ? 'EXISTS' : 'MISSING');
    
    if (token) {
        const url = `/api/v1/social-media/oauth/connect/linkedin?client_id=45&token=${encodeURIComponent(token)}`;
        console.log('Test - URL:', url.substring(0, 100));
        window.open(url, 'test', 'width=600,height=700');
    }
};

function updateFormLabels(platform) {
    const labelAccountId = document.getElementById('labelAccountId');
    const labelAccountName = document.getElementById('labelAccountName');
    const accountIdHelp = document.getElementById('accountIdHelp');
    const refreshTokenGroup = document.getElementById('refreshTokenGroup');
    const expiresInGroup = document.getElementById('expiresInGroup');

    const labels = {
        'instagram': {
            accountId: 'Instagram Business Account ID',
            accountName: 'Instagram Username',
            help: 'Format: 17841400000000000 (your Instagram Business Account ID)',
            showRefresh: true
        },
        'facebook': {
            accountId: 'Facebook Page ID',
            accountName: 'Page Name',
            help: 'Format: 123456789012345 (numeric Page ID)',
            showRefresh: false
        },
        'linkedin': {
            accountId: 'Person/Organization URN',
            accountName: 'LinkedIn Profile/Company Name',
            help: 'Format: urn:li:person:ABC123 or urn:li:organization:12345',
            showRefresh: true
        },
        'twitter': {
            accountId: 'Twitter User ID',
            accountName: 'Twitter Handle',
            help: 'Format: 1234567890 (numeric user ID)',
            showRefresh: true
        },
        'pinterest': {
            accountId: 'Pinterest Account ID',
            accountName: 'Pinterest Username',
            help: 'Your Pinterest account identifier',
            showRefresh: false
        }
    };

    const config = labels[platform] || labels['facebook'];

    labelAccountId.innerHTML = `${config.accountId} <span style="color: #ef4444;">*</span>`;
    labelAccountName.innerHTML = `${config.accountName} <span style="color: #ef4444;">*</span>`;
    accountIdHelp.textContent = config.help;

    refreshTokenGroup.style.display = config.showRefresh ? 'block' : 'none';
    expiresInGroup.style.display = config.showRefresh ? 'block' : 'none';
}

async function connectAccount(event) {
    event.preventDefault();

    const platform = document.getElementById('connectPlatform').value;
    const clientId = document.getElementById('connectClientId').value;
    const accountId = document.getElementById('connectAccountId').value.trim();
    const accountName = document.getElementById('connectAccountName').value.trim();
    const accessToken = document.getElementById('connectAccessToken').value.trim();
    const refreshToken = document.getElementById('connectRefreshToken').value.trim();
    const expiresIn = document.getElementById('connectExpiresIn').value;

    if (!platform || !clientId || !accountId || !accountName || !accessToken) {
        showNotification('Please fill in all required fields', 'error');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/accounts/connect`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                client_id: parseInt(clientId),
                platform: platform,
                platform_account_id: accountId,
                platform_account_name: accountName,
                access_token: accessToken,
                refresh_token: refreshToken || null,
                expires_in: expiresIn ? parseInt(expiresIn) : null
            })
        });

        const data = await response.json();

        if (response.ok) {
            showNotification(data.message || 'Account connected successfully!', 'success');
            closeAccountConnectionModal();
            loadConnectedAccounts();
        } else {
            showNotification(data.detail || 'Failed to connect account', 'error');
        }
    } catch (error) {
        console.error('Error connecting account:', error);
        showNotification('An error occurred while connecting the account', 'error');
    }
}


async function disconnectAccount(credentialId, platform) {
    if (!confirm(`Are you sure you want to disconnect this ${platform} account?`)) {
        return;
    }
    
    try {
        const token = localStorage.getItem('access_token') || getCookie('access_token');
        
        const response = await fetch(`/api/v1/social-media/disconnect-account/${credentialId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            showNotification(`${platform.charAt(0).toUpperCase() + platform.slice(1)} account disconnected`, 'success');
            loadConnectedAccounts();
        } else {
            throw new Error('Failed to disconnect account');
        }
    } catch (error) {
        console.error('Error disconnecting account:', error);
        showNotification('Failed to disconnect account', 'error');
    }
}



// =====================================================
// CALENDAR VIEW
// =====================================================

function loadCalendar() {
    const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'];

    const calendarMonth = document.getElementById('calendarMonth');
    if (calendarMonth) {
        calendarMonth.textContent = `${monthNames[currentMonth]} ${currentYear}`;
    }

    fetchCalendarData();
}

async function fetchCalendarData() {
    const grid = document.getElementById('calendarGrid');
    const clientId = document.getElementById('filterClient')?.value || '';

    try {
        const token = localStorage.getItem('access_token');

        let url = `${API_BASE}/calendar?month=${currentMonth + 1}&year=${currentYear}`;
        if (clientId) {
            url += `&client_id=${clientId}`;
        }

        const response = await fetch(url, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) {
            renderCalendar({});
            return;
        }

        const data = await response.json();
        renderCalendar(data.calendar || {});

    } catch (error) {
        console.error('Error loading calendar:', error);
        renderCalendar({});
    }
}

function renderCalendar(calendarData) {
    const grid = document.getElementById('calendarGrid');
    if (!grid) return;

    const firstDay = new Date(currentYear, currentMonth, 1).getDay();
    const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
    const today = new Date();

    let html = `
        <div class="calendar-grid">
            <div class="calendar-header-row">
                <div class="calendar-day-header">Sun</div>
                <div class="calendar-day-header">Mon</div>
                <div class="calendar-day-header">Tue</div>
                <div class="calendar-day-header">Wed</div>
                <div class="calendar-day-header">Thu</div>
                <div class="calendar-day-header">Fri</div>
                <div class="calendar-day-header">Sat</div>
            </div>
            <div class="calendar-days">
    `;

    for (let i = 0; i < firstDay; i++) {
        html += '<div class="calendar-day empty"></div>';
    }

    for (let day = 1; day <= daysInMonth; day++) {
        const dateStr = `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        const isToday = today.getDate() === day &&
            today.getMonth() === currentMonth &&
            today.getFullYear() === currentYear;

        const dayPosts = calendarData[dateStr] || [];

        html += `
            <div class="calendar-day ${isToday ? 'today' : ''}" onclick="showDayPosts('${dateStr}')">
                <div class="day-number">${day}</div>
                <div class="day-posts">
                    ${dayPosts.slice(0, 3).map(post => `
                        <div class="calendar-post ${post.platform}" title="${post.caption || ''}">
                            <i class="ti ti-brand-${post.platform}"></i>
                            <span>${truncateText(post.caption, 20)}</span>
                        </div>
                    `).join('')}
                    ${dayPosts.length > 3 ? `<div class="more-posts">+${dayPosts.length - 3} more</div>` : ''}
                </div>
            </div>
        `;
    }

    html += '</div></div>';
    grid.innerHTML = html;
}

function changeMonth(delta) {
    if (delta === 0) {
        const today = new Date();
        currentMonth = today.getMonth();
        currentYear = today.getFullYear();
    } else {
        currentMonth += delta;
        if (currentMonth > 11) {
            currentMonth = 0;
            currentYear++;
        } else if (currentMonth < 0) {
            currentMonth = 11;
            currentYear--;
        }
    }
    loadCalendar();
}

function showDayPosts(dateStr) {
    showNotification(`Showing posts for ${dateStr}`, 'info');
}

// =====================================================
// VIEW SWITCHING
// =====================================================
function switchView(view) {
    // Hide all views
   
    document.getElementById('calendarView')?.classList.remove('active');
    document.getElementById('listView')?.classList.remove('active');
    document.getElementById('inboxView')?.classList.remove('active');

    // Remove active state from all tabs
    document.querySelectorAll('.view-tab').forEach(tab => tab.classList.remove('active'));

    // Show selected view
    if (view === 'list') {
        document.getElementById('listView')?.classList.add('active');
        document.querySelector('.view-tab:first-child')?.classList.add('active');
        loadPosts();
    } else if (view === 'calendar') {
        document.getElementById('calendarView')?.classList.add('active');
        document.querySelector('.view-tab:nth-child(2)')?.classList.add('active');
        loadCalendar();
    } else if (view === 'inbox') {
        document.getElementById('inboxView')?.classList.add('active');
        document.querySelector('.view-tab:nth-child(3)')?.classList.add('active');
        loadInboxMessages();
    }
}


// =====================================================
// CREATE/EDIT POST MODAL
// =====================================================

function openPostModal() {
    currentEditingPostId = null;
    selectedContentId = null;
    selectedMediaUrls = [];
    selectedPlatforms = [];

    document.getElementById('modalTitle').textContent = 'Create New Post';
    document.getElementById('postForm').reset();
    document.getElementById('postModal').classList.add('active');
    document.getElementById('submitPostBtn').innerHTML = '<i class="ti ti-check"></i> Create Post';

    document.querySelectorAll('.platform-option').forEach(p => p.classList.remove('selected'));
    document.getElementById('postPlatform').value = '';

    document.getElementById('contentLibraryPicker').style.display = 'none';
    document.getElementById('mediaLibraryPicker').style.display = 'none';
    document.getElementById('bestTimesPanel').style.display = 'none';

    const mediaPreview = document.getElementById('selectedMediaPreview');
    if (mediaPreview) mediaPreview.innerHTML = '';

    updatePlatformCount();
}

function openCreatePostModal() {
    openPostModal();
}

async function editPost(postId) {
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_BASE}/posts/${postId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) throw new Error('Failed to load post');

        const data = await response.json();
        const post = data.post;

        currentEditingPostId = postId;
        document.getElementById('modalTitle').textContent = 'Edit Post';
        document.getElementById('submitPostBtn').innerHTML = '<i class="ti ti-check"></i> Update Post';

        document.getElementById('postClient').value = post.client_id;
        document.getElementById('postCaption').value = post.caption || '';
        document.getElementById('postHashtags').value = (post.hashtags || []).join(', ');
        document.getElementById('postStatus').value = post.status || 'draft';

        if (post.scheduled_at) {
            const date = new Date(post.scheduled_at);
            const localDateTime = new Date(date.getTime() - (date.getTimezoneOffset() * 60000))
                .toISOString().slice(0, 16);
            document.getElementById('postScheduledAt').value = localDateTime;
        }

        selectedPlatforms = post.platform ? post.platform.split(',') : [];
        document.querySelectorAll('.platform-option').forEach(p => {
            if (selectedPlatforms.includes(p.dataset.platform)) {
                p.classList.add('selected');
            } else {
                p.classList.remove('selected');
            }
        });
        document.getElementById('postPlatform').value = selectedPlatforms.join(',');

        selectedMediaUrls = post.media_urls || [];
        selectedContentId = post.content_id;

        updatePlatformCount();
        document.getElementById('postModal').classList.add('active');

    } catch (error) {
        console.error('Error loading post:', error);
        showNotification('Failed to load post details', 'error');
    }
}

function closePostModal() {
    document.getElementById('postModal').classList.remove('active');
}

// =====================================================
// SAVE POST
// =====================================================
// =====================================================
// SAVE POST (WITH CONFLICT DETECTION)
// =====================================================

async function savePost(event) {
    event.preventDefault();

    const submitBtn = document.getElementById('submitPostBtn');
    const originalBtnText = submitBtn.innerHTML;

    try {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="ti ti-loader"></i> Saving...';

        const token = localStorage.getItem('access_token');
        const clientId = document.getElementById('postClient').value;
        const platforms = document.getElementById('postPlatform').value;
        const caption = document.getElementById('postCaption').value;
        const hashtagsInput = document.getElementById('postHashtags').value;
        const hashtags = hashtagsInput.split(',').map(h => h.trim()).filter(h => h);
        const status = document.getElementById('postStatus').value;
        const scheduledAt = document.getElementById('postScheduledAt').value;

        if (!clientId) {
            showNotification('Please select a client', 'error');
            throw new Error('Client required');
        }

        if (!platforms) {
            showNotification('Please select at least one platform', 'error');
            throw new Error('Platform required');
        }

        if (!caption.trim()) {
            showNotification('Please enter a caption', 'error');
            throw new Error('Caption required');
        }

        // ✅ NEW: Check for scheduling conflicts if scheduling a post
        if (status === 'scheduled' && scheduledAt) {
            const platformList = platforms.split(',').filter(p => p.trim());
            const firstPlatform = platformList[0].trim();
            
            try {
                const conflictResponse = await fetch(`${API_BASE}/check-conflicts`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        client_id: parseInt(clientId),
                        platform: firstPlatform,
                        scheduled_at: scheduledAt
                    })
                });
                
                if (conflictResponse.ok) {
                    const conflictData = await conflictResponse.json();
                    
                    if (conflictData.has_conflicts) {
                        // Build detailed conflict message
                        let conflictMessage = `⚠️ SCHEDULING CONFLICT DETECTED!\n\n`;
                        conflictMessage += `Found ${conflictData.conflict_count} post(s) scheduled within 2 hours:\n\n`;
                        
                        conflictData.conflicts.forEach((conflict, index) => {
                            conflictMessage += `${index + 1}. "${conflict.caption_preview}"\n`;
                            conflictMessage += `   Scheduled: ${new Date(conflict.scheduled_at).toLocaleString()}\n`;
                            conflictMessage += `   Time difference: ${conflict.time_difference}\n\n`;
                        });
                        
                        conflictMessage += `${conflictData.recommendation}\n\n`;
                        conflictMessage += `Do you want to proceed anyway?`;
                        
                        const proceed = confirm(conflictMessage);
                        
                        if (!proceed) {
                            throw new Error('Cancelled due to scheduling conflicts');
                        }
                    }
                }
            } catch (error) {
                if (error.message === 'Cancelled due to scheduling conflicts') {
                    throw error;
                }
                console.error('Conflict check failed:', error);
                // Continue even if conflict check fails
            }
        }

        const platformList = platforms.split(',').filter(p => p.trim());
        let successCount = 0;

        for (const platform of platformList) {
            const postData = {
                client_id: parseInt(clientId),
                content_id: selectedContentId,
                platform: platform.trim(),
                caption: caption,
                media_urls: selectedMediaUrls,
                hashtags: hashtags,
                scheduled_at: scheduledAt || null,
                status: status
            };

            let url = `${API_BASE}/posts`;
            let method = 'POST';

            if (currentEditingPostId && platformList.length === 1) {
                url += `/${currentEditingPostId}`;
                method = 'PUT';
            }

            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(postData)
            });

            if (response.ok) {
                successCount++;
            }
        }

        if (successCount > 0) {
            showNotification(`Successfully saved ${successCount} post(s)`, 'success');
            closePostModal();
            loadPosts();
            loadCalendar();
            loadStats();
        } else {
            throw new Error('Failed to save any posts');
        }

    } catch (error) {
        console.error('Error saving post:', error);
        if (!['Client required', 'Platform required', 'Caption required', 'Cancelled due to scheduling conflicts'].includes(error.message)) {
            showNotification(error.message || 'Failed to save post', 'error');
        }
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalBtnText;
    }
}

// =====================================================
// DELETE POST
// =====================================================

async function deletePost(postId) {
    if (!confirm('Are you sure you want to delete this post?')) return;

    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_BASE}/posts/${postId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) throw new Error('Failed to delete post');

        showNotification('Post deleted successfully', 'success');
        loadPosts();
        loadCalendar();
        loadStats();

    } catch (error) {
        console.error('Error deleting post:', error);
        showNotification('Failed to delete post', 'error');
    }
}



// =====================================================
// PUBLISH POST
// =====================================================

async function publishPost(postId) {
    if (!confirm('Publish this post now? It will be posted to the social media platform immediately.')) {
        return;
    }

    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_BASE}/posts/${postId}/publish`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (response.ok && data.success) {
            showNotification(data.message || 'Post published successfully!', 'success');
            loadPosts();
            loadCalendar();
            loadStats();
        } else {
            showNotification(data.detail || data.error || 'Failed to publish post', 'error');
        }
    } catch (error) {
        console.error('Error publishing post:', error);
        showNotification('Failed to publish post. Please check if the social media account is connected.', 'error');
    }
}
// =====================================================
// CONTENT LIBRARY INTEGRATION (MODULE 5)
// =====================================================

async function loadContentLibrary() {
    const clientId = document.getElementById('postClient').value;
    const picker = document.getElementById('contentLibraryPicker');

    if (!clientId) {
        showNotification('Please select a client first', 'error');
        return;
    }

    picker.innerHTML = '<div class="loading-state"><div class="loader-spinner"></div><p>Loading content...</p></div>';
    picker.style.display = 'block';

    try {
        const token = localStorage.getItem('access_token');

        let response = await fetch(`/api/v1/content/list?client_id=${clientId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) {
            response = await fetch(`/api/v1/content?client_id=${clientId}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
        }

        if (!response.ok) throw new Error('Failed to load content library');

        const data = await response.json();
        displayContentLibrary(data.content || data.data || []);

    } catch (error) {
        console.error('Error loading content library:', error);
        picker.innerHTML = `<div style="text-align: center; padding: 2rem; color: #64748b;">Failed to load content library</div>`;
    }
}

function displayContentLibrary(content) {
    const picker = document.getElementById('contentLibraryPicker');

    if (!content || content.length === 0) {
        picker.innerHTML = `<div style="text-align: center; padding: 2rem; color: #64748b;">No saved content found</div>`;
        return;
    }

    picker.innerHTML = content.map(item => `
        <div class="content-card" onclick="selectContent(${item.content_id || item.id}, this)">
            <div class="content-card-platform">${item.platform || 'General'}</div>
            <div class="content-card-text">${truncateText(item.content_text || item.text || '', 100)}</div>
        </div>
    `).join('');
}

function selectContent(contentId, element) {
    selectedContentId = contentId;

    document.querySelectorAll('.content-card').forEach(card => card.classList.remove('selected'));
    element.classList.add('selected');

    const contentText = element.querySelector('.content-card-text')?.textContent || '';
    document.getElementById('postCaption').value = contentText;

    showNotification('Content loaded successfully', 'success');
}

// =====================================================
// MEDIA LIBRARY INTEGRATION (MODULE 8)
// =====================================================

async function loadMediaLibrary() {
    const clientId = document.getElementById('postClient').value;
    const picker = document.getElementById('mediaLibraryPicker');

    if (!clientId) {
        showNotification('Please select a client first', 'error');
        return;
    }

    picker.innerHTML = '<div class="loading-state"><div class="loader-spinner"></div><p>Loading media...</p></div>';
    picker.style.display = 'grid';

    try {
        const token = localStorage.getItem('access_token');

        let response = await fetch(`/api/v1/media-studio/assets?client_id=${clientId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) {
            response = await fetch(`/api/v1/media/assets?client_id=${clientId}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
        }

        if (!response.ok) throw new Error('Failed to load media library');

        const data = await response.json();
        displayMediaLibrary(data.assets || data.data || []);

    } catch (error) {
        console.error('Error loading media library:', error);
        picker.innerHTML = `<div style="text-align: center; padding: 2rem; color: #64748b; grid-column: 1/-1;">Failed to load media library</div>`;
    }
}

function displayMediaLibrary(assets) {
    const picker = document.getElementById('mediaLibraryPicker');

    if (!assets || assets.length === 0) {
        picker.innerHTML = `<div style="text-align: center; padding: 2rem; color: #64748b; grid-column: 1/-1;">No media assets found</div>`;
        return;
    }

    picker.innerHTML = assets.map(asset => {
        const fileUrl = asset.file_url || asset.url;
        const isSelected = selectedMediaUrls.includes(fileUrl);
        return `
            <div class="media-card ${isSelected ? 'selected' : ''}" onclick="toggleMedia('${fileUrl}')">
                <img src="${fileUrl}" alt="${asset.asset_name || 'Asset'}" onerror="this.src='/static/images/placeholder.png'">
                <div class="media-card-type">${asset.asset_type || 'image'}</div>
                <div class="checkmark"><i class="ti ti-check"></i></div>
            </div>
        `;
    }).join('');
}

function toggleMedia(url) {
    const index = selectedMediaUrls.indexOf(url);

    if (index > -1) {
        selectedMediaUrls.splice(index, 1);
    } else {
        selectedMediaUrls.push(url);
    }

    event.target.closest('.media-card')?.classList.toggle('selected');
    showNotification(`${selectedMediaUrls.length} media selected`, 'info');
    updateSelectedMediaPreview();
}

function updateSelectedMediaPreview() {
    const preview = document.getElementById('selectedMediaPreview');
    if (!preview) return;

    if (selectedMediaUrls.length === 0) {
        preview.innerHTML = '';
        return;
    }

    preview.innerHTML = `
        <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 1rem;">
            ${selectedMediaUrls.map(url => `
                <div style="position: relative; width: 60px; height: 60px; border-radius: 8px; overflow: hidden;">
                    <img src="${url}" style="width: 100%; height: 100%; object-fit: cover;">
                    <button onclick="removeMedia('${url}')" style="position: absolute; top: 2px; right: 2px; width: 20px; height: 20px; border-radius: 50%; background: #ef4444; border: none; color: white; cursor: pointer;">×</button>
                </div>
            `).join('')}
        </div>
    `;
}

function removeMedia(url) {
    const index = selectedMediaUrls.indexOf(url);
    if (index > -1) selectedMediaUrls.splice(index, 1);
    updateSelectedMediaPreview();
}

// =====================================================
// AI BEST TIMES - COMPLETELY FIXED
// =====================================================

async function getBestTimes() {
    const clientId = document.getElementById('postClient').value;
    const platforms = document.getElementById('postPlatform').value;
    const panel = document.getElementById('bestTimesPanel');

    if (!clientId) {
        showNotification('Please select a client first', 'error');
        return;
    }

    if (!platforms) {
        showNotification('Please select at least one platform first', 'error');
        return;
    }

    panel.innerHTML = '<div class="loading-state"><div class="loader-spinner"></div><p>Analyzing best times...</p></div>';
    panel.style.display = 'block';

    try {
        const token = localStorage.getItem('access_token');
        const platformList = platforms.split(',');
        const firstPlatform = platformList[0].trim();

        const response = await fetch(`${API_BASE}/best-times`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                client_id: parseInt(clientId),
                platform: firstPlatform
            })
        });

        if (!response.ok) throw new Error('Failed to get best times');

        const data = await response.json();
        console.log('Best times API response:', data);

        const times = data.recommended_times || [];
        displayBestTimes(times);

    } catch (error) {
        console.error('Error getting best times:', error);
        panel.innerHTML = `<div style="text-align: center; padding: 2rem; color: #64748b;">Failed to analyze best times</div>`;
    }
}

function displayBestTimes(times) {
    const panel = document.getElementById('bestTimesPanel');

    if (!times || times.length === 0) {
        panel.innerHTML = `<div style="text-align: center; padding: 2rem; color: #64748b;">No best time recommendations available</div>`;
        return;
    }

    let html = '<div class="best-times-grid">';

    times.forEach(time => {
        // Parse values safely
        const day = time.day || 'Unknown';
        const hour = parseInt(time.hour) || 12;
        let score = parseFloat(time.engagement_score) || 0;

        // FIX: Normalize score - keep dividing by 100 until it's in 0-100 range
        while (score > 100) {
            score = score / 100;
        }

        // Format time for display (convert 24h to 12h format)
        const hour12 = hour % 12 || 12;
        const ampm = hour >= 12 ? 'PM' : 'AM';
        const timeDisplay = `${hour12}:00 ${ampm}`;

        html += `
            <div class="best-time-item" onclick="useBestTime('${day}', ${hour})" style="cursor: pointer;">
                <div class="best-time-info">
                    <div class="best-time-icon">
                        <i class="ti ti-clock"></i>
                    </div>
                    <div class="best-time-details">
                        <h4>${day}</h4>
                        <p>${timeDisplay}</p>
                    </div>
                </div>
                <div class="best-time-score">
                    <span class="score-badge">${score.toFixed(1)}%</span>
                </div>
            </div>
        `;
    });

    html += '</div>';
    panel.innerHTML = html;
    panel.style.display = 'block';
}

function useBestTime(day, hour) {
    console.log('useBestTime called with:', day, hour);

    // Get form elements
    const dateInput = document.getElementById('postScheduledAt');
    const statusSelect = document.getElementById('postStatus');

    if (!dateInput) {
        console.error('Date input not found');
        showNotification('Error: Date input not found', 'error');
        return;
    }

    if (!statusSelect) {
        console.error('Status select not found');
        showNotification('Error: Status select not found', 'error');
        return;
    }

    // FIXED: Day mapping aligned with JavaScript's getDay() where Sunday = 0
    // Backend uses Monday = 0, but we receive day NAME so we map to JS days
    const dayToJsIndex = {
        'Sunday': 0,
        'Monday': 1,
        'Tuesday': 2,
        'Wednesday': 3,
        'Thursday': 4,
        'Friday': 5,
        'Saturday': 6
    };

    const targetDayIndex = dayToJsIndex[day];

    if (targetDayIndex === undefined) {
        console.error('Invalid day:', day);
        showNotification('Invalid day selected', 'error');
        return;
    }

    // Ensure hour is a number
    const targetHour = parseInt(hour);
    if (isNaN(targetHour) || targetHour < 0 || targetHour > 23) {
        console.error('Invalid hour:', hour);
        showNotification('Invalid hour selected', 'error');
        return;
    }

    // Calculate next occurrence of this day
    const now = new Date();
    const currentDayIndex = now.getDay(); // JavaScript: Sunday = 0

    let daysUntil = targetDayIndex - currentDayIndex;
    if (daysUntil <= 0) {
        daysUntil += 7; // Next week
    }

    // Create target date
    const targetDate = new Date();
    targetDate.setDate(targetDate.getDate() + daysUntil);
    targetDate.setHours(targetHour, 0, 0, 0);

    // Format for datetime-local input: YYYY-MM-DDTHH:MM
    const year = targetDate.getFullYear();
    const month = String(targetDate.getMonth() + 1).padStart(2, '0');
    const dateNum = String(targetDate.getDate()).padStart(2, '0');
    const hourStr = String(targetHour).padStart(2, '0');

    const formattedDateTime = `${year}-${month}-${dateNum}T${hourStr}:00`;

    console.log('Setting datetime to:', formattedDateTime);
    console.log('Target date object:', targetDate);

    // SET THE VALUES DIRECTLY
    dateInput.value = formattedDateTime;
    statusSelect.value = 'scheduled';

    // Verify the values were set
    console.log('Date input value after set:', dateInput.value);
    console.log('Status select value after set:', statusSelect.value);

    // Visual feedback
    const hour12 = targetHour % 12 || 12;
    const ampm = targetHour >= 12 ? 'PM' : 'AM';

    showNotification(`Scheduled for ${day} at ${hour12}:00 ${ampm}`, 'success');
}

// =====================================================
// TRENDING TOPICS
// =====================================================

async function loadTrendingTopics() {
    const container = document.getElementById('trendingTopics');
    if (!container) return;

    try {
        const token = localStorage.getItem('access_token');
        const platform = document.getElementById('trendingPlatformFilter')?.value || '';

        let url = `${API_BASE}/trending`;
        if (platform) url += `?platform=${platform}`;

        const response = await fetch(url, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) throw new Error('Failed to load trends');

        const data = await response.json();
        displayTrendingTopics(data.topics || data.trending || data.trends || []);

    } catch (error) {
        console.error('Error loading trending topics:', error);
        container.innerHTML = '<p style="color: #94a3b8; text-align: center;">Unable to load trending topics</p>';
    }
}

function displayTrendingTopics(topics) {
    const container = document.getElementById('trendingTopics');

    if (!topics || topics.length === 0) {
        container.innerHTML = '<p style="color: #94a3b8; text-align: center;">No trending topics available</p>';
        return;
    }

    container.innerHTML = `
        <div class="trending-grid">
            ${topics.slice(0, 6).map(topic => `
                <div class="trending-card" onclick="useTrend('${(topic.topic || topic.name || '').replace(/'/g, "\\'")}')">
                    <div class="trending-header">
                        <span class="trending-platform">${topic.platform || 'All'}</span>
                        <span class="trending-volume">
                            <i class="ti ti-trending-up"></i> ${formatNumber(topic.volume || 0)}
                        </span>
                    </div>
                    <div class="trending-topic">${topic.topic || topic.name}</div>
                    <span class="trending-category">${topic.category || 'Trending'}</span>
                </div>
            `).join('')}
        </div>
    `;
}

function useTrend(topic) {
    const caption = document.getElementById('postCaption');
    if (caption) {
        caption.value += (caption.value ? ' ' : '') + topic;
        showNotification('Trend added to caption', 'success');
    }
}

function formatNumber(num) {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
}

// =====================================================
// PERFORMANCE SUMMARIES
// =====================================================

async function loadPerformanceSummaries() {
    const container = document.getElementById('performanceSummaries');
    if (!container) return;

    try {
        const token = localStorage.getItem('access_token');
        const clientId = document.getElementById('filterClient')?.value || '';

        let url = `${API_BASE}/analytics/summary`;
        if (clientId) url += `?client_id=${clientId}`;

        const response = await fetch(url, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) throw new Error('Failed to load performance data');

        const data = await response.json();
        displayPerformanceSummaries(data.summaries || data.analytics || []);

    } catch (error) {
        console.error('Error loading performance summaries:', error);
        container.innerHTML = '<p style="color: #94a3b8; text-align: center;">Unable to load performance data</p>';
    }
}

function displayPerformanceSummaries(summaries) {
    const container = document.getElementById('performanceSummaries');
    if (!container) return;

    if (!summaries || summaries.length === 0) {
        container.innerHTML = '<p style="color: #94a3b8; text-align: center;">No performance data available</p>';
        return;
    }

    container.innerHTML = summaries.map(summary => {
        const platform = summary.platform || 'Unknown';
        return `
            <div class="performance-card">
                <div class="performance-header">
                    <div class="platform-badge platform-${platform.toLowerCase()}">
                        <i class="ti ti-brand-${platform.toLowerCase()}"></i>
                        ${platform}
                    </div>
                </div>
                <div class="metrics-row">
                    <div class="metric-item">
                        <span class="metric-label">Posts</span>
                        <span class="metric-value">${summary.total_posts || 0}</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">Engagement</span>
                        <span class="metric-value">${formatNumber(summary.engagement || 0)}</span>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// =====================================================
// NOTIFICATIONS
// =====================================================

function showNotification(message, type = 'info') {
    const existing = document.querySelector('.notification');
    if (existing) existing.remove();

    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <i class="ti ti-${type === 'success' ? 'check' : type === 'error' ? 'x' : 'info-circle'}"></i>
        <span>${message}</span>
    `;

    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
        color: white;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Animation styles
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);

// =====================================================
// MEDIA UPLOAD HANDLER
// =====================================================

async function handleMediaUpload(event) {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    const clientId = document.getElementById('postClient').value;
    if (!clientId) {
        showNotification('Please select a client first', 'error');
        event.target.value = '';
        return;
    }

    showNotification('Uploading media...', 'info');

    for (const file of files) {
        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('client_id', clientId);
            formData.append('asset_type', file.type.startsWith('video/') ? 'video' : 'image');
            formData.append('asset_name', file.name);

            const token = localStorage.getItem('access_token');
            const response = await fetch('/api/v1/media-studio/upload', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
                body: formData
            });

            if (response.ok) {
                const result = await response.json();
                if (result.file_url) {
                    selectedMediaUrls.push(result.file_url);
                }
            }
        } catch (error) {
            console.error('Error uploading file:', error);
        }
    }

    updateSelectedMediaPreview();
    showNotification(`${files.length} file(s) uploaded`, 'success');
    event.target.value = '';
}


// =====================================================
// ACCOUNT CONNECTION MANAGEMENT
// =====================================================

async function loadConnectedAccounts() {
    try {
        const token = localStorage.getItem('access_token') || getCookie('access_token');
        
        const response = await fetch('/api/v1/social-media/connected-accounts', {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error('Failed to load connected accounts');
        }

        const data = await response.json();
        const accounts = data.accounts || [];
        
        console.log('Connected accounts:', accounts);
        
        displayConnectedAccounts(accounts);
        
    } catch (error) {
        console.error('Error loading connected accounts:', error);
        document.getElementById('connectedAccountsDisplay').innerHTML = `
            <p style="color: #ef4444;">Failed to load connected accounts</p>
        `;
    }
}


function displayConnectedAccounts(accounts) {
    const container = document.getElementById('connectedAccountsDisplay');
    
    if (!container) {
        console.error('❌ connectedAccountsDisplay element not found');
        return;
    }
    
    console.log(`Displaying ${accounts.length} connected accounts`);
    
    if (accounts.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 2rem; color: #64748b;">
                <i class="ti ti-unlink" style="font-size: 3rem; opacity: 0.5;"></i>
                <p style="margin-top: 1rem;">No social media accounts connected yet.</p>
                <p style="font-size: 0.9rem;">Click "Connect New Account" to get started.</p>
            </div>
        `;
        return;
    }
    
    const platformIcons = {
        'instagram': 'ti-brand-instagram',
        'facebook': 'ti-brand-facebook',
        'linkedin': 'ti-brand-linkedin',
        'twitter': 'ti-brand-twitter',
        'pinterest': 'ti-brand-pinterest'
    };
    
    const platformColors = {
        'instagram': '#E1306C',
        'facebook': '#1877F2',
        'linkedin': '#0A66C2',
        'twitter': '#1DA1F2',
        'pinterest': '#E60023'
    };
    
    let html = '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1rem;">';
    
    accounts.forEach(account => {
        const icon = platformIcons[account.platform] || 'ti-link';
        const color = platformColors[account.platform] || '#64748b';
        
        // Handle both 'credential_id' and 'id' column names
        const accountId = account.credential_id || account.id;
        const accountName = account.platform_account_name || account.platform;
        const clientName = account.client_name || 'Client';
        
        console.log(`Rendering: ${account.platform} (ID: ${accountId}) - ${accountName}`);
        
        html += `
            <div style="background: white; border: 2px solid #e2e8f0; border-radius: 12px; padding: 1.25rem; transition: all 0.2s;"
                onmouseover="this.style.borderColor='${color}'; this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px ${color}33';" 
                onmouseout="this.style.borderColor='#e2e8f0'; this.style.transform='translateY(0)'; this.style.boxShadow='none';">
                
                <div style="display: flex; align-items: start; gap: 1rem;">
                    <div style="width: 48px; height: 48px; border-radius: 12px; background: linear-gradient(135deg, ${color}22, ${color}44); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                        <i class="ti ${icon}" style="font-size: 1.5rem; color: ${color};"></i>
                    </div>
                    
                    <div style="flex: 1; min-width: 0;">
                        <div style="font-weight: 600; color: #1e293b; margin-bottom: 0.25rem; font-size: 1rem;">
                            ${accountName}
                        </div>
                        <div style="font-size: 0.85rem; color: #64748b; text-transform: capitalize; margin-bottom: 0.25rem;">
                            <i class="ti ti-brand-${account.platform}"></i> ${account.platform}
                        </div>
                        <div style="font-size: 0.8rem; color: #94a3b8;">
                            <i class="ti ti-user"></i> ${clientName}
                        </div>
                        ${account.token_expires_at ? `
                            <div style="font-size: 0.75rem; color: #f59e0b; margin-top: 0.5rem;">
                                <i class="ti ti-clock"></i> Expires: ${new Date(account.token_expires_at).toLocaleDateString()}
                            </div>
                        ` : ''}
                    </div>
                </div>
                
                <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #e2e8f0; display: flex; justify-content: flex-end;">
                    <button 
                        onclick="disconnectAccount(${accountId}, '${account.platform}')" 
                        style="padding: 0.5rem 1rem; border-radius: 8px; border: 1px solid #fca5a5; background: #fef2f2; color: #ef4444; cursor: pointer; display: flex; align-items: center; gap: 0.5rem; font-size: 0.875rem; font-weight: 500; transition: all 0.2s;"
                        onmouseover="this.style.background='#ef4444'; this.style.color='white'; this.style.borderColor='#ef4444';"
                        onmouseout="this.style.background='#fef2f2'; this.style.color='#ef4444'; this.style.borderColor='#fca5a5';"
                        title="Disconnect ${accountName}">
                        <i class="ti ti-unlink"></i>
                        Disconnect
                    </button>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
    
    console.log('✅ Accounts displayed successfully');
}


// Show account connection instructions when platform selected but not connected
function showConnectionInstructions(platform) {
    showNotification(`Please connect your ${platform} account first to publish posts.`, 'warning');

    // Could open a modal with OAuth instructions here
    // For now, show basic message
}





// =====================================================
// EXPOSE FUNCTIONS GLOBALLY
// =====================================================

window.openPostModal = openPostModal;
window.openCreatePostModal = openCreatePostModal;
window.closePostModal = closePostModal;
window.editPost = editPost;
window.deletePost = deletePost;
window.publishPost = publishPost;
window.savePost = savePost;
window.loadPosts = loadPosts;
window.loadCalendar = loadCalendar;
window.loadContentLibrary = loadContentLibrary;
window.loadMediaLibrary = loadMediaLibrary;
window.selectContent = selectContent;
window.toggleMedia = toggleMedia;
window.removeMedia = removeMedia;
window.getBestTimes = getBestTimes;
window.useBestTime = useBestTime;
window.useTrend = useTrend;
window.switchView = switchView;
window.changeMonth = changeMonth;
window.showDayPosts = showDayPosts;
window.handleMediaUpload = handleMediaUpload;
window.loadTrendingTopics = loadTrendingTopics;

window.loadConnectedAccounts = loadConnectedAccounts;
window.disconnectAccount = disconnectAccount;
window.displayConnectedAccounts = displayConnectedAccounts;