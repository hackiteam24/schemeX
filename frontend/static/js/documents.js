/* ==================== */
/* Documents Page JavaScript */
/* ==================== */

document.addEventListener('DOMContentLoaded', () => {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const uploadProgress = document.getElementById('uploadProgress');
    let currentDocuments = [];
    // Drag and drop handlers
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        handleFiles(files);
    });
    
    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });
    
    // File input handler
    fileInput.addEventListener('change', (e) => {
        const files = e.target.files;
        handleFiles(files);
    });
    
    // Handle file upload
    async function handleFiles(files) {
        if (files.length === 0) return;
        
        for (const file of files) {
            // Validate file type
            const validTypes = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png'];
            if (!validTypes.includes(file.type)) {
                showToast(`Invalid file type: ${file.name}. Please upload PDF, JPG, or PNG files.`, 'error');
                continue;
            }
            
            // Validate file size (5MB)
            const maxSize = 5 * 1024 * 1024;
            if (file.size > maxSize) {
                showToast(`File too large: ${file.name}. Maximum size is 5MB.`, 'error');
                continue;
            }
            
            // Upload file
            await uploadFile(file);
        }
    }
    
    // Upload single file
    async function uploadFile(file) {
        const formData = new FormData();
        formData.append('document', file);
        
        const docType = fileInput.getAttribute('data-type');
        if (docType) {
            formData.append('document_type', docType);
            fileInput.removeAttribute('data-type');
        }
        
        // Show upload progress
        showUploadProgress(file);
        
        try {
            showToast(`Uploading ${file.name}...`, 'info');
            
            const response = await API.postForm('/api/documents/upload/', formData);
            
            showToast(`${file.name} uploaded successfully!`, 'success');
            
            // Reload documents to refresh both lists dynamically
            await loadDocuments();
            
        } catch (error) {
            showToast(`Failed to upload ${file.name}. Please try again.`, 'error');
        }
        
        // Hide upload progress
        setTimeout(() => {
            uploadProgress.style.display = 'none';
        }, 1000);
    }
    
    // Show upload progress
    function showUploadProgress(file) {
        uploadProgress.style.display = 'block';
        uploadProgress.innerHTML = `
            <div class="progress-item">
                <div class="progress-info">
                    <span class="file-name">${file.name}</span>
                    <span class="file-size">${formatFileSize(file.size)}</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: 0%;"></div>
                </div>
                <span class="progress-percentage">0%</span>
            </div>
        `;
    }
    
    // Update upload progress
    function updateUploadProgress(percentage) {
        const progressFill = uploadProgress.querySelector('.progress-fill');
        const progressPercentage = uploadProgress.querySelector('.progress-percentage');
        
        if (progressFill && progressPercentage) {
            progressFill.style.width = `${percentage}%`;
            progressPercentage.textContent = `${percentage}%`;
        }
    }
    
    // Format file size
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }
    
    // Add uploaded document to grid
    function addUploadedDocument(doc) {
        const uploadedDocsGrid = document.querySelector('.uploaded-docs-grid');
        
        const docCard = document.createElement('div');
        docCard.className = 'uploaded-doc-card slide-up';
        
        const fileUrl = doc.file_url || doc.file || '';
        const isPdf = fileUrl.toLowerCase().endsWith('.pdf');
        const iconClass = isPdf ? 'fa-file-pdf' : 'fa-file-image';
        
        // Format date
        const uploadDate = doc.upload_date ? new Date(doc.upload_date).toLocaleDateString() : 'Just now';
        
        // Verification badge style
        let badgeClass = 'badge-warning';
        let statusDisplay = 'Pending Verification';
        if (doc.verification_status === 'verified') {
            badgeClass = 'badge-success';
            statusDisplay = 'Verified';
        } else if (doc.verification_status === 'rejected') {
            badgeClass = 'badge-danger';
            statusDisplay = 'Rejected';
        }
        
        docCard.innerHTML = `
            <div class="doc-preview">
                <i class="fa-solid ${iconClass}"></i>
            </div>
            <div class="doc-details">
                <h4>${doc.document_type_display || doc.document_type || 'Document'}</h4>
                <p>Uploaded on ${uploadDate}</p>
                <span class="badge ${badgeClass}">${statusDisplay}</span>
            </div>
            <div class="doc-actions">
                <a href="${fileUrl}" target="_blank" class="icon-btn" title="View">
                    <i class="fa-solid fa-eye"></i>
                </a>
                <button class="icon-btn" title="Download" onclick="downloadDocument('${doc.id}')">
                    <i class="fa-solid fa-download"></i>
                </button>
                <button class="icon-btn" title="Delete" onclick="deleteDocument(this, '${doc.id}')">
                    <i class="fa-solid fa-trash"></i>
                </button>
            </div>
        `;
        
        uploadedDocsGrid.appendChild(docCard);
    }
    
    // Add required document card
    function addRequiredDocument(reqDoc) {
        const requiredDocsList = document.querySelector('.required-docs-list');
        
        const docCard = document.createElement('div');
        docCard.className = `doc-item ${reqDoc.uploaded ? 'uploaded' : 'pending'}`;
        
        const iconClass = reqDoc.uploaded ? 'fa-solid fa-file-circle-check' : 'fa-solid fa-file-circle-exclamation';
        const badgeClass = reqDoc.uploaded ? 'badge-success' : 'badge-warning';
        const statusDisplay = reqDoc.uploaded ? 'Uploaded' : 'Pending';
        
        docCard.innerHTML = `
            <div class="doc-icon">
                <i class="${iconClass}"></i>
            </div>
            <div class="doc-info">
                <h4>${reqDoc.name}</h4>
                <p>Required for: ${reqDoc.scheme}</p>
            </div>
            <div class="doc-status">
                <span class="badge ${badgeClass}">${statusDisplay}</span>
            </div>
            <div class="doc-actions">
                ${reqDoc.uploaded ? '' : `
                    <button class="icon-btn" title="Upload" onclick="uploadDocument('${reqDoc.name}')">
                        <i class="fa-solid fa-upload"></i>
                    </button>
                `}
            </div>
        `;
        
        requiredDocsList.appendChild(docCard);
    }
    
    // Update required document status
    function updateRequiredDocumentStatus(doc) {
        const docItems = document.querySelectorAll('.doc-item.pending');
        
        docItems.forEach(item => {
            const title = item.querySelector('h4').textContent.toLowerCase();
            const docName = doc.name.toLowerCase();
            
            if (title.includes('aadhaar') && docName.includes('aadhaar')) {
                item.classList.remove('pending');
                item.querySelector('.doc-status').innerHTML = '<span class="badge badge-success">Uploaded</span>';
                item.querySelector('.doc-actions').innerHTML = `
                    <button class="icon-btn" title="View">
                        <i class="fa-solid fa-eye"></i>
                    </button>
                    <button class="icon-btn" title="Delete">
                        <i class="fa-solid fa-trash"></i>
                    </button>
                `;
            }
        });
    }
    
    // Upload specific document type
    window.uploadDocument = function(type) {
        fileInput.setAttribute('data-type', type);
        fileInput.click();
    };
    
    // View document
    window.viewDocument = function(id) {
        showToast('Opening document viewer...', 'info');
    };
    
    // Download document
    window.downloadDocument = async function(id) {
        try {
            showToast('Downloading document...', 'info');
            
            const response = await API.get(`/api/documents/${id}/download/`);
            
            // Create download link
            const link = document.createElement('a');
            link.href = response.download_url;
            link.download = '';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            showToast('Document download started!', 'success');
            
        } catch (error) {
            showToast('Failed to download document. Please try again.', 'error');
        }
    };
    
    // Delete document
    window.deleteDocument = async function(btn, id) {
        if (!confirm('Are you sure you want to delete this document?')) {
            return;
        }
        
        try {
            await API.delete(`/api/documents/${id}/`);
            
            showToast('Document deleted successfully!', 'success');
            
            // Reload documents to update both lists dynamically
            await loadDocuments();
            
        } catch (error) {
            showToast('Failed to delete document. Please try again.', 'error');
        }
    };
    
    // Load existing documents
    async function loadDocuments() {
        try {
            const response = await API.get('/api/documents/');
             currentDocuments = response.documents || [];
            
            // Clear lists first to remove spinners
            const uploadedDocsGrid = document.querySelector('.uploaded-docs-grid');
            const requiredDocsList = document.querySelector('.required-docs-list');
            if (uploadedDocsGrid) uploadedDocsGrid.innerHTML = '';
            if (requiredDocsList) requiredDocsList.innerHTML = '';
            
            // Render uploaded documents
            if (response.documents && response.documents.length > 0) {
                response.documents.forEach(doc => {
                    addUploadedDocument(doc);
                });
            } else {
                if (uploadedDocsGrid) {
                    uploadedDocsGrid.innerHTML = `
                        <div class="empty-state">
                            <i class="fa-solid fa-folder-open"></i>
                            <h3>No uploaded documents</h3>
                            <p>Your uploaded files will appear here</p>
                        </div>
                    `;
                }
            }
            
            // Render required documents checklist
            if (response.required_documents && response.required_documents.length > 0) {
                response.required_documents.forEach(reqDoc => {
                    addRequiredDocument(reqDoc);
                });
                
                const pendingCount = response.required_documents.filter(d => !d.uploaded).length;
                const badge = document.querySelector('.required-docs-section .badge');
                if (badge) {
                    badge.textContent = `${pendingCount} Pending`;
                    badge.className = `badge ${pendingCount > 0 ? 'badge-warning' : 'badge-success'}`;
                }
            } else {
                if (requiredDocsList) {
                    requiredDocsList.innerHTML = `
                        <div class="empty-state">
                            <i class="fa-solid fa-clipboard-check"></i>
                            <h3>No required documents</h3>
                            <p>No active applications needing documents</p>
                        </div>
                    `;
                }
                const badge = document.querySelector('.required-docs-section .badge');
                if (badge) {
                    badge.textContent = '0 Pending';
                    badge.className = 'badge badge-success';
                }
            }
            
        } catch (error) {
            console.error('Failed to load documents:', error);
        }
    }
    
    
    window.downloadAllDocuments = function () {
        if (!currentDocuments || currentDocuments.length === 0) {
            showToast('No documents to download', 'info');
            return;
        }
        currentDocuments.forEach((doc, index) => {
            setTimeout(() => {
                downloadDocument(doc.id);
            }, index * 600);
        });
    };

    const downloadAllBtn = document.getElementById('downloadAllBtn');
    if (downloadAllBtn) {
        downloadAllBtn.addEventListener('click', downloadAllDocuments);
    }

    // Load documents on page load
    loadDocuments();
});
