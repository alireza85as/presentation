/**
 * Zen Editor Logic
 * Framework-free, Vanilla JS Class
 */
class ZenEditor {
    constructor() {
        this.config = window.APP_CONFIG;
        this.state = {
            article: { title: '', sections: [] },
            images: [],
            pdfUrl: null,
            loading: false,
            currentSectionIndex: null, // For modal editing
            pickerMode: false // If true, clicking an image selects it for current section
        };

        this.elements = {
            topicInput: document.getElementById('doc-topic'),
            sectionsList: document.getElementById('sections-list'),
            galleryGrid: document.getElementById('gallery-grid'),
            pickerGrid: document.getElementById('picker-grid'),
            tabs: document.querySelectorAll('.nav-item'),
            tabPanes: document.querySelectorAll('.tab-pane'),
            
            // Edit Modal
            editModal: document.getElementById('editor-modal'),
            modalTitleInput: document.getElementById('modal-input-title'),
            modalContentInput: document.getElementById('modal-input-content'),
            modalImageSelector: document.getElementById('modal-image-selector'),
            
            // Picker Modal
            pickerModal: document.getElementById('picker-modal'),
            
            // Finish Tab
            templateSelect: document.getElementById('template-select'),
            downloadLinks: document.getElementById('download-links'),
            miniPreview: document.getElementById('mini-preview'),
            
            // Conclusion
            conclusionInput: document.getElementById('conclusion-input')
        };

        this.init();
    }

    async init() {
        this.bindEvents();
        await this.loadContent();
        this.renderTemplates();
        
        // Auto-save loop
        setInterval(() => this.saveData(), 10000);
    }

    bindEvents() {
        // Tab Switching
        this.elements.tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const target = tab.dataset.tab;
                this.switchTab(target);
            });
        });

        // Add Section
        document.getElementById('btn-add-section').addEventListener('click', () => {
            this.state.article.sections.push({ title: 'بخش جدید', content: '', image: null });
            this.renderSections();
            this.openEditModal(this.state.article.sections.length - 1);
        });

        // Edit Modal Actions
        document.getElementById('btn-close-modal').addEventListener('click', () => this.closeEditModal());
        document.getElementById('btn-save-modal').addEventListener('click', () => {
            this.saveModalChanges();
            this.closeEditModal();
        });
        document.getElementById('btn-delete-section').addEventListener('click', () => {
            if(confirm('حذف این بخش؟')) {
                this.state.article.sections.splice(this.state.currentSectionIndex, 1);
                this.renderSections();
                this.closeEditModal();
                this.saveData();
            }
        });

        // Image Selection
        this.elements.modalImageSelector.addEventListener('click', () => {
            this.openPickerModal();
        });
        document.getElementById('btn-close-picker').addEventListener('click', () => {
            this.elements.pickerModal.classList.remove('open');
        });

        // Upload
        document.getElementById('upload-trigger').addEventListener('click', () => {
            document.getElementById('file-input').click();
        });
        document.getElementById('file-input').addEventListener('change', (e) => this.handleUpload(e));

        // Regenerate
        document.getElementById('btn-regenerate').addEventListener('click', () => this.regenerate());
        
        // Topic Input
        this.elements.topicInput.addEventListener('input', (e) => {
            this.state.article.title = e.target.value;
        });
        
        // Conclusion Input
        this.elements.conclusionInput.addEventListener('input', (e) => {
            this.state.article.conclusion = e.target.value;
        });
    }

    switchTab(tabName) {
        // Update Nav
        this.elements.tabs.forEach(t => t.classList.remove('active'));
        document.querySelector(`.nav-item[data-tab="${tabName}"]`).classList.add('active');

        // Update Panes
        this.elements.tabPanes.forEach(p => p.classList.remove('active'));
        document.getElementById(`tab-${tabName}`).classList.add('active');
    }

    // --- Data Loading ---

    async loadContent() {
        try {
            const res = await fetch(this.config.urls.content);
            const data = await res.json();
            
            // Merge defaults
            this.state.article = data.article || { title: '', sections: [], conclusion: '' };
            if (!this.state.article.sections) this.state.article.sections = [];
            if (!this.state.article.conclusion) this.state.article.conclusion = '';
            
            this.state.images = data.images || [];
            this.state.pdfUrl = data.pdf_url;
            
            // Initial Render
            this.renderSections();
            this.renderImages();
            
            // Load conclusion
            this.elements.conclusionInput.value = this.state.article.conclusion || '';
            
            if (this.state.pdfUrl) {
                this.elements.miniPreview.src = this.state.pdfUrl;
                this.updateDownloadLinks(this.state.pdfUrl);
            }
            
        } catch (e) {
            console.error(e);
            alert('خطا در بارگذاری محتوا');
        }
    }

    // --- Rendering ---

    renderSections() {
        const list = this.elements.sectionsList;
        list.innerHTML = '';
        
        this.state.article.sections.forEach((section, index) => {
            const card = document.createElement('div');
            card.className = 'section-card';
            
            // Improved image indicator
            let imageIndicator = '';
            if (section.image) {
                imageIndicator = '<div class="card-img-indicator"></div>';
            } else {
                imageIndicator = '<div class="card-img-indicator missing" title="بدون تصویر"></div>';
            }
            
            card.innerHTML = `
                <div class="drag-handle" title="جابجایی">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                        <circle cx="4" cy="3" r="1.5"/>
                        <circle cx="12" cy="3" r="1.5"/>
                        <circle cx="4" cy="8" r="1.5"/>
                        <circle cx="12" cy="8" r="1.5"/>
                        <circle cx="4" cy="13" r="1.5"/>
                        <circle cx="12" cy="13" r="1.5"/>
                    </svg>
                </div>
                ${imageIndicator}
                <div class="card-title">${section.title || 'بدون عنوان'}</div>
                <div class="card-preview">${section.content.substring(0, 50)}...</div>
            `;
            card.onclick = () => this.openEditModal(index);
            list.appendChild(card);
        });

        // Make Sortable
        new Sortable(list, {
            animation: 150,
            handle: '.drag-handle', // Only drag from handle
            ghostClass: 'sortable-ghost',
            dragClass: 'sortable-drag',
            onEnd: (evt) => {
                const item = this.state.article.sections.splice(evt.oldIndex, 1)[0];
                this.state.article.sections.splice(evt.newIndex, 0, item);
                this.saveData(); // Save order
            }
        });
    }

    renderImages() {
        const grid = this.elements.galleryGrid;
        const picker = this.elements.pickerGrid;
        
        const html = this.state.images.map(url => `
            <div class="gallery-thumb" data-url="${url}">
                <img src="${url}" loading="lazy">
                <button class="btn-del-img" data-url="${url}">&times;</button>
            </div>
        `).join('');

        grid.innerHTML = html;
        picker.innerHTML = html; // Reuse same HTML for picker

        // Bind Delete Events (Gallery Only)
        grid.querySelectorAll('.btn-del-img').forEach(btn => {
            btn.onclick = (e) => {
                e.stopPropagation();
                this.deleteImage(btn.dataset.url);
            };
        });
        
        // Bind Picker Events
        picker.querySelectorAll('.gallery-thumb').forEach(thumb => {
            thumb.onclick = () => {
                this.selectImageForSection(thumb.dataset.url);
            };
        });
        // Hide delete buttons in picker
        picker.querySelectorAll('.btn-del-img').forEach(b => b.style.display = 'none');
    }

    renderTemplates() {
        // Simple hardcoded templates for now
        const opts = [
            {id: 'classic', name: 'کلاسیک (رسمی و اداری)'},
            {id: 'modern', name: 'مدرن (شیک و مینیمال)'},
            {id: 'creative', name: 'خلاقانه (رنگی و جذاب)'}
        ];
        this.elements.templateSelect.innerHTML = opts.map(o => `<option value="${o.id}">${o.name}</option>`).join('');
    }

    // --- Modal Logic ---

    openEditModal(index) {
        this.state.currentSectionIndex = index;
        const section = this.state.article.sections[index];
        
        // console.log('Opening edit modal for section:', index);
        // console.log('Section data:', section);
        // console.log('Section image:', section.image);
        
        this.elements.modalTitleInput.value = section.title || '';
        this.elements.modalContentInput.value = section.content || '';
        this.updateModalImagePreview(section.image);
        
        this.elements.editModal.classList.add('open');
    }

    closeEditModal() {
        this.elements.editModal.classList.remove('open');
        this.state.currentSectionIndex = null;
    }

    saveModalChanges() {
        const index = this.state.currentSectionIndex;
        if (index === null) return;
        
        const section = this.state.article.sections[index];
        section.title = this.elements.modalTitleInput.value;
        section.content = this.elements.modalContentInput.value;
        // Image is updated directly via picker
        
        this.renderSections();
        this.saveData();
    }

    updateModalImagePreview(url) {
        const box = this.elements.modalImageSelector.querySelector('.img-preview-box');
        const hint = this.elements.modalImageSelector.querySelector('.img-hint');
        
        if (url) {
            box.innerHTML = `<img src="${url}">`;
            if (hint) hint.style.display = 'none';
        } else {
            box.innerHTML = '';
            if (hint) hint.style.display = 'block';
        }
    }

    openPickerModal() {
        this.elements.pickerModal.classList.add('open');
    }

    selectImageForSection(url) {
        const index = this.state.currentSectionIndex;
        if (index !== null) {
            this.state.article.sections[index].image = url;
            this.updateModalImagePreview(url);
            this.elements.pickerModal.classList.remove('open');
        }
    }

    // --- API Interactions ---

    async saveData() {
        document.getElementById('save-indicator').textContent = 'در حال ذخیره...';
        try {
            await fetch(this.config.urls.save, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.config.csrfToken
                },
                body: JSON.stringify({ article: this.state.article })
            });
            document.getElementById('save-indicator').textContent = 'ذخیره شد';
        } catch (e) {
            document.getElementById('save-indicator').textContent = 'خطا در ذخیره';
        }
    }

    async regenerate() {
        const btn = document.getElementById('btn-regenerate');
        const oldText = btn.textContent;
        btn.textContent = 'در حال ساخت...';
        btn.disabled = true;

        try {
            await this.saveData(); // Save first
            
            const res = await fetch(this.config.urls.regenerate, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.config.csrfToken
                },
                body: JSON.stringify({
                    article: this.state.article,
                    template: this.elements.templateSelect.value
                })
            });
            
            const data = await res.json();
            if (data.pdf_url) {
                 this.state.pdfUrl = data.pdf_url;
                 this.elements.miniPreview.src = data.pdf_url;
                 this.updateDownloadLinks(data.pdf_url);
                 alert('PDF با موفقیت ساخته شد');
            }
            
        } catch (e) {
            alert('خطا در بازسازی فایل');
        } finally {
            btn.textContent = oldText;
            btn.disabled = false;
        }
    }

    async handleUpload(e) {
        const files = e.target.files;
        if (!files.length) return;

        const formData = new FormData();
        for (let i = 0; i < files.length; i++) {
            formData.append('image', files[i]);
        }

        try {
            const res = await fetch(this.config.urls.upload, {
                method: 'POST',
                headers: { 'X-CSRFToken': this.config.csrfToken },
                body: formData
            });
            const data = await res.json();
            if (data.image_url) {
                this.state.images.push(data.image_url);
                this.renderImages();
            }
        } catch (e) {
             alert('خطا در آپلود');
        }
    }

    async deleteImage(url) {
        if (!confirm('حذف شود؟')) return;
        const filename = url.split('/').pop();
        await fetch(this.config.urls.deleteImage, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.config.csrfToken
            },
            body: JSON.stringify({ filename })
        });
        
        this.state.images = this.state.images.filter(u => u !== url);
        this.renderImages();
    }

    updateDownloadLinks(pdfUrl) {
        let html = `<a href="${pdfUrl}" target="_blank" class="download-btn">دانلود PDF</a>`;
        this.elements.downloadLinks.innerHTML = html;
    }
}

// Start
document.addEventListener('DOMContentLoaded', () => new ZenEditor());
