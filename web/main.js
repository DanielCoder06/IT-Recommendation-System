document.addEventListener("DOMContentLoaded", () => {
    const dropZone = document.getElementById("dropZone");
    const dropPrompt = document.getElementById("dropPrompt");
    const cvFileInput = document.getElementById("cvFile");
    const fileNameDisplay = document.getElementById("fileNameDisplay");
    const cvForm = document.getElementById("cvForm");

    // Xử lý kéo thả file vào vùng dropZone
    ["dragenter", "dragover"].forEach(event => {
        dropZone.addEventListener(event, (e) => {
            e.preventDefault();
            dropZone.classList.add("dragover");
        });
    });

    ["dragleave", "drop"].forEach(event => {
        dropZone.addEventListener(event, (e) => {
            e.preventDefault();
            dropZone.classList.remove("dragover");
        });
    });

    // Thả file
    dropZone.addEventListener("drop", (e) => {
        const files = e.dataTransfer.files;
        if (files && files.length > 0) {
            // Gán file vào input để submit form có thể đọc 
            cvFileInput.files = files;
            handleFile(files[0]);
        }
    });

    // Chọn file
    cvFileInput.addEventListener("change", (e) => {
        if (e.target.files && e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });

    function handleFile(file) {
        if (!file.name.toLowerCase().endsWith(".pdf")) {
            alert("Vui lòng chọn file CV định dạng .pdf");
            cvFileInput.value = "";
            fileNameDisplay.textContent = "";
            fileNameDisplay.style.display = "none";
            dropPrompt.style.display = "block";
            return;
        }
        // Ẩn dòng chữ hướng dẫn và hiện tên file đã chọn
        dropPrompt.style.display = "none";
        fileNameDisplay.textContent = file.name;
        fileNameDisplay.style.display = "inline-block";
    }

    const jobsDisplaySection = document.getElementById("jobsDisplaySection");
    const jobsSectionTitle = document.getElementById("jobsSectionTitle");
    const recommendCountText = document.getElementById("recommendCountText");
    const jobsRecommendGrid = document.getElementById("jobsRecommendGrid");

    // Xử lý gửi form (Tìm kiếm / Gợi ý 10 việc làm phù hợp)
    cvForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        if (!cvFileInput.files || cvFileInput.files.length === 0) {
            alert("Vui lòng cung cấp file CV của bạn trước khi tìm kiếm!");
            return;
        }

        const file = cvFileInput.files[0];
        const submitBtn = document.getElementById("btnSubmitCV");

        // Trạng thái đang tải dữ liệu
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = "Đang tìm kiếm...";
        }

        // Hiện vùng hiển thị kết quả và trạng thái đang phân tích
        if (jobsDisplaySection) {
            jobsDisplaySection.style.display = "block";
        }
        jobsSectionTitle.textContent = "Việc làm gợi ý cho bạn";
        recommendCountText.textContent = `(Đang phân tích CV: ${file.name}...)`;
        jobsRecommendGrid.style.display = "block";
        jobsRecommendGrid.innerHTML = `
            <div style="text-align: center; color: #666; padding: 40px; background: #fafafa; border: 1px dashed #ccc; border-radius: 6px;">
                Đang phân tích cấu trúc, kỹ năng CV và tìm kiếm công việc phù hợp nhất...
            </div>
        `;

        try {
            const formData = new FormData();
            formData.append("file", file);
            formData.append("exclude_senior", "true");
            formData.append("top_k", "10");

            const response = await fetch("/api/recommend-cv", {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                throw new Error("Không thể kết nối tới server");
            }

            const resData = await response.json();
            const jobs = resData.data || [];

            recommendCountText.textContent = `(Tìm thấy ${jobs.length} công việc phù hợp nhất theo CV: ${file.name})`;

            if (jobs.length === 0) {
                jobsRecommendGrid.innerHTML = `
                    <div style="grid-column: 1 / -1; text-align: center; color: #888; padding: 30px;">
                        Không tìm thấy công việc phù hợp với CV này.
                    </div>
                `;
                return;
            }

            // Render danh sách 10 công việc dạng bảng 
            jobsRecommendGrid.style.display = "block";
            jobsRecommendGrid.innerHTML = `
                <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                    <thead>
                        <tr style="background-color: #f2f2f2;">
                            <th style="padding: 10px; border: 1px solid #ccc; width: 60px; text-align: center;">Hạng</th>
                            <th style="padding: 10px; border: 1px solid #ccc;">Tên vị trí</th>
                            <th style="padding: 10px; border: 1px solid #ccc;">Công ty</th>
                            <th style="padding: 10px; border: 1px solid #ccc;">Địa điểm</th>
                            <th style="padding: 10px; border: 1px solid #ccc; text-align: center; width: 120px;">Chi tiết</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${jobs.map((job, index) => `
                            <tr>
                                <td style="padding: 10px; border: 1px solid #ccc; text-align: center; font-weight: bold; color: #28a745;">${index + 1}</td>
                                <td style="padding: 10px; border: 1px solid #ccc; font-weight: 500;">${job.title}</td>
                                <td style="padding: 10px; border: 1px solid #ccc;">${job.company}</td>
                                <td style="padding: 10px; border: 1px solid #ccc;">${job.location}</td>
                                <td style="padding: 10px; border: 1px solid #ccc; text-align: center;">
                                    <a href="${job.url}" target="_blank" style="color: #007bff; text-decoration: none; font-weight: 500;">Xem chi tiết</a>
                                </td>
                            </tr>
                        `).join("")}
                    </tbody>
                </table>
            `;

        } catch (error) {
            console.error("Lỗi tìm việc làm theo CV:", error);
            jobsRecommendGrid.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; color: red; padding: 30px;">
                    Không thể phân tích CV hoặc server đang bận. Vui lòng kiểm tra lại server.
                </div>
            `;
        } finally {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = "Tìm kiếm";
            }
        }
    });

    // Chuyển đổi giữa 2 Page: Upload & Gợi ý <-> Danh sách Job IT
    const tabRecommend = document.getElementById("tabRecommend");
    const tabAllJobs = document.getElementById("tabAllJobs");
    const pageRecommend = document.getElementById("pageRecommend");
    const pageAllJobs = document.getElementById("pageAllJobs");
    const jobsGrid = document.getElementById("jobsGrid");
    const jobsTotalText = document.getElementById("jobsTotalText");
    const pageInfoText = document.getElementById("pageInfoText");
    const btnPrevPage = document.getElementById("btnPrevPage");
    const btnNextPage = document.getElementById("btnNextPage");

    let currentPage = 1;
    let totalPages = 1;
    const limit = 9;

    tabRecommend.addEventListener("click", () => {
        tabRecommend.classList.add("active");
        tabAllJobs.classList.remove("active");
        pageRecommend.classList.add("active");
        pageAllJobs.classList.remove("active");
    });

    tabAllJobs.addEventListener("click", () => {
        tabAllJobs.classList.add("active");
        tabRecommend.classList.remove("active");
        pageAllJobs.classList.add("active");
        pageRecommend.classList.remove("active");

        // Tải trang 1 khi mở tab
        loadJobsFromBackend(currentPage);
    });

    // Nút "Xem thêm" chuyển sang tab Danh sách công việc IT
    const btnViewMoreJobs = document.getElementById("btnViewMoreJobs");
    if (btnViewMoreJobs) {
        btnViewMoreJobs.addEventListener("click", () => {
            tabAllJobs.click();
            window.scrollTo({ top: 0, behavior: "smooth" });
        });
    }

    // Sự kiện chuyển trang
    btnPrevPage.addEventListener("click", () => {
        if (currentPage > 1) {
            currentPage--;
            loadJobsFromBackend(currentPage);
        }
    });

    btnNextPage.addEventListener("click", () => {
        if (currentPage < totalPages) {
            currentPage++;
            loadJobsFromBackend(currentPage);
        }
    });

    // Nút cập nhật việc làm mới từ các nguồn (Crawl & Update DB)
    const btnUpdateJobs = document.getElementById("btnUpdateJobs");
    const updateStatusBanner = document.getElementById("updateStatusBanner");
    let updateBannerTimeout = null;

    function showUpdateBanner(message, type = "info", autoDismiss = false) {
        if (!updateStatusBanner) return;
        if (updateBannerTimeout) {
            clearTimeout(updateBannerTimeout);
            updateBannerTimeout = null;
        }
        updateStatusBanner.className = `update-status-banner ${type}`;
        updateStatusBanner.innerHTML = message;
        updateStatusBanner.style.display = "block";

        if (autoDismiss) {
            updateBannerTimeout = setTimeout(() => {
                updateStatusBanner.style.display = "none";
            }, 5000);
        }
    }

    if (btnUpdateJobs) {
        btnUpdateJobs.addEventListener("click", async () => {
            const originalText = btnUpdateJobs.innerHTML;
            btnUpdateJobs.disabled = true;
            btnUpdateJobs.innerHTML = "Đang cập nhật...";
            showUpdateBanner("Hệ thống đang kết nối và cào dữ liệu việc làm IT mới nhất từ các nguồn (Jobicy, Arbeitnow)... Vui lòng đợi trong giây lát.", "info");

            try {
                const response = await fetch("/api/jobs/update", {
                    method: "POST",
                });
                const resData = await response.json();

                if (resData.success) {
                    const d = resData.data;
                    showUpdateBanner(
                        `<strong>Cập nhật thành công!</strong> Tìm thấy <strong>${d.it_jobs_count}</strong> việc làm IT phù hợp, đã lưu/cập nhật <strong>${d.saved_jobs}</strong> việc làm vào hệ thống. (Tổng hiện có: ${d.active_jobs} việc làm).`,
                        "success",
                        true
                    );
                    loadJobsFromBackend(currentPage);
                } else {
                    showUpdateBanner(`<strong>Cập nhật thất bại:</strong> ${resData.error || "Server gặp lỗi khi cào dữ liệu"}`, "error");
                }
            } catch (err) {
                console.error("Lỗi khi cập nhật việc làm:", err);
                showUpdateBanner("<strong>Không thể kết nối tới server!</strong> Vui lòng khởi động lại server hoặc kiểm tra kết nối mạng.", "error");
            } finally {
                btnUpdateJobs.disabled = false;
                btnUpdateJobs.innerHTML = originalText;
            }
        });
    }

    // Hàm gọi FastAPI Backend
    async function loadJobsFromBackend(page = 1) {
        jobsGrid.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; color: #666; padding: 40px;">
                Đang tải dữ liệu công việc (Trang ${page})...
            </div>
        `;

        try {
            const response = await fetch(`http://127.0.0.1:8000/api/jobs?page=${page}&limit=${limit}`);
            if (!response.ok) {
                throw new Error("Không thể kết nối tới server");
            }
            const resData = await response.json();
            const jobs = resData.data || [];
            totalPages = resData.total_pages || 1;
            currentPage = resData.page || 1;

            jobsTotalText.textContent = `Tổng cộng: ${resData.total} việc làm`;
            pageInfoText.textContent = `Trang ${currentPage} / ${totalPages}`;

            btnPrevPage.disabled = (currentPage <= 1);
            btnNextPage.disabled = (currentPage >= totalPages);

            if (jobs.length === 0) {
                jobsGrid.innerHTML = `
                    <div style="grid-column: 1 / -1; text-align: center; color: #888; padding: 40px;">
                        Không tìm thấy công việc phù hợp.
                    </div>
                `;
                return;
            }

            // Đổ 9 job vào dạng Grid Card
            jobsGrid.innerHTML = jobs.map((job) => `
                <div class="job-card-item">
                    <div>
                        <div class="job-item-title">${job.title}</div>
                        <div class="job-item-meta"><strong>Công ty:</strong> ${job.company}</div>
                        <div class="job-item-meta"><strong>Địa điểm:</strong> ${job.location}</div>
                    </div>
                    <div class="job-item-footer">
                        <span style="font-size: 12px; color: #28a745;">Đang tuyển</span>
                        <a href="${job.url}" target="_blank">Xem chi tiết</a>
                    </div>
                </div>
            `).join("");

        } catch (error) {
            console.error("Lỗi tải jobs:", error);
            jobsGrid.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; color: red; padding: 40px;">
                    Hãy kiểm tra lại server.
                </div>
            `;
        }
    }
});
